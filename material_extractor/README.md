# Material Extractor

Reads supplier material-declaration documents (PDF / XLSX) and produces a
unified material composition report from a BOM.

## How it works

```
input file  ──▶  templates/  ──▶  normalizer  ──▶  CSV
                 (detect+extract)  (materials.yaml)
```

1. **templates/** — one file per supplier format. Each exposes `detect(path)`
   and `extract(path)`. The pipeline tries each template's `detect()` and the
   first match extracts the rows.
2. **normalizer** — maps raw material names to canonical names + categories
   using `materials.yaml`.
3. **pipeline** — writes one CSV per file under `output/individual/` and a
   combined `output/all_materials.csv`.

## Run

```bash
python -m material_extractor <file-or-dir> [--output output]

# examples
python -m material_extractor templates/test_files
python -m material_extractor ../Data --output output
```

## Add a new supplier format

Create `templates/template14.py` with two functions:

```python
def detect(path: str) -> bool:
    # return True if this file is your format
    ...

def extract(path: str) -> list[dict]:
    # return rows like {"material": ..., "substance": ..., "weight_mg": ...}
    ...
```

That's it — the pipeline discovers it automatically. No registration, no YAML
template, no wiring.

## Add / teach a new material

Add one entry to `materials.yaml`:

```yaml
Copper (Cu):
  category: Metal
  aliases:
  - copper
  - cu
```

Any raw name matching an alias (case-insensitive) normalizes to the canonical
name and category.

## Layout

```
material_extractor/
  templates/        one file per supplier + test_files/
  materials.yaml    normalization data
  normalizer.py     alias -> canonical + category
  pipeline.py       detect -> extract -> normalize -> CSV
  __main__.py       CLI entry point
  tests/
  output/
```

## Notes

- `template4.py` handles a scanned form via OCR and needs the optional extras:
  `pip install -e ".[ocr]"`. If those deps are missing the pipeline just skips
  that template.
- Weights are normalized to milligrams inside each template.

## Test

```bash
pytest
```
