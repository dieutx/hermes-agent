---
name: excel
description: "Read, create, edit, search, and convert Excel spreadsheets (.xlsx). Use when the user mentions spreadsheets, Excel files, .xlsx, cell data, CSV conversion, or tabular data operations. Supports multi-sheet workbooks, cell ranges, header-aware reading, and bidirectional CSV conversion."
version: 1.0.0
author: dieutx
license: MIT
metadata:
  hermes:
    tags: [Excel, XLSX, Spreadsheet, CSV, Productivity, Data, Tables]
    related_skills: [nano-pdf, powerpoint, ocr-and-documents]
  prerequisites:
    pip: [openpyxl]
---

# Excel Spreadsheet Skill

Read, create, edit, search, and convert Excel (.xlsx) files. 8 commands
for complete spreadsheet management — no Excel installation needed.

Requires: `pip install openpyxl`

---

## When to Use

- User asks to read, open, or inspect an .xlsx file
- User wants to create a new spreadsheet from data
- User asks to edit cells, update values, or append rows
- User wants to search for values across sheets
- User needs to convert between .xlsx and .csv formats
- User mentions "spreadsheet", "Excel", "cells", or "tabular data"
- User uploads a .xlsx file and asks questions about its contents

---

## Prerequisites

```bash
pip install openpyxl
```

No API keys or external services required — all operations are local.

---

## Quick Reference

Script path: ~/.hermes/skills/productivity/excel/scripts/excel_tool.py

```
python3 excel_tool.py info     <file>
python3 excel_tool.py read     <file> [--sheet NAME] [--range A1:C10] [--headers] [--limit N]
python3 excel_tool.py create   <file> [--sheet NAME] [--data '[[...]]'] [--force]
python3 excel_tool.py edit     <file> --cell A1 --value "hello" [--sheet NAME]
python3 excel_tool.py search   <file> <query> [--sheet NAME] [--limit N]
python3 excel_tool.py to-csv   <file> [--sheet NAME] [--output out.csv]
python3 excel_tool.py from-csv <csv_file> <xlsx_file> [extra.csv ...] [--sheet-names ...] [--no-style]
python3 excel_tool.py add-row  <file> --data '["a","b",42]' [--sheet NAME]
```

All commands output structured JSON for easy parsing.

---

## Procedure

### 1. Inspect a Workbook

Get sheet names, dimensions, row/column counts — useful before reading.

```bash
python3 ~/.hermes/skills/productivity/excel/scripts/excel_tool.py \
  info report.xlsx
```

Output:
```json
{
  "file": "report.xlsx",
  "sheet_count": 3,
  "sheets": [
    {"name": "Sales", "dimensions": "A1:F150", "max_row": 150, "max_column": 6},
    {"name": "Expenses", "dimensions": "A1:D80", "max_row": 80, "max_column": 4},
    {"name": "Summary", "dimensions": "A1:C10", "max_row": 10, "max_column": 3}
  ],
  "active_sheet": "Sales"
}
```

### 2. Read Data

Read cell data from a sheet. Supports cell ranges, row limits, and
header-aware mode (first row becomes dict keys).

```bash
# Read first 20 rows from active sheet
python3 excel_tool.py read report.xlsx --limit 20

# Read specific range
python3 excel_tool.py read report.xlsx --range A1:D10

# Read with headers (returns array of objects instead of arrays)
python3 excel_tool.py read report.xlsx --headers

# Read from a specific sheet
python3 excel_tool.py read report.xlsx --sheet Expenses --headers --limit 50
```

With `--headers`, output looks like:
```json
{
  "headers": ["Name", "Amount", "Date", "Category"],
  "data": [
    {"Name": "Alice", "Amount": 150.0, "Date": "2026-01-15", "Category": "Sales"},
    {"Name": "Bob", "Amount": 230.5, "Date": "2026-01-16", "Category": "Support"}
  ]
}
```

Without `--headers`, output is raw arrays:
```json
{
  "data": [
    ["Name", "Amount", "Date", "Category"],
    ["Alice", 150.0, "2026-01-15", "Sales"]
  ]
}
```

### 3. Create a Workbook

Create a new .xlsx file with optional initial data.

```bash
# Empty workbook
python3 excel_tool.py create new.xlsx

# With data (JSON array of rows)
python3 excel_tool.py create budget.xlsx \
  --data '[["Item","Cost","Qty"],["Laptop",1200,5],["Monitor",400,10]]' \
  --sheet "Q1 Budget"

# Overwrite existing
python3 excel_tool.py create report.xlsx --force --data '[["a","b"],[1,2]]'
```

### 4. Edit a Cell

Update a specific cell value. Numbers are auto-detected.

