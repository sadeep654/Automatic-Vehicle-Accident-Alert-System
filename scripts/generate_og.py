#!/usr/bin/env python3
"""
GitHub-style OG Card Generator — improved with bottom color bar and GitHub mark.

Expects (optional) images at:
- assets/brand-logo.png   (your profile avatar, top-right)
- assets/github-mark.png  (GitHub mark icon to place bottom-right)

Outputs: social_preview.png
Dependencies: Pillow
"""

import os
import argparse
from PIL import Image, ImageDraw, ImageFont, ImageOps

FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def measure(draw, text, font):
    try:
        bbox = draw.textbbox((0,0), text, font=font)
        return bbox[2]-bbox[0], bbox[3]-bbox[1]
    except Exception:
        try:
            return font.getsize(text)
        except Exception:
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
            if cur:
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
    spacing = 60
    for label, count in items:
        text = f"{count} {label}"
        draw.text((x, y), text, font=font, fill=color)
        tw, _ = measure(draw, text, font)
        x += tw + spacing

def paste_thumbnail(base_img, img_path, box_x, box_y, max_size):
    try:
        im = Image.open(img_path).convert("RGBA")
        im.thumbnail((max_size, max_size))
        # optional white border for clarity (like your avatar had)
        # create rounded mask for nicer look
        w, h = im.size
        mask = Image.new("L", (w, h), 0)
        draw_mask = ImageDraw.Draw(mask)
        radius = min(w, h) // 6
        draw_mask.rounded_rectangle([0,0,w,h], radius=radius, fill=255)
        # create background box
        bg = Image.new("RGBA", (w, h), (255,255,255,0))
        base_img.paste(im, (box_x, box_y), mask)
        return True
    except Exception:
        return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="social_preview.png")
    ap.add_argument("--title", default="username/repo")
    ap.add_argument("--subtitle", default="A concise project description.")
    ap.add_argument("--author", default="")
    ap.add_argument("--sha", default="")
    ap.add_argument("--logo", default="assets/brand-logo.png")
    ap.add_argument("--github-mark", default="assets/github-mark.png")
    args = ap.parse_args()

    W, H = 1280, 640
    BG = (255,255,255)
    TEXT = (24, 28, 32)
    SUBTEXT = (95, 106, 118)
    stats_color = (96, 110, 125)

    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    left = 100
    right = W - 260
    maxw = right - left

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

    # owner small
    if owner:
        owner_text = f"{owner}/"
        draw.text((left, y), owner_text, font=font_owner, fill=SUBTEXT)
        ow, oh = measure(draw, owner_text, font_owner)
        y += oh + 10

    # repo (bold) — reduce size to fit if necessary
    rw, rh = measure(draw, repo, font_repo)
    if rw > maxw:
        for s in range(64, 28, -2):
            font_repo = load_font(FONT_BOLD, s)
            rw, rh = measure(draw, repo, font_repo)
            if rw <= maxw:
                break
    draw.text((left, y), repo, font=font_repo, fill=TEXT)
    y += rh + 20

    # subtitle
    desc = args.subtitle or ""
    lines = wrap_text(desc, font_desc, maxw, draw)[:3]
    for line in lines:
        draw.text((left, y), line, font=font_desc, fill=SUBTEXT)
        _, lh = measure(draw, line, font_desc)
        y += lh + 6

    # stats row
    y += 24
    draw_stats(draw, left, y, font_stats, stats_color)

    # meta bottom-left (author + sha)
    meta = ""
    if args.author:
        meta = f"by {args.author}"
    if args.sha:
        meta = meta + (" • " if meta else "") + args.sha[:7]
    if meta:
        draw.text((left, H - 60), meta, font=font_stats, fill=SUBTEXT)

    # place profile avatar if exists (top-right)
    logo_path = args.logo
    if os.path.exists(logo_path):
        # draw small white rounded square bg then paste avatar so it stands out
        try:
            avatar = Image.open(logo_path).convert("RGBA")
            # make thumbnail
            avatar.thumbnail((180,180))
            av_w, av_h = avatar.size
            # position top-right
            lx = W - 260 + (260 - av_w) // 2
            ly = 100
            # paste with mask for transparency
            img.paste(avatar, (lx, ly), avatar)
        except Exception:
            pass

    # bottom color bar (two segments)
    bar_h = 18
    # left segment - warm red/orange
    left_color = (232, 76, 61)    # warm red
    # right segment - blue
    right_color = (44, 111, 180)  # blue
    # draw left ~60% and right ~40% (like GitHub sample)
    split = int(W * 0.6)
    draw.rectangle([0, H - bar_h, split, H], fill=left_color)
    draw.rectangle([split, H - bar_h, W, H], fill=right_color)

    # small github mark bottom-right (above the bar)
    gh_path = args.github_mark if hasattr(args, "github_mark") else "assets/github-mark.png"
    if os.path.exists(gh_path):
        try:
            gh = Image.open(gh_path).convert("RGBA")
            gh.thumbnail((36, 36))
            gx = W - 48 - gh.size[0]
            gy = H - bar_h - gh.size[1] - 12
            img.paste(gh, (gx, gy), gh)
        except Exception:
            pass
    else:
        # fallback: draw a subtle circle placeholder where GitHub icon would be
        gx = W - 48 - 30
        gy = H - bar_h - 30 - 12
        draw.ellipse([gx, gy, gx+30, gy+30], fill=(240,240,240))

    # save
    img.save(args.output, quality=95)
    print("Generated", args.output)

if __name__ == "__main__":
    main()
