---
name: qr-code
description: "Use this skill any time QR codes are involved — generating QR codes from URLs, text, WiFi credentials, contacts (vCard), email, SMS, calendar events, or GPS coordinates; decoding QR codes from images; batch-generating multiple QR codes; creating dynamic QR codes with changeable destinations; or previewing QR as ASCII art. Trigger whenever the user mentions \"QR code,\" \"QR,\" \"scan code,\" \"WiFi QR,\" \"vCard,\" or wants to encode any data into a scannable image."
version: 1.0.0
author: dieutx
license: MIT
metadata:
  hermes:
    tags: [QR Code, WiFi, vCard, Contact, SMS, Calendar, Geolocation, Generator, Scanner, Productivity]
    related_skills: [image-tools]
  prerequisites:
    pip: [qrcode, Pillow]
---

# QR Code Toolkit

12 commands across core generation, data-type encoding, dynamic QR management, and utility tools.

## Quick Reference

| Task | Command |
|------|---------|
| Generate from URL/text | `python3 qr_tool.py generate "https://..." -o qr.png` |
| Generate SVG | `python3 qr_tool.py generate "data" -o qr.svg` |
| WiFi connection QR | `python3 qr_tool.py wifi --ssid "Name" --password "pass"` |
| Contact card (vCard) | `python3 qr_tool.py contact --name "Alice" --phone "+123"` |
| Email (mailto) | `python3 qr_tool.py email --email "a@b.com" --subject "Hi"` |
| SMS message | `python3 qr_tool.py sms --phone "+123" --message "Hello"` |
| Calendar event | `python3 qr_tool.py event --title "Meeting" --start "2026-04-01 09:00"` |
| GPS location | `python3 qr_tool.py geo --lat 37.7749 --lon -122.4194` |
| Decode from image | `python3 qr_tool.py decode image.png` |
| Batch from file | `python3 qr_tool.py batch -i urls.txt` |
| Dynamic QR (changeable) | `python3 qr_tool.py dynamic --action create --url "..."` |
| ASCII preview | `python3 qr_tool.py preview "Hello"` |
| Validate input | `python3 qr_tool.py validate --type url "https://..."` |

Script path: `~/.hermes/skills/productivity/qr-code/scripts/qr_tool.py`

---

## Core Commands

### Generate

Create QR codes from any text or URL. Supports PNG, JPG, WebP, SVG, and PDF output.

```bash
# Basic URL
python3 qr_tool.py generate "https://example.com" -o link.png

# SVG output (vector, scalable)
python3 qr_tool.py generate "https://example.com" -o link.svg

# Custom colors + caption
python3 qr_tool.py generate "data" --color navy --background lightyellow --caption "SCAN ME" -o styled.png

# Logo overlay (use high error correction)
python3 qr_tool.py generate "data" --error-correction H --logo company_logo.png -o branded.png

# Larger size
python3 qr_tool.py generate "data" --box-size 20 --border 2 -o large.png
```

**Error correction levels:**

| Level | Recovery | Best for |
|-------|----------|----------|
| L | 7% | Maximum data capacity |
| M | 15% | Default — good balance |
| Q | 25% | Printed materials |
| H | 30% | Logo overlay, damaged codes |

### Decode

Read QR codes from image files:

```bash
python3 qr_tool.py decode photo.png
```

Requires `pyzbar`: `pip install pyzbar`

### Batch

Generate multiple QR codes from a text file (one entry per line):

```bash
python3 qr_tool.py batch -i urls.txt --output-dir ./qr_codes/ --format png
python3 qr_tool.py batch -i urls.txt --format svg
```

Maximum 500 entries per batch. Supports PNG, SVG, JPG, WebP output.

---

## Data Type Commands

### WiFi

Generates a QR code that phones auto-connect to WiFi when scanned:

```bash
python3 qr_tool.py wifi --ssid "MyNetwork" --password "secret123"
python3 qr_tool.py wifi --ssid "Office" --password "p@ss" --auth WPA --hidden
```

