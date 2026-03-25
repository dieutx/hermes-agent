---
name: excel
description: "Use this skill any time a .xlsx file is involved in any way — as input, output, or both. This includes: creating spreadsheets, data tables, or workbooks; reading, parsing, or extracting data from any .xlsx file (even if the data will be used elsewhere, like in a chart or summary); editing cells, adding rows, or updating values; converting between .xlsx and .csv in either direction; searching for values across sheets. Trigger whenever the user mentions \"spreadsheet,\" \"Excel,\" \"cells,\" \"CSV,\" \".xlsx\", \"tabular data,\" or references an Excel filename. If a .xlsx file needs to be opened, created, or touched, use this skill."
version: 1.0.0
author: dieutx
license: MIT
metadata:
  hermes:
    tags: [Excel, XLSX, Spreadsheet, CSV, Productivity, Data, Tables, Office]
    related_skills: [nano-pdf, powerpoint, word]
  prerequisites:
    pip: [openpyxl]
---

# Excel Spreadsheet Skill

## Quick Reference

| Task | Command |
|------|---------|
| Create multi-sheet workbook | `python3 excel_tool.py create file.xlsx --from-json '[...]'` |
| Create simple sheet | `python3 excel_tool.py create file.xlsx --data '[[...]]'` |
| Read data with headers | `python3 excel_tool.py read file.xlsx --headers` |
| Inspect workbook | `python3 excel_tool.py info file.xlsx` |
| Update a cell | `python3 excel_tool.py edit file.xlsx --cell B3 --value 42` |
| Search for values | `python3 excel_tool.py search file.xlsx "query"` |
| Append a row | `python3 excel_tool.py add-row file.xlsx --data '[...]'` |
| Excel → CSV | `python3 excel_tool.py to-csv file.xlsx` |
| CSV → styled Excel | `python3 excel_tool.py from-csv data.csv output.xlsx` |

Script path: `~/.hermes/skills/productivity/excel/scripts/excel_tool.py`

---

## Creating Workbooks

### Multi-Sheet Structured Creation (recommended)

Build a complete workbook with multiple sheets, styled headers, and auto column widths — **all in one call** via `--from-json`:

```bash
python3 excel_tool.py create report.xlsx --from-json '[
  {"name": "Sales", "data": [
    ["Region", "Q1", "Q2", "Total"],
    ["APAC", 50000, 55000, 105000],
    ["EMEA", 35000, 40000, 75000]
  ]},
  {"name": "Expenses", "data": [
    ["Category", "Amount"],
    ["Engineering", 120000],
    ["Marketing", 45000]
  ]}
]'
```

Each sheet gets styled headers, auto column widths, and frozen header row.

### Simple Single-Sheet

```bash
python3 excel_tool.py create data.xlsx --data '[["Name","Score"],["Alice",95],["Bob",82]]'
```

---

## Reading Data

```bash
python3 excel_tool.py read report.xlsx --headers              # objects with column keys
python3 excel_tool.py read report.xlsx --sheet "Expenses"      # specific sheet
python3 excel_tool.py read report.xlsx --range A1:D10          # cell range
python3 excel_tool.py info report.xlsx                         # metadata
```

---

## Editing

```bash
python3 excel_tool.py edit report.xlsx --cell B3 --value 42    # update cell
python3 excel_tool.py add-row report.xlsx --data '["New",99]'  # append row
python3 excel_tool.py search report.xlsx "revenue"             # find values
```

---

## CSV Conversion

```bash
# CSV → styled Excel (auto-width, headers, encoding detection)
python3 excel_tool.py from-csv data.csv output.xlsx

# Multiple CSVs → one workbook
python3 excel_tool.py from-csv sales.csv report.xlsx expenses.csv --sheet-names "Sales" "Expenses"

# Excel → CSV
python3 excel_tool.py to-csv report.xlsx --output data.csv
```

---

## Spreadsheet Tips

- **First row always headers** — bold, descriptive
- **Separate sheets** for raw data vs. summaries
- **Name sheets clearly** — "Sales Q1", not "Sheet1"
- **One data type per column**

---

## Security

- **Formula injection blocked** — `=`, `+`, `-`, `@` prefixes escaped
- **Overwrite protection** — `create` requires `--force`, `from-csv` rejects existing
- **Memory caps** — search: 10K rows, export/import: 100K rows

---

## Dependencies

```bash
pip install openpyxl
```
