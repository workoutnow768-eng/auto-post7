"""
Per-slide image generation prompts for the workout content bank -- same
shape as recipe-page's image_prompts.py, adapted for fitness/gym photography
instead of food photography.

Slide 1 = a hero shot representing the routine or topic (someone mid-move,
or a symbolic gym/home-workout scene for "tip" posts).
Slides 2-4 = the actual exercise or moment being described, matching the
slide's "sub" text -- real demonstration shots, not generic stock gym pics.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from workout_ideas import WORKOUTS

STYLE_SUFFIX = (
    "realistic fitness photography, natural or gym lighting, "
    "shallow depth of field, clean modern home-gym or gym setting, "
    "athletic and motivating tone, high detail, no text or watermarks, "
    "shot on a mirrorless camera, editorial fitness magazine quality"
)


def build_prompts_for_workout(workout):
    """Returns a list of 4 prompt strings, one per slide, in slide order."""
    title = workout["title"]
    prompts = []

    if workout["type"] == "routine":
        # Slide 1: a dynamic hero shot of someone mid-exercise, representing
        # the routine as a whole.
        prompts.append(
            f"A fit person performing an exercise associated with '{title}', "
            f"dynamic mid-motion action shot, {STYLE_SUFFIX}"
        )
        # Slides 2-4: the specific move being described
        for slide in workout["slides"][1:]:
            step_desc = slide["sub"]
            prompts.append(
                f"A person demonstrating good form while {_actionize(step_desc)}, "
                f"clear full-body view showing proper technique, {STYLE_SUFFIX}"
            )
    else:
        # "tip" posts: slide 1 is a symbolic/topical hero shot, slides 2-4
        # illustrate the specific point being made (a form cue, a rest-day
        # scene, etc.) rather than a literal exercise step.
        prompts.append(
            f"A symbolic fitness photo representing the topic '{title}', "
            f"gym or home-workout setting, {STYLE_SUFFIX}"
        )
        for slide in workout["slides"][1:]:
            point_desc = slide["sub"]
            prompts.append(
                f"A photo illustrating the idea: {_actionize(point_desc)}, "
                f"in a fitness/gym context, {STYLE_SUFFIX}"
            )

    return prompts


def _actionize(step_text):
    return step_text[0].lower() + step_text[1:] if step_text else step_text


def build_all_prompts():
    """Returns {workout_title: [prompt1, prompt2, prompt3, prompt4]} for the whole bank."""
    return {w["title"]: build_prompts_for_workout(w) for w in WORKOUTS}


if __name__ == "__main__":
    all_prompts = build_all_prompts()
    for title, prompts in list(all_prompts.items())[:2]:
        print(f"=== {title} ===")
        for i, p in enumerate(prompts, start=1):
            print(f"  Slide {i}: {p}")
        print()
    print(f"Total workout entries with prompts ready: {len(all_prompts)}")