### Contact (vCard)

Create a contact card QR — scanning adds the person to phone contacts:

```bash
python3 qr_tool.py contact --name "Alice Smith" --phone "+1234567890" --email "alice@example.com"
python3 qr_tool.py contact --name "Bob Lee" --phone "+1987654321" --org "Acme Corp" --title "CTO" --url "https://acme.com"
```

Supports: name, phone, email, organization, title, URL, address.

### Email (mailto)

Pre-filled email QR — scanning opens the email app with fields populated:

```bash
python3 qr_tool.py email --email "hello@example.com" --subject "Meeting Request" --body "Let's discuss the project"
```

### SMS

Pre-filled SMS QR — scanning opens the messaging app:

```bash
python3 qr_tool.py sms --phone "+1234567890" --message "Hello from Hermes"
```

### Calendar Event

iCal-format event QR — scanning adds the event to the phone's calendar:

```bash
python3 qr_tool.py event --title "Team Standup" --start "2026-04-01 09:00" --end "2026-04-01 09:30" --location "Room 42"
python3 qr_tool.py event --title "Conference" --start "2026-05-15 10:00" --description "Annual tech conference"
```

### Geolocation

GPS coordinate QR — scanning opens maps at the location:

```bash
python3 qr_tool.py geo --lat 37.7749 --lon -122.4194
python3 qr_tool.py geo --lat 48.8566 --lon 2.3522 --caption "Paris"
```

Output includes a Google Maps link for reference.

---

## Advanced Commands

### Dynamic QR

Create QR codes whose destination can be changed later without reprinting:

```bash
# Create a dynamic QR
python3 qr_tool.py dynamic --action create --url "https://example.com/page1" -o menu_qr.png

# Update the destination (QR image stays the same)
python3 qr_tool.py dynamic --action update --id abc12345 --url "https://example.com/page2"

# List all dynamic QR codes
python3 qr_tool.py dynamic --action list

# Delete
python3 qr_tool.py dynamic --action delete --id abc12345
```

Mappings are stored in `~/.hermes/qr_dynamic.json`.

---

## Utility Commands

### Preview (ASCII)

Render a QR code as ASCII art directly in the terminal — useful for quick testing without generating a file:

```bash
python3 qr_tool.py preview "Hello World"
python3 qr_tool.py preview "https://example.com" --json
```

### Validate

Check if input data is valid for a specific QR type before generating:

```bash
python3 qr_tool.py validate --type url "https://example.com"
python3 qr_tool.py validate --type email "user@example.com"
python3 qr_tool.py validate --type phone "+1234567890"
python3 qr_tool.py validate --type geo "37.7749,-122.4194"
```

---

## Output Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| PNG | `.png` | Default, lossless |
| JPEG | `.jpg` | Smaller, lossy |
| WebP | `.webp` | Modern, small |
| SVG | `.svg` | Vector, scalable, ideal for print |
| PDF | `.pdf` | Print-ready |

---

## Design Tips

- **Dark on light** — dark foreground on light background scans most reliably
- **Error correction H** when using logo overlay — the logo covers ~20% of the code
- **SVG for print** — vector format scales to any size without pixelation
- **Caption** — adds a "SCAN ME" frame below the QR for physical displays
- **Test your QR** — always scan with a phone camera to verify before printing

---

## Pitfalls

- **Logo overlay** — requires `--error-correction H`. Lower levels may not scan with a logo.
- **Batch cap** — maximum 500 entries per batch.
- **Decoding** — requires `pyzbar` (`pip install pyzbar`). Generation works without it.
- **Colors** — low-contrast combinations won't scan. Keep strong contrast.
- **Dynamic QR** — requires you to host your own redirect service. The tool manages the mapping database.
- **vCard size** — very long contact details may produce large QR codes that are harder to scan.

---

## Dependencies

```bash
pip install qrcode Pillow           # required — generation
pip install pyzbar                   # optional — decoding only
```
