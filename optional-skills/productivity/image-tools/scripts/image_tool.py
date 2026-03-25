#!/usr/bin/env python3
"""
Image Processing Tool for Hermes Agent
-----------------------------------------
Convert, resize, compress, inspect, and combine images across 70+ formats.

Architecture:
  - Format conversion with auto transparency handling (RGBA → JPEG)
  - Batch processing with 500-file safety cap
  - Images-to-PDF combining with layout options
  - EXIF metadata extraction
  - All output as structured JSON

Security:
  - Resize capped at 20,000px per side to prevent memory exhaustion
  - Batch capped at 500 files
  - PDF page cap at 200 images
  - No shell/subprocess/eval — pure Pillow library calls

Requires: pip install Pillow

Usage:
  python3 image_tool.py info      image.png [--exif]
  python3 image_tool.py convert   input.png output.jpg [--quality 85]
  python3 image_tool.py resize    input.jpg -o out.jpg --width 800
  python3 image_tool.py compress  input.jpg -o out.jpg --quality 60
  python3 image_tool.py thumbnail input.jpg -o thumb.jpg --size 200
  python3 image_tool.py batch     ./photos/ --format webp
  python3 image_tool.py to-pdf    img1.jpg img2.png -o combined.pdf
  python3 image_tool.py formats
  python3 image_tool.py strip     input.jpg -o clean.jpg
"""

import argparse
import json
import os
import sys
from typing import Optional, List


def _check_pillow():
    try:
        from PIL import Image  # noqa: F401
        return True
    except ImportError:
        sys.exit("Pillow not installed.\n  pip install Pillow\n")


def _file_size_str(path: str) -> str:
    size = os.path.getsize(path)
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024*1024):.1f} MB"


def _get_save_kwargs(ext: str, quality: int = 85) -> dict:
    """Get format-specific save parameters."""
    ext = ext.lower()
    kwargs = {}
    if ext in (".jpg", ".jpeg"):
        kwargs["quality"] = quality
        kwargs["optimize"] = True
    elif ext == ".webp":
        kwargs["quality"] = quality
        kwargs["method"] = 4
    elif ext == ".png":
        kwargs["optimize"] = True
    elif ext == ".tiff" or ext == ".tif":
        kwargs["compression"] = "tiff_deflate"
    elif ext == ".avif":
        kwargs["quality"] = quality
    return kwargs


def cmd_info(args):
    """Show image metadata: format, size, mode, file size."""
    _check_pillow()
    from PIL import Image
    from PIL.ExifTags import TAGS

    if not os.path.exists(args.file):
        sys.exit(f"File not found: {args.file}")

    img = Image.open(args.file)
    out = {
        "file": args.file,
        "format": img.format,
        "mode": img.mode,
        "width": img.size[0],
        "height": img.size[1],
        "megapixels": round(img.size[0] * img.size[1] / 1_000_000, 2),
        "file_size": _file_size_str(args.file),
        "file_size_bytes": os.path.getsize(args.file),
    }

    # EXIF data
    if args.exif:
        exif = {}
        raw_exif = img.getexif()
        if raw_exif:
            for tag_id, value in raw_exif.items():
                tag = TAGS.get(tag_id, tag_id)
                try:
                    exif[str(tag)] = str(value)[:200]
                except Exception:
                    pass
        out["exif"] = exif if exif else "no EXIF data"

    img.close()
    print(json.dumps(out, indent=2, default=str))


def cmd_convert(args):
    """Convert image between formats."""
    _check_pillow()
    from PIL import Image

    if not os.path.exists(args.input):
        sys.exit(f"File not found: {args.input}")

    img = Image.open(args.input)
    original_format = img.format
    original_size = os.path.getsize(args.input)

    # Handle mode conversion for format compatibility
    out_ext = os.path.splitext(args.output)[1].lower()
    if out_ext in (".jpg", ".jpeg") and img.mode in ("RGBA", "P", "LA"):
        # JPEG doesn't support transparency — flatten to white background
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        background.paste(img, mask=img.split()[-1] if "A" in img.mode else None)
        img = background
    elif out_ext in (".jpg", ".jpeg") and img.mode != "RGB":
        img = img.convert("RGB")

    kwargs = _get_save_kwargs(out_ext, args.quality)
    img.save(args.output, **kwargs)
    img.close()

    new_size = os.path.getsize(args.output)
    print(json.dumps({
        "converted": args.output,
        "from_format": original_format,
        "to_format": out_ext.replace(".", "").upper(),
        "original_size": _file_size_str(args.input),
        "new_size": _file_size_str(args.output),
        "size_change": f"{((new_size - original_size) / original_size * 100):+.1f}%",
    }, indent=2))


