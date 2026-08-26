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
import re
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
        # "Factual days" (the YouTube channel) is intentionally excluded --
        # confirmed 2026-08-26 in the manual Buffer web flow that Buffer
        # requires video content for YouTube and blocks image-only carousels
        # with "Please include a video." This pipeline only generates image
        # carousels, so Factual days should only be added back once a
        # video-capable path exists.
        "channels": ["ai_facts4u", "daily_ai_factz"],
        "ideas_module": "recipe_ideas",
        "ideas_attr": "RECIPES",
        "prompts_module": "image_prompts_recipe",
        "prompts_func": "build_prompts_for_recipe",
        # Separate Buffer account (podcasterclips) from the workout pipeline
        # -- FIX 2026-08-26: previously both pipelines shared one
        # BUFFER_ACCESS_TOKEN secret, which meant the recipe pipeline was
        # silently querying the WORKOUT account's channels and failing
        # 100% of the time. See buffer_client.py's module docstring.
        "buffer_token_env": "BUFFER_ACCESS_TOKEN_RECIPE",
    },
    "workout": {
        "state_path": os.path.join(REPO_ROOT, "state", "workout_state.json"),
        "output_subdir": "output/workout",
        "channels": ["30secfitness", "30sec_fitness", "Crunch time"],
        "ideas_module": "workout_ideas",
        "ideas_attr": "WORKOUTS",
        "prompts_module": "image_prompts_workout",
        "prompts_func": "build_prompts_for_workout",
        # Separate Buffer account (workoutnow768) from the recipe pipeline.
        "buffer_token_env": "BUFFER_ACCESS_TOKEN_WORKOUT",
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
        # FIX 2026-08-26 (round 3): titles with punctuation like "?" or ":"
        # (e.g. "Myth vs Fact: Does Cardio Kill Gains?") produced a folder
        # name containing that punctuation, which broke the
        # raw.githubusercontent.com URL handed to Buffer -- a bare "?" in a
        # URL starts the query string, silently truncating the path before
        # "/slide_1.png". Confirmed via a live Actions run log (run #7):
        # "Buffer rejected the post ... Image could not be read from its
        # URL." for exactly that item, while titles without punctuation
        # scheduled fine. Now strips everything except lowercase
        # letters/digits/underscores instead of only stripping parens.
        slug = re.sub(r"[^a-z0-9_]+", "", item["title"].lower().replace(" ", "_"))
        slug = re.sub(r"_+", "_", slug).strip("_")[:40]
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

    success_count = 0
    attempt_count = 0
    for item in manifest["items"]:
        image_urls = [raw_url(p) for p in item["image_repo_paths"]]
        for channel_name in cfg["channels"]:
            attempt_count += 1
            try:
                buffer_client.create_post(
                    channel_name, item["text"], image_urls, item["scheduled_at"], cfg["buffer_token_env"]
                )
                print(f"[OK] Scheduled '{item['title']}' to {channel_name} for {item['scheduled_at']}")
                success_count += 1
            except Exception as e:
                print(f"[ERROR] Failed to schedule '{item['title']}' to {channel_name}: {e}")

    print(f"[SUMMARY] {success_count}/{attempt_count} posts scheduled successfully.")

    if success_count == 0:
        # Never silently advance the rotation index / scheduled_up_to when
        # NOTHING actually got posted -- confirmed 2026-08-24 this can
        # happen (every create_post call failed on a bad API shape) while
        # the workflow still reported "Success" overall, which would have
        # silently burned a day's worth of content bank entries and left a
        # real gap in the posting schedule. Fail loudly instead so the
        # GitHub Actions run shows red and the manifest is left in place
        # for inspection/retry -- state is NOT updated.
        raise RuntimeError(
            f"All {attempt_count} Buffer post attempts failed for '{name}' -- "
            f"NOT advancing state (last_day_index/scheduled_up_to unchanged). "
            f"See [ERROR] lines above for details."
        )

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
