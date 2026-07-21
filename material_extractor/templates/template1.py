import csv
import pdfplumber

# Target case size
SIZE = "0402"

# Rows to skip — they are summaries, not materials
SKIP_ROWS = {"Homogeneous Level Weight", "Total Weight"}

# Case sizes live in the Annex table (page 2), row index 1
CASE_SIZES_ROW = 1
# Material rows start after the header row (index 2)
HEADER_ROW = 2


def detect(pdf_path: str) -> bool:
    """Return True if this PDF matches the Annex 3 table layout used by template1."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) < 2:
                return False
            text = pdf.pages[1].extract_text() or ""
    except Exception:
        return False

    return (
        "Homogeneous Level Weight" in text
        and "Total Weight" in text
        and "0402" in text
    )


def extract(pdf_path: str) -> list[dict]:
    with pdfplumber.open(pdf_path) as pdf:
        table = pdf.pages[1].extract_tables()[0]  # Annex 3 table

    case_sizes = [c for c in table[CASE_SIZES_ROW][4:] if c]  # e.g. ['0402', '0603', ...]

    results = []
    current_level = None

    for row in table[HEADER_ROW + 1:]:
        level, material, substance, cas, *weights = row

        # Track the current homogeneous level (merged cells come as None)
        if level and level not in SKIP_ROWS:
            current_level = level

        # Skip summary rows and rows without a real material name
        if not material or level in SKIP_ROWS:
            continue

        results.append({
            "material":  material,
            "substance": substance,
            "weight_mg": dict(zip(case_sizes, weights))[SIZE],
        })

    return results


def save_csv(records: list[dict], output_path: str) -> None:
    if not records:
        return
    fieldnames = ["material", "substance", "weight_mg"]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


if __name__ == "__main__":
    records = extract(r"env-test/template1.pdf")
    save_csv(records, "materials.csv")