"""
Per-slide image generation prompts for each recipe, written for
Higgsfield's Nano Banana (or similar photorealistic food-photography model).

Slide 1 = finished dish, styled hero shot.
Slides 2-4 = the actual step in progress, close-up, matching the recipe's
step text -- e.g. "melting butter and garlic in a pan" rather than a
generic food photo, since the user specifically wants real step photos
under real step text, not stock filler.

Once Higgsfield is connected (via CLI/MCP after `higgsfield auth login`
on the user's machine), these prompts feed directly into the generation
call, one image per slide, then get passed into make_slides.py's
photo_paths argument.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from recipe_ideas import RECIPES

STYLE_SUFFIX = (
    "overhead or 45-degree angle food photography, natural daylight, "
    "shallow depth of field, rustic wooden or marble surface, "
    "vibrant appetizing colors, high detail, no text or watermarks, "
    "shot on a mirrorless camera, editorial food magazine quality"
)


def build_prompts_for_recipe(recipe):
    """Returns a list of 4 prompt strings, one per slide, in slide order."""
    title = recipe["title"]
    prompts = []

    # Slide 1: hero shot of the finished dish
    prompts.append(
        f"A beautifully plated {title}, finished and ready to eat, "
        f"{STYLE_SUFFIX}"
    )

    # Slides 2-4: the actual step being performed
    for slide in recipe["slides"][1:]:
        step_desc = slide["sub"]
        prompts.append(
            f"Close-up action shot of a home cook's hands {_actionize(step_desc)} "
            f"while making {title}, {STYLE_SUFFIX}"
        )

    return prompts


def _actionize(step_text):
    """Light rewrite of a terse recipe instruction into a descriptive visual phrase."""
    return step_text[0].lower() + step_text[1:] if step_text else step_text


def build_all_prompts():
    """Returns {recipe_title: [prompt1, prompt2, prompt3, prompt4]} for the whole bank."""
    return {r["title"]: build_prompts_for_recipe(r) for r in RECIPES}


if __name__ == "__main__":
    all_prompts = build_all_prompts()
    for title, prompts in list(all_prompts.items())[:2]:
        print(f"=== {title} ===")
        for i, p in enumerate(prompts, start=1):
            print(f"  Slide {i}: {p}")
        print()
    print(f"Total recipes with prompts ready: {len(all_prompts)}")
