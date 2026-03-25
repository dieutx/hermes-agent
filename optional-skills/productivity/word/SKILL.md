---
name: word
description: "Use this skill any time a .docx file is involved in any way — as input, output, or both. This includes: creating reports, proposals, letters, or any Word document; reading, parsing, or extracting text from any .docx file (even if the extracted content will be used elsewhere, like in an email or summary); editing, find-and-replace, or updating existing documents; converting between Word and Markdown in either direction; searching for content across paragraphs and tables. Trigger whenever the user mentions \"document,\" \"Word,\" \"report,\" \"proposal,\" \".docx\", or references a Word filename, regardless of what they plan to do with the content afterward. If a .docx file needs to be opened, created, or touched, use this skill."
version: 1.0.0
author: dieutx
license: MIT
metadata:
  hermes:
    tags: [Word, DOCX, Document, Markdown, Productivity, Office, Report]
    related_skills: [nano-pdf, powerpoint, excel]
  prerequisites:
    pip: [python-docx]
---

# Word Document Skill

## Quick Reference

| Task | Command |
|------|---------|
| Create structured document | `python3 word_tool.py create file.docx --from-json '[...]'` |
| Read/analyze content | `python3 word_tool.py read file.docx --limit 50` |
| Inspect metadata | `python3 word_tool.py info file.docx` |
| Find and replace | `python3 word_tool.py edit file.docx --find "old" --replace "new" --all` |
| Search for text | `python3 word_tool.py search file.docx "query"` |
| Add heading/paragraph | `python3 word_tool.py add file.docx --text "..." --heading 1` |
| Word → Markdown | `python3 word_tool.py to-md file.docx` |
| Markdown → Word | `python3 word_tool.py from-md notes.md output.docx` |
| Extract plain text | `python3 word_tool.py extract file.docx` |

Script path: `~/.hermes/skills/productivity/word/scripts/word_tool.py`

---

## Creating Documents

### Structured Creation (recommended)

Build a full document with headings, paragraphs, lists, tables, quotes, and page breaks — **all in one call** via `--from-json`:

```bash
python3 word_tool.py create report.docx --title "Q1 Report" --from-json '[
  {"type": "heading", "level": 1, "text": "Executive Summary"},
  {"type": "paragraph", "text": "Revenue grew **35%** year-over-year."},
  {"type": "heading", "level": 2, "text": "Key Metrics"},
  {"type": "bullets", "items": ["Revenue: $2.4M", "Users: 50K", "NPS: 72"]},
  {"type": "heading", "level": 2, "text": "Roadmap"},
  {"type": "numbered", "items": ["Q1: Launch", "Q2: Scale", "Q3: Optimize"]},
  {"type": "quote", "text": "Ship fast, iterate faster."},
  {"type": "heading", "level": 2, "text": "Budget"},
  {"type": "table", "headers": ["Category","Amount"], "rows": [["Dev","$50K"],["Marketing","$15K"]]},
  {"type": "pagebreak"},
  {"type": "heading", "level": 1, "text": "Appendix"},
  {"type": "paragraph", "text": "Details available upon request."}
]'
```

**Supported element types:**

| Type | Fields | Description |
|------|--------|-------------|
| `heading` | `text`, `level` (1-9) | Section heading |
| `paragraph` | `text` | Body text — supports `**bold**` and `*italic*` |
| `bullets` | `items` (array) | Unordered list |
| `numbered` | `items` (array) | Ordered list |
| `table` | `headers`, `rows` | Table with bold header row |
| `quote` | `text` | Blockquote (Quote style) |
| `pagebreak` | — | Page break |

### Simple Text Mode

```bash
python3 word_tool.py create note.docx --content "First paragraph.\nSecond paragraph."
```

---

## Reading Content

```bash
# Structured JSON with types, styles, heading levels
python3 word_tool.py read report.docx --limit 50

# With empty paragraphs included
python3 word_tool.py read report.docx --include-empty

# Metadata: paragraphs, tables, sections, images, styles, page layout
python3 word_tool.py info report.docx
```

The `read` command returns typed elements:
- `heading` with `level` (1-9) and `style` (e.g., "Heading 1")
- `paragraph` with `bold`/`italic` flags when present
- `table` with full row/column data

