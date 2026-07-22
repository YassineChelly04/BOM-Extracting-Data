"""
default_template — generic OCR fallback (best effort, NOT exact).

The pipeline uses this ONLY when no other template detected a file. It OCRs
every page and, on each table row, treats a CAS number as the anchor: the text
just before it is the material name, the first number after it is the weight.

Unlike template4.py (which is tuned for one exact scanned form), this makes no
assumptions about a specific layout — so its output is a best guess, not a
guaranteed-correct extraction.

paddleocr / pymupdf are imported inside the functions, so simply importing this
module is cheap; the heavy OCR engine only loads when extract() actually runs.
"""
import logging
import re

logging.disable(logging.WARNING)

_OCR = None
_CAS = re.compile(r"^\d{2,7}-\d{2}-\d$")
_NUM = re.compile(r"^\d+(\.\d+)?$")


def _get_ocr():
    global _OCR
    if _OCR is None:
        from paddleocr import PaddleOCR
        _OCR = PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            lang="en",
        )
    return _OCR


def _ocr_items(pdf_path: str, page_index: int, zoom: float = 3.0):
    import fitz
    import numpy as np

    doc = fitz.open(pdf_path)
    pix = doc[page_index].get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    doc.close()
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        img = img[:, :, :3]

    result = _get_ocr().ocr(img, cls=True)
    items = []
    if not result or not result[0]:
        return items
    for line in result[0]:
        box, text = line[0], line[1][0]
        items.append({
            "text": text.strip(),
            "y": sum(p[1] for p in box) / 4,
            "x0": min(p[0] for p in box),
        })
    return items


def _cluster_rows(items, y_gap: float = 9.0):
    items = sorted(items, key=lambda i: i["y"])
    rows, current, last_y = [], [], None
    for it in items:
        if last_y is None or (it["y"] - last_y) <= y_gap:
            current.append(it)
        else:
            rows.append(current)
            current = [it]
        last_y = it["y"]
    if current:
        rows.append(current)
    for row in rows:
        row.sort(key=lambda i: i["x0"])
    return rows


def detect(path: str) -> bool:
    # Generic fallback — never claims a file itself; the pipeline calls extract()
    # directly when nothing else matched.
    return False


def extract(pdf_path: str) -> list[dict]:
    import fitz

    doc = fitz.open(pdf_path)
    n_pages = doc.page_count
    doc.close()

    results = []
    for page_index in range(n_pages):
        for row in _cluster_rows(_ocr_items(pdf_path, page_index)):
            texts = [c["text"] for c in row]
            cas = next((t for t in texts if _CAS.match(t)), None)
            if not cas:
                continue
            idx = texts.index(cas)
            name = texts[idx - 1] if idx >= 1 else ""
            if not name or _NUM.match(name):
                continue
            weight = next((t for t in texts[idx + 1:] if _NUM.match(t)), None)
            if weight is None:
                continue
            results.append({
                "material": name.strip(),
                "substance": cas,
                "weight_mg": weight,
            })
    return results


def save_csv(records: list[dict], output_path: str) -> None:
    if not records:
        return
    import csv
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["material", "substance", "weight_mg"])
        writer.writeheader()
        writer.writerows(records)
