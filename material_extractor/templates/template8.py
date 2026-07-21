"""
Template 8: LITEON — Material Composition Declaration (.pdf)
Table on page 1: Element name | CAS No. | substance weight (last column, in mg).
Skips rows with no CAS, total rows, and header rows.
"""
import csv
from decimal import Decimal
import pdfplumber

SKIP_ELEMENTS = {"ttl wt = 1.60 mg", None, ""}
SKIP_CAS = {"Trade secret", ""}


def detect(pdf_path: str) -> bool:
    if not pdf_path.lower().endswith(".pdf"):
        return False
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = pdf.pages[0].extract_text() or ""
        return "MATERIAL COMPOSITION DECLARATION" in text and "CAS No." in text and "LITEON" in text.upper()
    except Exception:
        return False


def extract(pdf_path: str) -> list[dict]:
    with pdfplumber.open(pdf_path) as pdf:
        table = pdf.pages[0].extract_tables()[0]

    results = []
    for row in table[3:]:  # skip 3 header rows
        # columns: Composition part | Material name | Material mass (mg) | Material mass (%) | Element name | CAS No. | Element % | substance weight
        if len(row) < 8:
            continue
        _, _, _, _, element, cas, _, weight_mg = row[:8]

        if not element or element in SKIP_ELEMENTS:
            continue
        if not cas or cas.strip() in SKIP_CAS:
            continue
        if not weight_mg:
            continue

        # Skip the total/approved rows
        try:
            val = Decimal(str(weight_mg).strip())
        except Exception:
            continue

        results.append({
            "material":  element.strip(),
            "substance": cas.strip(),
            "weight_mg": f"{val:.10f}".rstrip("0").rstrip("."),
        })

    return results


def save_csv(records: list[dict], output_path: str) -> None:
    if not records:
        return
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["material", "substance", "weight_mg"])
        writer.writeheader()
        writer.writerows(records)
