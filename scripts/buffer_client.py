"""
Thin client for Buffer's public GraphQL API (api.buffer.com), used to
create scheduled posts directly from GitHub Actions with no browser.

Docs referenced: https://developers.buffer.com/examples/create-image-post.html
The schema for `channels` (listing connected channels/profiles) was not
directly confirmed against a live example at the time this was written
-- it's a best-effort guess based on the documented shape of the API. If
`get_channel_id` errors, check developers.buffer.com for the current
`channels`/`profiles` query shape and adjust below.

Multi-image (carousel) posts: `assets` is documented as an ordered list
where each entry is exactly one of image/video/document/link, which
should support N images by passing N `{"image": {"url": ...}}` entries
-- same idea as attaching multiple photos in the Buffer web composer.
This has NOT been verified end-to-end against a live account yet (no
valid token available in this environment) -- watch the first real run
closely in Buffer's queue.
"""
import os
import requests

API_URL = "https://api.buffer.com"


def _headers():
    token = os.environ["BUFFER_ACCESS_TOKEN"]
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _graphql(query, variables=None):
    resp = requests.post(API_URL, headers=_headers(), json={"query": query, "variables": variables or {}}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data and data["errors"]:
        raise RuntimeError(f"Buffer GraphQL error: {data['errors']}")
    return data["data"]


_CHANNELS_QUERY = """
query ListChannels {
  channels {
    id
    name
    service
  }
}
"""


def list_channels():
    """Returns [{"id": ..., "name": ..., "service": ...}, ...] for the authenticated account."""
    data = _graphql(_CHANNELS_QUERY)
    return data.get("channels", [])


_channel_cache = {}


def get_channel_id(channel_name):
    """Looks up a channel's id by exact display name, case-sensitive match first,
    falling back to case-insensitive. Raises if not found or ambiguous."""
    if not _channel_cache:
        for ch in list_channels():
            _channel_cache[ch["name"]] = ch["id"]

    if channel_name in _channel_cache:
        return _channel_cache[channel_name]

    lowered = channel_name.strip().lower()
    matches = [cid for name, cid in _channel_cache.items() if name.strip().lower() == lowered]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise RuntimeError(
            f"No Buffer channel found named '{channel_name}'. "
            f"Available channels: {list(_channel_cache.keys())}"
        )
    raise RuntimeError(f"Multiple channels matched '{channel_name}': {matches}")


_CREATE_POST_MUTATION = """
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on PostActionSuccess {
      post { id text }
    }
    ... on MutationError {
      message
    }
  }
}
"""


def create_post(channel_name, text, image_urls, scheduled_at_iso8601):
    """
    Schedules one post to one channel with one or more images.
    scheduled_at_iso8601: e.g. "2026-08-26T19:00:00Z"
    """
    channel_id = get_channel_id(channel_name)
    assets = [{"image": {"url": url}} for url in image_urls]
    variables = {
        "input": {
            "text": text,
            "channelId": channel_id,
            "schedulingType": "custom",
            "scheduledAt": scheduled_at_iso8601,
            "assets": assets,
        }
    }
    result = _graphql(_CREATE_POST_MUTATION, variables)
    payload = result.get("createPost", {})
    if "message" in payload:
        raise RuntimeError(f"Buffer rejected the post for '{channel_name}': {payload['message']}")
    return payload.get("post")
