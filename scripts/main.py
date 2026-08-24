"""
Orchestrator for one pipeline run (recipe or workout). Runs headlessly in
GitHub Actions -- generates images via Higgsfield's REST API, renders
carousels locally, and schedules posts via Buffer's GraphQL API.

Split into two phases (see workflow YAML), because Buffer needs to fetch
each image from its public raw.githubusercontent.com URL -- which only
exists AFTER the rendered images are committed and pushed. Running
"schedule" before that push happens would hand Buffer a URL that 404s.

  generate: renders all of today's carousels, writes a manifest.json per
            pipeline listing image paths + captions + scheduled times.
            The workflow then commits + pushes these images.
  schedule: reads the manifest (now safely live on raw.githubusercontent
            .com) and creates the actual Buffer posts, then updates
            state/*.json and bumps the rotation index.

Usage: python scripts/main.py generate recipe
       python scripts/main.py schedule recipe
"""
import os
import sys
import json
import datetime

sys.path.insert(0, os.path.dirname(__file__))

import higgsfield_client
import buffer_client
import make_slides

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PIPELINES = {
    "recipe": {
        "state_path": os.path.join(REPO_ROOT, "state", "recipe_state.json"),
        "output_subdir": "output/recipe",
        "channels": ["ai_facts4u", "daily_ai_factz", "Factual days"],
        "ideas_module": "recipe_ideas",
        "ideas_attr": "RECIPES",
        "prompts_module": "image_prompts_recipe",
        "prompts_func": "build_prompts_for_recipe",
    },
    "workout": {
        "state_path": os.path.join(REPO_ROOT, "state", "workout_state.json"),
        "output_subdir": "output/workout",
        "channels": ["30secfitness", "30sec_fitness", "Crunch time"],
        "ideas_module": "workout_ideas",
        "ideas_attr": "WORKOUTS",
        "prompts_module": "image_prompts_workout",
        "prompts_func": "build_prompts_for_workout",
    },
}


def manifest_path(cfg):
    return os.path.join(REPO_ROOT, cfg["output_subdir"], "manifest.json")


def load_state(path):
    with open(path) as f:
        return json.load(f)


def save_state(path, state):
    with open(path, "w") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def raw_url(repo_relative_path):
    repo = os.environ.get("GITHUB_REPOSITORY")  # "owner/repo"
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    if not repo:
        raise RuntimeError("GITHUB_REPOSITORY env var not set -- are you running outside GitHub Actions?")
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{repo_relative_path}"


def next_scheduled_times(state, count):
    """Returns `count` ISO8601 UTC timestamps, continuing from state['scheduled_up_to'],
    stepping through state['daily_time_slots_uk'] (approximated as UTC -- London is
    UTC+0 in winter/UTC+1 in summer; good enough for a daily cadence, not
    minute-precise)."""
    slots = state["daily_time_slots_uk"]
    last = datetime.datetime.fromisoformat(state["scheduled_up_to"].replace("Z", "+00:00"))
    day = last.date() + datetime.timedelta(days=1)
    times = []
    for i in range(count):
        slot = slots[i % len(slots)]
        hh, mm = [int(x) for x in slot.split(":")]
        dt = datetime.datetime(day.year, day.month, day.day, hh, mm, tzinfo=datetime.timezone.utc)
        times.append(dt)
        if (i + 1) % len(slots) == 0:
            day = day + datetime.timedelta(days=1)
    return times


def phase_generate(name):
    cfg = PIPELINES[name]
    state = load_state(cfg["state_path"])

    ideas_module = __import__(cfg["ideas_module"])
    bank = getattr(ideas_module, cfg["ideas_attr"])
    prompts_module = __import__(cfg["prompts_module"])
    build_prompts = getattr(prompts_module, cfg["prompts_func"])

    posts_per_day = state.get("posts_per_day", 3)
    count = posts_per_day
    start_index = state["last_day_index"] + 1

    scheduled_times = next_scheduled_times(state, count)
    today_tag = datetime.datetime.utcnow().strftime("%Y%m%d")

    manifest_items = []

    for i in range(count):
        bank_index = (start_index + i) % len(bank)
        item = bank[bank_index]
        slug = item["title"].lower().replace(" ", "_").replace("(", "").replace(")", "").replace("/", "-")[:40]
        item_out_dir = os.path.join(REPO_ROOT, cfg["output_subdir"], f"{today_tag}_{slug}")
        os.makedirs(item_out_dir, exist_ok=True)

        prompts = build_prompts(item)
        photo_paths = []
        for slide_i, prompt in enumerate(prompts, start=1):
            out_path = os.path.join(item_out_dir, f"source_{slide_i}.png")
            try:
                higgsfield_client.generate_image(prompt, out_path)
                photo_paths.append(out_path)
            except higgsfield_client.GenerationBlocked:
                print(f"[SAFETY] Slide {slide_i} of '{item['title']}' was flagged nsfw by Higgsfield -- "
                      f"skipping this photo, slide will render on a placeholder background instead.")
                photo_paths.append(None)
            except higgsfield_client.GenerationFailed as e:
                print(f"[WARN] Slide {slide_i} of '{item['title']}' failed to generate: {e} -- using placeholder.")
                photo_paths.append(None)

        slide_paths = make_slides.render_carousel(item, bank_index, item_out_dir, photo_paths=photo_paths)
        repo_relative_paths = [os.path.relpath(p, REPO_ROOT) for p in slide_paths]

        manifest_items.append({
            "title": item["title"],
            "bank_index": bank_index,
            "text": f"{item['caption']}\n\n{item['hashtags']}",
            "image_repo_paths": repo_relative_paths,
            "scheduled_at": scheduled_times[i].strftime("%Y-%m-%dT%H:%M:%SZ"),
        })

    manifest = {
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "start_index": start_index,
        "count": count,
        "final_scheduled_up_to": scheduled_times[-1].strftime("%Y-%m-%dT%H:%M:%SZ"),
        "items": manifest_items,
    }
    os.makedirs(os.path.dirname(manifest_path(cfg)), exist_ok=True)
    with open(manifest_path(cfg), "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"[OK] Generated {count} carousels for '{name}'. Manifest written to {manifest_path(cfg)}")


def phase_schedule(name):
    cfg = PIPELINES[name]
    state = load_state(cfg["state_path"])

    with open(manifest_path(cfg)) as f:
        manifest = json.load(f)

    for item in manifest["items"]:
        image_urls = [raw_url(p) for p in item["image_repo_paths"]]
        for channel_name in cfg["channels"]:
            try:
                buffer_client.create_post(channel_name, item["text"], image_urls, item["scheduled_at"])
                print(f"[OK] Scheduled '{item['title']}' to {channel_name} for {item['scheduled_at']}")
            except Exception as e:
                print(f"[ERROR] Failed to schedule '{item['title']}' to {channel_name}: {e}")

    state["last_day_index"] = manifest["start_index"] + manifest["count"] - 1
    state["scheduled_up_to"] = manifest["final_scheduled_up_to"]
    state["last_run_at"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    state["last_run_slot"] = "github_actions_autonomous_bot"
    save_state(cfg["state_path"], state)

    # manifest served its purpose; remove so it doesn't get committed/confused with next run
    os.remove(manifest_path(cfg))


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("generate", "schedule") or sys.argv[2] not in PIPELINES:
        print(f"Usage: python main.py <generate|schedule> <{'|'.join(PIPELINES)}>")
        sys.exit(1)
    phase, pipeline = sys.argv[1], sys.argv[2]
    (phase_generate if phase == "generate" else phase_schedule)(pipeline)
