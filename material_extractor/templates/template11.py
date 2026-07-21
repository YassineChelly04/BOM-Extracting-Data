"""
Template 12: EDS — Ingredient Composition Table (Murata-style)
Single table. Substance mass (mg) is in col index 6. Skips the Total row.
"""
import csv
import pdfplumber

SKIP_PARTS = {"Total （Design value）", None, ""}


def detect(pdf_path: str) -> bool:
    if not pdf_path.lower().endswith(".pdf"):
        return False
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = pdf.pages[0].extract_text() or ""
        return "EDS" in text and "Ingredient composition table" in text and "CAS No." in text
    except Exception:
        return False


def extract(pdf_path: str) -> list[dict]:
    with pdfplumber.open(pdf_path) as pdf:
        table = pdf.pages[0].extract_tables()[0]

    results = []
    for row in table[3:]:  # skip 3 header rows
        # cols: Part | Type name | Compound Mass(mg) | Ratio(%) | Substance | CAS No. | Compound Mass(mg) | Comp.(%) | Ratio(%) | Purposes | Remark
        part, _, _, _, substance, cas, mass_mg, *_ = row

        if part in SKIP_PARTS and not substance:
            continue
        if not substance or not cas or not mass_mg:
            continue
        try:
            float(mass_mg)
        except (ValueError, TypeError):
            continue

        results.append({
            "material":  substance.strip(),
            "substance": cas.strip(),
            "weight_mg": mass_mg.strip(),
        })

    return results


def save_csv(records: list[dict], output_path: str) -> None:
    if not records:
        return
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["material", "substance", "weight_mg"])
        writer.writeheader()
        writer.writerows(records)
