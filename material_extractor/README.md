# Material Extractor

Production-ready material declaration extraction and normalization system for electronics BOM/MD documents.

## Features

- **Template-based extraction** - Declarative YAML templates for different manufacturer formats
- **Auto-detection** - Automatic template matching via keywords, patterns, and table structure
- **Scalable normalization** - External YAML dictionaries for material/substance names with fuzzy matching
- **Multiple formats** - PDF (pdfplumber) and Excel (pandas/openpyxl) support
- **Parallel processing** - Batch process directories with configurable workers
- **Aggregation** - Automatic cross-template material aggregation
- **CLI & API** - Both command-line and programmatic interfaces
- **Extensible** - Easy to add new templates and normalization rules

## Quick Start

```bash
# Install
pip install -e .

# Initialize project
material-extractor init

# Extract from single file
material-extractor extract input.pdf -o output.csv

# Extract from directory
material-extractor run input_dir output_dir --parallel

# Normalize materials
material-extractor normalize output.csv

# List templates
material-extractor templates
```

## Project Structure

```
material_extractor/
├── src/material_extractor/
│   ├── cli/                 # Command-line interface
│   │   ├── main.py          # Main entry point
│   │   └── commands/        # Subcommands
│   ├── core/                # Core pipeline
│   │   ├── pipeline.py      # Extraction pipeline
│   │   ├── detector.py      # Template detection
│   │   └── extractor.py     # Base extractors
│   ├── extractors/          # Template-specific extractors
│   ├── models/              # Pydantic data models
│   ├── normalization/       # Material normalization
│   │   ├── normalizer.py    # Scalable normalizer
│   │   └── data/            # YAML dictionaries
│   ├── templates/           # Template registry
│   │   ├── registry.py      # Template management
│   │   └── defaults.py      # Built-in templates
│   └── config.py            # Configuration
├── templates/               # User templates (YAML)
│   ├── pdf/
│   └── excel/
├── data/                    # Normalization data
│   └── normalization/
│       ├── materials.yaml
│       └── substances.yaml
├── tests/                   # Test suite
└── output/                  # Extraction outputs
```

## Built-in Templates

| Template ID | Manufacturer | Format | Description |
|-------------|--------------|--------|-------------|
| `molex_bom` | Molex/TE | PDF | Annex 3 table with case sizes |
| `wurth_md` | Würth | PDF | Semi-Component breakdown |
| `molex_compliance` | Molex | PDF | Product Compliance Declaration |
| `vishay_mlcc` | Vishay | PDF | MLCC material declaration |
| `samsung_mlcc` | Samsung | Excel | MLCC Excel format |
| `yageo_mlcc` | Yageo | Excel | MLCC Excel format |

## Adding New Templates

Create a YAML file in `templates/pdf/` or `templates/excel/`:

```yaml
metadata:
  template_id: "my_vendor_md"
  name: "My Vendor Material Declaration"
  version: "1.0.0"
  source_type: "pdf"
  page_indices: [0]
  detection_method: "text_pattern"
  detection_keywords:
    - "Material Declaration"
    - "MyVendor"
  header_keywords:
    - "Material"
    - "Weight"
  priority: 10
  enabled: true

extraction:
  extractor_type: "pdf_table"
  extractor_class: "GenericPDFTableExtractor"
  target_size: "0603"

normalization: {}

output:
  fields: ["material", "substance", "weight_mg"]
  include_raw: true
```

Then reload: `material-extractor init` or restart the pipeline.

## Normalization

Materials are normalized using external YAML files in `data/normalization/`:

```yaml
# materials.yaml
"Copper (Cu)":
  category: "Metal"
  aliases:
    - "copper"
    - "cu"
    - "copper (cu)"

# substances.yaml  
"Copper (Cu)":
  aliases:
    - "cu"
    - "copper"
  cas_number: "7440-50-8"
```

The normalizer uses:
1. Exact alias match (highest confidence)
2. Fuzzy matching (configurable threshold)
3. Category mapping

Add new materials via CLI:
```bash
material-extractor normalize add-material "New Material" Metal --aliases "alias1,alias2"
```

## Configuration

Create `.env` or `config.yaml`:

```yaml
data_dir: "data"
templates_dir: "templates"
output_dir: "output"
max_workers: 4
fuzzy_match_threshold: 0.85
default_category: "Unknown"
```

## Output Formats

- **CSV** - Standard tabular output
- **JSON** - Structured with metadata
- **Parquet** - Columnar for analytics
- **Aggregated** - Cross-file material summary

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=material_extractor

# Specific test types
pytest -m unit
pytest -m integration
```

## Architecture

```
Input File
    │
    ▼
Template Detection (keywords/patterns/headers)
    │
    ▼
Extractor (PDF/Excel specific)
    │
    ▼
Raw Material Records
    │
    ▼
Normalization (alias/fuzzy/CAS)
    │
    ▼
Normalized Records + Categories
    │
    ▼
Output (CSV/JSON) + Aggregation
```

## License

MIT