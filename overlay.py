#!/usr/bin/env python3
"""
overlay.py - Draw text (with emoji) or image overlay onto product images from CSV.

CSV format (no header, one output image per row):
  type, value, output_filename

  type = "text" or "image"
  value = the text string (emoji supported), OR path to overlay image (png recommended)

Examples:
  text,  "📏 200x200mm ⌀1,0mm", image001.jpg
  image, /path/to/logo.png,      image002.jpg

Usage:
  python overlay.py \
    --image base.jpg \
    --csv attributes.csv \
    --output-dir output \
    --font ~/Library/Fonts/IBMPlexSans-Medium.ttf \
    --font-size 48 \
    --color "#333333" \
    --position bottom-left \
    --x 20 --y 20 \
    --overlay-size 150

Emoji support:
  pip install pilmoji --break-system-packages
  (falls back to plain Pillow if not installed, emoji will render as boxes)

Requirements:
  pip install pillow --break-system-packages
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


def get_xy(anchor, img_w, img_h, obj_w, obj_h, ox, oy):
    positions = {
        "top-left": (ox, oy),
        "top-right": (img_w - obj_w - ox, oy),
        "bottom-left": (ox, img_h - obj_h - oy),
        "bottom-right": (img_w - obj_w - ox, img_h - obj_h - oy),
        "center": ((img_w - obj_w) // 2, (img_h - obj_h) // 2),
    }
    return positions[anchor]


def measure_text(img, label, font):
    """Measure text size, using pilmoji if available."""
    if HAS_PILMOJI:
        with Pilmoji(img) as pj:
            size = pj.getsize(label, font)
            return size[0], size[1]
    else:
        draw = ImageDraw.Draw(img)
        bbox = draw.textbbox((0, 0), label, font=font)
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


def draw_image(img, overlay_path, overlay_width, position, ox, oy):
    overlay = Image.open(os.path.expanduser(overlay_path)).convert("RGBA")
    ratio = overlay_width / overlay.width
    new_h = int(overlay.height * ratio)
    overlay = overlay.resize((overlay_width, new_h), Image.LANCZOS)
    x, y = get_xy(position, img.width, img.height, overlay_width, new_h, ox, oy)
    img.paste(overlay, (x, y), mask=overlay)
    return overlay_width, new_h, x, y


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--image", required=True, help="Base product image")
    p.add_argument("--csv", required=True, help="CSV: type, value, output_filename")
    p.add_argument("--output-dir", default="output", help="Output folder")
    p.add_argument(
        "--font", default=None, help="Path to .ttf font (required for text rows)"
    )
    p.add_argument("--font-size", type=int, default=48, help="Font size (default: 48)")
    p.add_argument(
        "--color", default="#333333", help="Text color hex (default: #333333)"
    )
    p.add_argument(
        "--x", type=int, default=20, help="Horizontal offset px (default: 20)"
    )
    p.add_argument("--y", type=int, default=20, help="Vertical offset px (default: 20)")
    p.add_argument(
        "--position",
        default="bottom-left",
        choices=["top-left", "top-right", "bottom-left", "bottom-right", "center"],
        help="Anchor position (default: bottom-left)",
    )
    p.add_argument(
        "--overlay-size",
        type=int,
        default=150,
        help="Image overlay width in px (default: 150)",
    )
    args = p.parse_args()

    if HAS_PILMOJI:
        print("✓ pilmoji found — emoji rendering enabled")
    else:
        print("⚠ pilmoji not found — emoji will render as boxes")
        print("  Fix: pip install pilmoji --break-system-packages\n")

    image_path = os.path.expanduser(args.image)
    if not os.path.exists(image_path):
        print(f"ERROR: Base image not found: {image_path}")
        return

    font = None
    if args.font:
        font_path = os.path.expanduser(args.font)
        if not os.path.exists(font_path):
            print(f"ERROR: Font not found: {font_path}")
            return
        font = ImageFont.truetype(font_path, args.font_size)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    base = Image.open(image_path)
    print(f"Base image: {base.width}x{base.height}px")

    with open(args.csv, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    print(f"Processing {len(rows)} rows...\n")

    for i, row in enumerate(rows):
        if not row:
            continue

        row_type = row[0].strip().lower()
        value = row[1].strip() if len(row) > 1 else ""
        out_name = (
            row[2].strip()
            if len(row) > 2 and row[2].strip()
            else f"image_{i+1:04d}.jpg"
        )
        if not Path(out_name).suffix:
            out_name += ".jpg"

        img = base.copy().convert("RGBA")

        if row_type == "text":
            if not font:
                print(f"  [{i+1}] SKIP: --font required for text rows")
                continue
            w, h, x, y = draw_text(
                img, value, font, args.color, args.position, args.x, args.y
            )
            print(f"  [{i+1}] text  '{value}' -> {out_name}  (at {x},{y}, {w}x{h}px)")

        elif row_type == "image":
            overlay_path = os.path.expanduser(value)
            if not os.path.exists(overlay_path):
                print(f"  [{i+1}] SKIP: overlay image not found: {overlay_path}")
                continue
            w, h, x, y = draw_image(
                img, overlay_path, args.overlay_size, args.position, args.x, args.y
            )
            print(f"  [{i+1}] image '{value}' -> {out_name}  (at {x},{y}, {w}x{h}px)")

        else:
            print(f"  [{i+1}] SKIP: unknown type '{row_type}' (use 'text' or 'image')")
            continue

        out_path = out_dir / out_name
        img.convert("RGB").save(str(out_path), quality=92)

    print(f"\nDone. Output in '{out_dir}/'")


if __name__ == "__main__":
    main()
