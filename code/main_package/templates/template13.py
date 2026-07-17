"""
Template 14: YAGEO — Material Composition Declaration (材料成分表)
Single table, Content(mg) in col index 6. Skips Total and empty rows.
Handles merged CAS cells (e.g. 'Glass Frit( contain Pb' + ')65997-18-4').
"""
import csv
import pdfplumber

SKIP_PARTS = {"Total", "", None}


def detect(pdf_path: str) -> bool:
    if not pdf_path.lower().endswith(".pdf"):
        return False
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = pdf.pages[0].extract_text() or ""
        return "YAGEO" in text and "Material Composition Declaration" in text and "Content(mg)" in text
    except Exception:
        return False


def extract(pdf_path: str) -> list[dict]:
    with pdfplumber.open(pdf_path) as pdf:
        table = pdf.pages[0].extract_tables()[0]

    results = []
    for row in table[1:]:  # skip header
        no, part, part_wt, material, substance, cas, content_mg, *_ = row

        if part in SKIP_PARTS and not substance:
            continue
        if not substance or not content_mg:
            continue

        # Fix split CAS cells e.g. 'Glass Frit( contain Pb' + ')65997-18-4'
        cas = str(cas or "").strip()
        if cas.startswith(")"):
            cas = cas[1:]

        try:
            float(content_mg)
        except (ValueError, TypeError):
            continue

        results.append({
            "material":  substance.replace("\n", " ").strip(),
            "substance": cas,
            "weight_mg": content_mg.strip(),
        })

    return results


def save_csv(records: list[dict], output_path: str) -> None:
    if not records:
        return
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["material", "substance", "weight_mg"])
        writer.writeheader()
        writer.writerows(records)
