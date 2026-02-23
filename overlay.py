#!/usr/bin/env python3
"""
overlay.py - Bulk overlay text or image onto product images from CSV.

Two CSV modes:

  MODE 1 - single base image, multiple outputs:
    type, value, output_filename
    text, "📏 200x200mm ⌀1,0mm", image001.jpg
    image, /path/to/logo.png, image002.jpg

  MODE 2 - different base image per row:
    input_image, type, value, output_filename
    base1.jpg, text, "200x200cm 1mm", output-sku1321.jpg
    base2.jpg, image, /path/to/logo.png, output-sku1822.jpg

  The script auto-detects the mode based on whether the first column
  looks like a file path (ends in .jpg/.png/.webp etc.)

Usage:
  # Mode 1 - single base image
  python overlay.py \
    --image base.jpg \
    --csv attributes.csv \
    --font ~/Library/Fonts/IBMPlexSans-Medium.ttf \
    --font-size 48 --color "#333333" --position bottom-left --x 20 --y 20

  # Mode 2 - image per row (no --image needed)
  python overlay.py \
    --csv attributes.csv \
    --font ~/Library/Fonts/IBMPlexSans-Medium.ttf \
    --font-size 48 --color "#333333" --position bottom-left --x 20 --y 20

Requirements:
  pip install pillow pilmoji --break-system-packages
"""

import argparse
import csv
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

try:
    from pilmoji import Pilmoji
    HAS_PILMOJI = True
except ImportError:
    HAS_PILMOJI = False

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}


def is_image_path(value):
    return Path(value).suffix.lower() in IMAGE_EXTENSIONS


def get_xy(anchor, img_w, img_h, obj_w, obj_h, ox, oy):
    return {
        "top-left":     (ox, oy),
        "top-right":    (img_w - obj_w - ox, oy),
        "bottom-left":  (ox, img_h - obj_h - oy),
        "bottom-right": (img_w - obj_w - ox, img_h - obj_h - oy),
        "center":       ((img_w - obj_w) // 2, (img_h - obj_h) // 2),
    }[anchor]


def measure_text(img, label, font):
    if HAS_PILMOJI:
        with Pilmoji(img) as pj:
            s = pj.getsize(label, font)
            return s[0], s[1]
    bbox = ImageDraw.Draw(img).textbbox((0, 0), label, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_text(img, label, font, color, position, ox, oy):
    text_w, text_h = measure_text(img, label, font)
    x, y = get_xy(position, img.width, img.height, text_w, text_h, ox, oy)
    if HAS_PILMOJI:
        with Pilmoji(img) as pj:
            pj.text((x, y), label, font=font, fill=color)
    else:
        draw = ImageDraw.Draw(img)
        bbox = draw.textbbox((0, 0), label, font=font)
        draw.text((x - bbox[0], y - bbox[1]), label, font=font, fill=color)
    return text_w, text_h, x, y


def draw_image_overlay(img, overlay_path, overlay_width, position, ox, oy):
    overlay = Image.open(os.path.expanduser(overlay_path)).convert("RGBA")
    new_h   = int(overlay.height * overlay_width / overlay.width)
    overlay = overlay.resize((overlay_width, new_h), Image.LANCZOS)
    x, y    = get_xy(position, img.width, img.height, overlay_width, new_h, ox, oy)
    img.paste(overlay, (x, y), mask=overlay)
    return overlay_width, new_h, x, y


def process_row(base, row_type, value, out_path, font, args):
    img = base.copy().convert("RGBA")

    if row_type == "text":
        if not font:
            return "SKIP: --font required for text rows"
        w, h, x, y = draw_text(img, value, font, args.color, args.position, args.x, args.y)
        info = f"text '{value}' at {x},{y} ({w}x{h}px)"

    elif row_type == "image":
        overlay_path = os.path.expanduser(value)
        if not os.path.exists(overlay_path):
            return f"SKIP: overlay not found: {overlay_path}"
        w, h, x, y = draw_image_overlay(img, overlay_path, args.overlay_size, args.position, args.x, args.y)
        info = f"image '{value}' at {x},{y} ({w}x{h}px)"

    else:
        return f"SKIP: unknown type '{row_type}' (use 'text' or 'image')"

    img.convert("RGB").save(str(out_path), quality=92)
    return f"OK: {info} -> {out_path}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--image",        default=None,          help="Base image (Mode 1 only)")
    p.add_argument("--csv",          required=True,         help="CSV file")
    p.add_argument("--output-dir",   default="output",      help="Output folder (default: output)")
    p.add_argument("--font",         default=None,          help="Path to .ttf font")
    p.add_argument("--font-size",    type=int, default=48,  help="Font size pt (default: 48)")
    p.add_argument("--color",        default="#333333",     help="Text color hex (default: #333333)")
    p.add_argument("--position",     default="bottom-left",
                   choices=["top-left", "top-right", "bottom-left", "bottom-right", "center"])
    p.add_argument("--x",            type=int, default=20,  help="Horizontal offset px (default: 20)")
    p.add_argument("--y",            type=int, default=20,  help="Vertical offset px (default: 20)")
    p.add_argument("--overlay-size", type=int, default=150, help="Image overlay width px (default: 150)")
    args = p.parse_args()

    print(f"{'✓' if HAS_PILMOJI else '⚠'} pilmoji {'enabled' if HAS_PILMOJI else 'not found — emoji will render as boxes'}")

    font = None
    if args.font:
        font_path = os.path.expanduser(args.font)
        if not os.path.exists(font_path):
            print(f"ERROR: Font not found: {font_path}"); return
        font = ImageFont.truetype(font_path, args.font_size)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load base image for Mode 1
    base_image = None
    if args.image:
        image_path = os.path.expanduser(args.image)
        if not os.path.exists(image_path):
            print(f"ERROR: Base image not found: {image_path}"); return
        base_image = Image.open(image_path)
        print(f"Mode 1 — single base image: {image_path} ({base_image.width}x{base_image.height}px)")

    with open(args.csv, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.reader(f) if r]

    # Auto-detect mode from first row
    first = rows[0]
    mode2 = len(first) >= 4 or (len(first) >= 1 and is_image_path(first[0].strip()))

    if mode2:
        print(f"Mode 2 — image per row")
    elif not base_image:
        print("ERROR: Mode 1 requires --image"); return

    print(f"Processing {len(rows)} rows...\n")

    image_cache = {}

    for i, row in enumerate(rows):
        if mode2:
            if len(row) < 3:
                print(f"  [{i+1}] SKIP: not enough columns"); continue
            img_path  = os.path.expanduser(row[0].strip())
            row_type  = row[1].strip().lower()
            value     = row[2].strip()
            out_name  = row[3].strip() if len(row) > 3 and row[3].strip() else f"image_{i+1:04d}.jpg"

            if img_path not in image_cache:
                if not os.path.exists(img_path):
                    print(f"  [{i+1}] SKIP: input image not found: {img_path}"); continue
                image_cache[img_path] = Image.open(img_path)
            base = image_cache[img_path]
        else:
            row_type = row[0].strip().lower()
            value    = row[1].strip() if len(row) > 1 else ""
            out_name = row[2].strip() if len(row) > 2 and row[2].strip() else f"image_{i+1:04d}.jpg"
            base     = base_image

        if not Path(out_name).suffix:
            out_name += ".jpg"

        out_path = out_dir / out_name
        result   = process_row(base, row_type, value, out_path, font, args)
        print(f"  [{i+1}] {result}")

    print(f"\nDone. Output in '{out_dir}/'")


if __name__ == "__main__":
    main()
