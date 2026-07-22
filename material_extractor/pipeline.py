"""Extraction pipeline.

For each input file it walks the templates in templates/, asks each one
"is this your format?" (template.detect), and the first one that says yes does
the extraction. The rows are normalized and written to CSV.

A "template" is any module in the templates/ folder that exposes:

    detect(path: str) -> bool
    extract(path: str) -> list[dict]      # dicts with material / substance / weight_mg

That is the entire contract. Drop a new templateN.py in templates/ and it is
picked up automatically -- no registration, no YAML, no wiring.

Detection order (a good, cheap-first process):
  1. TEXT templates first — fast, they only read the PDF/Excel text or tables.
  2. If none match, OCR templates (anything that imports paddleocr) are loaded
     lazily and tried — so the heavy OCR engine only loads when a file actually
     needs it, never on a normal text run.
  3. If still nothing matches, templates/default_template.py (a generic OCR
     extractor) is the last resort.

Results are cached per file (keyed by size+mtime) so re-runs skip the work
entirely — the cache is invalidated automatically whenever any template or
materials.yaml changes.
"""
from __future__ import annotations

import csv
import importlib
import importlib.util
import json
import pkgutil
import re
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

from material_extractor import templates as templates_pkg
from material_extractor.normalizer import DEFAULT_DATA_FILE, Normalizer

OUTPUT_FIELDS = ["material", "substance", "weight_mg", "category", "raw_material", "template", "source_file"]
SUMMARY_FIELDS = ["material", "category", "total_weight_mg", "occurrences"]
DEFAULT_TEMPLATE = "default_template"


def _to_mg(value) -> float:
    """Coerce a template's weight_mg (str / int / float / Decimal) to a float.

    Templates already convert to milligrams; this only unifies the *type* so
    every row in every CSV is a clean number ready for summing. Unparseable
    values become 0.0 rather than crashing the run.
    """
    try:
        return round(float(str(value).strip()), 6)
    except (ValueError, TypeError, AttributeError):
        return 0.0


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


# --- template discovery -------------------------------------------------------

def _template_names() -> list[str]:
    """All template module names, ordered by the number in their filename
    (template2 before template10), then alphabetically."""
    def order(info):
        m = re.search(r"\d+", info.name)
        return (int(m.group()) if m else 9999, info.name)
    return [info.name for info in sorted(pkgutil.iter_modules(templates_pkg.__path__), key=order)]


def _uses_ocr(name: str) -> bool:
    """True if the module's source imports paddleocr — checked WITHOUT importing
    it, so the heavy OCR engine never loads during discovery."""
    spec = importlib.util.find_spec(f"{templates_pkg.__name__}.{name}")
    if spec and spec.origin:
        try:
            return "paddleocr" in Path(spec.origin).read_text(encoding="utf-8")
        except OSError:
            return False
    return False


def _import(name: str) -> ModuleType | None:
    try:
        module = importlib.import_module(f"{templates_pkg.__name__}.{name}")
    except Exception as exc:  # missing optional dep, syntax error, etc.
        print(f"[skip] template '{name}' could not be imported: {exc}")
        return None
    if hasattr(module, "detect") and hasattr(module, "extract"):
        return module
    return None


def discover_templates() -> list[ModuleType]:
    """Eagerly import the TEXT templates (fast). OCR templates and the default
    fallback are loaded lazily by the pipeline only when needed."""
    modules = []
    for name in _template_names():
        if name == DEFAULT_TEMPLATE or _uses_ocr(name):
            continue
        module = _import(name)
        if module:
            modules.append(module)
    return modules


def _ocr_template_names() -> list[str]:
    """Names of OCR templates (excluding the generic default), deferred."""
    return [n for n in _template_names() if n != DEFAULT_TEMPLATE and _uses_ocr(n)]


# --- caching ------------------------------------------------------------------

def _code_signature() -> str:
    """A fingerprint of the template code + normalization data. When any of it
    changes, cached results are discarded so stale extractions never linger."""
    paths = list(Path(templates_pkg.__path__[0]).glob("*.py")) + [DEFAULT_DATA_FILE]
    return str(max((p.stat().st_mtime_ns for p in paths if p.exists()), default=0))


def _file_signature(path: Path) -> str:
    st = path.stat()
    return f"{st.st_size}:{st.st_mtime_ns}"


def _load_cache(cache_path: Path | None) -> dict:
    if not cache_path or not cache_path.exists():
        return {}
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if data.get("code_sig") != _code_signature():
        return {}  # code/data changed → ignore stale cache
    return data.get("entries", {})


# --- pipeline -----------------------------------------------------------------

