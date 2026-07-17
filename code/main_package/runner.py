"""
runner.py — Auto-detect the right template and extract data from a PDF.

Usage:
    from main_package.runner import run
    run("path/to/file.pdf", "output.csv")

    
Adding a new template:
    1. Create main_package/templates/template16.py
    2. Implement detect(pdf_path) -> bool
    3. Implement extract(pdf_path) -> list[dict]
    4. Implement save_csv(records, output_path) -> None
    That's it — runner picks it up automatically.
"""
import importlib
import pkgutil
from main_package import templates as templates_pkg


def _load_templates():
    """Discover and import all template modules in the templates package."""
    modules = []
    for _, name, _ in pkgutil.iter_modules(templates_pkg.__path__):
        module = importlib.import_module(f"main_package.templates.{name}")
        modules.append(module)
    return modules


def run(pdf_path: str, output_path: str) -> None:
    for template in _load_templates():
        try:
            matched = template.detect(pdf_path)
        except Exception:
            # Some templates only support PDFs or XLSX files; skip incompatible detectors.
            continue

        if matched:
            print(f"Matched: {template.__name__}")
            records = template.extract(pdf_path)
            template.save_csv(records, output_path)
            print(f"Saved {len(records)} rows → {output_path}")
            return

    raise ValueError(f"No matching template found for: {pdf_path}\nAdd a new template to main_package/templates/")