"""
Dog-fight video pipeline: 3 episodes a day.

  generate: for today's 3 matchups -> start frame (Grok Image 2.0 with the
            locked reference images) -> 15s 720p video (Seedance 2.0
            image-to-video, native audio) -> saves MP4s + manifest.json.
            The workflow then commits + pushes the MP4s.
  schedule: reads the manifest, posts each video to every channel in
            CHANNELS via Buffer (video asset, IG as a Reel), then advances
            state/dogfight_state.json.

Usage: python scripts/dogfight.py generate
       python scripts/dogfight.py schedule
"""
import os
import sys
import json
import datetime

sys.path.insert(0, os.path.dirname(__file__))

import hf_api
import buffer_client
import dogfight_bank as bank

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STATE_PATH = os.path.join(REPO_ROOT, "state", "dogfight_state.json")
OUTPUT_SUBDIR = "output/dogfight"
MANIFEST_PATH = os.path.join(REPO_ROOT, OUTPUT_SUBDIR, "manifest.json")
TOKEN_ENV = "BUFFER_ACCESS_TOKEN_DOGS"


def load_state():
    with open(STATE_PATH) as f:
        return json.load(f)


def save_state(state):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def uk_slot_to_utc(day, hhmm):
    """UK local time -> UTC, handling BST/GMT properly."""
    from zoneinfo import ZoneInfo
    hh, mm = [int(x) for x in hhmm.split(":")]
    local = datetime.datetime(day.year, day.month, day.day, hh, mm, tzinfo=ZoneInfo("Europe/London"))
    return local.astimezone(datetime.timezone.utc)


def next_post_day(state):
    """Posts go out the day after the last scheduled day, but never in the past."""
    tomorrow = datetime.datetime.now(datetime.timezone.utc).date() + datetime.timedelta(days=1)
    last = state.get("scheduled_up_to")
    if not last:
        return tomorrow
    last_day = datetime.datetime.fromisoformat(last.replace("Z", "+00:00")).date()
    return max(last_day + datetime.timedelta(days=1), tomorrow)


def ringside(exclude_key, crew):
    return ", ".join(v["ringside"] for k, v in crew.items() if k != exclude_key)


def image_prompt(m):
    r, p = bank.ROUGH[m["rough"]], bank.POSH[m["posh"]]
    return (
        "Photorealistic cinematic still styled like a retro arcade fighting game, 9:16 vertical. "
        "Use reference image 1 exactly for the boxing ring, setting, lighting, crowd layout and HUD style, "
        "reference image 2 for the dog character designs, and reference image 3 for the Doberman. "
        "A boxing ring in the middle of a posh new-build estate green, overcast evening, red-brick houses and a "
        "'No Ball Games' sign in the background, red ropes, white canvas, floodlights on poles at each corner. "
        "All dogs are anthropomorphic, standing upright on hind legs with human-like posture, real dog faces and fur.\n\n"
        "FIGHTERS, centred in the lower two-thirds of the frame, side-on to the camera, facing each other in classic "
        "fighting-game stance, knees bent, fists up, mid-bounce:\n"
        f"FRAME LEFT: {r['fighter']}, eyes locked on his opponent.\n"
        f"FRAME RIGHT: {p['fighter']}.\n\n"
        "RINGSIDE, behind the ropes, faces visible: on the left side the rough crew (the big black-and-tan Doberman in "
        f"the brown sheepskin coat and gold chain in the centre, {ringside(m['rough'], bank.ROUGH)}) shouting and pointing. "
        f"On the right side the posh crew ({ringside(m['posh'], bank.POSH)}) looking tense.\n\n"
        "HUD OVERLAY, retro arcade fighting-game style: at the very top of the frame, two long yellow health bars with "
        "red backing side by side, each starting from the outer edge and meeting at a small round timer showing '99' "
        f"in the centre. Under the left bar, bold white pixel-style text: '{r['hud']}'. Under the right bar: '{p['hud']}'. "
        "In the centre of the frame between the fighters, huge bold red-and-yellow angled text with a black outline "
        "and a motion-blur streak: 'FIGHT!'\n\n"
        "Vivid, punchy colour grade with saturated reds and yellows, sharp detail, 35mm lens at the fighters' chest "
        "height, deep focus. No humans. No other text besides the HUD."
    )


