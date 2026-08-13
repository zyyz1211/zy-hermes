# -*- coding: utf-8 -*-
"""批量提取目录下所有 PDF 为 txt，供关键词检索。
用法: python extract_pdfs.py <知识库目录>   (Windows Python，需 pymupdf)
输出: <目录>/_extracted/*.txt，用后请清理。
"""
import fitz  # pymupdf
import os
import sys
import glob


def main(kb_dir: str) -> None:
    out_dir = os.path.join(kb_dir, "_extracted")
    os.makedirs(out_dir, exist_ok=True)
    for pdf in sorted(glob.glob(os.path.join(kb_dir, "*.pdf"))):
        try:
            doc = fitz.open(pdf)
            text = "\n".join(page.get_text() for page in doc)
            base = os.path.basename(pdf).replace(".pdf", ".txt")
            with open(os.path.join(out_dir, base), "w", encoding="utf-8") as f:
                f.write(text)
            print(f"{base}: {len(doc)}页, {len(text)}字")
            doc.close()
        except Exception as e:
            print(f"{pdf}: ERROR {e}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
