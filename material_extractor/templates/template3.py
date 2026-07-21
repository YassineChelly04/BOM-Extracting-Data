"""
Template 3: Molex - Product Compliance Declaration
Substance rows across pages 1 & 2, Mass (Grams) column converted to weight_mg.
"""
import csv
from decimal import Decimal
import pdfplumber


def detect(pdf_path: str) -> bool:
    """Return True if this PDF matches the Molex Product Compliance Declaration layout."""
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text() or ""
    return (
        "Product Compliance Declaration" in text
        and "molex" in text.lower()
        and "Product Composition" in text
    )


def extract(pdf_path: str) -> list[dict]:
    with pdfplumber.open(pdf_path) as pdf:
        rows = []
        for page in pdf.pages[:2]:
            tables = page.extract_tables()
            if tables:
                rows += tables[0][1:]  # skip header on each page
 
    results = []
    for name, type_, cas, _, mass_g in rows:
        if type_ != "Substance" or not mass_g:
            continue
        weight_mg = Decimal(mass_g) * 1000
        results.append({
            "material":  name.strip(),
            "substance": cas.strip() if cas else "",
            "weight_mg": f"{weight_mg:.10f}".rstrip("0").rstrip("."),
        })
 
    return results
    with pdfplumber.open(pdf_path) as pdf:
        rows = []
        for page in pdf.pages[:2]:
            tables = page.extract_tables()
            if tables:
                rows += tables[0][1:]

    results = []
    for name, type_, cas, _, mass_g in rows:
        if type_ != "Substance" or not mass_g:
            continue
        results.append(
            {
                "material": name.strip(),
                "substance": cas.strip() if cas else "",
                "weight_mg": round(float(mass_g) * 1000, 6),
            }
        )

    return results


def save_csv(records: list[dict], output_path: str) -> None:
    if not records:
        return
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["material", "substance", "weight_mg"])
        writer.writeheader()
        writer.writerows(records)