---

## Editing Workflow

### Find and Replace

```bash
# Single replacement (first match only)
python3 word_tool.py edit report.docx --find "2025" --replace "2026"

# Replace all occurrences (paragraphs + table cells)
python3 word_tool.py edit report.docx --find "Q1" --replace "Q2" --all
```

Preserves run-level formatting — only the text changes, not bold/italic/font.

### Append Content

```bash
python3 word_tool.py add report.docx --text "Conclusion" --heading 1
python3 word_tool.py add report.docx --text "Final thoughts go here."
python3 word_tool.py add report.docx --text "Important note" --style "Intense Quote"
```

### Search

```bash
python3 word_tool.py search report.docx "revenue" --limit 20
```

Case-insensitive, searches paragraphs and table cells.

---

## Converting Between Formats

### Word → Markdown

```bash
python3 word_tool.py to-md report.docx --output report.md
```

Converts:
- Headings → `# ## ###`
- Bold/italic runs → `**bold**` `*italic*`
- List Bullet → `- items`
- List Number → `1. items`
- Quote → `> blockquote`
- Tables → `| markdown | tables |`

### Markdown → Word

```bash
python3 word_tool.py from-md notes.md report.docx --title "Report Title"
```

Converts all Markdown elements to properly styled Word elements using native styles (Heading 1, List Bullet, Table Grid, etc.).

### Plain Text Extraction

```bash
# To stdout (capped at 5000 chars)
python3 word_tool.py extract report.docx

# To file (full content)
python3 word_tool.py extract report.docx --output report.txt
```

---

## Document Structure Tips

**Don't create flat documents.** A wall of normal paragraphs is hard to navigate.

### For Reports and Proposals

- **Start with a title** (Heading 0) and executive summary
- **Use Heading 1** for major sections, **Heading 2** for subsections
- **Use bullet lists** for key points — easier to scan than paragraphs
- **Include a table** for budgets, timelines, or comparisons
- **End with next steps** or a conclusion heading

### For Meeting Notes

- **Title**: Meeting name + date
- **Heading 1**: Each agenda item
- **Bullets**: Discussion points
- **Numbered list**: Action items with owners

### Document Structure Example

```json
[
  {"type": "heading", "level": 1, "text": "Project Overview"},
  {"type": "paragraph", "text": "Brief description of the project."},
  {"type": "heading", "level": 2, "text": "Goals"},
  {"type": "bullets", "items": ["Goal 1", "Goal 2", "Goal 3"]},
  {"type": "heading", "level": 2, "text": "Timeline"},
  {"type": "table", "headers": ["Phase","Duration","Owner"], "rows": [
    ["Design", "2 weeks", "Alice"],
    ["Build", "6 weeks", "Bob"],
    ["Test", "2 weeks", "Charlie"]
  ]},
  {"type": "heading", "level": 1, "text": "Next Steps"},
  {"type": "numbered", "items": ["Review proposal", "Assign budget", "Kick off"]}
]
```

---

## QA (Recommended)

After creating a document, verify it:

```bash
# Check structure
python3 word_tool.py info output.docx

# Read content to verify
python3 word_tool.py read output.docx --limit 30

# Extract text to check for errors
python3 word_tool.py extract output.docx
```

---

## Pitfalls

- **Run-level replacement** — `edit` replaces within individual runs. If "hello world" is split across two runs ("hello" + " world"), the find string won't match. Use `extract` to verify text, then edit specific words.
- **Read-only safety** — `info`, `read`, `search`, `to-md`, `extract` never modify the original file.
- **Overwrite protection** — `create` requires `--force` to overwrite, `from-md` rejects existing output.
- **No .doc support** — only .docx (Office Open XML). Convert .doc to .docx first.
- **No macros** — python-docx handles .docx only, not .docm. No macro execution risk.
- **Images** — `info` reports image count, but images are not extracted or included in conversions.
- **Formulas** — calculated fields (TOC, cross-references) may show cached values. Regenerate in Word if needed.

---

## Dependencies

```bash
pip install python-docx
```

No other packages, no API keys, no external services needed.
