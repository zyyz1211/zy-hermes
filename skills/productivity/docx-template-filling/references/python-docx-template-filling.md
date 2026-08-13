# python-docx Template Filling — Debug Workflow

This reference documents the complete workflow for filling a Word template with merged cells, discovered while filling a Chinese "干部履历表" (Cadre Resume Form) template.

## Step-by-Step Debug Workflow

### 1. Convert legacy .doc to .docx

```bash
"C:/Program Files/LibreOffice/program/soffice.exe" --headless --convert-to docx input.doc --outdir ./output/
```

### 2. Inspect the table structure

Write an inspection script:

```python
from docx import Document
from lxml import etree

nsmap = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

doc = Document("template.docx")
table = doc.tables[0]  # Tables are 0-indexed

for ri in range(len(table.rows)):
    row = table.rows[ri]
    tcs = row._tr.findall('w:tc', nsmap)
    print(f"\n=== Row {ri} ({len(tcs)} TC elements) ===")
    for tci, tc in enumerate(tcs):
        tc_pr = tc.find('w:tcPr', nsmap)
        info = {}
        if tc_pr is not None:
            gs = tc_pr.find('w:gridSpan', nsmap)
            hm = tc_pr.find('w:hMerge', nsmap)
            vm = tc_pr.find('w:vMerge', nsmap)
            if gs is not None:
                info['gridSpan'] = gs.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
            if hm is not None:
                info['hMerge'] = hm.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', 'continue')
            if vm is not None:
                info['vMerge'] = vm.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', 'continue')
        # Get text from all runs in the TC
        texts = []
        for p in tc.findall('w:p', nsmap):
            for r in p.findall('w:r', nsmap):
                t = r.find('w:t', nsmap)
                if t is not None and t.text:
                    texts.append(t.text)
        text = ' | '.join(texts) if texts else '(empty)'
        print(f"  TC{tci}: gridSpan={info.get('gridSpan','1')} "
              f"hMerge={info.get('hMerge','-')} vMerge={info.get('vMerge','-')} "
              f"text='{text[:60]}'")
```

### 3. Map python-docx cells to XML TCs

python-docx expands merged cells into virtual indices. For example, a row with 7 `<w:tc>` elements may report 8 cells via `.cells[]`. The first TC with `gridSpan=2` maps to python-docx `.cells[0]` AND `.cells[1]`.

**Rule of thumb**: Always work with XML TC indices, not python-docx cell indices.

### 4. Write data using XML manipulation

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
    tcs = row._tr.findall('w:tc', nsmap)
    if tci < len(tcs):
        return tcs[tci]
    return None

# Example: write to TC 1 of row 0
set_tc_text(get_tc(table.rows[0], 1), '<姓名>')
```

### 5. Verify the output

```python
# Read back with python-docx
doc2 = Document('output.docx')
table2 = doc2.tables[0]
for ri, row in enumerate(table2.rows):
    texts = [cell.text.strip()[:40] for cell in row.cells]
    filled = [t for t in texts if t]
    if filled:
        print(f"Row {ri}: {filled}")
```

Also verify with LibreOffice rendering:
```bash
"C:/Program Files/LibreOffice/program/soffice.exe" --headless --convert-to pdf output.docx
```

## Real-World Example: 干部履历表

A Chinese "Cadre Resume Form" template with this structure:

| Rows | Pattern | Notes |
|------|---------|-------|
| 0-3 | 7 TCs (1:1:1:1:1:1:1) | Name, gender, birth, ethnicity, etc. TC6 has vMerge |
| 4-7 | 5 TCs (2:1:2:1:2) | Education section. TC2 & TC4 have gridSpan=2 AND vMerge |
| 8-9 | 2 TCs (N:M) | Current position (TC1 gridSpan=5) and resume (TC1 gridSpan=7) |

### Data mapping for this template:

**Row 0**: TC1=姓名, TC4=性别, TC6=出生年月(vMerge across rows 0-2)
**Row 1**: TC1=民族, TC3=籍贯, TC5=出生地
**Row 2**: TC1=入党时间, TC3=参加工作时间, TC5=健康状况
**Row 3**: TC1=专业技术职务, TC4=熟悉专业/有何专长
**Row 4** (全日制, vMerge=restart): TC2=学历+学位(gridSpan2), TC4=毕业院校+专业(gridSpan2)
**Row 5** (全日制, vMerge=continue): Same cells as row 4 — write only to row 4
**Row 8**: TC1=现任职务(gridSpan5)
**Row 9**: TC1=简历(gridSpan7)

### Save to a new file (avoid permission errors)

```python
doc.save(r"C:\Users\<user>\Desktop\履历表（已填写）.docx")
```