```bash
python3 excel_tool.py edit report.xlsx --cell B3 --value "Updated"
python3 excel_tool.py edit report.xlsx --cell C5 --value "42.5" --sheet Sales
```

Output shows old and new values for verification:
```json
{
  "cell": "B3",
  "old_value": "Original",
  "new_value": "Updated"
}
```

### 5. Search

Find cells containing a value (case-insensitive substring match).

```bash
python3 excel_tool.py search report.xlsx "revenue"
python3 excel_tool.py search report.xlsx "2026" --sheet Sales --limit 20
```

Output:
```json
{
  "query": "revenue",
  "matches": 3,
  "results": [
    {"cell": "A1", "value": "Total Revenue", "row": 1, "column": 1},
    {"cell": "B15", "value": "Revenue Q1", "row": 15, "column": 2},
    {"cell": "B30", "value": "Revenue Q2", "row": 30, "column": 2}
  ]
}
```

### 6. Export to CSV

Convert a sheet to CSV format.

```bash
# Auto-named output (report_Sales.csv)
python3 excel_tool.py to-csv report.xlsx --sheet Sales

# Custom output path
python3 excel_tool.py to-csv report.xlsx --output data.csv
```

### 7. Import from CSV

Convert CSV files into a professionally formatted .xlsx workbook.
Auto-detects encoding (UTF-8, GBK, GB2312), applies styled headers
(bold white on blue), auto-adjusts column widths, and freezes the
header row.

```bash
# Single file with auto formatting
python3 excel_tool.py from-csv data.csv output.xlsx

# Custom sheet name
python3 excel_tool.py from-csv data.csv output.xlsx --sheet "Imported Data"

# Multiple CSVs merged into one workbook (each becomes a sheet)
python3 excel_tool.py from-csv sales.csv report.xlsx expenses.csv inventory.csv \
  --sheet-names "Sales" "Expenses" "Inventory"

# Skip styling (raw data only)
python3 excel_tool.py from-csv data.csv output.xlsx --no-style
```

Features:
- Auto encoding detection (UTF-8, UTF-8-SIG, GBK, GB2312, Latin-1)
- Styled headers: bold white text on blue background, centered
- Auto column widths (CJK characters counted as 2 units, capped at 50)
- Frozen header row for easy scrolling
- Numeric strings auto-converted to numbers
- Multi-file merge: each CSV becomes a separate sheet

### 8. Append a Row

Add a row to the bottom of a sheet.

```bash
python3 excel_tool.py add-row report.xlsx --data '["New Item", 99.5, 3, "Misc"]'
python3 excel_tool.py add-row report.xlsx --data '["2026-03-25", "Payment received"]' --sheet Log
```

---

## Common Workflows

### Analyze an uploaded spreadsheet
```bash
python3 excel_tool.py info uploaded.xlsx          # What sheets exist?
python3 excel_tool.py read uploaded.xlsx --headers # Read with column names
python3 excel_tool.py search uploaded.xlsx "total" # Find summary rows
```

### Create a report from scratch
```bash
python3 excel_tool.py create report.xlsx \
  --data '[["Month","Revenue","Costs"],["Jan",50000,35000],["Feb",55000,37000]]' \
  --sheet "2026 Report"
```

### Convert between formats
```bash
python3 excel_tool.py to-csv data.xlsx --output data.csv    # xlsx → csv
python3 excel_tool.py from-csv data.csv data.xlsx           # csv → xlsx
```

### Batch update cells
```bash
python3 excel_tool.py edit report.xlsx --cell A1 --value "Updated Title"
python3 excel_tool.py edit report.xlsx --cell B2 --value "1500"
python3 excel_tool.py add-row report.xlsx --data '["New entry", 42]'
```

---

## Pitfalls

- **Read-only mode** — `info`, `read`, `search`, and `to-csv` open files
  in read-only mode and never modify the original.
- **Large files** — use `--limit` when reading files with thousands of rows
  to avoid excessive output. Default limit is 100 rows.
- **Formulas** — `read` returns computed values (data_only=True), not the
  formula text. If the file was never opened in Excel, computed values
  may be None.
- **Date formatting** — dates are returned as strings. The original Excel
  date format is not preserved in JSON output.
- **File locking** — if the file is open in Excel, writes may fail on
  Windows. Close Excel first.
- **CSV encoding** — CSV export uses UTF-8 encoding. Import also expects
  UTF-8.
- **No .xls support** — only .xlsx (Office Open XML) is supported.
  Convert .xls files to .xlsx first.

---

## Verification

```bash
pip install openpyxl
python3 ~/.hermes/skills/productivity/excel/scripts/excel_tool.py \
  create /tmp/test.xlsx --data '[["hello","world"],[1,2]]'
python3 ~/.hermes/skills/productivity/excel/scripts/excel_tool.py \
  read /tmp/test.xlsx
```
