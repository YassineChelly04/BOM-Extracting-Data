"""Extraction pipeline.

For each input file it walks the templates in templates/, asks each one
"is this your format?" (template.detect), and the first one that says yes does
the extraction. The rows are normalized and written to CSV.

A "template" is any module in the templates/ folder that exposes:

    detect(path: str) -> bool
    extract(path: str) -> list[dict]      # dicts with material / substance / weight_mg

That is the entire contract. Drop a new templateN.py in templates/ and it is
picked up automatically -- no registration, no YAML, no wiring.
"""
from __future__ import annotations

import csv
import importlib
import pkgutil
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

from material_extractor import templates as templates_pkg
from material_extractor.normalizer import Normalizer

OUTPUT_FIELDS = ["material", "substance", "weight_mg", "category", "raw_material", "template", "source_file"]


@dataclass
class Result:
    """Outcome of processing one file."""

    source_file: str
    template: str | None = None
    records: list[dict] = field(default_factory=list)
    error: str | None = None

    @property
    def matched(self) -> bool:
        return self.template is not None


def discover_templates() -> list[ModuleType]:
    """Import every module in the templates package that looks like a template.

    Templates whose heavy optional dependencies are missing (e.g. the OCR
    template needs paddleocr) are skipped with a warning instead of crashing.
    """
    modules: list[ModuleType] = []
    for info in sorted(pkgutil.iter_modules(templates_pkg.__path__), key=lambda m: m.name):
        try:
            module = importlib.import_module(f"{templates_pkg.__name__}.{info.name}")
        except Exception as exc:  # missing optional dep, syntax error, etc.
            print(f"[skip] template '{info.name}' could not be imported: {exc}")
            continue
        if hasattr(module, "detect") and hasattr(module, "extract"):
            modules.append(module)
    return modules


class Pipeline:
    """Detect -> extract -> normalize -> write."""

    def __init__(self, normalizer: Normalizer | None = None,
                 templates: list[ModuleType] | None = None):
        self.normalizer = normalizer or Normalizer()
        self.templates = templates if templates is not None else discover_templates()

    def process_file(self, path: Path) -> Result:
        result = Result(source_file=str(path))
        for template in self.templates:
            try:
                if not template.detect(str(path)):
                    continue
            except Exception:
                continue  # a template that errors on detect just doesn't match

            result.template = template.__name__.rsplit(".", 1)[-1]
            try:
                rows = template.extract(str(path))
            except Exception as exc:
                result.error = f"{result.template}: {exc}"
                return result

            for row in rows:
                record = self.normalizer.normalize_record(dict(row))
                record["template"] = result.template
                record["source_file"] = path.name
                result.records.append(record)
            return result
        return result  # no template matched

    def process_path(self, path: Path) -> list[Result]:
        files = [path] if path.is_file() else sorted(
            p for p in path.rglob("*") if p.suffix.lower() in (".pdf", ".xlsx", ".xls")
        )
        return [self.process_file(f) for f in files]


def write_csv(records: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow(record)


def run(input_path: Path, output_dir: Path) -> list[Result]:
    """Process a file or directory, writing one CSV per file plus an aggregate."""
    pipeline = Pipeline()
    results = pipeline.process_path(input_path)

    all_records: list[dict] = []
    for result in results:
        if result.records:
            write_csv(result.records, output_dir / "individual" / f"{Path(result.source_file).stem}.csv")
            all_records.extend(result.records)

    if all_records:
        write_csv(all_records, output_dir / "all_materials.csv")

    return results
