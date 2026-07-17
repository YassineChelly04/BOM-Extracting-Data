"""
Template 4: IPC-1752 Material / RoHS Composition Declaration (scanned form)
Uses PaddleOCR instead of pdfplumber because the source PDF is a scanned
image (no extractable text layer), so table cells must be reconstructed
from OCR text boxes rather than read with pdfplumber's table extractor.

Output: only `substance` and `weight_mg` per user's requirement.

Install requirements (once):
    pip install "paddleocr[all]"
    pip install pymupdf          # used to rasterize PDF pages to images
"""
import logging

logging.disable(logging.WARNING)

import csv
import re
from decimal import Decimal, InvalidOperation

import fitz  # PyMuPDF - rasterizes PDF pages into images for OCR
from paddleocr import PaddleOCR

# ---------------------------------------------------------------------------
# OCR engine (loaded once, reused across calls)
# ---------------------------------------------------------------------------
_OCR = None


def _get_ocr() -> PaddleOCR:
    global _OCR
    if _OCR is None:
        _OCR = PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            lang="en",
            # Tighter detection boxes reduce the chance that a nearby
            # +/-  edit-button glyph gets fused into the same text box
            # as the cell's real content.
            text_det_unclip_ratio=1.3,
        )
    return _OCR


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _render_page(pdf_path: str, page_index: int, zoom: float = 4.0):
    """Rasterize a single PDF page to an RGB numpy array (high dpi for OCR).
    zoom bumped 3.0 -> 4.0: more pixels between adjacent glyphs/cells means
    fewer merged OCR boxes.
    """
    doc = fitz.open(pdf_path)
    page = doc[page_index]
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    doc.close()

    import numpy as np
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        img = img[:, :, :3]
    return img


def _ocr_page(pdf_path: str, page_index: int):
    """Run PaddleOCR on one page, return list of dicts with text + position."""
    img = _render_page(pdf_path, page_index)
    ocr = _get_ocr()
    result = ocr.ocr(img, cls=True)

    items = []
    if not result or not result[0]:
        return items

    for line in result[0]:
        box = line[0]
        text = line[1][0]

        x = sum(p[0] for p in box) / 4
        y = sum(p[1] for p in box) / 4
        x0 = min(p[0] for p in box)
        height = max(p[1] for p in box) - min(p[1] for p in box)

        cleaned = _strip_ui_artifacts(text.strip())
        if cleaned:
            items.append({"text": cleaned, "x": x, "y": y, "x0": x0, "h": height})

    return items


# ---------------------------------------------------------------------------
# OCR text cleanup
# ---------------------------------------------------------------------------

# The form has small clickable "+I -I / +M -M / +C -C / +S -S" edit buttons
# immediately to the left of several cells. When they render close enough
# together, PaddleOCR sometimes fuses the button glyphs into the same text
# box as the real cell content, e.g. "-MTermination" or "+S-sBarium Titanate".
# Strip a leading run of these button-like fragments.
_UI_ARTIFACT_RE = re.compile(r'^(?:[+\-]{1,2}\s*[ICMSicms]{1,2}\s*){1,3}(?=[A-Za-z])')
# Tokens that are ONLY a button/arrow (nothing else) - drop outright.
_UI_ONLY_RE = re.compile(r'^[+\-]{1,2}[ICMSicms]{0,2}$|^[▼\-]$')


def _strip_ui_artifacts(text: str) -> str:
    if _UI_ONLY_RE.match(text):
        return ""
    prev = None
    while prev != text:
        prev = text
        text = _UI_ARTIFACT_RE.sub('', text)
    return text.strip()


def _cluster_rows(items, y_gap: float = 9.0):
    """Group OCR text boxes into table rows using consecutive-gap clustering
    (NOT running-mean clustering). Running-mean clustering lets the cluster
    center drift as items are added, which can silently absorb the next
    physical row into the current one on tightly packed tables. Splitting
    strictly on the gap between consecutive sorted y-values avoids that.
    """
    items = sorted(items, key=lambda i: i["y"])
    rows = []
    current = []
    last_y = None
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


_CAS_RE = re.compile(r"^\d{2,7}-\d{2}-\d$")
_NUM_RE = re.compile(r"^\d+(\.\d+)?$")
_UOM_TO_MG = {"mg": Decimal(1), "g": Decimal(1000), "kg": Decimal(1_000_000), "ug": Decimal("0.001")}


def _parse_row(row_texts: list[str]) -> dict | None:
    """
    Turn a row of left-to-right OCR strings from the substance table into a
    {substance, weight_mg} record. Only substance name + final weight are
    kept, per requirement.
    """
    cas = None
    for t in row_texts:
        if _CAS_RE.match(t):
            cas = t
            break
    if not cas:
        return None  # not a substance row

    cas_idx = row_texts.index(cas)

    # Substance name = token immediately before the CAS number.
    substance = row_texts[cas_idx - 1] if cas_idx >= 1 else ""
    # Common OCR corrections
    OCR_FIXES = {
        "opper": "Copper",
        "ickel": "Nickel",
        "arium Titanate": "Barium Titanate",
        "in": "Tin",
    }

    substance = OCR_FIXES.get(substance, substance)
    if not substance or _NUM_RE.match(substance):
        return None  # malformed row, skip rather than guess

    # Final substance weight = first number found *after* the CAS number,
    # paired with the unit that immediately follows it (defaults to mg).
    weight_val, unit = None, "mg"
    tail = row_texts[cas_idx + 1:]
    for i, t in enumerate(tail):
        if _NUM_RE.match(t):
            weight_val = t
            if i + 1 < len(tail) and tail[i + 1].lower() in _UOM_TO_MG:
                unit = tail[i + 1].lower()
            break

    if weight_val is None:
        return None

    try:
        weight_mg = Decimal(weight_val) * _UOM_TO_MG.get(unit, Decimal(1))
    except InvalidOperation:
        return None

    return {
        "material": substance.strip(),
        "substance": cas,
        "weight_mg": f"{weight_mg:.10f}".rstrip("0").rstrip("."),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect(pdf_path: str) -> bool:
    """Return True if this scanned PDF matches the IPC-1752 Material
    Composition Declaration layout."""
    items = _ocr_page(pdf_path, 0)
    text = " ".join(i["text"] for i in items)
    return (
        "Material Composition Declaration" in text
        and "IPC" in text
        and "1752" in text
    )


def extract(pdf_path: str) -> list[dict]:
    doc = fitz.open(pdf_path)
    n_pages = doc.page_count
    doc.close()

    results = []
    for page_index in range(n_pages):
        items = _ocr_page(pdf_path, page_index)
        page_text = " ".join(i["text"] for i in items)
        if "Homogeneous Material" not in page_text and "Substance" not in page_text:
            continue  # skip pages without the substance table

        for row in _cluster_rows(items):
            row_texts = [r["text"] for r in row]
            record = _parse_row(row_texts)
            if record:
                results.append(record)

    return results


def save_csv(records: list[dict], output_path: str) -> None:
    if not records:
        return
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["material", "substance", "weight_mg"])
        writer.writeheader()
        writer.writerows(records)


if __name__ == "__main__":
    import sys

    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "template4.pdf"
    if detect(pdf_path):
        records = extract(pdf_path)
        save_csv(records, "template4_output.csv")
        print(f"Extracted {len(records)} substance rows -> template4_output.csv")
    else:
        print("This PDF does not match the IPC-1752 Material Composition Declaration layout.")