def cmd_resize(args):
    """Resize an image by width, height, or scale factor."""
    _check_pillow()
    from PIL import Image

    if not os.path.exists(args.input):
        sys.exit(f"File not found: {args.input}")

    img = Image.open(args.input)
    orig_w, orig_h = img.size

    if args.scale:
        new_w = int(orig_w * args.scale)
        new_h = int(orig_h * args.scale)
    elif args.width and args.height:
        new_w, new_h = args.width, args.height
    elif args.width:
        ratio = args.width / orig_w
        new_w = args.width
        new_h = int(orig_h * ratio)
    elif args.height:
        ratio = args.height / orig_h
        new_w = int(orig_w * ratio)
        new_h = args.height
    else:
        sys.exit("Specify --width, --height, or --scale")

    # Safety cap
    if new_w > 20000 or new_h > 20000:
        sys.exit(f"Output too large: {new_w}x{new_h}. Maximum 20000px per side.")

    resampling = Image.LANCZOS
    img = img.resize((new_w, new_h), resampling)

    output = args.output or args.input
    out_ext = os.path.splitext(output)[1].lower()
    kwargs = _get_save_kwargs(out_ext, args.quality)

    if out_ext in (".jpg", ".jpeg") and img.mode != "RGB":
        img = img.convert("RGB")

    img.save(output, **kwargs)
    img.close()

    print(json.dumps({
        "resized": output,
        "from": f"{orig_w}x{orig_h}",
        "to": f"{new_w}x{new_h}",
        "file_size": _file_size_str(output),
    }, indent=2))


def cmd_compress(args):
    """Compress image to reduce file size."""
    _check_pillow()
    from PIL import Image

    if not os.path.exists(args.input):
        sys.exit(f"File not found: {args.input}")

    img = Image.open(args.input)
    original_size = os.path.getsize(args.input)

    output = args.output or args.input
    out_ext = os.path.splitext(output)[1].lower()

    if out_ext in (".jpg", ".jpeg") and img.mode != "RGB":
        img = img.convert("RGB")

    kwargs = _get_save_kwargs(out_ext, args.quality)
    img.save(output, **kwargs)
    img.close()

    new_size = os.path.getsize(output)
    saved = original_size - new_size
    pct = (saved / original_size * 100) if original_size > 0 else 0

    print(json.dumps({
        "compressed": output,
        "original_size": _file_size_str(args.input),
        "new_size": _file_size_str(output),
        "saved": _file_size_str(args.input).replace(_file_size_str(args.input), f"{saved} bytes"),
        "reduction": f"{pct:.1f}%",
        "quality": args.quality,
    }, indent=2))


def cmd_thumbnail(args):
    """Create a thumbnail (preserves aspect ratio)."""
    _check_pillow()
    from PIL import Image

    if not os.path.exists(args.input):
        sys.exit(f"File not found: {args.input}")

    img = Image.open(args.input)
    orig_w, orig_h = img.size

    size = args.size
    img.thumbnail((size, size), Image.LANCZOS)

    output = args.output or f"thumb_{os.path.basename(args.input)}"
    out_ext = os.path.splitext(output)[1].lower()
    if out_ext in (".jpg", ".jpeg") and img.mode != "RGB":
        img = img.convert("RGB")

    kwargs = _get_save_kwargs(out_ext, 85)
    img.save(output, **kwargs)
    img.close()

    print(json.dumps({
        "thumbnail": output,
        "original": f"{orig_w}x{orig_h}",
        "size": f"{img.size[0]}x{img.size[1]}",
        "max_dimension": size,
    }, indent=2))


