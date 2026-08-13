# -*- coding: utf-8 -*-
r"""PDF 扫描件 OCR 自动化工具 - PaddleOCR(首选) / Tesseract(后备)"""
import os, sys, re, argparse, subprocess, tempfile, shutil
from pathlib import Path

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSDATA_FALLBACK = str(Path.home() / "tessdata")

def detect_engines():
    engines = []
    try:
        from paddleocr import PaddleOCR
        engines.append(("paddle", PaddleOCR))
    except ImportError:
        pass
    if os.path.exists(TESSERACT_PATH):
        langs = _tesseract_langs()
        if "chi_sim" in langs:
            engines.append(("tesseract", {"lang": "chi_sim+eng"}))
        elif _download_chi_sim():
            engines.append(("tesseract", {"lang": "chi_sim+eng"}))
        else:
            engines.append(("tesseract", {"lang": "eng"}))
    return engines

def _tesseract_langs():
    env = os.environ.copy()
    td = _find_tessdata()
    if td: env["TESSDATA_PREFIX"] = td
    try:
        r = subprocess.run([TESSERACT_PATH, "--list-langs"], capture_output=True, text=True, env=env, timeout=10)
        return [l.strip() for l in r.stdout.strip().split("\n")[1:] if l.strip() and not l.startswith("List")]
    except: return []

def _find_tessdata():
    sd = os.path.join(os.path.dirname(TESSERACT_PATH), "tessdata")
    if os.path.isdir(sd) and os.path.exists(os.path.join(sd, "chi_sim.traineddata")): return sd
    os.makedirs(TESSDATA_FALLBACK, exist_ok=True); return TESSDATA_FALLBACK

def _download_chi_sim():
    t = os.path.join(TESSDATA_FALLBACK, "chi_sim.traineddata")
    if os.path.exists(t): return True
    print("下载中文语言包...")
    try:
        import urllib.request
        urllib.request.urlretrieve("https://gh-proxy.com/https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata", t)
        print(f"完成 ({os.path.getsize(t)//1024//1024}MB)"); return True
    except: return False

def pdf_to_images(pdf_path, dpi=300):
    import fitz
    doc = fitz.open(pdf_path)
    images, tmpdir = [], tempfile.mkdtemp(prefix="ocr_")
    print(f"PDF {doc.page_count}页，导出图片...")
    for i, pg in enumerate(doc):
        t = pg.get_text().strip()
        if len(t) > 50:
            tp = os.path.join(tmpdir, f"p{i+1}.txt")
            with open(tp, "w", encoding="utf-8") as f: f.write(t)
            images.append(("text", tp))
        else:
            pix = pg.get_pixmap(dpi=dpi)
            ip = os.path.join(tmpdir, f"p{i+1}.png")
            pix.save(ip); images.append(("image", ip))
    doc.close(); return images, tmpdir

_CORRECTIONS = {"跟陵":"跟踪","肌报":"报送","确霞":"确需","颉导":"领导","简字":"签字","盐章":"盖章","顶目":"项目","临肘":"临时"}
def _clean(t):
    for w, c in _CORRECTIONS.items(): t = t.replace(w, c)
    return re.sub(r'\n{3,}|\s+\n', '\n\n', t).strip()

def ocr_tesseract(img, lang="chi_sim+eng"):
    env = os.environ.copy(); env["TESSDATA_PREFIX"] = _find_tessdata()
    try:
        r = subprocess.run([TESSERACT_PATH, img, "stdout", "-l", lang], capture_output=True, text=True, env=env, timeout=60)
        return _clean(r.stdout) if (r.returncode == 0 and r.stdout.strip()) else f"[ERR] {r.stderr[:200]}"
    except subprocess.TimeoutExpired: return "[TIMEOUT]"
    except Exception as e: return f"[EXC: {e}]"

_ocr = None
def ocr_paddle(img):
    global _ocr
    if _ocr is None:
        print("  初始化 PaddleOCR...")
        from paddleocr import PaddleOCR
        _ocr = PaddleOCR(use_textline_orientation=True, lang="ch")
    r = _ocr.ocr(img)
    if not r or not isinstance(r, list) or len(r) == 0: return "[无结果]"
    item = r[0]
    if isinstance(item, dict) and "rec_texts" in item:
        return "\n".join(t for t, s in zip(item["rec_texts"], item.get("rec_scores", [1]*len(item["rec_texts"]))) if s > 0.5) or "[无结果]"
    if isinstance(item, list):
        lines = []
        for ln in item:
            if isinstance(ln, list) and len(ln) > 1:
                tc = ln[1]
                if isinstance(tc, (list, tuple)) and len(tc) >= 2 and tc[1] > 0.5: lines.append(tc[0])
                elif isinstance(tc, str): lines.append(tc)
        return "\n".join(lines) or "[无结果]"
    return "[无结果]"

def ocr_file(input_path, engine="auto", dpi=300):
    input_path = os.path.abspath(input_path)
    if not os.path.exists(input_path): print(f"文件不存在: {input_path}"); sys.exit(1)
    ext = os.path.splitext(input_path)[1].lower(); tmpdir = None
    images = pdf_to_images(input_path, dpi) if ext == ".pdf" else ([("image", input_path)] if ext in (".png",".jpg",".jpeg",".tiff",".bmp") else (print("不支持"); sys.exit(1)))
    if engine == "auto":
        es = detect_engines()
        if not es: print("无可用OCR引擎"); sys.exit(1)
        en, ec = es[0]
    elif engine == "paddle": en, ec = "paddle", None
    elif engine == "tesseract": en, ec = "tesseract", {"lang":"chi_sim+eng"}
    else: print("未知引擎"); sys.exit(1)
    print(f"引擎: {en}")
    results = []
    for i, (pt, p) in enumerate(images):
        if pt == "text":
            with open(p, encoding="utf-8") as f: results.append(f.read())
        else:
            print(f"  OCR 第{i+1}页...", end=" ", flush=True)
            t = ocr_paddle(p) if en == "paddle" else ocr_tesseract(p, ec.get("lang","chi_sim+eng"))
            print(f"({len(t)}字符)"); results.append(t)
    if tmpdir: shutil.rmtree(tmpdir, ignore_errors=True)
    return results, en

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="PDF/图片OCR")
    p.add_argument("input"); p.add_argument("-o","--output"); p.add_argument("--engine", choices=["auto","tesseract","paddle"], default="auto")
    p.add_argument("--format", choices=["text","json"], default="text"); p.add_argument("--dpi", type=int, default=300)
    a = p.parse_args()
    rs, en = ocr_file(a.input, a.engine, a.dpi)
    out = ""
    if a.format == "json":
        import json as j
        out = j.dumps({"source": os.path.abspath(a.input), "engine": en, "pages": [{"page": i+1, "text": t} for i, t in enumerate(rs)]}, ensure_ascii=False, indent=2)
    else:
        for i, t in enumerate(rs):
            if len(rs) > 1: out += f"\n{'='*60}\n第{i+1}页\n{'='*60}\n\n"
            out += t + "\n"
    if a.output:
        with open(a.output, "w", encoding="utf-8") as f: f.write(out)
        print(f"已保存: {os.path.abspath(a.output)}")
    else: print(out)
