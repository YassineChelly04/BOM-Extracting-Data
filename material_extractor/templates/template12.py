"""
Template 13: Stackpole SEI — Material Declaration Data Sheet
Single table, multi-value cells (newline-separated). Skips Total Weight row.
"""
import csv
import pdfplumber


def detect(pdf_path: str) -> bool:
    if not pdf_path.lower().endswith(".pdf"):
        return False
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = pdf.pages[0].extract_text() or ""
        return "Material Declaration Data Sheet" in text and "BOM Item" in text and "Material PPM" in text
    except Exception:
        return False


def extract(pdf_path: str) -> list[dict]:
    with pdfplumber.open(pdf_path) as pdf:
        table = pdf.pages[0].extract_tables()[0]

    results = []
    for row in table[1:]:  # skip header
        bom_item, materials, cas_numbers, weights, *_ = row

        if not materials or not weights or "Total Weight" in str(bom_item or ""):
            continue

        # Cells may contain multiple newline-separated values
        mat_list = str(materials).split("\n")
        cas_list = str(cas_numbers).split("\n") if cas_numbers else []
        wgt_list = str(weights).split("\n")

        for i, mat in enumerate(mat_list):
            mat = mat.strip()
            cas = cas_list[i].strip() if i < len(cas_list) else ""
            wgt = wgt_list[i].strip() if i < len(wgt_list) else ""

            if not mat or not wgt:
                continue
            try:
                float(wgt)
            except (ValueError, TypeError):
                continue

            results.append({
                "material":  mat,
                "substance": cas,
                "weight_mg": wgt,
            })

    return results


def save_csv(records: list[dict], output_path: str) -> None:
    if not records:
        return
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["material", "substance", "weight_mg"])
        writer.writeheader()
        writer.writerows(records)
