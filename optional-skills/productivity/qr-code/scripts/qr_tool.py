#!/usr/bin/env python3
"""
QR Code Toolkit for Hermes Agent
-----------------------------------
Generate, decode, and manage QR codes with 12 commands.

Architecture:
  - Shared utility: _generate_qr_image(), _generate_qr_svg(), _save_image()
  - Data builders: _build_wifi_string(), _build_vcard(), _build_mailto(), etc.
  - Input validation: _validate_url(), _validate_email(), _validate_phone(), etc.
  - Sanitization: _sanitize_field() prevents vCard/iCal injection

Security:
  - All user input sanitized before embedding in structured formats (vCard, iCal)
  - Filenames derived from user input are cleaned of path separators
  - Batch generation capped at 500 entries
  - Data size warnings for QR capacity limits
  - No shell/subprocess/eval — pure library calls

Requires: pip install qrcode Pillow
Optional: pip install pyzbar (for decoding only)

Usage:
  python3 qr_tool.py generate "https://example.com" -o qr.png
  python3 qr_tool.py wifi --ssid "Net" --password "pass"
  python3 qr_tool.py contact --name "Alice" --phone "+1234567890"
  python3 qr_tool.py decode image.png
  python3 qr_tool.py preview "Hello World"
  python3 qr_tool.py batch --input urls.txt
  python3 qr_tool.py validate --type url "https://example.com"
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Dependency checks
# ---------------------------------------------------------------------------

def _check_qrcode():
    try:
        import qrcode  # noqa: F401
        return True
    except ImportError:
        sys.exit("qrcode not installed.\n  pip install qrcode Pillow\n")


def _check_pillow():
    try:
        from PIL import Image  # noqa: F401
        return True
    except ImportError:
        sys.exit("Pillow not installed.\n  pip install Pillow\n")


# ---------------------------------------------------------------------------
# Shared QR generator utility
# ---------------------------------------------------------------------------

# Error correction level mapping
EC_LEVELS = {"L": 1, "M": 0, "Q": 3, "H": 2}  # qrcode constants

def _get_ec(level: str) -> int:
    """Map error correction string to qrcode constant."""
    import qrcode
    mapping = {
        "L": qrcode.constants.ERROR_CORRECT_L,
        "M": qrcode.constants.ERROR_CORRECT_M,
        "Q": qrcode.constants.ERROR_CORRECT_Q,
        "H": qrcode.constants.ERROR_CORRECT_H,
    }
    return mapping.get(level.upper(), qrcode.constants.ERROR_CORRECT_M)


def _generate_qr_image(
    data: str,
    box_size: int = 10,
    border: int = 4,
    error_correction: str = "M",
    fill_color: str = "black",
    back_color: str = "white",
) -> "Image":
    """Core QR generation — returns a PIL Image."""
    _check_qrcode()
    _check_pillow()
    import qrcode
    from PIL import Image

    qr = qrcode.QRCode(
        version=None,
        error_correction=_get_ec(error_correction),
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fill_color, back_color=back_color).convert("RGB")
    return img


def _generate_qr_svg(data: str, box_size: int = 10, border: int = 4,
                      error_correction: str = "M") -> str:
    """Generate QR code as SVG string."""
    _check_qrcode()
    import qrcode
    import qrcode.image.svg
    import io

    factory = qrcode.image.svg.SvgPathImage
    qr = qrcode.QRCode(
        version=None,
        error_correction=_get_ec(error_correction),
        box_size=box_size,
        border=border,
        image_factory=factory,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image()

    buf = io.BytesIO()
    img.save(buf)
    return buf.getvalue().decode("utf-8")


def _apply_logo(img, logo_path: str, logo_ratio: float = 0.2):
    """Overlay a logo at the center of the QR image."""
    from PIL import Image

    if not os.path.exists(logo_path):
        return img

    logo = Image.open(logo_path).convert("RGBA")
    qr_w, qr_h = img.size
    logo_max = int(min(qr_w, qr_h) * logo_ratio)
    logo.thumbnail((logo_max, logo_max), Image.LANCZOS)

    # White background pad for logo
    pad = 4
    bg = Image.new("RGB", (logo.size[0] + pad * 2, logo.size[1] + pad * 2), "white")
    pos_logo = (pad, pad)
    bg.paste(logo, pos_logo, logo)

    pos = ((qr_w - bg.size[0]) // 2, (qr_h - bg.size[1]) // 2)
    img.paste(bg, pos)
    return img


def _apply_frame(img, caption: str = "SCAN ME", font_size: int = 20):
    """Add a frame with caption below the QR code."""
    from PIL import Image, ImageDraw, ImageFont

    qr_w, qr_h = img.size
    frame_h = font_size + 20
    framed = Image.new("RGB", (qr_w, qr_h + frame_h), "white")
    framed.paste(img, (0, 0))

    draw = ImageDraw.Draw(framed)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except (IOError, OSError):
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), caption, font=font)
    text_w = bbox[2] - bbox[0]
    text_x = (qr_w - text_w) // 2
    text_y = qr_h + (frame_h - font_size) // 2
    draw.text((text_x, text_y), caption, fill="black", font=font)

    return framed


def _save_image(img, output: str, quality: int = 95):
    """Save image with format-appropriate settings."""
    ext = os.path.splitext(output)[1].lower()
    kwargs = {}
    if ext in (".jpg", ".jpeg"):
        kwargs["quality"] = quality
    elif ext == ".webp":
        kwargs["quality"] = quality
    elif ext == ".pdf":
        img.save(output, "PDF")
        return
    img.save(output, **kwargs)


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

def _validate_url(url: str) -> Tuple[bool, str]:
    pattern = re.compile(r'^https?://[^\s/$.?#].[^\s]*$', re.IGNORECASE)
    if pattern.match(url):
        return True, "Valid URL"
    return False, f"Invalid URL format: {url}"


def _validate_email(email: str) -> Tuple[bool, str]:
    pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    if pattern.match(email):
        return True, "Valid email"
    return False, f"Invalid email format: {email}"


def _validate_phone(phone: str) -> Tuple[bool, str]:
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    if re.match(r'^\+?\d{7,15}$', cleaned):
        return True, "Valid phone number"
    return False, f"Invalid phone number: {phone}"


def _validate_wifi(ssid: str, auth: str) -> Tuple[bool, str]:
    if not ssid.strip():
        return False, "SSID cannot be empty"
    if auth.upper() not in ("WPA", "WEP", "nopass"):
        return False, f"Invalid auth type: {auth}. Use WPA, WEP, or nopass"
    return True, "Valid WiFi config"


def _validate_geo(lat: float, lon: float) -> Tuple[bool, str]:
    if -90 <= lat <= 90 and -180 <= lon <= 180:
        return True, "Valid coordinates"
    return False, f"Invalid coordinates: lat={lat}, lon={lon}"


# ---------------------------------------------------------------------------
# Input sanitization
# ---------------------------------------------------------------------------

def _sanitize_field(value: str) -> str:
    """Remove newlines and carriage returns to prevent vCard/iCal field injection."""
    return value.replace("\r", "").replace("\n", " ").strip()


def _check_data_size(data: str, max_bytes: int = 4296):
    """Check QR data doesn't exceed capacity. Warn but don't block."""
    encoded = data.encode("utf-8")
    if len(encoded) > max_bytes:
        print(f"Warning: data is {len(encoded)} bytes (QR max ~{max_bytes}). "
              f"Code may not scan reliably.", file=sys.stderr)


# ---------------------------------------------------------------------------
# Data format builders
# ---------------------------------------------------------------------------

def _build_wifi_string(ssid: str, password: str, auth: str = "WPA",
                        hidden: bool = False) -> str:
    h = "true" if hidden else "false"
    # Escape special chars in SSID and password
    ssid_escaped = ssid.replace("\\", "\\\\").replace(";", "\\;").replace('"', '\\"')
    pwd_escaped = password.replace("\\", "\\\\").replace(";", "\\;").replace('"', '\\"')
    return f"WIFI:S:{ssid_escaped};T:{auth.upper()};P:{pwd_escaped};H:{h};;"


def _build_vcard(name: str, phone: str = "", email: str = "",
                  org: str = "", title: str = "", url: str = "",
                  address: str = "") -> str:
    # Sanitize all fields to prevent vCard injection
    name = _sanitize_field(name)
    phone = _sanitize_field(phone)
    email = _sanitize_field(email)
    org = _sanitize_field(org)
    title = _sanitize_field(title)
    url = _sanitize_field(url)
    address = _sanitize_field(address)

    lines = ["BEGIN:VCARD", "VERSION:3.0"]
    parts = name.split(" ", 1)
    first = parts[0]
    last = parts[1] if len(parts) > 1 else ""
    lines.append(f"N:{last};{first};;;")
    lines.append(f"FN:{name}")
    if phone:
        lines.append(f"TEL;TYPE=CELL:{phone}")
    if email:
        lines.append(f"EMAIL:{email}")
    if org:
        lines.append(f"ORG:{org}")
    if title:
        lines.append(f"TITLE:{title}")
    if url:
        lines.append(f"URL:{url}")
    if address:
        lines.append(f"ADR;TYPE=WORK:;;{address};;;;")
    lines.append("END:VCARD")
    return "\r\n".join(lines)


def _build_mailto(email: str, subject: str = "", body: str = "") -> str:
    parts = [f"mailto:{email}"]
    params = []
    if subject:
        params.append(f"subject={_url_encode(subject)}")
    if body:
        params.append(f"body={_url_encode(body)}")
    if params:
        parts.append("?" + "&".join(params))
    return "".join(parts)


def _build_sms(phone: str, message: str = "") -> str:
    if message:
        return f"SMSTO:{phone}:{message}"
    return f"SMSTO:{phone}"


def _build_event(title: str, start: str, end: str = "",
                  location: str = "", description: str = "") -> str:
    # Sanitize to prevent iCal injection
    title = _sanitize_field(title)
    location = _sanitize_field(location)
    description = _sanitize_field(description)

    lines = [
        "BEGIN:VEVENT",
        f"SUMMARY:{title}",
        f"DTSTART:{_format_datetime(start)}",
    ]
    if end:
        lines.append(f"DTEND:{_format_datetime(end)}")
    if location:
        lines.append(f"LOCATION:{location}")
    if description:
        lines.append(f"DESCRIPTION:{description}")
    lines.append("END:VEVENT")
    return "\r\n".join(["BEGIN:VCALENDAR", "VERSION:2.0"] + lines + ["END:VCALENDAR"])


def _build_geo(lat: float, lon: float) -> str:
    return f"geo:{lat},{lon}"


def _url_encode(s: str) -> str:
    """Simple URL encoding for mailto params."""
    import urllib.parse
    return urllib.parse.quote(s, safe='')


def _format_datetime(dt_str: str) -> str:
    """Convert datetime string to iCal format (YYYYMMDDTHHMMSS)."""
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S", "%Y%m%dT%H%M%S"):
        try:
            dt = datetime.strptime(dt_str, fmt)
            return dt.strftime("%Y%m%dT%H%M%S")
        except ValueError:
            continue
    # Return as-is if already in iCal format
    if re.match(r'^\d{8}T\d{6}$', dt_str):
        return dt_str
    sys.exit(f"Invalid datetime: {dt_str}. Use YYYY-MM-DD HH:MM format.")


# ---------------------------------------------------------------------------
# Dynamic QR tracking (JSON-based)
# ---------------------------------------------------------------------------

_DYNAMIC_DB = os.path.expanduser("~/.hermes/qr_dynamic.json")


def _load_dynamic_db() -> Dict[str, Any]:
    if os.path.exists(_DYNAMIC_DB):
        try:
            with open(_DYNAMIC_DB, "r") as f:
                return json.load(f)
        except Exception:
            return {"mappings": {}, "scans": []}
    return {"mappings": {}, "scans": []}


def _save_dynamic_db(db: Dict[str, Any]):
    os.makedirs(os.path.dirname(_DYNAMIC_DB), exist_ok=True)
    with open(_DYNAMIC_DB, "w") as f:
        json.dump(db, f, indent=2)


# ---------------------------------------------------------------------------
# Commands — Core
# ---------------------------------------------------------------------------

def cmd_generate(args):
    """Generate QR code from text/URL."""
    data = args.data
    if not data.strip():
        sys.exit("Data cannot be empty.")
    _check_data_size(data)

    output = args.output or "qr_output.png"
    ext = os.path.splitext(output)[1].lower()

    # SVG output
    if ext == ".svg":
        svg = _generate_qr_svg(data, args.box_size, args.border, args.error_correction)
        with open(output, "w", encoding="utf-8") as f:
            f.write(svg)
        print(json.dumps({
            "created": output, "format": "SVG",
            "data_length": len(data),
            "data_preview": data[:100],
        }, indent=2))
        return

    # Raster output
    img = _generate_qr_image(
        data, args.box_size, args.border, args.error_correction,
        args.color or "black", args.background or "white",
    )

    if args.logo:
        if args.error_correction.upper() != "H":
            print("Warning: logo overlay works best with --error-correction H", file=sys.stderr)
        img = _apply_logo(img, args.logo)

    if args.caption:
        img = _apply_frame(img, args.caption)

    _save_image(img, output, args.quality)

    print(json.dumps({
        "created": output,
        "format": ext.replace(".", "").upper() or "PNG",
        "size": f"{img.size[0]}x{img.size[1]}",
        "data_length": len(data),
        "error_correction": args.error_correction.upper(),
        "data_preview": data[:100] + ("..." if len(data) > 100 else ""),
    }, indent=2))


def cmd_decode(args):
    """Decode QR code from image."""
    _check_pillow()
    from PIL import Image

    if not os.path.exists(args.file):
        sys.exit(f"File not found: {args.file}")

    try:
        from pyzbar.pyzbar import decode as zbar_decode
        img = Image.open(args.file)
        results = zbar_decode(img)
        if results:
            decoded = []
            for r in results:
                decoded.append({
                    "data": r.data.decode("utf-8", errors="replace"),
                    "type": r.type,
                    "rect": {"x": r.rect.left, "y": r.rect.top,
                             "w": r.rect.width, "h": r.rect.height},
                })
            print(json.dumps({
                "file": args.file,
                "qr_codes_found": len(decoded),
                "results": decoded,
            }, indent=2))
            return
        print(json.dumps({"file": args.file, "qr_codes_found": 0, "results": []}, indent=2))
        return
    except ImportError:
        pass

    print(json.dumps({
        "file": args.file,
        "error": "No QR decoder available. Install: pip install pyzbar",
    }, indent=2))


def cmd_batch(args):
    """Generate QR codes from a text file."""
    _check_qrcode()
    import qrcode

    if not os.path.exists(args.input):
        sys.exit(f"File not found: {args.input}")

    output_dir = args.output_dir or "qr_batch_output"
    os.makedirs(output_dir, exist_ok=True)

    with open(args.input, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    if len(lines) > 500:
        sys.exit(f"Too many entries ({len(lines)}). Maximum 500.")

    fmt = args.format or "png"
    results = []

    for i, line in enumerate(lines):
        filename = f"qr_{i+1:04d}.{fmt}"
        filepath = os.path.join(output_dir, filename)

        if fmt == "svg":
            svg = _generate_qr_svg(line)
            with open(filepath, "w") as f:
                f.write(svg)
        else:
            img = _generate_qr_image(line)
            _save_image(img, filepath)

        results.append({"file": filepath, "data": line[:80]})

    print(json.dumps({
        "output_dir": output_dir,
        "format": fmt.upper(),
        "generated": len(results),
        "files": results[:20],
    }, indent=2))


# ---------------------------------------------------------------------------
# Commands — Data Types
# ---------------------------------------------------------------------------

def cmd_wifi(args):
    """Generate WiFi connection QR code."""
    valid, msg = _validate_wifi(args.ssid, args.auth)
    if not valid:
        sys.exit(msg)

    data = _build_wifi_string(args.ssid, args.password, args.auth, args.hidden)
    # Sanitize SSID for filename — remove path separators and special chars
    safe_ssid = re.sub(r'[^\w\-]', '_', args.ssid)[:30]
    output = args.output or f"wifi_{safe_ssid}.png"

    img = _generate_qr_image(data, box_size=12, error_correction="H")
    if args.caption is not False:
        img = _apply_frame(img, f"WiFi: {args.ssid}")
    _save_image(img, output)

    print(json.dumps({
        "created": output, "ssid": args.ssid, "auth": args.auth,
        "hidden": args.hidden,
        "note": "Scan with phone camera to auto-connect.",
    }, indent=2))


def cmd_contact(args):
    """Generate vCard contact QR code."""
    if not args.name:
        sys.exit("--name is required")

    vcard = _build_vcard(
        args.name, args.phone or "", args.email or "",
        args.org or "", args.title or "", args.url or "",
        args.address or "",
    )
    safe_name = re.sub(r'[^\w\-]', '_', args.name)[:30]
    output = args.output or f"contact_{safe_name}.png"

    img = _generate_qr_image(vcard, box_size=10, error_correction="M")
    _save_image(img, output)

    print(json.dumps({
        "created": output, "name": args.name,
        "fields": {k: v for k, v in {
            "phone": args.phone, "email": args.email,
            "org": args.org, "title": args.title,
        }.items() if v},
    }, indent=2))


def cmd_email(args):
    """Generate mailto QR code."""
    valid, msg = _validate_email(args.email)
    if not valid:
        sys.exit(msg)

    data = _build_mailto(args.email, args.subject or "", args.body or "")
    output = args.output or "email_qr.png"

    img = _generate_qr_image(data)
    _save_image(img, output)

    print(json.dumps({
        "created": output, "email": args.email,
        "subject": args.subject or None,
    }, indent=2))


def cmd_sms(args):
    """Generate SMS QR code."""
    valid, msg = _validate_phone(args.phone)
    if not valid:
        sys.exit(msg)

    data = _build_sms(args.phone, args.message or "")
    output = args.output or "sms_qr.png"

    img = _generate_qr_image(data)
    _save_image(img, output)

    print(json.dumps({
        "created": output, "phone": args.phone,
        "message": (args.message or "")[:50] or None,
    }, indent=2))


def cmd_event(args):
    """Generate calendar event QR code."""
    data = _build_event(
        args.title, args.start, args.end or "",
        args.location or "", args.description or "",
    )
    output = args.output or "event_qr.png"

    img = _generate_qr_image(data, error_correction="M")
    _save_image(img, output)

    print(json.dumps({
        "created": output, "title": args.title,
        "start": args.start, "end": args.end or None,
        "location": args.location or None,
    }, indent=2))


def cmd_geo(args):
    """Generate geolocation QR code."""
    valid, msg = _validate_geo(args.lat, args.lon)
    if not valid:
        sys.exit(msg)

    data = _build_geo(args.lat, args.lon)
    output = args.output or "geo_qr.png"

    img = _generate_qr_image(data)
    if args.caption is not False:
        img = _apply_frame(img, f"{args.lat:.4f}, {args.lon:.4f}")
    _save_image(img, output)

    print(json.dumps({
        "created": output, "latitude": args.lat, "longitude": args.lon,
        "maps_url": f"https://maps.google.com/?q={args.lat},{args.lon}",
    }, indent=2))


# ---------------------------------------------------------------------------
# Commands — Advanced
# ---------------------------------------------------------------------------

def cmd_dynamic(args):
    """Create or update a dynamic QR code with changeable destination."""
    db = _load_dynamic_db()

    if args.action == "create":
        short_id = hashlib.sha256(f"{args.url}{time.time()}".encode()).hexdigest()[:8]
        db["mappings"][short_id] = {
            "url": args.url,
            "created": datetime.now().isoformat(),
            "scans": 0,
        }
        _save_dynamic_db(db)

        # Generate QR pointing to the short ID (user hosts their own redirect)
        redirect_url = f"https://your-domain.com/qr/{short_id}"
        output = args.output or f"dynamic_{short_id}.png"

        img = _generate_qr_image(redirect_url, error_correction="H")
        _save_image(img, output)

        print(json.dumps({
            "created": output, "short_id": short_id,
            "destination": args.url, "redirect_url": redirect_url,
            "note": "Update destination with: qr_tool.py dynamic --action update --id SHORT_ID --url NEW_URL",
        }, indent=2))

    elif args.action == "update":
        if not args.id or not args.url:
            sys.exit("--id and --url required for update")
        if args.id not in db["mappings"]:
            sys.exit(f"Short ID not found: {args.id}")
        db["mappings"][args.id]["url"] = args.url
        db["mappings"][args.id]["updated"] = datetime.now().isoformat()
        _save_dynamic_db(db)
        print(json.dumps({"updated": args.id, "new_url": args.url}, indent=2))

    elif args.action == "list":
        entries = []
        for sid, info in db.get("mappings", {}).items():
            entries.append({"id": sid, **info})
        print(json.dumps({"dynamic_qr_codes": len(entries), "entries": entries}, indent=2))

    elif args.action == "delete":
        if not args.id:
            sys.exit("--id required for delete")
        if args.id in db["mappings"]:
            del db["mappings"][args.id]
            _save_dynamic_db(db)
            print(json.dumps({"deleted": args.id}, indent=2))
        else:
            sys.exit(f"Short ID not found: {args.id}")


# ---------------------------------------------------------------------------
# Commands — Utility
# ---------------------------------------------------------------------------

def cmd_preview(args):
    """Render QR code as ASCII art in terminal."""
    _check_qrcode()
    import qrcode

    qr = qrcode.QRCode(
        error_correction=_get_ec(args.error_correction),
        box_size=1, border=1,
    )
    qr.add_data(args.data)
    qr.make(fit=True)

    # Build ASCII representation
    matrix = qr.get_matrix()
    lines = []
    for row in matrix:
        line = ""
        for cell in row:
            line += "██" if cell else "  "
        lines.append(line)

    ascii_art = "\n".join(lines)
    print(ascii_art)

    if args.json:
        print(json.dumps({
            "data": args.data,
            "size": f"{len(matrix)}x{len(matrix)}",
            "ascii_lines": len(lines),
        }, indent=2))


def cmd_validate(args):
    """Validate data for a specific QR type."""
    validators = {
        "url": lambda d: _validate_url(d),
        "email": lambda d: _validate_email(d),
        "phone": lambda d: _validate_phone(d),
        "geo": lambda d: _validate_geo(*[float(x) for x in d.split(",")]) if "," in d else (False, "Use: lat,lon"),
    }

    if args.type not in validators:
        sys.exit(f"Unknown type: {args.type}. Available: {', '.join(validators.keys())}")

    valid, message = validators[args.type](args.data)
    print(json.dumps({
        "type": args.type,
        "data": args.data,
        "valid": valid,
        "message": message,
    }, indent=2))


# ---------------------------------------------------------------------------
# CLI — Argument Parser
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="qr_tool.py",
        description="QR Code Toolkit — generate, decode, and manage QR codes",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- Core ---

    p_gen = sub.add_parser("generate", help="Generate QR from text/URL")
    p_gen.add_argument("data", help="Text, URL, or data to encode")
    p_gen.add_argument("-o", "--output", help="Output file (png/jpg/webp/svg/pdf)")
    p_gen.add_argument("--box-size", type=int, default=10, help="Pixel size per module (default: 10)")
    p_gen.add_argument("--border", type=int, default=4, help="Border width in modules (default: 4)")
    p_gen.add_argument("--color", help="Foreground color (default: black)")
    p_gen.add_argument("--background", help="Background color (default: white)")
    p_gen.add_argument("--error-correction", default="M", choices=["L", "M", "Q", "H"])
    p_gen.add_argument("--logo", help="Center logo image (use with -ec H)")
    p_gen.add_argument("--caption", help="Text caption below QR code")
    p_gen.add_argument("--quality", type=int, default=95, help="JPEG/WebP quality (default: 95)")

    p_dec = sub.add_parser("decode", help="Decode QR from image")
    p_dec.add_argument("file", help="Image file")

    p_batch = sub.add_parser("batch", help="Batch generate from text file")
    p_batch.add_argument("--input", "-i", required=True, help="Text file (one per line)")
    p_batch.add_argument("--output-dir", help="Output directory")
    p_batch.add_argument("--format", default="png", choices=["png", "svg", "jpg", "webp"])

    # --- Data Types ---

    p_wifi = sub.add_parser("wifi", help="WiFi connection QR")
    p_wifi.add_argument("--ssid", required=True)
    p_wifi.add_argument("--password", required=True)
    p_wifi.add_argument("--auth", default="WPA", choices=["WPA", "WEP", "nopass"])
    p_wifi.add_argument("--hidden", action="store_true")
    p_wifi.add_argument("-o", "--output")
    p_wifi.add_argument("--caption", default=None, nargs="?", const=True)

    p_contact = sub.add_parser("contact", help="vCard contact QR")
    p_contact.add_argument("--name", required=True)
    p_contact.add_argument("--phone")
    p_contact.add_argument("--email")
    p_contact.add_argument("--org")
    p_contact.add_argument("--title")
    p_contact.add_argument("--url")
    p_contact.add_argument("--address")
    p_contact.add_argument("-o", "--output")

    p_email = sub.add_parser("email", help="Email (mailto) QR")
    p_email.add_argument("--email", required=True)
    p_email.add_argument("--subject")
    p_email.add_argument("--body")
    p_email.add_argument("-o", "--output")

    p_sms = sub.add_parser("sms", help="SMS message QR")
    p_sms.add_argument("--phone", required=True)
    p_sms.add_argument("--message")
    p_sms.add_argument("-o", "--output")

    p_event = sub.add_parser("event", help="Calendar event QR")
    p_event.add_argument("--title", required=True)
    p_event.add_argument("--start", required=True, help="Start: YYYY-MM-DD HH:MM")
    p_event.add_argument("--end", help="End: YYYY-MM-DD HH:MM")
    p_event.add_argument("--location")
    p_event.add_argument("--description")
    p_event.add_argument("-o", "--output")

    p_geo = sub.add_parser("geo", help="Geolocation QR")
    p_geo.add_argument("--lat", type=float, required=True, help="Latitude")
    p_geo.add_argument("--lon", type=float, required=True, help="Longitude")
    p_geo.add_argument("-o", "--output")
    p_geo.add_argument("--caption", default=None, nargs="?", const=True)

    # --- Advanced ---

    p_dyn = sub.add_parser("dynamic", help="Dynamic QR with changeable destination")
    p_dyn.add_argument("--action", required=True, choices=["create", "update", "list", "delete"])
    p_dyn.add_argument("--url", help="Destination URL")
    p_dyn.add_argument("--id", help="Short ID (for update/delete)")
    p_dyn.add_argument("-o", "--output")

    # --- Utility ---

    p_prev = sub.add_parser("preview", help="ASCII preview in terminal")
    p_prev.add_argument("data", help="Data to preview")
    p_prev.add_argument("--error-correction", default="M", choices=["L", "M", "Q", "H"])
    p_prev.add_argument("--json", action="store_true", help="Also output JSON metadata")

    p_val = sub.add_parser("validate", help="Validate data for QR type")
    p_val.add_argument("--type", required=True, choices=["url", "email", "phone", "geo"])
    p_val.add_argument("data", help="Data to validate")

    args = parser.parse_args()
    dispatch = {
        "generate": cmd_generate, "decode": cmd_decode, "batch": cmd_batch,
        "wifi": cmd_wifi, "contact": cmd_contact, "email": cmd_email,
        "sms": cmd_sms, "event": cmd_event, "geo": cmd_geo,
        "dynamic": cmd_dynamic,
        "preview": cmd_preview, "validate": cmd_validate,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
