"""
Thin client for Buffer's public GraphQL API (api.buffer.com), used to
create scheduled posts directly from GitHub Actions with no browser.

Docs referenced: https://developers.buffer.com/examples/create-image-post.html

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


_ORGANIZATIONS_QUERY = """
query GetOrganizations {
  account {
    organizations {
      id
      name
    }
  }
}
"""

_CHANNELS_QUERY = """
query GetChannels($organizationId: OrganizationId!) {
  channels(input: { organizationId: $organizationId }) {
    id
    name
    service
  }
}
"""

_org_id_cache = None


def get_organization_id():
    """
    Returns the first organization id on this Buffer account. Confirmed
    2026-08-24 (after a live GraphQL error) that `channels` requires an
    organizationId -- fetched via this separate `account.organizations`
    query, per developers.buffer.com/examples/get-organizations.html.
    If the account has multiple organizations/workspaces, this picks the
    first one -- fine here since both bot accounts (workoutnow768,
    podcasterclips) are single-organization Buffer Free-plan accounts.
    """
    global _org_id_cache
    if _org_id_cache:
        return _org_id_cache
    data = _graphql(_ORGANIZATIONS_QUERY)
    orgs = (data.get("account") or {}).get("organizations") or []
    if not orgs:
        raise RuntimeError("No organizations found on this Buffer account.")
    _org_id_cache = orgs[0]["id"]
    return _org_id_cache


def list_channels():
    """Returns [{"id": ..., "name": ..., "service": ...}, ...] for the authenticated account."""
    org_id = get_organization_id()
    data = _graphql(_CHANNELS_QUERY, {"organizationId": org_id})
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

    Confirmed 2026-08-24 (after a live GraphQL error) that "custom"/
    "scheduledAt" are wrong -- the actual shape per
    developers.buffer.com/guides/posts-and-scheduling.html is
    schedulingType: automatic (always this, regardless of timing) with
    mode: customScheduled and a "dueAt" field (not scheduledAt) for the
    specific timestamp.
    """
    channel_id = get_channel_id(channel_name)
    assets = [{"image": {"url": url}} for url in image_urls]
    variables = {
        "input": {
            "text": text,
            "channelId": channel_id,
            "schedulingType": "automatic",
            "mode": "customScheduled",
            "dueAt": scheduled_at_iso8601,
            "assets": assets,
        }
    }
    result = _graphql(_CREATE_POST_MUTATION, variables)
    payload = result.get("createPost", {})
    if "message" in payload:
        raise RuntimeError(f"Buffer rejected the post for '{channel_name}': {payload['message']}")
    return payload.get("post")
