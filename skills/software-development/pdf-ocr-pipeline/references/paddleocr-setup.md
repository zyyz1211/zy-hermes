# PaddleOCR Setup & API Reference (Windows)

## Installation on Windows

```bash
# Install paddlepaddle (CPU version, avoid 3.3.x bug)
pip install "paddlepaddle<3.3.0"

# Install paddleocr
pip install paddleocr
```

## Known Python 3.13 Compatibility Issues

### Bug: oneDNN `ConvertPirAttribute2RuntimeAttribute`
paddlepaddle 3.3.1 has a bug on Python 3.13:
```
NotImplementedError: (Unimplemented) ConvertPirAttribute2RuntimeAttribute
    not support [pir::ArrayAttribute<pir::DoubleAttribute>]
```
**Fix**: Downgrade to `paddlepaddle<3.3.0`

### Fix: Model files caching
First run downloads ~500MB of models to `C:\Users\<user>\.paddlex\official_models\`.
These are cached for subsequent runs.

## API Changes (v3.x → latest)

### Initialization

```python
# OLD (deprecated)
ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)

# NEW
ocr = PaddleOCR(use_textline_orientation=True, lang="ch")
```

### Inference Call

```python
# OLD
result = ocr.ocr(image_path, cls=True)

# NEW (cls parameter removed)
result = ocr.ocr(image_path)
```

### Return Format

```python
# OLD format (nested list)
result = [[[[x1,y1,x2,y2,x3,y3,x4,y4], (text, confidence)], ...]]
# Access: result[0][0][1][0]  # first text
#         result[0][0][1][1]  # first confidence

# NEW format (list of dicts)
result = [{
    'rec_texts': ['text1', 'text2'],
    'rec_scores': [0.9999, 0.9999],
    'dt_polys': [...],
    'rec_polys': [...],
    ...
}]
# Access: result[0]['rec_texts'][0]
#         result[0]['rec_scores'][0]
```

## Common OCR Corrections (Tesseract)

When using Tesseract for Chinese, common misreads:

| Wrong | Correct |
|-------|---------|
| 跟陵 | 跟踪 |
| 肌报 | 报送 |
| 确霞 | 确需 |
| 颉导 | 领导 |
| 简字 | 签字 |
| 盐章 | 盖章 |
| 顶目 | 项目 |
| 临肘 | 临时 |

## Tesseract Chinese Language Pack

```bash
# Download chi_sim.traineddata
curl -L -o "C:\Users\<user>\tessdata\chi_sim.traineddata" \
  "https://gh-proxy.com/https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata"

# Set env var
export TESSDATA_PREFIX="C:\Users\<user>\tessdata"

# Verify
tesseract --list-langs
# Should show: chi_sim
```