def video_prompt(m, finisher_template):
    r, p = bank.ROUGH[m["rough"]], bank.POSH[m["posh"]]
    winner, loser = (r, p) if m.get("winner", "rough") == "rough" else (p, r)
    w, l = winner["name"].replace("the ", "", 1), loser["name"].replace("the ", "", 1)
    loser_hair = loser.get("hair", "ears")
    finisher = finisher_template.format(loser=l)
    return (
        "Animate this exact frame as a photorealistic kickboxing match with a retro arcade fighting-game HUD. Keep every "
        f"character, outfit, the ring, the posh estate background and the HUD (two yellow health bars at the top, "
        f"'{r['hud']}' left, '{p['hud']}' right, round timer in the middle) identical to the start image. Camera stays "
        "side-on like a fighting game, with a small camera shake on each impact. All dogs stand upright with real human "
        "kickboxing technique, fast and athletic, and keep fully realistic dog faces, fur, jowls and expressions, filmed "
        "like a real televised fight broadcast. Realistic physics and weight on every hit. Everything plays at REAL SPEED "
        "except the single final finishing blow, which is the only slow-motion moment. Sport kickboxing in padded gloves, "
        "no blood, no injuries.\n\n"
        "0:00-3:00 COUNTDOWN: The 'FIGHT!' text is replaced by a huge bold red-and-yellow '3' that slams onto the centre "
        "of the screen, then '2', then '1', each with a flash and a deep arcade announcer voice counting "
        "'Three... two... one...'. Both fighters bounce on the spot, gloves up, staring each other down.\n\n"
        "3:00-4:00: Huge angled 'FIGHT!' text bursts onto the screen with a flash and the announcer shouts 'FIGHT!', then "
        "flies off. The round timer starts counting down.\n\n"
        f"4:00-6:00 (real speed): The {l} snaps a fast jab that clips the {w}'s face. The {w}'s head jolts back slightly, "
        f"his jowls ripple. The {w}'s health bar drops a little. He shakes his head and grins.\n\n"
        f"6:00-8:00 (real speed): The {l} throws a high kick. The {w} blocks it with his forearm with a heavy thud and "
        f"answers instantly with a hard low kick to the {l}'s thigh. The {l}'s leg buckles and his {loser_hair} shakes "
        "from the impact. Health bar drops.\n\n"
        f"8:00-11:00 (real speed): The {w} steps forward with a fast combo: jab to the face, right cross to the face, then "
        f"a body hook. Each one lands with a real glove thud, the {l}'s head snapping back and sideways, his {loser_hair} "
        "whipping, his lips and cheeks rippling, sweat spraying. He stumbles back into the ropes, wobbly. His health bar "
        "is nearly empty and flashing red.\n\n"
        f"11:00-13:30 (SLOW MOTION, the only slow-motion moment): The {l} bounces off the ropes toward the {w}. The {w} "
        f"lands {finisher}. Extreme slow motion: the {l}'s whole face ripples and compresses, cheeks and jowls rolling, "
        f"his {loser_hair} flying outward, a big arc of sweat and slobber spraying off and glittering in the floodlights, "
        "his body lifting off the canvas.\n\n"
        f"13:30-15:00 (real speed): The {l} drops flat onto the canvas, out cold. His health bar empties completely. Huge "
        "red-and-yellow 'K.O.!' text slams onto the centre of the screen and the announcer bellows 'K.O.!'. The "
        f"{w} raises both gloves. Ringside, the crowd erupts; the Doberman nods once.\n\n"
        "Audio: deep arcade announcer voice for the countdown, 'FIGHT!' and 'K.O.!', heavy realistic glove and kick "
        "impact thuds, fighters' breathing and grunts, rope creak, a deep slowed-down whoosh and boom on the slow-motion "
        "finisher, roaring crowd, energetic retro arcade fighting-game music."
    )


def caption(m, state):
    r, p = bank.ROUGH[m["rough"]], bank.POSH[m["posh"]]
    template = state.get("caption_template", "{rough} vs {posh} 🥊 Who's next?")
    return template.format(rough=r["hud"].title(), posh=p["hud"].title()) + "\n\n" + state.get("hashtags", "")


