# overlay.py

Bulk-overlay text or logo images onto product images. Useful for e-commerce category pages where the same base image is reused across variants (sizes, diameters, etc.).

---

## Install

```bash
pip install pillow pilmoji --break-system-packages
```

- **pillow** — image processing (required)
- **pilmoji** — emoji rendering in text (optional, falls back gracefully if missing)

---

## Usage

```bash
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
```

---

## Arguments

| Argument | Required | Default | Description |
|---|---|---|---|
| `--image` | ✓ | — | Base product image (jpg, png, webp) |
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

No header row. Three columns per line: `type, value, output_filename`

```
text,  "📏 200x200mm ⌀1,0mm", image001.jpg
text,  "📏 100x100mm ⌀1,2mm", image002.jpg
image, /path/to/logo.png,      image003.jpg
```

| Column | Description |
|---|---|
| `type` | `text` or `image` |
| `value` | Text string (emoji ok), or path to overlay PNG |
| `output_filename` | Output filename. Extension determines format (jpg/png). Auto-named `image_0001.jpg` if omitted. |

**Note:** If your text contains a comma (e.g. `⌀1,0mm`), wrap the value in double quotes.

---

## Examples

### Text overlay
```
text, "200x200mm", product-200x200.jpg
text, "📏 50×100 cm", foam-50x100.jpg
text, "⌀ 1,0mm / 5m", wire-1mm-5m.jpg
```

### Logo overlay
```
image, ~/assets/logo.png, product-with-logo.jpg
```

### Mixed
```
text,  "📏 200x200mm ⌀1,0mm", copper-200-1mm.jpg
image, ~/assets/badge.png,     copper-200-badge.jpg
text,  "📏 100x100mm ⌀1,2mm", copper-100-1mm.jpg
```

---

## Font tips

**macOS:**
```bash
# List available fonts
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
✓ pilmoji found — emoji rendering enabled
⚠ pilmoji not found — emoji will render as boxes
```

Pilmoji fetches emoji from the [Twemoji](https://twemoji.twitter.com/) CDN at render time, so an internet connection is required when using emoji.
