# overlay.py

Bulk-overlay text or logo images onto product images. Useful for e-commerce category pages where the same base image is reused across variants (sizes, diameters, etc.), or where each product has its own image.

---

## Install

```bash
pip install pillow pilmoji --break-system-packages
```

- **pillow** — image processing (required)
- **pilmoji** — emoji rendering in text (optional, falls back gracefully if missing)

---

## Usage

### Mode 1 — one base image, many outputs

```bash
python overlay.py \
  --image base.jpg \
  --csv attributes.csv \
  --output-dir output \
  --font ~/Library/Fonts/IBMPlexSans-Medium.ttf \
  --font-size 48 \
  --color "#333333" \
  --position bottom-left \
  --x 20 --y 20
```

### Mode 2 — different image per row (no --image needed)

```bash
python overlay.py \
  --csv attributes.csv \
  --output-dir output \
  --font ~/Library/Fonts/IBMPlexSans-Medium.ttf \
  --font-size 48 \
  --color "#333333" \
  --position bottom-left \
  --x 20 --y 20
```

Mode is **auto-detected** from the CSV — no flag needed.

---

## Arguments

| Argument | Required | Default | Description |
|---|---|---|---|
| `--image` | Mode 1 only | — | Base product image (jpg, png, webp) |
| `--csv` | ✓ | — | CSV file (see format below) |
| `--output-dir` | | `output` | Folder for output images |
| `--font` | ✓ for text | — | Path to .ttf font file (`~` supported) |
| `--font-size` | | `48` | Font size in pt |
| `--color` | | `#333333` | Text color as hex |
| `--position` | | `bottom-left` | Anchor: `top-left` `top-right` `bottom-left` `bottom-right` `center` |
| `--x` | | `20` | Horizontal offset from anchor in px |
| `--y` | | `20` | Vertical offset from anchor in px |
| `--overlay-size` | | `150` | Width in px for image overlays (height auto-scales) |

---

## CSV Format

No header row. Mode is detected automatically from the first column.

### Mode 1 — shared base image
First column is `text` or `image`:
```
type, value, output_filename
```

```
text,  "📏 200x200mm ⌀1,0mm", sku1321.jpg
text,  "📏 100x100mm ⌀1,2mm", sku1821.jpg
image, /path/to/logo.png,      sku1822.jpg
```

### Mode 2 — image per row
First column is the input image path:
```
input_image, type, value, output_filename
```

```
base1.jpg, text,  "200x200mm ⌀1,0mm",  sku1321.jpg
base2.jpg, text,  "100x100mm ⌀1,2mm",  sku1821.jpg
base3.jpg, image, /path/to/logo.png,    sku1822.jpg
```

### Column reference

| Column | Description |
|---|---|
| `input_image` | (Mode 2 only) Path to the base image for this row |
| `type` | `text` or `image` |
| `value` | Text string (emoji ok), or path to overlay PNG |
| `output_filename` | Output filename. Auto-named `image_0001.jpg` if omitted. |

> **Note:** If your text contains a comma (e.g. `⌀1,0mm`), wrap the value in double quotes.

---

## Font tips

**macOS** — list available fonts:
```bash
find /System/Library/Fonts /Library/Fonts ~/Library/Fonts -name "*.ttf" -o -name "*.ttc"
```

Common paths:
- `~/Library/Fonts/IBMPlexSans-Medium.ttf`
- `/System/Library/Fonts/Helvetica.ttc`
- `/Library/Fonts/Arial Bold.ttf`

**Linux:**
- `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf`
- `/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf`

---

## Emoji support

Install `pilmoji` for emoji rendering. The script prints on startup whether it's active:

```
✓ pilmoji enabled
⚠ pilmoji not found — emoji will render as boxes
```

Pilmoji fetches emoji from the [Twemoji](https://twemoji.twitter.com/) CDN at render time, so an internet connection is required when using emoji.
