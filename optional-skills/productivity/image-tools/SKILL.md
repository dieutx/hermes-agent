---
name: image-tools
description: "Use this skill any time image files need processing — converting between formats (PNG, JPEG, WebP, TIFF, BMP, GIF, AVIF, ICO, and 60+ more); resizing or scaling images; compressing to reduce file size; creating thumbnails; combining images into a PDF; removing EXIF metadata for privacy; batch converting directories; or inspecting image metadata. Trigger whenever the user mentions \"convert image,\" \"resize,\" \"compress,\" \"thumbnail,\" \"images to PDF,\" \"strip EXIF,\" \"image format,\" \"PNG to JPEG,\" \"WebP,\" or any image processing operation."
version: 1.0.0
author: dieutx
license: MIT
metadata:
  hermes:
    tags: [Image, Convert, Resize, Compress, Thumbnail, PDF, EXIF, PNG, JPEG, WebP, TIFF, GIF, AVIF, Pillow]
    related_skills: [qr-code, meme-generation, nano-pdf]
  prerequisites:
    pip: [Pillow]
---

# Image Processing Tool

9 commands for image conversion, manipulation, and PDF generation across 70+ formats.

## Quick Reference

| Task | Command |
|------|---------|
| Convert format | `python3 image_tool.py convert input.png output.jpg` |
| Resize | `python3 image_tool.py resize input.jpg -o out.jpg --width 800` |
| Compress | `python3 image_tool.py compress input.jpg -o out.jpg --quality 60` |
| Thumbnail | `python3 image_tool.py thumbnail input.jpg -o thumb.jpg --size 200` |
| Images → PDF | `python3 image_tool.py to-pdf img1.jpg img2.png -o doc.pdf` |
| Strip EXIF | `python3 image_tool.py strip photo.jpg -o clean.jpg` |
| Image info | `python3 image_tool.py info photo.jpg --exif` |
| Batch convert | `python3 image_tool.py batch ./photos/ --format webp` |
| List formats | `python3 image_tool.py formats` |

Script path: `~/.hermes/skills/productivity/image-tools/scripts/image_tool.py`

---

## Converting Between Formats

Supports 70+ readable formats and 10+ writable formats. Format is detected from the output file extension.

```bash
# Common conversions
python3 image_tool.py convert photo.png photo.jpg
python3 image_tool.py convert photo.png photo.webp
python3 image_tool.py convert photo.bmp photo.png
python3 image_tool.py convert photo.tiff photo.jpg --quality 90

# iPhone photos
python3 image_tool.py convert photo.heic photo.jpg

# To PDF (single image)
python3 image_tool.py convert diagram.png diagram.pdf
```

**Transparency handling:** When converting RGBA/transparent PNGs to JPEG (no transparency support), the tool auto-flattens to white background.

**Common conversions and why:**

| From → To | Size change | Use case |
|-----------|-------------|----------|
| PNG → JPEG | -70-90% | Photos, no transparency needed |
| PNG → WebP | -50-80% | Modern web, keeps transparency |
| JPEG → WebP | -30-50% | Smaller files, modern format |
| BMP → PNG | -80-95% | Lossless compression |
| TIFF → JPEG | -90%+ | Universal compatibility |

---

## Resizing Images

```bash
# By width (auto-scales height to keep aspect ratio)
python3 image_tool.py resize photo.jpg -o small.jpg --width 800

# By height
python3 image_tool.py resize photo.jpg -o small.jpg --height 600

# By both (may stretch)
python3 image_tool.py resize photo.jpg -o exact.jpg --width 800 --height 600

# By scale factor
python3 image_tool.py resize photo.jpg -o half.jpg --scale 0.5
```

Safety cap: maximum 20,000px per side.

---

## Compressing Images

```bash
python3 image_tool.py compress photo.jpg -o compressed.jpg --quality 60
python3 image_tool.py compress photo.jpg -o tiny.jpg --quality 30
```

**Quality guide:**

| Quality | Reduction | Visual |
|---------|-----------|--------|
| 85 | ~30% | Imperceptible |
| 60 | ~50-60% | Slight softening |
| 30 | ~70-80% | Visible artifacts |

---

## Images to PDF

Combine multiple images into a single PDF document. Each image becomes one page.

```bash
# Basic — each image as a page
python3 image_tool.py to-pdf scan1.jpg scan2.jpg scan3.jpg -o document.pdf

# Fit images to A4 page size
python3 image_tool.py to-pdf photo1.jpg photo2.jpg -o album.pdf --fit-page

# Landscape orientation
python3 image_tool.py to-pdf slide1.png slide2.png -o slides.pdf --fit-page --landscape
```

Use cases:
- **Document scanning** — combine scanned pages into one PDF
- **Photo albums** — create printable photo collections
- **Presentation export** — convert slide images to PDF
- **Report assembly** — combine charts and diagrams

Maximum 200 images per PDF. Transparent images auto-flattened to white background.

---

## Strip EXIF (Privacy)

Remove metadata (camera model, GPS location, timestamps) from photos before sharing:

```bash
python3 image_tool.py strip photo.jpg -o clean.jpg
python3 image_tool.py strip selfie.jpg -o safe_selfie.jpg --quality 90
```

Reports how many EXIF fields were removed.

---

## Thumbnails

```bash
python3 image_tool.py thumbnail photo.jpg -o thumb.jpg --size 200
python3 image_tool.py thumbnail photo.jpg -o icon.png --size 64
```

---

## Image Info

```bash
python3 image_tool.py info photo.jpg
python3 image_tool.py info photo.jpg --exif
```

Returns: format, dimensions, megapixels, color mode, file size, and optionally full EXIF metadata.

---

## Batch Convert

```bash
python3 image_tool.py batch ./photos/ --format webp
python3 image_tool.py batch ./screenshots/ --format jpg --quality 80 --output-dir ./converted/
```

Maximum 500 files per batch. Skips non-image files automatically.

---

## Pitfalls

- **JPEG no transparency** — converting RGBA/transparent to JPEG auto-flattens to white background. Use WebP or PNG to keep transparency.
- **Quality parameter** — only affects JPEG, WebP, and AVIF. PNG is always lossless.
- **Batch cap** — maximum 500 files per batch.
- **PDF cap** — maximum 200 images per PDF.
- **Resize safety** — maximum 20,000px per side to prevent memory issues.
- **HEIC/HEIF** — reading requires `pillow-heif` plugin: `pip install pillow-heif`
- **EXIF strip** — creates a clean copy; GPS, camera info, and timestamps are removed.

---

## Dependencies

```bash
pip install Pillow
pip install pillow-heif  # optional, for HEIC/HEIF (iPhone photos)
```
