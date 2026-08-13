---
name: docx-template-filling
description: "Open existing .docx templates and fill table cells with data — handling merged cells, complex table layouts, and python-docx gotchas."
version: 1.0.0
author: Hermes Agent (automatically generated)
license: Proprietary. LICENSE.txt has complete terms
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Word, DOCX, Templates, python-docx, Office, Productivity]
    category: productivity
    related_skills: [docx, excel-author, pdf]
---

# DOCX Template Filling

Open an existing `.docx` template document and populate its table cells with data. This is distinct from *creating* a new docx from scratch (see the `docx` skill for that) — it's for the common enterprise workflow of filling in pre-designed templates (forms, reports, certificates, resumes, contracts).

## When to Use

Use this skill whenever the user wants to:
- Fill in a pre-existing Word template with data
- Populate a .docx form/report/resume/contract with information from another source
- Work with complex merged-cell table layouts in Word documents
- Extract data from a filled docx template

Do NOT use for: creating new documents from scratch (use `docx` skill with docx-js npm), editing XML directly for tracked changes/comments (`docx` skill), or PDF work (`pdf` skill).

## Prerequisites

```bash
pip install python-docx lxml
```

On Windows, LibreOffice is useful for verification:
```bash
# Check if available at default path
ls "C:/Program Files/LibreOffice/program/soffice.exe"
```

## Core Technique: python-docx + XML

### The Problem

python-docx's `table.rows[r].cells[c]` API is misleading when cells are **merged** (vertical or horizontal). It expands merged cells into virtual indices that don't match actual `<w:tc>` XML elements:

```python
# This looks right but writes to a merged sibling!
table.rows[4].cells[3].text = '本科'  # May overwrite data in row 5!
```

### The Solution: Inspect XML Structure First

Always inspect the actual `<w:tc>` elements with lxml before writing:

```python
from lxml import etree
nsmap = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

row = table.rows[4]
tcs = row._tr.findall('w:tc', nsmap)
for tci, tc in enumerate(tcs):
    tc_pr = tc.find('w:tcPr', nsmap)
    info = {}
    if tc_pr is not None:
        gs = tc_pr.find('w:gridSpan', nsmap)
        hm = tc_pr.find('w:hMerge', nsmap)
        vm = tc_pr.find('w:vMerge', nsmap)
        if gs is not None: info['gridSpan'] = gs.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
        if hm is not None: info['hMerge'] = hm.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', 'continue')
        if vm is not None: info['vMerge'] = vm.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', 'continue')
    print(f"TC{tci}: gridSpan={info.get('gridSpan','1')} hMerge={info.get('hMerge','-')} vMerge={info.get('vMerge','-')}")
```

### Key XML Attributes

| Attribute | Meaning |
|-----------|---------|
| `gridSpan="N"` | This TC spans N visual columns |
| `hMerge` (no val) | Horizontal merge continuation |
| `hMerge val="restart"` | Starts a horizontal merge |
| `vMerge` (no val) | Vertical merge continuation |
| `vMerge val="restart"` | Starts a vertical merge group |

### Writing to Cells

Write directly to the XML `<w:tc>` element to bypass python-docx's abstraction:

```python
def set_tc_text(tc, text):
    """Replace all content of a <w:tc> element with a single paragraph of text."""
    for p in tc.findall('w:p', nsmap):
        tc.remove(p)
    p = etree.SubElement(tc, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p')
    r = etree.SubElement(p, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r')
    t = etree.SubElement(r, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
    t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    t.text = text

def get_tc(row, tci):
    """Get the <w:tc> element at index tci from the row."""
    tcs = row._tr.findall('w:tc', nsmap)
    return tcs[tci] if tci < len(tcs) else None
```

## Common Template Patterns

### Simple table (no merged data cells)
Rows typically have 7 `<w:tc>` elements, most with `gridSpan=1`:
- TC0 = gridSpan2 label
- TC1 = data cell
- TC2 = spacer
- TC3 = label
- TC4 = data cell
- TC5 = label
- TC6 = data cell (may be vMerge across multiple rows)

### Education section (merged vertical data cells)
Rows have 5 TCs with gridSpan on data cells:
- TC0 = gridSpan2 label (e.g. "学历/学位")
- TC1 = gridSpan1 label (e.g. "全日制教育")
- TC2 = gridSpan2 **data cell** (vertically merged with next row)
- TC3 = gridSpan1 label (e.g. "毕业院校系及专业")
- TC4 = gridSpan2 **data cell** (vertically merged with next row)

**Critical**: When TC2 and TC4 have `vMerge=restart` on row N and `vMerge=continue` on row N+1, you can only write ONE set of data — the merge means both rows share the same cell.

### Single-row section (2 TCs)
- TC0 = gridSpanN label
- TC1 = gridSpanM **data cell** (M spans all remaining columns)

## Verification

Use LibreOffice to render the docx, then inspect visually:

```bash
"C:/Program Files/LibreOffice/program/soffice.exe" --headless --convert-to pdf output.docx
```

Or read the docx back with `read_file` for a text view:
```python
from docx import Document
doc = Document('output.docx')
for row in doc.tables[0].rows:
    cells = [c.text.strip() for c in row.cells]
    print(cells)
```

## Pitfalls

- **python-docx cell indices != XML TC indices**: The `.cells[]` API expands merged cells into virtual indices. Always use XML `<w:tc>` inspection to find the real TC index.
- **Vertical merge writes affect ALL merged rows**: Writing to `vMerge=restart` or `vMerge=continue` writes to the same visual cell. You cannot put different data in vertically merged cells.
- **Don't use `xml.etree.ElementTree` for transforms**: It rewrites namespace prefixes and corrupts OOXML. Use `lxml.etree` with explicit namespace dict.
- **Permission errors on save**: The file may be open in Word. Save to a new filename or close the document first.
- **Legacy .doc must be converted first**: Use `"C:/Program Files/LibreOffice/program/soffice.exe" --headless --convert-to docx file.doc` before filling.

## References

See `references/python-docx-template-filling.md` for extended examples and the full debug workflow.