class Pipeline:
    """Detect -> extract -> normalize, with lazy OCR fallback and caching."""

    def __init__(self, normalizer: Normalizer | None = None,
                 templates: list[ModuleType] | None = None,
                 cache_path: Path | None = None):
        self.normalizer = normalizer or Normalizer()
        if templates is not None:
            self.templates = templates
            self._ocr_names: list[str] = []
        else:
            self.templates = discover_templates()
            self._ocr_names = _ocr_template_names()
        self._ocr_mods: list[ModuleType] | None = None   # lazy
        self._default: ModuleType | None = None          # lazy
        self.cache_path = cache_path
        self._cache = _load_cache(cache_path)

    def _load_ocr(self) -> None:
        """Import OCR templates + the default fallback the first time they are
        needed (this is where paddleocr actually loads)."""
        if self._ocr_mods is not None:
            return
        self._ocr_mods = [m for m in (_import(n) for n in self._ocr_names) if m]
        if DEFAULT_TEMPLATE in _template_names():
            self._default = _import(DEFAULT_TEMPLATE)

    def _add_records(self, rows, path: Path, result: Result) -> None:
        for row in rows:
            record = self.normalizer.normalize_record(dict(row))
            record["weight_mg"] = _to_mg(record.get("weight_mg"))
            record["template"] = result.template
            record["source_file"] = path.name
            result.records.append(record)

    def _first_match(self, path: Path, templates, result: Result) -> bool:
        for template in templates:
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
                return True
            self._add_records(rows, path, result)
            return True
        return False

    def process_file(self, path: Path) -> Result:
        result = Result(source_file=str(path))
        key = str(path.resolve())
        sig = _file_signature(path)

        cached = self._cache.get(key)
        if cached and cached.get("sig") == sig:
            result.template = cached.get("template")
            result.records = cached.get("records", [])
            result.error = cached.get("error")
            return result

        # 1. fast text templates
        if not self._first_match(path, self.templates, result):
            # 2. lazy OCR templates
            self._load_ocr()
            if not self._first_match(path, self._ocr_mods, result):
                # 3. generic OCR fallback
                if self._default is not None:
                    try:
                        rows = self._default.extract(str(path))
                    except Exception as exc:
                        result.error = f"{DEFAULT_TEMPLATE}: {exc}"
                        rows = []
                    if rows:
                        result.template = DEFAULT_TEMPLATE
                        self._add_records(rows, path, result)

        self._cache[key] = {"sig": sig, "template": result.template,
                            "records": result.records, "error": result.error}
        return result

    def process_path(self, path: Path) -> list[Result]:
        files = [path] if path.is_file() else sorted(
            p for p in path.rglob("*") if p.suffix.lower() in (".pdf", ".xlsx", ".xls")
        )
        return [self.process_file(f) for f in files]

    def save_cache(self) -> None:
        if not self.cache_path:
            return
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"code_sig": _code_signature(), "entries": self._cache}
        self.cache_path.write_text(json.dumps(payload), encoding="utf-8")


# --- output -------------------------------------------------------------------

def _fmt(value):
    """Render floats as plain decimals (no scientific notation like '3e-06')."""
    if isinstance(value, float):
        return f"{value:.10f}".rstrip("0").rstrip(".") or "0"
    return value


def write_csv(records: list[dict], out_path: Path, fieldnames: list[str] = OUTPUT_FIELDS) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow({k: _fmt(v) for k, v in record.items()})


def summarize(records: list[dict]) -> list[dict]:
    """Sum weight_mg per canonical material across every processed file.

    Returns one row per material: total weight and how many times it appeared,
    sorted heaviest first.
    """
    totals: dict[str, dict] = {}
    for record in records:
        material = record["material"]
        row = totals.setdefault(material, {
            "material": material,
            "category": record.get("category", "Unknown"),
            "total_weight_mg": 0.0,
            "occurrences": 0,
        })
        row["total_weight_mg"] += record.get("weight_mg", 0.0)
        row["occurrences"] += 1

    summary = sorted(totals.values(), key=lambda r: r["total_weight_mg"], reverse=True)
    for row in summary:
        row["total_weight_mg"] = round(row["total_weight_mg"], 6)
    return summary


def run(input_path: Path, output_dir: Path) -> list[Result]:
    """Process a file or directory, writing one CSV per file plus an aggregate."""
    pipeline = Pipeline(cache_path=output_dir / ".extract_cache.json")
    results = pipeline.process_path(input_path)

    all_records: list[dict] = []
    for result in results:
        if result.records:
            write_csv(result.records, output_dir / "individual" / f"{Path(result.source_file).stem}.csv")
            all_records.extend(result.records)

    if all_records:
        write_csv(all_records, output_dir / "all_materials.csv")
        write_csv(summarize(all_records), output_dir / "materials_summary.csv", SUMMARY_FIELDS)

    pipeline.save_cache()
    return results
