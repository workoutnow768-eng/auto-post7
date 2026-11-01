"""
Manual Buffer upload for hand-made dog-fight videos.

Triggered by .github/workflows/buffer-upload.yml (workflow_dispatch). The
`posts` input is a JSON list:
  [{"video_url": "https://...mp4", "caption": "...", "scheduled_at": "2026-11-02T12:00:00Z"}, ...]

  download: fetch each MP4 into output/buffer_uploads/ and write a manifest
            (the workflow then commits + pushes so Buffer can read the file
            from raw.githubusercontent.com -- same pattern as the other bots).
  schedule: post each video to every channel in BUFFER_CHANNELS.

Token: BUFFER_ACCESS_TOKEN_DOGS repo secret (never in code or chat).
"""
import os
import re
import sys
import json
import datetime

import requests

sys.path.insert(0, os.path.dirname(__file__))
import buffer_client  # noqa: E402

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_DIR = os.path.join(REPO_ROOT, "output", "buffer_uploads")
MANIFEST = os.path.join(OUT_DIR, "manifest.json")
TOKEN_ENV = "BUFFER_ACCESS_TOKEN_DOGS"


def download():
    posts = json.loads(os.environ["POSTS_JSON"])
    if not posts:
        raise RuntimeError("No posts given.")
    os.makedirs(OUT_DIR, exist_ok=True)
    stamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    items = []
    for i, p in enumerate(posts, start=1):
        datetime.datetime.fromisoformat(p["scheduled_at"].replace("Z", "+00:00"))  # validate
        resp = requests.get(p["video_url"], timeout=300)
        resp.raise_for_status()
        path = os.path.join(OUT_DIR, f"{stamp}_{i}.mp4")
        with open(path, "wb") as f:
            f.write(resp.content)
        print(f"[OK] downloaded {len(resp.content) // 1024} KB -> {os.path.relpath(path, REPO_ROOT)}")
        items.append({"repo_path": os.path.relpath(path, REPO_ROOT), "caption": p["caption"],
                      "scheduled_at": p["scheduled_at"]})
    with open(MANIFEST, "w") as f:
        json.dump(items, f, indent=2)


def schedule():
    channels = [c.strip() for c in os.environ.get("BUFFER_CHANNELS", "").split(",") if c.strip()]
    if not channels:
        raise RuntimeError("No Buffer channel names given.")
    with open(MANIFEST) as f:
        items = json.load(f)
    repo = os.environ["GITHUB_REPOSITORY"]
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    ok = total = 0
    for it in items:
        url = f"https://raw.githubusercontent.com/{repo}/{branch}/{it['repo_path']}"
        for ch in channels:
            total += 1
            try:
                buffer_client.create_video_post(ch, it["caption"], url, it["scheduled_at"], TOKEN_ENV)
                print(f"[OK] scheduled {it['repo_path']} -> {ch} at {it['scheduled_at']}")
                ok += 1
            except Exception as e:  # report every failure, keep going
                print(f"[ERROR] {it['repo_path']} -> {ch}: {e}")
    print(f"[SUMMARY] {ok}/{total} scheduled")
    os.remove(MANIFEST)
    if ok < total:
        raise RuntimeError(f"{total - ok} Buffer post(s) failed -- see [ERROR] lines.")


if __name__ == "__main__":
    {"download": download, "schedule": schedule}[sys.argv[1]]()
