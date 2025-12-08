#!/usr/bin/env python3
"""
Generate a simple OG/social preview card (1280x640) with repo title + description.
Dependencies: Pillow
"""

import os
import argparse
from PIL import Image, ImageDraw, ImageFont

DEFAULT_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
DEFAULT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def measure_text(draw, text, font):
    """
    Return (width, height) for the given text using the best available method.
    Compatible with multiple Pillow versions.
    """
    try:
        # Pillow >= 8: textbbox gives accurate bounding box
        bbox = draw.textbbox((0,0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        return (w, h)
    except Exception:
        try:
            # Older Pillow: font.getsize
            return font.getsize(text)
        except Exception:
            # Fallback: use draw.textsize if present
            if hasattr(draw, "textsize"):
                return draw.textsize(text, font=font)
            # Last resort
            return (len(text) * 6, 12)

def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        test = cur + (" " if cur else "") + w
        width, _ = measure_text(draw, test, font)
        if width <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="social_preview.png")
    ap.add_argument("--title", default="Repository")
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--author", default="")
    ap.add_argument("--sha", default="")
    ap.add_argument("--logo", default="assets/brand-logo.png")
    args = ap.parse_args()

    W, H = 1280, 640
    bg_color = (18, 40, 74)
    accent = (249, 208, 39)
    text_color = (255, 255, 255)
    muted = (200, 210, 220)

    img = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(img)

    # subtle stripes for texture (very light)
    for i in range(0, H, 4):
        alpha = int(6 * (i / H))
        # draw.line doesn't accept alpha on RGB image; use a slightly different color
        stripe_color = (bg_color[0] + alpha, bg_color[1] + alpha, bg_color[2] + alpha)
        draw.line([(0, i), (W, i)], fill=stripe_color, width=1)

    font_title = load_font(DEFAULT_BOLD, 48)
    font_sub = load_font(DEFAULT_FONT, 24)
    font_meta = load_font(DEFAULT_FONT, 18)

    padding = 60
    left = padding
    right_limit = W - padding

    title = args.title
    if len(title) > 60:
        title = title[:57] + "..."

    draw.text((left, 120), title, font=font_title, fill=accent)

    subtitle = args.subtitle or "A GitHub project"
    max_width = right_limit - left
    lines = wrap_text(subtitle, font_sub, max_width, draw)
    y = 200
    for line in lines[:5]:
        draw.text((left, y), line, font=font_sub, fill=text_color)
        _, h = measure_text(draw, line, font_sub)
        y += h + 6

    meta = f"by {args.author}" if args.author else ""
    if args.sha:
        meta += f" • {args.sha[:7]}"
    draw.text((left, H - 80), meta, font=font_meta, fill=muted)

    # right info box
    box_w, box_h = 420, 220
    box_x = W - padding - box_w
    box_y = 120
    draw.rectangle([box_x, box_y, box_x+box_w, box_y+box_h], outline=(255,255,255,20))

    sx = box_x + 24
    sy = box_y + 24
    draw.text((sx, sy), "★ 0  •  Forks: 0  •  Issues: 0", font=font_meta, fill=text_color)

    # logo (optional)
    if os.path.exists(args.logo):
        try:
            logo = Image.open(args.logo).convert("RGBA")
            logo.thumbnail((100,100))
            lx = box_x + box_w - logo.width - 20
            ly = box_y + 20
            img.paste(logo, (lx, ly), logo)
        except Exception:
            pass

    img.convert("RGB").save(args.output, quality=90)
    print("Generated", args.output)

if __name__ == "__main__":
    main()
