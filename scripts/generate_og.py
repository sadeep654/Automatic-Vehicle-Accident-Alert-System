#!/usr/bin/env python3
"""
OG card generator — guaranteed bottom bar + visible GitHub mark fallback.
Saves: social_preview.png
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
        b = draw.textbbox((0,0), text, font=font)
        return b[2]-b[0], b[3]-b[1]
    except Exception:
        try:
            return font.getsize(text)
        except Exception:
            return (len(text)*6, 20)

def wrap_text(text, font, max_w, draw):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        test = cur + (" " if cur else "") + w
        w_px, _ = measure(draw, test, font)
        if w_px <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def draw_stats(draw, x, y, font, color):
    items = [("Contributors", "1"), ("Issues", "0"), ("Stars", "0"), ("Forks", "0")]
    spacing = 64
    for label, count in items:
        text = f"{count} {label}"
        draw.text((x, y), text, font=font, fill=color)
        w, _ = measure(draw, text, font)
        x += w + spacing

def draw_github_fallback(draw, gx, gy):
    # Draw a small rounded square with "GH" letters so it is always visible
    box_w = 40
    box_h = 40
    r = 6
    rect = [gx, gy, gx + box_w, gy + box_h]
    draw.rounded_rectangle(rect, radius=r, fill=(36, 41, 46))
    # GH text
    try:
        f = load_font(FONT_BOLD, 18)
    except:
        f = load_font(FONT_REGULAR, 14)
    tw, th = measure(draw, "GH", f)
    tx = gx + (box_w - tw) // 2
    ty = gy + (box_h - th) // 2 - 1
    draw.text((tx, ty), "GH", font=f, fill=(255,255,255))
    print("Placed fallback GH mark at", gx, gy)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="social_preview.png")
    ap.add_argument("--title", default="username/repo")
    ap.add_argument("--subtitle", default="A project description.")
    ap.add_argument("--author", default="")
    ap.add_argument("--sha", default="")
    ap.add_argument("--logo", default="assets/brand-logo.png")
    ap.add_argument("--github-mark", default="assets/github-mark.png")
    args = ap.parse_args()

    W, H = 1280, 640
    BG = (255,255,255)
    TEXT = (28,32,36)
    SUB = (98,108,118)
    STATS = (100,110,124)

    img = Image.new("RGB", (W,H), BG)
    draw = ImageDraw.Draw(img)

    left = 100
    right = W - 260
    maxw = right - left

    raw = args.title or "unknown/repo"
    if "/" in raw:
        owner, repo = raw.split("/", 1)
    else:
        owner, repo = "", raw

    f_owner = load_font(FONT_REGULAR, 28)
    f_repo = load_font(FONT_BOLD, 64)
    f_desc = load_font(FONT_REGULAR, 26)
    f_stats = load_font(FONT_REGULAR, 22)

    y = 120
    if owner:
        owner_text = f"{owner}/"
        draw.text((left, y), owner_text, font=f_owner, fill=SUB)
        ow, oh = measure(draw, owner_text, f_owner)
        y += oh + 10

    # shrink repo text to fit width if needed
    rw, rh = measure(draw, repo, f_repo)
    if rw > maxw:
        for s in range(64, 28, -2):
            f_repo = load_font(FONT_BOLD, s)
            rw, rh = measure(draw, repo, f_repo)
            if rw <= maxw:
                break
    draw.text((left, y), repo, font=f_repo, fill=TEXT)
    y += rh + 18

    # description wrap (max 3 lines)
    desc = args.subtitle or ""
    lines = wrap_text(desc, f_desc, maxw, draw)[:3]
    for line in lines:
        draw.text((left, y), line, font=f_desc, fill=SUB)
        _, lh = measure(draw, line, f_desc)
        y += lh + 6

    # stats
    y += 18
    draw_stats(draw, left, y, f_stats, STATS)

    # meta bottom-left
    meta = ""
    if args.author:
        meta = f"by {args.author}"
    if args.sha:
        meta = meta + (" • " if meta else "") + args.sha[:7]
    if meta:
        draw.text((left, H-64), meta, font=f_stats, fill=SUB)

    # avatar/logo top-right (if exists)
    logo_ok = False
    if os.path.exists(args.logo):
        try:
            avatar = Image.open(args.logo).convert("RGBA")
            avatar.thumbnail((180,180))
            av_w, av_h = avatar.size
            lx = W - 260 + (260 - av_w)//2
            ly = 100
            img.paste(avatar, (lx, ly), avatar)
            logo_ok = True
            print("Placed avatar from", args.logo)
        except Exception as e:
            print("Avatar paste error:", e)

    # bottom colour bar (two colors)
    bar_h = 18
    left_color = (232,76,61)    # warm red
    right_color = (44,111,180)  # blue
    split = int(W * 0.6)
    # draw entire bar region explicitly so it's always visible
    draw.rectangle([0, H-bar_h, split, H], fill=left_color)
    draw.rectangle([split, H-bar_h, W, H], fill=right_color)

    # place GitHub mark (icon) above the bar right side
    gh_path = args.github_mark
    gh_placed = False
    if os.path.exists(gh_path):
        try:
            gh = Image.open(gh_path).convert("RGBA")
            gh.thumbnail((36,36))
            gx = W - 48 - gh.size[0]
            gy = H - bar_h - gh.size[1] - 12
            img.paste(gh, (gx, gy), gh)
            gh_placed = True
            print("Placed github-mark from", gh_path)
        except Exception as e:
            print("Error placing github mark:", e)

    if not gh_placed:
        # draw fallback so it's always visible
        gx = W - 48 - 40
        gy = H - bar_h - 40 - 12
        draw_github_fallback(draw, gx, gy)

    # write file and exit
    img.save(args.output, quality=95)
    print("Generated", args.output, "| bottom bar drawn | github mark placed:", gh_placed)

if __name__ == "__main__":
    main()
