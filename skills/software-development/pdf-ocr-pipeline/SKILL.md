---
name: pdf-ocr-pipeline
description: "End-to-end OCR pipeline for Chinese scanned PDFs using PaddleOCR (preferred) or Tesseract (fallback), with the pdf_ocr.py automation script."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [OCR, PDF, PaddleOCR, Tesseract, Chinese, Document-Scanning]
    related_skills: [ocr-and-documents, excel-author, docx]
---

# PDF OCR Pipeline (Chinese Documents)

End-to-end workflow for OCR-ing scanned Chinese PDFs and extracting structured text.

## Architecture

```
PDF → [PyMuPDF check for embedded text]
  ├─ Has text → extract directly (fast path)
  └─ Scanned (no text) → export pages as images
       ├─ PaddleOCR (preferred) → best Chinese accuracy
       └─ Tesseract (fallback) → chi_sim+eng
```

The `pdf_ocr.py` script (at `C:\Users\<user>\Desktop\09_工具脚本\pdf_ocr.py`) implements this full pipeline.

## Engine Comparison

| Engine | Chinese Accuracy | Install Size | Speed | Notes |
|--------|:---------------:|:------------:|:-----:|-------|
| **PaddleOCR** | ⭐ 90%+ | ~1GB | 0.5-2s/page | Best for Chinese, offline |
| **Tesseract** | 60-80% | ~50MB | Fast | Fallback only, needs chi_sim |

## Installation

### PaddleOCR (Recommended)

```bash
pip install paddlepaddle paddleocr
```

**Known issues on Windows Python 3.13:**
- paddlepaddle 3.3.1 has oneDNN compatibility bug → downgrade to `paddlepaddle<3.3.0`
- PaddleOCR API has changed in recent versions:
  - Init: use `use_textline_orientation=True` instead of deprecated `use_angle_cls=True`
  - Call: `ocr.ocr(image_path)` without `cls=True`
  - Return format is now a **list of dicts**, not nested lists:
    ```python
    result[0]['rec_texts']   # ['text1', 'text2', ...]
    result[0]['rec_scores']  # [0.999, 0.995, ...]
    ```

### Tesseract (Fallback)

```bash
# Install via winget
winget install --id TheDocumentFoundation.LibreOffice

# Chinese language pack
# Download chi_sim.traineddata to tessdata directory
# Set TESSDATA_PREFIX to a writable path (not Program Files)
```

## Usage

### pdf_ocr.py (Automated Pipeline)

Located at `C:\Users\<user>\Desktop\09_工具脚本\pdf_ocr.py`

```bash
# Auto-detect best engine (PaddleOCR > Tesseract)
python pdf_ocr.py "扫描件.pdf"

# Save to file
python pdf_ocr.py "扫描件.pdf" -o result.txt

# Force specific engine
python pdf_ocr.py "图片.png" --engine paddle
python pdf_ocr.py "扫描件.pdf" --engine tesseract

# JSON output
python pdf_ocr.py "扫描件.pdf" --format json
```

### Inline Python (Direct API calls)

```python
from pdf_ocr import ocr_file, detect_engines

# Check available engines
engines = detect_engines()

# OCR a file
results, engine_used = ocr_file("document.pdf")
for page_text in results:
    print(page_text)
```

## Pitfalls

1. **PaddleOCR + Python 3.13**: paddlepaddle 3.3.x has oneDNN bug. Install `paddlepaddle<3.3.0` to work around.
2. **PaddleOCR API version mismatch**: The return format changed in recent versions. The `pdf_ocr.py` script handles both old (nested list) and new (dict with `rec_texts`/`rec_scores`) formats.
3. **Tesseract no Chinese**: Default install has only `eng` and `osd`. Must download `chi_sim.traineddata`.
4. **Tessdata permissions**: `Program Files\tessdata` is write-protected. Set `TESSDATA_PREFIX` to a user-writable directory.
5. **MSYS path issues**: When calling Tesseract from bash on Windows, use Windows native paths (`C:\...`) not MSYS paths (`/c/...`).
6. **PDF is scanned vs digital**: Always check `page.get_text().strip()` first. If empty, it's a scanned image → needs OCR.

## Workflow for Multi-Document Processing

When processing several documents (e.g., filling a tracking table):

1. **Read the target Excel/table** first to understand the required fields
2. **Batch OCR all PDFs** in parallel using subagents:
   - One subagent per PDF (they run concurrently)
   - Pass file paths and field mapping in the context
3. **Consolidate results** and write to the target Excel using openpyxl
4. **Flag uncertain fields** (OCR may misread numbers/special chars)