def phase_generate():
    state = load_state()
    count = state.get("posts_per_day", 3)
    start = state["last_index"] + 1
    day = next_post_day(state)
    slots = state["daily_time_slots_uk"]
    tag = datetime.datetime.utcnow().strftime("%Y%m%d")

    items = []
    for i in range(count):
        idx = (start + i) % len(bank.MATCHUPS)
        m = bank.MATCHUPS[idx]
        finisher = bank.FINISHERS[(start + i) % len(bank.FINISHERS)]
        out_dir = os.path.join(REPO_ROOT, OUTPUT_SUBDIR, f"{tag}_{i + 1}_{m['rough']}_vs_{m['posh']}")
        items.append({"index": idx, "matchup": m, "finisher": finisher, "out_dir": out_dir,
                      "slot": slots[i % len(slots)]})

    print(f"[INFO] Generating {count} start frames...")
    img_jobs = [{"prompt": image_prompt(it["matchup"]), "reference_urls": bank.REFERENCE_URLS,
                 "out_path": os.path.join(it["out_dir"], "start.png")} for it in items]
    img_results, img_errors = hf_api.run_concurrent(hf_api.generate_image, img_jobs)

    print(f"[INFO] Generating videos...")
    vid_jobs, vid_map = [], []
    for i, it in enumerate(items):
        if img_results[i] is None:
            print(f"[WARN] Start frame failed for {it['matchup']}: {img_errors[i]}")
            continue
        vid_jobs.append({"prompt": video_prompt(it["matchup"], it["finisher"]), "image_url": img_results[i][1],
                         "out_path": os.path.join(it["out_dir"], "episode.mp4"),
                         "duration": state.get("duration", 15), "resolution": state.get("resolution", "720p")})
        vid_map.append(i)
    vid_results, vid_errors = hf_api.run_concurrent(hf_api.generate_video, vid_jobs)

    errors = [e for e in img_errors + vid_errors if e is not None]
    hard = [e for e in errors if not isinstance(e, hf_api.GenerationBlocked)]
    done = []
    for j, i in enumerate(vid_map):
        if vid_results[j] is None:
            print(f"[WARN] Video failed for {items[i]['matchup']}: {vid_errors[j]}")
            continue
        it = items[i]
        done.append({
            "title": f"{it['matchup']['rough']} vs {it['matchup']['posh']}",
            "text": caption(it["matchup"], state),
            "video_repo_path": os.path.relpath(vid_results[j], REPO_ROOT),
            "scheduled_at": uk_slot_to_utc(day, it["slot"]).strftime("%Y-%m-%dT%H:%M:%SZ"),
        })

    if not done:
        raise RuntimeError(f"No episodes generated ({len(hard)} hard failures, {len(errors) - len(hard)} nsfw blocks). "
                           f"First error: {errors[0] if errors else 'none'}. If this is a credits/auth error, check "
                           "cloud.higgsfield.ai billing and the HIGGSFIELD_API_KEY_ID/SECRET secrets.")
    if hard:
        print(f"[WARN] {len(hard)} generation(s) failed; posting the {len(done)} that worked.")

    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    with open(MANIFEST_PATH, "w") as f:
        json.dump({"start_index": start, "count": count, "day": day.isoformat(), "items": done}, f, indent=2)
    print(f"[OK] {len(done)}/{count} episodes ready for {day.isoformat()}.")


def phase_schedule():
    state = load_state()
    channels = state.get("channels") or []
    if not channels:
        raise RuntimeError("No Buffer channels set -- add channel names to 'channels' in state/dogfight_state.json.")
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    repo = os.environ["GITHUB_REPOSITORY"]
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    ok = attempts = 0
    for item in manifest["items"]:
        url = f"https://raw.githubusercontent.com/{repo}/{branch}/{item['video_repo_path']}"
        for ch in channels:
            attempts += 1
            try:
                buffer_client.create_video_post(ch, item["text"], url, item["scheduled_at"], TOKEN_ENV)
                print(f"[OK] Scheduled {item['title']} to {ch} at {item['scheduled_at']}")
                ok += 1
            except Exception as e:
                print(f"[ERROR] {item['title']} -> {ch}: {e}")
    print(f"[SUMMARY] {ok}/{attempts} posts scheduled.")
    if ok == 0:
        raise RuntimeError("Every Buffer post failed -- state NOT advanced. See [ERROR] lines above.")

    state["last_index"] = manifest["start_index"] + manifest["count"] - 1
    state["scheduled_up_to"] = uk_slot_to_utc(datetime.date.fromisoformat(manifest["day"]),
                                              state["daily_time_slots_uk"][-1]).strftime("%Y-%m-%dT%H:%M:%SZ")
    state["last_run_at"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    save_state(state)
    os.remove(MANIFEST_PATH)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("generate", "schedule", "preview"):
        print("Usage: python scripts/dogfight.py <generate|schedule|preview>")
        sys.exit(1)
    if sys.argv[1] == "preview":
        st = load_state()
        m = bank.MATCHUPS[(st["last_index"] + 1) % len(bank.MATCHUPS)]
        print(image_prompt(m), "\n\n----\n\n", video_prompt(m, bank.FINISHERS[0]), "\n\n----\n\n", caption(m, st))
    else:
        {"generate": phase_generate, "schedule": phase_schedule}[sys.argv[1]]()
