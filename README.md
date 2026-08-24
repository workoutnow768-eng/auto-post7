# social-bot

Fully autonomous daily content bot for two Buffer accounts:
- **Fitness** (workoutnow768): 30secfitness / 30sec_fitness / Crunch time
- **Food** (podcasterclips): ai_facts4u / daily_ai_factz / Factual days

Runs entirely on GitHub's servers via GitHub Actions on a daily cron. No
laptop, no Chrome, no Claude session required once set up. This replaces
the `requires_local_device: true` scheduled tasks that needed the user's
computer on and Chrome logged in.

## How it works

1. A GitHub Actions workflow (`.github/workflows/daily-post.yml`) runs
   once a day.
2. For each pipeline (recipe-page, workout-page) it picks the next 3
   content-bank entries per `state/*.json`.
3. For each slide, it calls **Higgsfield's developer REST API**
   (`platform.higgsfield.ai`, key-pair auth) to generate a photo, polls
   until done, and downloads the result. If Higgsfield reports the
   image as `nsfw`, that image is discarded and regenerated (never used)
   -- this is an automated version of the standing "no 18+ content, ever"
   rule.
4. It renders each 4-5 slide carousel locally with Pillow (same
   `make_slides.py` logic used in the manual pipeline), and commits the
   finished PNGs into the repo under `output/`.
5. It calls **Buffer's GraphQL API** (`api.buffer.com`) to schedule a
   post per channel, referencing the images via their
   `raw.githubusercontent.com` URL (since the images now live in this
   public repo).
6. It updates `state/*.json` (rotation index, scheduled-through
   timestamp) and commits everything back.

## Setup (one-time, by you)

### 1. Add repo secrets
Go to **Settings > Secrets and variables > Actions > New repository
secret** and add:

| Secret name | Where to get it |
|---|---|
| `HIGGSFIELD_API_KEY_ID` | [cloud.higgsfield.ai](https://cloud.higgsfield.ai) -- API Keys section |
| `HIGGSFIELD_API_KEY_SECRET` | same page, shown once when you create the key |
| `BUFFER_ACCESS_TOKEN` | Buffer's developer settings -- create a new Personal Access Token with publish permissions. **The token currently saved in the old `recipe-page` project returned a 401 in testing and should be treated as invalid/expired -- generate a fresh one.** |

I never see or handle these values -- you paste them directly into
GitHub's UI.

### 2. Verify channel names
The bot looks up each Buffer channel by exact display name (via the
`channels` query) rather than a hardcoded ID, since IDs aren't something
I have -- and channel names are stable, unlike browser `deviceId`s which
we found flip between accounts. Confirm these 6 names match exactly what
you see in Buffer before the first run:
`30secfitness`, `30sec_fitness`, `Crunch time`, `ai_facts4u`,
`daily_ai_factz`, `Factual days`.

### 3. Enable Actions & test
GitHub Actions is usually enabled by default on a new repo. Once secrets
are added, trigger a manual run from the **Actions** tab ("Run workflow")
to confirm everything works before waiting for the first scheduled run.

## Known open questions / things to verify on first real run
- **Multi-image carousel support**: Buffer's public GraphQL API's
  `assets` field is documented as an ordered list, which should support
  multiple images per post the same way the manual browser flow does --
  but this hasn't been tested end-to-end against real credentials yet
  (I don't have a valid token to test with). The very first automated
  run should be watched closely in Buffer's queue to confirm all slides
  attach, not just the first.
- **Channel lookup field names**: the exact GraphQL schema for listing
  channels (`channels { id name service }`) is a best-effort based on
  the one documented example page: if it errors, check
  `https://developers.buffer.com` for the current schema and adjust
  `scripts/buffer_client.py`'s `get_channel_id` function.
- Higgsfield's MCP connector (used in earlier manual sessions) explicitly
  does **not** honor the "Unlimited" plan toggle -- MCP and the
  developer API both always charge credits at standard rates. Budget
  accordingly (roughly 4-5 images/day per pipeline, ~8-10 total).

## Fallback
The original `requires_local_device: true` scheduled tasks
("Recipe Page - Evening Batch", "Workout Page - Evening Batch") are left
in place and untouched as a manual fallback in case this bot needs
debugging -- they still work whenever the user's laptop + Chrome are
available. Once this bot is confirmed reliable for a few days, those can
be disabled.
