"""
Thin client for Higgsfield's developer REST API (platform.higgsfield.ai),
used instead of the MCP connector because this runs headlessly in GitHub
Actions with no Claude session attached.

Docs: https://docs.higgsfield.ai/docs -- key-pair auth, async job model
(submit -> poll status_url -> download image url once status=="completed").

Safety: if a job comes back with status "nsfw", the image is NEVER
returned or used -- this is the automated equivalent of the standing
"stop immediately on any 18+ content" instruction. The caller should
treat a GenerationBlocked exception as "skip this image, try a different
prompt or just proceed without it," never retry the identical prompt
blindly forever.
"""
import os
import time
import requests
import concurrent.futures

BASE_URL = "https://platform.higgsfield.ai"
# FIX 2026-08-26: this was missing "/v2/" -- confirmed against the live docs
# (docs.higgsfield.ai/docs/guides/images and /docs/models) that the Soul
# endpoint is versioned. The un-versioned path 404s, which was being
# silently swallowed by generate_image()'s except clause and falling back
# to a placeholder gradient -- EVERY image this bot has generated so far
# (both "successful" and failed runs) was a blank placeholder, never a
# real photo. Confirmed by downloading and viewing the actual committed
# PNGs from the Aug 24 and Aug 25 runs.
GENERATE_ENDPOINT = f"{BASE_URL}/higgsfield-ai/soul/v2/standard"

POLL_INTERVAL_SECONDS = 5
POLL_TIMEOUT_SECONDS = 180


class GenerationBlocked(Exception):
    """Raised when Higgsfield flags a generation as nsfw -- never use the result."""


class GenerationFailed(Exception):
    pass


def _auth_header():
    key_id = os.environ["HIGGSFIELD_API_KEY_ID"]
    key_secret = os.environ["HIGGSFIELD_API_KEY_SECRET"]
    return {"Authorization": f"Key {key_id}:{key_secret}"}


def submit_image_job(prompt, aspect_ratio="3:4", resolution="720p"):
    """
    Submits one image generation job, returns the status_url to poll.

    Valid aspect_ratio values for the Soul model (confirmed 2026-08-24 after
    a live 422 on "4:5", which is NOT valid): 9:16, 3:4, 2:3, 1:1, 4:3, 16:9,
    3:2. "3:4" is the closest portrait ratio to the carousel's actual 4:5
    render target -- make_slides.py cover-crops to 1080x1350 regardless, so
    the exact source ratio doesn't need to match exactly.
    """
    resp = requests.post(
        GENERATE_ENDPOINT,
        headers={**_auth_header(), "Content-Type": "application/json", "Accept": "application/json"},
        json={"prompt": prompt, "aspect_ratio": aspect_ratio, "resolution": resolution},
        timeout=30,
    )
    if not resp.ok:
        raise GenerationFailed(f"HTTP {resp.status_code} from Higgsfield: {resp.text[:500]}")
    data = resp.json()
    status_url = data.get("status_url")
    if not status_url:
        raise GenerationFailed(f"No status_url in response: {data}")
    return status_url


def poll_until_done(status_url, poll_interval=POLL_INTERVAL_SECONDS, timeout=POLL_TIMEOUT_SECONDS):
    """Polls status_url until a terminal state. Returns the final JSON payload."""
    elapsed = 0
    while elapsed < timeout:
        resp = requests.get(status_url, headers=_auth_header(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status")
        if status == "completed":
            return data
        if status == "nsfw":
            raise GenerationBlocked(f"Higgsfield flagged this generation as nsfw: {data}")
        if status in ("failed", "canceled"):
            raise GenerationFailed(f"Generation ended in status={status}: {data}")
        # "queued" or "in_progress" -- keep waiting
        time.sleep(poll_interval)
        elapsed += poll_interval
    raise GenerationFailed(f"Timed out after {timeout}s waiting on {status_url}")


def download_image(image_url, out_path):
    resp = requests.get(image_url, timeout=60)
    resp.raise_for_status()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(resp.content)
    return out_path


def generate_image(prompt, out_path, aspect_ratio="3:4", resolution="720p", max_retries=2):
    """
    End-to-end: submit -> poll -> download. Retries once (with the same
    prompt) if the job fails for a transient reason. NEVER retries past
    an nsfw block by silently reusing the flagged image -- raises
    GenerationBlocked so the caller can decide (skip slide, try a
    different/softer prompt, or abort the batch).
    """
    last_err = None
    for attempt in range(max_retries):
        try:
            status_url = submit_image_job(prompt, aspect_ratio=aspect_ratio, resolution=resolution)
            result = poll_until_done(status_url)
            images = result.get("images") or []
            if not images or not images[0].get("url"):
                raise GenerationFailed(f"Completed but no image url in payload: {result}")
            return download_image(images[0]["url"], out_path)
        except GenerationBlocked:
            raise  # never swallow/retry an nsfw block silently
        except (GenerationFailed, requests.RequestException) as e:
            last_err = e
            time.sleep(3)
    raise GenerationFailed(f"Failed after {max_retries} attempts: {last_err}")


# FIX 2026-08-26 (round 5, scaling): generate_image() was being called in a
# plain sequential for-loop, one slide at a time -- submit, then block on
# poll_until_done (up to 180s), then download, THEN move to the next slide.
# Confirmed live (run #8, first run with real credits): the "Generate
# recipe carousels" step alone took 14m34s for just 3 items -- with real
# images actually taking 1-3 min each to generate, that's ~N * per-image-
# time, which stops being viable once this scales past 2 pipelines (8+
# channels would mean 8x the sequential wait, potentially over an hour per
# run). Since each generate_image() call is I/O-bound (waiting on HTTP
# requests, not CPU work), Python threads work fine here despite the GIL --
# they're blocked on network I/O, which releases the GIL. This runs N jobs
# concurrently (capped by max_workers) instead of one at a time, so total
# wall-clock time approaches the slowest single image instead of the sum
# of all of them.
def generate_images_concurrent(jobs, max_workers=5):
    """
    jobs: list of dicts, each with at least {"prompt": ..., "out_path": ...}
    and optionally {"aspect_ratio": ..., "resolution": ...}.

    Returns (results, errors) -- both lists the same length/order as jobs.
    results[i] is the out_path on success, None on failure/nsfw-block.
    errors[i] is None on success, or the GenerationBlocked/GenerationFailed
    exception instance on failure -- callers use this to tell a safety
    block apart from a plain failure (same distinction the old sequential
    per-slide try/except made) and to log the same [SAFETY]/[WARN] lines
    as before.

    max_workers=5 is a conservative default -- deliberately not "as many as
    there are jobs" to avoid hammering Higgsfield's API with a burst of
    concurrent submissions from a single run. Tune upward if Higgsfield's
    rate limits comfortably allow it.
    """
    results = [None] * len(jobs)
    errors = [None] * len(jobs)

    def _run_one(index, job):
        try:
            path = generate_image(
                job["prompt"],
                job["out_path"],
                aspect_ratio=job.get("aspect_ratio", "3:4"),
                resolution=job.get("resolution", "720p"),
            )
            return index, path, None
        except (GenerationBlocked, GenerationFailed) as e:
            return index, None, e

    if not jobs:
        return results, errors

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, len(jobs))) as pool:
        futures = [pool.submit(_run_one, i, job) for i, job in enumerate(jobs)]
        for future in concurrent.futures.as_completed(futures):
            index, path, err = future.result()
            results[index] = path
            errors[index] = err

    return results, errors
