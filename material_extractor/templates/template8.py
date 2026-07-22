"""
Template 8: LITEON — Material Composition Declaration (.pdf)
Table on page 1: Element name | CAS No. | substance weight (last column, in mg).
Skips rows with no CAS, total rows, and header rows.
"""
import csv
from decimal import Decimal, InvalidOperation
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
    current_part_mass = None  # running part mass, used by the percentage-only variant

    for row in table[3:]:  # skip 3 header rows
        # Track the part mass in col 2. It appears only on the first row of each
        # part group (merged cells are None on the rows below it).
        if len(row) > 2 and row[2] and "ttl" not in str(row[2]).lower():
            try:
                current_part_mass = Decimal(str(row[2]).strip())
            except InvalidOperation:
                pass

        # --- Variant A: 8 columns, absolute substance weight in the last column ---
        # cols: part | material | mass(mg) | mass(%) | element | CAS | element(%) | weight(mg)
        if len(row) >= 8:
            _, _, _, _, element, cas, _, weight_mg = row[:8]
            if not element or element in SKIP_ELEMENTS:
                continue
            if not cas or cas.strip() in SKIP_CAS:
                continue
            if not weight_mg:
                continue
            try:
                val = Decimal(str(weight_mg).strip())
            except InvalidOperation:
                continue
            results.append({
                "material":  element.strip(),
                "substance": cas.strip(),
                "weight_mg": f"{val:.10f}".rstrip("0").rstrip("."),
            })
            continue

        # --- Variant B: 7 columns, only an element % — derive mg from the part mass ---
        # cols: part | material | mass(mg) | mass(%) | element | CAS | element(%)
        if len(row) >= 7:
            element, cas, pct_raw = row[4], row[5], row[6]
            if not element or element in SKIP_ELEMENTS:
                continue
            if current_part_mass is None or not pct_raw:
                continue
            try:
                pct = Decimal(str(pct_raw).replace("%", "").strip())
            except InvalidOperation:
                continue
            val = current_part_mass * pct / 100
            results.append({
                "material":  element.strip(),
                "substance": cas.strip() if cas else "",
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