def cmd_batch(args):
    """Batch convert all images in a directory."""
    _check_pillow()
    from PIL import Image

    if not os.path.isdir(args.input_dir):
        sys.exit(f"Directory not found: {args.input_dir}")

    output_dir = args.output_dir or args.input_dir + "_converted"
    os.makedirs(output_dir, exist_ok=True)

    target_ext = f".{args.format.lower().strip('.')}"
    image_exts = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif",
                  ".webp", ".ico", ".psd", ".avif", ".heic", ".heif"}

    converted = []
    errors = []
    max_files = 500  # safety cap

    for fname in sorted(os.listdir(args.input_dir)):
        if len(converted) >= max_files:
            break
        ext = os.path.splitext(fname)[1].lower()
        if ext not in image_exts:
            continue

        src = os.path.join(args.input_dir, fname)
        out_name = os.path.splitext(fname)[0] + target_ext
        dst = os.path.join(output_dir, out_name)

        try:
            img = Image.open(src)
            if target_ext in (".jpg", ".jpeg") and img.mode != "RGB":
                if img.mode in ("RGBA", "P", "LA"):
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    bg.paste(img, mask=img.split()[-1] if "A" in img.mode else None)
                    img = bg
                else:
                    img = img.convert("RGB")

            kwargs = _get_save_kwargs(target_ext, args.quality)
            img.save(dst, **kwargs)
            img.close()
            converted.append({"src": fname, "dst": out_name})
        except Exception as e:
            errors.append({"file": fname, "error": str(e)})

    print(json.dumps({
        "output_dir": output_dir,
        "target_format": target_ext.replace(".", "").upper(),
        "converted": len(converted),
        "errors": len(errors),
        "files": converted[:20],  # show first 20
        "error_details": errors[:10] if errors else [],
    }, indent=2))


def cmd_formats(args):
    """List all supported image formats."""
    _check_pillow()
    from PIL import Image

    read_exts = sorted(Image.registered_extensions().keys())
    # Common writable formats
    write_fmts = ["PNG", "JPEG", "WEBP", "GIF", "BMP", "TIFF", "ICO", "PDF", "PPM"]
    try:
        # Check AVIF support
        Image.new("RGB", (1, 1)).save("/dev/null", "AVIF")
        write_fmts.append("AVIF")
    except Exception:
        pass

    print(json.dumps({
        "readable_extensions": read_exts,
        "readable_count": len(read_exts),
        "writable_formats": sorted(write_fmts),
        "common_conversions": [
            "PNG → JPEG (reduce size, lose transparency)",
            "JPEG → WEBP (30-50% smaller, modern format)",
            "PNG → WEBP (much smaller, keeps transparency)",
            "BMP → PNG (lossless compression)",
            "TIFF → JPEG (universal compatibility)",
            "HEIC → JPEG (iPhone photos → universal)",
            "GIF → WEBP (animated, smaller file)",
        ],
    }, indent=2))


def cmd_to_pdf(args):
    """Combine multiple images into a single PDF document."""
    _check_pillow()
    from PIL import Image

    files = args.images
    if not files:
        sys.exit("No images specified.")

    # Safety cap
    if len(files) > 200:
        sys.exit(f"Too many images ({len(files)}). Maximum 200 per PDF.")

    # Validate all files exist
    for f in files:
        if not os.path.exists(f):
            sys.exit(f"File not found: {f}")

    output = args.output or "combined.pdf"

    images = []
    errors = []

    for f in files:
        try:
            img = Image.open(f)
            # Convert to RGB (PDF doesn't support RGBA/P modes well)
            if img.mode in ("RGBA", "P", "LA"):
                bg = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                bg.paste(img, mask=img.split()[-1] if "A" in img.mode else None)
                img = bg
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # Optional resize to fit standard page (A4-ish)
            if args.fit_page:
                # A4 at 150 DPI: 1240 x 1754 px
                page_w, page_h = 1240, 1754
                if args.landscape:
                    page_w, page_h = page_h, page_w
                img.thumbnail((page_w, page_h), Image.LANCZOS)

            images.append(img)
        except Exception as e:
            errors.append({"file": f, "error": str(e)})

    if not images:
        sys.exit("No valid images to combine.")

    # Save as multi-page PDF
    first = images[0]
    rest = images[1:] if len(images) > 1 else []
    first.save(output, "PDF", save_all=True, append_images=rest, resolution=150.0)

    # Close all
    for img in images:
        img.close()

    print(json.dumps({
        "created": output,
        "pages": len(images),
        "errors": len(errors),
        "file_size": _file_size_str(output),
        "error_details": errors[:10] if errors else [],
    }, indent=2))


