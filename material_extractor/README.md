# Material Extractor

Reads supplier material-declaration documents (PDF / XLSX) and produces one
unified material-composition report (CSV) from a BOM.

Every supplier writes their document differently, so a human can read them all
but a computer needs specific instructions per layout. This tool answers three
questions for each file:

1. **Which supplier's format is this?** → *detection*
2. **What materials and weights are inside?** → *extraction*
3. **What is the standard name for each material?** → *normalization*

Then it writes the answer to a spreadsheet.

---

## Architecture

```
                          you type a command
                                  │
                                  ▼
        ┌─────────────────────────────────────────────┐
        │                __main__.py                   │   the "front door"
        │   python -m material_extractor Data          │   (command line)
        └───────────────────────┬─────────────────────┘
                                 ▼
        ┌─────────────────────────────────────────────┐
        │                 pipeline.py                  │   the "manager"
        └───────────────────────┬─────────────────────┘
          ┌──────────────────────┼───────────────────────┐
          ▼                      ▼                        ▼
  ┌──────────────┐      ┌─────────────────┐      ┌────────────────┐
  │ templates/   │      │  normalizer.py  │      │  writes CSV    │
  │ template1.py │      │      reads      │      │  to output/    │
  │   ...        │◄─────│  materials.yaml │      └────────────────┘
  │ template13.py│      └─────────────────┘
  └──────────────┘
   13 "readers",
   one per supplier
```

Think of it as a mailroom: `__main__.py` is the front desk, `pipeline.py` is
the manager, each `templateN.py` is a clerk who only knows one supplier's
paperwork, and `normalizer.py` + `materials.yaml` is a translator with a
dictionary.

---

## How one file is processed

```
1. pipeline.py asks each template in turn:  template.detect(file)?
2. first template that says "yes" wins  →  template.extract(file)
3. each extracted row  →  normalizer  →  official name + category
4. rows written to  output/individual/<file>.csv  and  output/all_materials.csv
```

The only thing that differs per supplier is *which* template handles steps 1–2.

---

## Run

```bash
python -m material_extractor <file-or-dir> [--output output]

# examples
python -m material_extractor templates/test_files      # the bundled samples
python -m material_extractor ../Data --output output   # the real datasheets
```

Output:
- `output/individual/<name>.csv` — one report per input file
- `output/all_materials.csv` — everything combined

---

## Add a new supplier format

Create `templates/template14.py` with two functions (this is the whole contract):

```python
def detect(path: str) -> bool:
    # Return True if this file is your supplier's format.
    # Usually: open the file and look for a keyword.
    ...

def extract(path: str) -> list[dict]:
    # Return rows: {"material": ..., "substance": ..., "weight_mg": ...}
    # weight_mg must be in milligrams (convert grams/etc. here).
    ...
```

That's it — the pipeline discovers it automatically. **No registration, no YAML
template, no wiring.** The `templates/` folder *is* the registry.

---

## Add / teach a new material

Add one entry to `materials.yaml`:

```yaml
Copper (Cu):          # the official name
  category: Metal      # its category
  aliases:             # messy versions that all mean "Copper (Cu)"
  - copper
  - cu
```

Any raw name matching an alias (case-insensitive) is normalized to the canonical
name and category. Unknown names pass through unchanged with category `Unknown`.

---

## Files

| File | Role |
|------|------|
| `__main__.py`    | Command-line front door. Parses your command, prints the summary. |
| `pipeline.py`    | The manager: discovers templates, runs detect → extract → normalize → CSV. |
| `templates/*.py` | One clerk per supplier. Each exposes `detect()` + `extract()`. |
| `normalizer.py`  | Translator: turns messy names into official names + categories. |
| `materials.yaml` | The dictionary of material names, aliases, and categories. |
| `__init__.py`    | Marks the package and re-exports `Pipeline`, `Normalizer`, `run`. |
| `pyproject.toml` | Project ID + dependency list. |
| `tests/`         | Safety net: runs every sample file through the pipeline. |

---

## Notes

- `template4.py` reads *scanned* PDFs (images) using OCR and needs optional
  extras: `pip install -e ".[ocr]"`. If those are missing, the pipeline simply
  skips that one template instead of crashing.
- Weights are converted to **milligrams inside each template**, so everything
  downstream is in the same unit.

---

## Test

```bash
pytest
```

Runs every bundled sample file through the pipeline and checks that a template
matched, materials came out, and weights are valid.
