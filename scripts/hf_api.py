"""
Generic client for Higgsfield's model API (api.higgsfield.ai), used by the
dog-fight video pipeline. Kept separate from higgsfield_client.py so the
existing recipe/workout pipelines are untouched.

Docs (checked 2026-10-03):
  - Auth:   Authorization: Key <KEY_ID>:<KEY_SECRET>
  - Flow:   POST <model endpoint> -> {status_url} -> poll -> completed
  - Image:  POST /xai/grok-imagine-image-2.0
            {prompt, aspect_ratio, resolution, quality, image_urls[0..10]}
            completed -> images[0].url
  - Video:  POST /bytedance/seedance-2.0/image-to-video
            {image_url, prompt, duration 4-15, resolution, generate_audio}
            completed -> video.url
Terminal statuses: completed, failed, nsfw, canceled.

Same safety rule as the rest of the repo: an "nsfw" result is NEVER used.
"""
import os
import time
import concurrent.futures

import requests

BASE_URL = os.environ.get("HIGGSFIELD_API_BASE", "https://api.higgsfield.ai")

IMAGE_ENDPOINT = f"{BASE_URL}/xai/grok-imagine-image-2.0"
VIDEO_ENDPOINT = f"{BASE_URL}/bytedance/seedance-2.0/image-to-video"


class GenerationBlocked(Exception):
    """Higgsfield flagged the job as nsfw -- never use the result."""


class GenerationFailed(Exception):
    pass


def _auth():
    return {
        "Authorization": f"Key {os.environ['HIGGSFIELD_API_KEY_ID']}:{os.environ['HIGGSFIELD_API_KEY_SECRET']}"
    }


def _submit(endpoint, body):
    resp = requests.post(
        endpoint,
        headers={**_auth(), "Content-Type": "application/json", "Accept": "application/json"},
        json=body,
        timeout=60,
    )
    if not resp.ok:
        raise GenerationFailed(f"HTTP {resp.status_code} from {endpoint}: {resp.text[:500]}")
    data = resp.json()
    if not data.get("status_url"):
        raise GenerationFailed(f"No status_url in response: {data}")
    return data["status_url"]


def _poll(status_url, timeout, interval=10):
    waited = 0
    while waited < timeout:
        resp = requests.get(status_url, headers=_auth(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status")
        if status == "completed":
            return data
        if status == "nsfw":
            raise GenerationBlocked(f"Flagged nsfw: {data}")
        if status in ("failed", "canceled"):
            raise GenerationFailed(f"Ended with status={status}: {data}")
        time.sleep(interval)
        waited += interval
    raise GenerationFailed(f"Timed out after {timeout}s waiting on {status_url}")


def _download(url, out_path):
    resp = requests.get(url, timeout=300)
    resp.raise_for_status()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(resp.content)
    return out_path


def _run(endpoint, body, timeout, pick_url, retries=2):
    """Submit -> poll -> return the output URL. Retries transient failures,
    never retries an nsfw block (raises GenerationBlocked)."""
    last = None
    for _ in range(retries):
        try:
            data = _poll(_submit(endpoint, body), timeout)
            url = pick_url(data)
            if not url:
                raise GenerationFailed(f"Completed but no output url: {data}")
            return url
        except GenerationBlocked:
            raise
        except (GenerationFailed, requests.RequestException) as e:
            last = e
            time.sleep(5)
    raise GenerationFailed(f"Failed after {retries} attempts: {last}")


def generate_image(prompt, reference_urls, out_path, aspect_ratio="9:16", resolution="2k"):
    """Returns (local_path, hosted_url). hosted_url is Higgsfield's CDN copy,
    which is passed straight into the video step."""
    body = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
        "quality": "medium",
        "image_urls": list(reference_urls)[:10],
    }
    url = _run(IMAGE_ENDPOINT, body, timeout=600,
               pick_url=lambda d: ((d.get("images") or [{}])[0]).get("url"))
    return _download(url, out_path), url


def generate_video(prompt, image_url, out_path, duration=15, resolution="720p", generate_audio=True):
    body = {
        "image_url": image_url,
        "prompt": prompt,
        "duration": duration,
        "resolution": resolution,
        "generate_audio": generate_audio,
    }
    url = _run(VIDEO_ENDPOINT, body, timeout=1800,
               pick_url=lambda d: (d.get("video") or {}).get("url"))
    return _download(url, out_path)


def run_concurrent(fn, jobs, max_workers=3):
    """jobs: list of kwargs dicts for fn. Returns (results, errors) in order."""
    results, errors = [None] * len(jobs), [None] * len(jobs)
    if not jobs:
        return results, errors

    def one(i, kw):
        try:
            return i, fn(**kw), None
        except (GenerationBlocked, GenerationFailed) as e:
            return i, None, e

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, len(jobs))) as pool:
        for fut in concurrent.futures.as_completed([pool.submit(one, i, kw) for i, kw in enumerate(jobs)]):
            i, res, err = fut.result()
            results[i], errors[i] = res, err
    return results, errors
