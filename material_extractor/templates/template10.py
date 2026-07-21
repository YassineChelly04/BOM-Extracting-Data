"""
Template 11: Harwin — Material Declaration
Multiple product variants on one page, each with its own table.
Weight column is in grams — converted to mg. Skips impurity rows (weight = 0 or tolerance-only).
"""
import csv
from decimal import Decimal
import pdfplumber

SKIP_SUBSTANCES = {"Other Impurities", "", None}


def detect(pdf_path: str) -> bool:
    if not pdf_path.lower().endswith(".pdf"):
        return False
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = pdf.pages[0].extract_text() or ""
        return "HARWIN" in text.upper() and "Homogeneous Material Location" in text and "Weight (g)" in text
    except Exception:
        return False


def extract(pdf_path: str) -> list[dict]:
    with pdfplumber.open(pdf_path) as pdf:
        # Collect all material tables (tables 2, 5, ... — every other table is a material table)
        tables = pdf.pages[0].extract_tables()

    # Material tables are those with header "Homogeneous Material Location"
    results = []
    seen = set()  # deduplicate across variants

    for table in tables:
        if not table or table[0][0] != "Homogeneous Material Location":
            continue
        for row in table[1:]:
            location, weight_g, tolerance, substance, cas = row[:5]
            if not substance or substance in SKIP_SUBSTANCES or not cas:
                continue
            try:
                w = Decimal(str(weight_g).strip())
                if w <= 0:
                    continue
            except Exception:
                continue

            key = (substance.strip(), cas.strip())
            if key in seen:
                continue
            seen.add(key)

            weight_mg = w * 1000
            results.append({
                "material":  substance.strip(),
                "substance": cas.strip(),
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
