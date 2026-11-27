#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""글마다 표지 이미지를 무료로(외부 API 없이) 생성한다. og:image / 목록 썸네일용."""
import hashlib
import os
import textwrap

from PIL import Image, ImageDraw, ImageFont

FONT_BOLD = r"C:\Windows\Fonts\malgunbd.ttf"
FONT_REG = r"C:\Windows\Fonts\malgun.ttf"
W, H = 1200, 630

PALETTES = [
    ((37, 99, 235), (29, 78, 216)),   # blue
    ((234, 88, 12), (194, 65, 12)),    # orange
    ((5, 150, 105), (4, 120, 87)),     # green
    ((124, 58, 237), (109, 40, 217)),  # purple
]


def pick_palette(key):
    idx = int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16) % len(PALETTES)
    return PALETTES[idx]


def make_cover(title, out_path, brand="생활정보 꿀팁"):
    top, bottom = pick_palette(title)
    img = Image.new("RGB", (W, H), top)
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    title_font = ImageFont.truetype(FONT_BOLD, 64)
    brand_font = ImageFont.truetype(FONT_REG, 32)

    wrapped = textwrap.wrap(title, width=16)[:4]
    total_h = len(wrapped) * 78
    y = (H - total_h) / 2 - 20
    for line in wrapped:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        w = bbox[2] - bbox[0]
        draw.text(((W - w) / 2 + 3, y + 3), line, font=title_font, fill=(0, 0, 0, 80))
        draw.text(((W - w) / 2, y), line, font=title_font, fill="white")
        y += 78

    draw.text((40, H - 70), brand, font=brand_font, fill=(255, 255, 255, 230))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, "JPEG", quality=88)


if __name__ == "__main__":
    import sys
    make_cover(sys.argv[1], sys.argv[2])
    print("saved", sys.argv[2])
