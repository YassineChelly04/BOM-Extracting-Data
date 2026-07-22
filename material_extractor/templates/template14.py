"""
Template 14: ROHM — REACH SVHC Report (.pdf)
A lead (Pb) SVHC declaration for ROHM diode products. Page 2 holds one table
listing each package type with the lead mass (mg) contained in its die-attach.
The declared substance is Lead (Pb), CAS 7439-92-1 (stated on page 1).

Columns (page 2):
  Products Name | Product mass(mg) | Part Name | Part mass(mg) |
  Substance mass(mg) | Concentration(wt%) | Concentration(wt%) | List rev.
"""
import csv
from decimal import Decimal, InvalidOperation
import pdfplumber

LEAD_NAME = "Lead (Pb)"
LEAD_CAS = "7439-92-1"


def detect(pdf_path: str) -> bool:
    if not pdf_path.lower().endswith(".pdf"):
        return False
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = pdf.pages[0].extract_text() or ""
        return "SVHC" in text and "REACH" in text and "ROHM" in text
    except Exception:
        return False


def extract(pdf_path: str) -> list[dict]:
    with pdfplumber.open(pdf_path) as pdf:
        if len(pdf.pages) < 2:
            return []
        table = pdf.pages[1].extract_tables()[0]

    results = []
    for row in table[1:]:  # skip header
        if len(row) < 5:
            continue
        substance_mass = row[4]  # 含有量(mg) — lead mass in this package
        if not substance_mass:
            continue
        try:
            weight_mg = Decimal(str(substance_mass).strip())
        except InvalidOperation:
            continue

        results.append({
            "material":  LEAD_NAME,
            "substance": LEAD_CAS,
            "weight_mg": f"{weight_mg:.10f}".rstrip("0").rstrip("."),
        })

    return results


def save_csv(records: list[dict], output_path: str) -> None:
    if not records:
        return
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["material", "substance", "weight_mg"])
        writer.writeheader()
        writer.writerows(records)
