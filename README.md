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
| `BUFFER_ACCESS_TOKEN_RECIPE` | A Buffer Personal Access Token with publish permissions, created **while logged into the podcasterclips account** (food pipeline). |
| `BUFFER_ACCESS_TOKEN_WORKOUT` | A Buffer Personal Access Token with publish permissions, created **while logged into the workoutnow768 account** (fitness pipeline). |

**Note (2026-08-26):** these used to be one shared `BUFFER_ACCESS_TOKEN`
secret. That was a real bug, not just a simplification -- both pipelines
looked up channels using whichever account that one token belonged to, so
the recipe pipeline was silently querying the fitness account's channels
and failing every single scheduling attempt (confirmed in a live Actions
run log). If you still have the old `BUFFER_ACCESS_TOKEN` secret set,
delete it and add the two above instead -- one token per Buffer account.

I never see or handle these values -- you paste them directly into
GitHub's UI.

### 2. Verify channel names
The bot looks up each Buffer channel by exact display name (matching
either the `name` or `displayName` field, since it wasn't clear which one
holds the label you see in Buffer's UI) rather than a hardcoded ID, since
IDs aren't something I have -- and channel names are stable, unlike
browser `deviceId`s which we found flip between accounts. Confirm these
names match exactly what you see in Buffer before the first run:
`30secfitness`, `30sec_fitness`, `Crunch time`, `ai_facts4u`,
`daily_ai_factz`.

**`Factual days` (the podcasterclips YouTube channel) is intentionally
NOT in the active channel list.** Confirmed 2026-08-26 in the manual
Buffer web flow that Buffer requires video content for YouTube and blocks
image-only carousels with "Please include a video." This pipeline only
generates image carousels, so add it back in `scripts/main.py`'s
`PIPELINES["recipe"]["channels"]` only once there's a video-capable path.

### 3. Enable Actions & test
GitHub Actions is usually enabled by default on a new repo. Once secrets
are added, trigger a manual run from the **Actions** tab ("Run workflow")
to confirm everything works before waiting for the first scheduled run.

## Fixed 2026-08-26 (post-mortem on the first few live runs)
The bot ran 5 times on its own before this fix pass (2 succeeded, 3 failed).
Two real bugs were found and fixed:

1. **Every image generated so far was a blank placeholder gradient, never a
   real photo.** `scripts/higgsfield_client.py` was calling
   `.../higgsfield-ai/soul/standard` -- the real endpoint (confirmed against
   live docs.higgsfield.ai) is versioned: `.../higgsfield-ai/soul/v2/standard`.
   The un-versioned URL 404s, which `generate_image()`'s error handling
   silently swallowed and fell back to a placeholder background. This was
   confirmed by downloading and viewing the actual PNGs committed by past
   runs. **If you already have real posts live/scheduled from before this
   fix, check both Buffer accounts' Sent/Queue history for gradient-only
   carousels and remove or reschedule them** -- a scan on 2026-08-26 found
   none currently live on either account, but double-check.
2. **Both pipelines shared one Buffer token**, so the recipe pipeline was
   always querying the fitness account's channels and failing 100% of the
   time. Fixed by splitting into `BUFFER_ACCESS_TOKEN_RECIPE` /
   `BUFFER_ACCESS_TOKEN_WORKOUT` (see secrets table above) -- you need to
   add both before the next run.

Also removed: an unused `scripts/claude_client.py` (Anthropic API client
for dynamic content generation) and the `anthropic` dependency that had
been added but never wired into `main.py` and had no API key secret
configured -- dead code, deleted rather than left dangling.

## Known open questions / things to verify on the next real run
- **Multi-image carousel support**: Buffer's public GraphQL API's
  `assets` field is documented as an ordered list, which supports
  multiple images per post the same way the manual browser flow does.
  Confirmed against live docs 2026-08-26, but still worth watching the
  next automated run closely in Buffer's queue to confirm all slides
  attach, not just the first.
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
