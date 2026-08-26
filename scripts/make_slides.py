"""
Renders a 4-slide recipe carousel (1080x1350, 4:5 ratio -- good for both
Instagram and TikTok photo-mode).

Design: full-bleed food photo as the background, with a dark gradient
scrim at the bottom so bold white text sits cleanly over the image --
the standard high-engagement recipe-carousel look. Falls back to a
warm gradient placeholder when a real photo isn't available yet (e.g.
before Higgsfield image generation is connected), so layout/typography
can be previewed independently of the photo pipeline.
"""
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350

# Safe-zone margins so text doesn't sit under TikTok/Instagram's own UI
# (username, caption, like/comment/share icons, "..." menu). These are
# starting estimates -- update once we have a real screenshot to measure
# against. TikTok's UI typically eats the bottom ~18-20% and right ~12-14%
# of a 4:5 or 9:16 post; Instagram Reels/feed is similar on the bottom.
SAFE_BOTTOM = 0.20  # fraction of H reserved at the bottom, kept clear of text
SAFE_RIGHT = 0.14   # fraction of W reserved at the right, kept clear of text
TEXT_BLOCK_BOTTOM = int(H * (1 - SAFE_BOTTOM))

PALETTES = [
    {"accent": (255, 140, 66), "placeholder": [(255, 214, 170), (214, 96, 54)]},
    {"accent": (108, 201, 132), "placeholder": [(214, 240, 214), (58, 122, 90)]},
    {"accent": (188, 140, 255), "placeholder": [(232, 220, 250), (108, 74, 182)]},
]

FONT_DIR_CANDIDATES = [
    "/usr/share/fonts/truetype/google-fonts",
]


def _font(size, weight="Bold"):
    for d in FONT_DIR_CANDIDATES:
        path = os.path.join(d, f"Poppins-{weight}.ttf")
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    fallback = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    if os.path.exists(fallback):
        return ImageFont.truetype(fallback, size)
    return ImageFont.load_default()


def _placeholder_background(palette):
    """Warm gradient standing in for a real food photo until one is available."""
    top, bottom = palette["placeholder"]
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        t = y / H
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        for x in range(0, W, 4):
            for dx in range(4):
                if x + dx < W:
                    px[x + dx, y] = (r, g, b)
    return img


def _load_background(photo_path, palette):
    if photo_path and os.path.exists(photo_path):
        img = Image.open(photo_path).convert("RGB")
        # cover-crop to W x H
        src_ratio = img.width / img.height
        dst_ratio = W / H
        if src_ratio > dst_ratio:
            new_h = H
            new_w = int(H * src_ratio)
        else:
            new_w = W
            new_h = int(W / src_ratio)
        img = img.resize((new_w, new_h))
        left = (new_w - W) // 2
        top = (new_h - H) // 2
        img = img.crop((left, top, left + W, top + H))
        return img
    return _placeholder_background(palette)


def _draw_scrim(img):
    """
    Dark gradient over roughly the bottom half so white text stays readable
    over any photo. The gradient itself covers full width/height (looks
    intentional either way); it's the TEXT placement in render_slide that
    respects the safe zone, not the scrim.
    """
    scrim = Image.new("L", (1, H), 0)
    for y in range(H):
        if y < H * 0.38:
            scrim.putpixel((0, y), 0)
        else:
            t = (y - H * 0.38) / (H * 0.62)
            scrim.putpixel((0, y), int(min(1, t * 1.15) * 235))
    scrim = scrim.resize((W, H))
    black = Image.new("RGB", (W, H), (10, 8, 6))
    img.paste(black, (0, 0), scrim)
    return img


def _wrap_and_draw(draw, text, font, max_width, x_center, y, fill, line_gap=1.15, shadow=True):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] > max_width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)

    line_h = font.size * line_gap
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        tx = x_center - tw / 2
        if shadow:
            draw.text((tx + 3, y + 3), line, font=font, fill=(0, 0, 0, 160))
        draw.text((tx, y), line, font=font, fill=fill)
        y += line_h
    return y


