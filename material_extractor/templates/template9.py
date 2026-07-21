"""
Template 10: Vishay — Material Declaration Sheet
Page 1, large table. Substance rows have a CAS number and weight in col index 5.
Section header rows have substance name empty and weight is the section total.
"""
import csv
import pdfplumber

SKIP_SUBSTANCES = {"", None, "Miscellaneous", "miscellaneous"}
SKIP_CAS = {"System", "", None}


def detect(pdf_path: str) -> bool:
    if not pdf_path.lower().endswith(".pdf"):
        return False
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = pdf.pages[0].extract_text() or ""
        return "Vishay" in text and "Material Declaration Sheet" in text and "Homogenous Material Name" in text
    except Exception:
        return False


def extract(pdf_path: str) -> list[dict]:
    with pdfplumber.open(pdf_path) as pdf:
        table = pdf.pages[0].extract_tables()[0]

    results = []
    for row in table:
        # cols: '' | Homogenous Material Name | Material Classification | Substance Name | CAS number | Weight (mg) | % | ppm | % total | RoHS | ''
        if len(row) < 6:
            continue
        substance = row[3]
        cas       = row[4]
        weight    = row[5]

        if not substance or not cas or not weight:
            continue
        if cas in SKIP_CAS or substance in SKIP_SUBSTANCES:
            continue
        try:
            float(weight)
        except (ValueError, TypeError):
            continue

        results.append({
            "material":  substance.strip(),
            "substance": cas.strip(),
            "weight_mg": weight.strip(),
        })

    return results


def save_csv(records: list[dict], output_path: str) -> None:
    if not records:
        return
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["material", "substance", "weight_mg"])
        writer.writeheader()
        writer.writerows(records)
