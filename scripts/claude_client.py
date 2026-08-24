"""
Claude API client for dynamic content generation.
Generates recipe ideas and workout tips using Claude to supplement the static content banks.
"""
import os
from anthropic import Anthropic

client = Anthropic()

def generate_recipe_idea():
    """
    Generate a single recipe idea using Claude.
    Returns a dict matching the shape of recipe_ideas.RECIPES entries.
    """
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": """Generate a single quick and easy recipe (under 20 minutes) in JSON format.
                The JSON must have this exact structure:
                {
                    "title": "Recipe name",
                    "total_time": "X min",
                    "servings": "N",
                    "slides": [
                        {"heading": "Title slide heading", "sub": "Subtitle", "detail": "Optional details"},
                        {"heading": "Step 1 heading", "sub": "Step description", "detail": "Coaching tips"},
                        {"heading": "Step 2 heading", "sub": "Step description", "detail": "Coaching tips"},
                        {"heading": "Step 3 heading", "sub": "Step description", "detail": "Coaching tips"}
                    ],
                    "caption": "Social media caption (2-3 sentences)",
                    "hashtags": "#tag1 #tag2 #tag3 #tag4 #tag5"
                }
                
                Return ONLY the JSON, no other text."""
            }
        ]
    )
    
    import json
    try:
        recipe = json.loads(message.content[0].text)
        print(f"[CLAUDE] Generated recipe: {recipe['title']}")
        return recipe
    except (json.JSONDecodeError, KeyError) as e:
        print(f"[WARN] Claude recipe generation failed to parse: {e}")
        return None


def generate_workout_idea():
    """
    Generate a single workout/fitness tip using Claude.
    Returns a dict matching the shape of workout_ideas.WORKOUTS entries.
    """
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": """Generate a single fitness tip or quick workout in JSON format.
                The JSON must have this exact structure:
                {
                    "type": "routine" or "tip",
                    "title": "Workout or tip title",
                    "duration": "X min or Quick Read",
                    "level": "All Levels or Beginner or Intermediate",
                    "badge_step": "MOVE", "FACT", "FIX", etc",
                    "badge_intro": "Plural form like QUICK MOVES or KEY FACTS",
                    "slides": [
                        {"heading": "Title slide heading", "sub": "Subtitle"},
                        {"heading": "Step/Fact 1", "sub": "Description", "detail": "Full coaching details"},
                        {"heading": "Step/Fact 2", "sub": "Description", "detail": "Full coaching details"},
                        {"heading": "Step/Fact 3", "sub": "Description", "detail": "Full coaching details"}
                    ],
                    "caption": "Social media caption (2-3 sentences)",
                    "hashtags": "#tag1 #tag2 #tag3 #tag4 #tag5"
                }
                
                Return ONLY the JSON, no other text."""
            }
        ]
    )
    
    import json
    try:
        workout = json.loads(message.content[0].text)
        print(f"[CLAUDE] Generated workout: {workout['title']}")
        return workout
    except (json.JSONDecodeError, KeyError) as e:
        print(f"[WARN] Claude workout generation failed to parse: {e}")
        return None


def enhance_caption(text, style="casual"):
    """
    Use Claude to enhance or rewrite a caption for social media.
    """
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": f"""Rewrite this caption for TikTok/social media in a {style} tone.
                Keep it 2-3 sentences, add relevant emojis, make it engaging.
                
                Original caption:
                {text}
                
                Return ONLY the rewritten caption, no other text."""
            }
        ]
    )
    
    return message.content[0].text.strip()