def render_slide(slide_num, total_slides, heading, sub, palette, out_path, photo_path=None, detail=None,
                  badge_step="STEP", badge_intro="EASY STEPS"):
    img = _load_background(photo_path, palette)
    img = _draw_scrim(img)
    draw = ImageDraw.Draw(img)

    accent = palette["accent"]

    # Progress dots (top) -- shows this is a 4-part carousel. Top placement
    # is safe on both platforms; the risk zone is bottom + right, not top.
    dot_y = 64
    total_w = total_slides * 34
    start_x = (W - total_w) / 2 + 17
    for i in range(total_slides):
        cx = start_x + i * 34
        r = 9 if (i + 1) == slide_num else 6
        color = accent if (i + 1) == slide_num else (255, 255, 255)
        alpha_img = Image.new("RGBA", (r * 2, r * 2), (0, 0, 0, 0))
        d2 = ImageDraw.Draw(alpha_img)
        d2.ellipse([0, 0, r * 2, r * 2], fill=color + (255 if (i + 1) == slide_num else 160,))
        img.paste(alpha_img, (int(cx - r), int(dot_y - r)), alpha_img)

    draw = ImageDraw.Draw(img)

    # Text width stays clear of the right-side icon column (like/comment/
    # share/bookmark stack that TikTok and Instagram both render there).
    text_max_width = W - int(W * SAFE_RIGHT) - 100  # 100px left margin to match
    text_center_x = (100 + (W - int(W * SAFE_RIGHT))) / 2

    # Work upward from the safe-zone floor so nothing sits under the
    # platform's caption/username/icon bar at the very bottom.
    # First measure the block height by doing a dry layout pass, then
    # position it so its bottom edge lands exactly on TEXT_BLOCK_BOTTOM.
    heading_size = 74 if slide_num == 1 else 60
    heading_font = _font(heading_size, "Bold")
    sub_font = _font(36, "Medium")
    detail_font = _font(30, "Medium")
    badge_font = _font(42, "Bold") if slide_num > 1 else _font(36, "Bold")

    badge_label = f"{badge_step} {slide_num - 1}" if slide_num > 1 else f"{total_slides - 1} {badge_intro}"
    badge_h = draw.textbbox((0, 0), badge_label, font=badge_font)[3] + 28

    heading_lines = _measure_wrap(draw, heading, heading_font, text_max_width)
    sub_lines = _measure_wrap(draw, sub, sub_font, text_max_width - 40)
    detail_lines = _measure_wrap(draw, detail, detail_font, text_max_width - 40) if detail else []

    block_h = (
        badge_h + 28
        + len(heading_lines) * heading_font.size * 1.15
        + 12 + len(sub_lines) * sub_font.size * 1.15
        + (16 + len(detail_lines) * detail_font.size * 1.25 if detail_lines else 0)
    )

    y = TEXT_BLOCK_BOTTOM - block_h

    # Step / intro badge
    bbox = draw.textbbox((0, 0), badge_label, font=badge_font)
    bw = bbox[2] - bbox[0]
    pad_x, pad_y = (28, 14) if slide_num > 1 else (26, 12)
    bx0 = text_center_x - bw / 2 - pad_x
    by0 = y - pad_y
    bx1 = text_center_x + bw / 2 + pad_x
    by1 = y + (bbox[3] - bbox[1]) + pad_y
    draw.rounded_rectangle([bx0, by0, bx1, by1], radius=16, fill=accent)
    draw.text((text_center_x - bw / 2, y - bbox[1]), badge_label, font=badge_font, fill=(255, 255, 255))
    y = by1 + 28

    # Heading
    y = _wrap_and_draw(draw, heading, heading_font, text_max_width, text_center_x, y, (255, 255, 255))

    # Sub text (the core instruction -- what to actually do)
    y += 12
    y = _wrap_and_draw(draw, sub, sub_font, text_max_width - 40, text_center_x, y, (255, 240, 225))

    # Optional extra detail line (a tip, a "why", or texture/visual cue)
    if detail_lines:
        y += 16
        _wrap_and_draw(draw, detail, detail_font, text_max_width - 40, text_center_x, y, (255, 210, 170), shadow=True)

    # Bottom accent bar -- thin, sits inside the platform's own UI zone so
    # it doesn't compete with real content there
    draw.rectangle([0, H - 10, W, H], fill=accent)

    # FIX 2026-08-26 (round 4): Instagram's Content Publishing API only
    # accepts JPEG -- confirmed against Meta's own developer docs ("JPEG is
    # the only image format supported... PNG is not supported") -- and a
    # live Buffer queue error ("Instagram is reporting that the image
    # format isn't supported") on a post using a .png. img is already RGB
    # (no alpha channel survives _load_background/_draw_scrim/the dot
    # overlay paste), so this is a safe straight re-encode.
    img.save(out_path, "JPEG", quality=92)
    return out_path


def _measure_wrap(draw, text, font, max_width):
    """Same wrapping logic as _wrap_and_draw, but just returns the line list (for height math)."""
    if not text:
        return []
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] > max_width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def render_carousel(recipe, day_index, out_dir, photo_paths=None):
    """
    photo_paths: optional list of 4 image file paths (one per slide), same
    order as recipe['slides']. Pass None (or a shorter list) to fall back
    to the warm-gradient placeholder for any missing slide -- lets the
    pipeline run end-to-end before Higgsfield is connected.

    recipe/content dict may optionally set "badge_step" / "badge_intro" to
    override the default "STEP" / "EASY STEPS" badge wording (e.g. "MOVE" /
    "QUICK MOVES" for a workout routine, "FACT" / "KEY FACTS" for a tip post).
    """
    os.makedirs(out_dir, exist_ok=True)
    palette = PALETTES[day_index % len(PALETTES)]
    slides = recipe["slides"]
    photo_paths = photo_paths or [None] * len(slides)
    badge_step = recipe.get("badge_step", "STEP")
    badge_intro = recipe.get("badge_intro", "EASY STEPS")

    paths = []
    for i, slide in enumerate(slides, start=1):
        out_path = os.path.join(out_dir, f"slide_{i}.jpg")
        photo = photo_paths[i - 1] if i - 1 < len(photo_paths) else None
        detail = slide.get("detail")
        render_slide(i, len(slides), slide["heading"], slide["sub"], palette, out_path, photo_path=photo, detail=detail,
                     badge_step=badge_step, badge_intro=badge_intro)
        paths.append(out_path)
    return paths


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from workout_ideas import get_workout_for_day

    day_index = 0
    workout = get_workout_for_day(day_index)
    out_dir = os.path.join(os.path.dirname(__file__), "..", "output", "sample_day0")
    paths = render_carousel(workout, day_index, out_dir)
    print("Workout:", workout["title"])
    for p in paths:
        print(" -", p)