def cmd_strip(args):
    """Remove EXIF metadata from an image (privacy cleanup)."""
    _check_pillow()
    from PIL import Image

    if not os.path.exists(args.input):
        sys.exit(f"File not found: {args.input}")

    img = Image.open(args.input)
    output = args.output or args.input

    # Create a clean copy without EXIF
    clean = Image.new(img.mode, img.size)
    clean.putdata(list(img.getdata()))

    ext = os.path.splitext(output)[1].lower()
    kwargs = _get_save_kwargs(ext, args.quality)
    if ext in (".jpg", ".jpeg") and clean.mode != "RGB":
        clean = clean.convert("RGB")

    clean.save(output, **kwargs)

    # Check what was removed
    original_exif = img.getexif()
    fields_removed = len(original_exif) if original_exif else 0

    img.close()
    clean.close()

    print(json.dumps({
        "stripped": output,
        "source": args.input,
        "exif_fields_removed": fields_removed,
        "original_size": _file_size_str(args.input),
        "new_size": _file_size_str(output),
    }, indent=2))


def main():
    parser = argparse.ArgumentParser(
        prog="image_tool.py",
        description="Image processing tool — convert, resize, compress, combine to PDF",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # info
    p_info = sub.add_parser("info", help="Image metadata: format, size, mode, EXIF")
    p_info.add_argument("file")
    p_info.add_argument("--exif", action="store_true", help="Include EXIF data")

    # convert
    p_conv = sub.add_parser("convert", help="Convert between image formats")
    p_conv.add_argument("input", help="Source image")
    p_conv.add_argument("output", help="Output path (format from extension)")
    p_conv.add_argument("--quality", type=int, default=85, help="Quality 1-100 (JPEG/WebP, default: 85)")

    # resize
    p_rsz = sub.add_parser("resize", help="Resize image by dimensions or scale")
    p_rsz.add_argument("input", help="Source image")
    p_rsz.add_argument("--output", "-o", help="Output path (default: overwrite)")
    p_rsz.add_argument("--width", type=int, help="Target width (auto-scales height)")
    p_rsz.add_argument("--height", type=int, help="Target height (auto-scales width)")
    p_rsz.add_argument("--scale", type=float, help="Scale factor (e.g., 0.5 for half)")
    p_rsz.add_argument("--quality", type=int, default=85, help="Output quality (default: 85)")

    # compress
    p_cmp = sub.add_parser("compress", help="Compress image to reduce file size")
    p_cmp.add_argument("input", help="Source image")
    p_cmp.add_argument("--output", "-o", help="Output path (default: overwrite)")
    p_cmp.add_argument("--quality", type=int, default=60, help="Quality 1-100 (default: 60)")

    # thumbnail
    p_thm = sub.add_parser("thumbnail", help="Create thumbnail (preserves aspect ratio)")
    p_thm.add_argument("input", help="Source image")
    p_thm.add_argument("--output", "-o", help="Output path")
    p_thm.add_argument("--size", type=int, default=200, help="Max dimension in px (default: 200)")

    # batch
    p_bat = sub.add_parser("batch", help="Batch convert all images in a directory")
    p_bat.add_argument("input_dir", help="Directory of images")
    p_bat.add_argument("--format", required=True, help="Target format (jpg, png, webp, etc.)")
    p_bat.add_argument("--output-dir", help="Output directory (default: {input}_converted/)")
    p_bat.add_argument("--quality", type=int, default=85, help="Output quality (default: 85)")

    # to-pdf
    p_pdf = sub.add_parser("to-pdf", help="Combine images into a PDF document")
    p_pdf.add_argument("images", nargs="+", help="Image files to combine")
    p_pdf.add_argument("-o", "--output", help="Output PDF path (default: combined.pdf)")
    p_pdf.add_argument("--fit-page", action="store_true", help="Resize images to fit A4 page")
    p_pdf.add_argument("--landscape", action="store_true", help="Use landscape orientation (with --fit-page)")

    # strip
    p_strip = sub.add_parser("strip", help="Remove EXIF metadata (privacy cleanup)")
    p_strip.add_argument("input", help="Source image")
    p_strip.add_argument("-o", "--output", help="Output path (default: overwrite)")
    p_strip.add_argument("--quality", type=int, default=90, help="Output quality (default: 90)")

    # formats
    sub.add_parser("formats", help="List all supported image formats")

    args = parser.parse_args()
    dispatch = {
        "info": cmd_info, "convert": cmd_convert, "resize": cmd_resize,
        "compress": cmd_compress, "thumbnail": cmd_thumbnail,
        "batch": cmd_batch, "to-pdf": cmd_to_pdf, "strip": cmd_strip,
        "formats": cmd_formats,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
