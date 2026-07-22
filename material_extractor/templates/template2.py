"""
Template 2: Würth Elektronik — Material Declaration (WL-SMCW layout)
Page 1, Table 2: Semi-Component breakdown with Substances and Average mass [%].
"""
import csv
import pdfplumber


def detect(pdf_path: str) -> bool:
    """Return True if this PDF matches the Würth Elektronik material declaration layout."""
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text() or ""
    return "Semi-Component" in text and "Average mass [%]" in text and "Würth Elektronik" in text


def extract(pdf_path: str) -> list[dict]:
    with pdfplumber.open(pdf_path) as pdf:
        tables = pdf.pages[0].extract_tables()

    material_table = tables[1]  # Semi-Component breakdown
    part_table     = tables[2]  # Part List (Type/Size/PartNo, Mass)

    # Parse total mass from "0.01g" -> 0.01 (comma is a European decimal point)
    raw_mass = part_table[1][1]                           # e.g. "0.01g"
    total_mass_g = float(raw_mass.lower().replace("g", "").replace(",", ".").strip())

    results = []
    for row in material_table[1:]:                        # skip header
        if len(row) < 5:
            continue
        _, _, substance, _, avg_mass = row[:5]
        if not substance or not avg_mass:
            continue
        # Average mass [%] may use a comma as the decimal separator ("17,000" = 17.0)
        try:
            pct = float(str(avg_mass).replace(",", ".").strip())
        except ValueError:
            continue
        weight_mg = round(pct / 100 * total_mass_g * 1000, 4)
        results.append({
            "material":  substance.replace("\n", " "),
            "weight_mg": weight_mg,
        })

    return results


def save_csv(records: list[dict], output_path: str) -> None:
    if not records:
        return
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["material", "weight_mg"])
        writer.writeheader()
        writer.writerows(records)