"""
Template 6: IHS Normalized Format — Material Declaration Data Sheet (.pdf)
Columns: Sub Part | Sub Part Weight (mg) | Sub Part Details | Sub Part Substance | CAS Number | Sub Part Substance Weight (mg) | ...
Skips the Total Weight summary row.
"""
import csv
import pdfplumber

SKIP_SUBSTANCES = {"Total Weight\n(mg)", "Total Weight"}


def detect(pdf_path: str) -> bool:
    """Return True if this PDF matches the IHS Normalized Format layout."""
    if not pdf_path.lower().endswith(".pdf"):
        return False
    try:
        with pdfplumber.open(pdf_path) as pdf:
            tables = pdf.pages[0].extract_tables()
            if len(tables) < 2 or len(tables[1]) < 5:
                return False
            # Text is garbled (cid codes) so detect via table data
            row = tables[1][4]
            return len(row) >= 5 and row[0] in ("CERAMIC", "ELECTRODE", "PLATING", "TERMINATION")
    except Exception:
        return False


def extract(pdf_path: str) -> list[dict]:
    with pdfplumber.open(pdf_path) as pdf:
        rows = []
        for page in pdf.pages:
            tables = page.extract_tables()
            if len(tables) >= 2:
                rows += tables[1][4:]  # skip garbled header rows (cid codes)

    results = []
    for row in rows:
        sub_part, _, _, substance, cas, weight_mg, *_ = row

        if not substance or not weight_mg:
            continue
        if substance in SKIP_SUBSTANCES or "cid" in str(substance):
            continue
        # Skip the total weight row (cas is garbled or empty)
        try:
            float(weight_mg)
        except (ValueError, TypeError):
            continue

        results.append({
            "material":  substance.replace("\n", " ").strip(),
            "substance": cas.strip() if cas else "",
            "weight_mg": str(weight_mg).strip(),
        })

    return results


def save_csv(records: list[dict], output_path: str) -> None:
    if not records:
        return
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["material", "substance", "weight_mg"])
        writer.writeheader()
        writer.writerows(records)
