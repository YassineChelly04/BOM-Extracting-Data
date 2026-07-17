import sys
sys.path.insert(0, r"C:\Users\yassi\Desktop\V1\MCF8315C-Q1_MC121EVM_SLVC913\BOM\code")

from main_package.runner import run

files = []

for i in range(1, 14):
    extension = "xlsx" if i in (5, 7) else "pdf"
    files.append(
        (fr"env-test\template{i}.{extension}", f"template{i}_output.csv")
    )

for pdf_path, output_path in files:
    try:
        run(pdf_path, output_path)
    except Exception as exc:
        print(f"FAILED: {pdf_path} -> {exc}")
