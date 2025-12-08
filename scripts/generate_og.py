#!/usr/bin/env python3
"""
GitHub-style OG Card Generator
Creates a clean white preview card:
- small owner text
- bold repo name
- description (wrapped)
- stats row (contributors/issues/stars/forks)
- GitHub avatar on the right
"""

import os
import argparse
from PIL import Image, ImageDraw, ImageFont

FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def measure(draw, text, font):
    try:
        bbox = draw.textbbox((0,0), text, font=font)
        return bbox[2]-bbox[0], bbox[3]-bbox[1]
    except:
        try:
            return font.getsize(text)
        except:
            return (len(text)*6, 20)

def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines = []
    cur = ""

    for w in words:
        test = cur + (" " if cur else "") + w
        w_px, _ = measure(draw, test, font)
        if w_px <= max_width:
            cur = test
        else:
            lines.append(cur)
            cur = w

    if cur:
        lines.append(cur)
    return lines


def draw_stats(draw, x, y, font, color):
    items = [
        ("Contributors", "1"),
        ("Issues", "0"),
        ("Stars", "0"),
        ("Forks", "0"),
    ]
    spacing = 70
    for label, count in items:
        text = f"{count} {label}"
        draw.text((x, y), text, font=font, fill=color)
        tw, _ = measure(draw, text, font)
        x += tw + spacing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="social_preview.png")
    ap.add_argument("--title")
    ap.add_argument("--subtitle")
    ap.add_argument("--author")
    ap.add_argument("--sha")
    ap.add_argument("--logo", default="assets/brand-logo.png")
    args = ap.parse_args()

    W, H = 1280, 640
    BG = (255, 255, 255)
    TEXT = (30, 35, 40)
    SUBTEXT = (100, 110, 120)

    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    left = 100
    right = W - 260

    raw = args.title or "unknown/repo"
    if "/" in raw:
        owner, repo = raw.split("/", 1)
    else:
        owner, repo = "", raw

    font_owner = load_font(FONT_REGULAR, 30)
    font_repo = load_font(FONT_BOLD, 64)
    font_desc = load_font(FONT_REGULAR, 26)
    font_stats = load_font(FONT_REGULAR, 22)

    y = 120

    # Owner (small)
    if owner:
        owner_text = f"{owner}/"
        draw.text((left, y), owner_text, font=font_owner, fill=SUBTEXT)
        ow, oh = measure(draw, owner_text, font_owner)
        y += oh + 10

    # Repo bold
    # shrink if too wide
    rw, rh = measure(draw, repo, font_repo)
    maxw = right - left
    if rw > maxw:
        for sz in range(64, 28, -4):
            font_repo = load_font(FONT_BOLD, sz)
            rw, rh = measure(draw, repo, font_repo)
            if rw <= maxw:
                break

    draw.text((left, y), repo, font=font_repo, fill=TEXT)
    y += rh + 20

    # Subtitle / Description
    desc = args.subtitle or ""
    lines = wrap_text(desc, font_desc, maxw, draw)[:3]
    for line in lines:
        draw.text((left, y), line, font=font_desc, fill=SUBTEXT)
        _, lh = measure(draw, line, font_desc)
        y += lh + 6

    # Stats row
    y += 25
    draw_stats(draw, left, y, font_stats, SUBTEXT)

    # Meta line bottom-left
    meta = ""
    if args.author:
        meta = f"by {args.author}"
    if args.sha:
        meta += f" • {args.sha[:7]}"
    draw.text((left, H - 60), meta, font=font_stats, fill=SUBTEXT)

    # Avatar / logo
    if os.path.exists(args.logo):
        try:
            avatar = Image.open(args.logo).convert("RGBA")
            avatar.thumbnail((180, 180))
            img.paste(avatar, (W - 260, 100), avatar)
        except:
            pass

    img.save(args.output, quality=95)
    print("Generated", args.output)


if __name__ == "__main__":
    main()
