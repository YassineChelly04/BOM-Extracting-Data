"""Functional tests: extract materials from real PDF/Excel files."""
import pytest
from pathlib import Path
from material_extractor.templates.registry import TemplateManager
from material_extractor.extractors import create_extractor
from material_extractor.normalization import get_normalizer
from material_extractor.models import SourceType

TEST_FILES_DIR = Path("templates/test_files")
TEMPLATES_DIR = Path("templates")

# Files known to match a template (mapped by analysis):
# template1.pdf  — generic MLCC, no match
# template4.pdf  — scanned image, no match
# template6.pdf  — AVX CID-font, no match


def _detect_file_type(path: Path) -> SourceType:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return SourceType.PDF
    if suffix in (".xlsx", ".xls"):
        return SourceType.EXCEL
    return SourceType.UNKNOWN


MATCHED_FILES = {
    "template2.pdf":  "wurth_md",
    "template3.pdf":  "molex_compliance",
    "template5.xlsx": "nexperia_excel",
    "template7.xlsx": "ti_excel",
    "template8.pdf":  "liteon_composition",
    "template9.pdf":  "vishay_mlcc",
    "template10.pdf": "harwin_declaration",
    "template11.pdf": "eds_composition",
    "template12.pdf": "stackpole_sei",
    "template13.pdf": "yageo_mlcc",
}


@pytest.mark.functional
def test_all_matched_files_extract_successfully():
    """Run the full pipeline on every test file that has a matching template."""
    tm = TemplateManager(templates_dir=TEMPLATES_DIR)
    normalizer = get_normalizer()
    normalizer.load()

    assert len(tm.get_enabled_templates()) > 0, "No templates loaded"

    tested = 0

    for fname, expected_tid in sorted(MATCHED_FILES.items()):
        file_path = TEST_FILES_DIR / fname
        if not file_path.exists():
            pytest.skip(f"{fname} not found")

        file_type = _detect_file_type(file_path)

        # --- Step 1: detect ---
        template = tm.detect_template(file_path, file_type)
        assert template is not None, f"{fname}: no template detected (expected {expected_tid})"
        assert template.metadata.template_id == expected_tid, \
            f"{fname}: expected template {expected_tid}, got {template.metadata.template_id}"

        # --- Step 2: extract ---
        extractor = create_extractor(template)
        result = extractor.extract(file_path)
        assert result.success, f"{fname}: extraction failed: {result.errors}"
        assert len(result.records) > 0, f"{fname}: no records extracted"

        # --- Step 3: normalize ---
        for record in result.records:
            normalized = normalizer.normalize_record(record)
            assert normalized.material.strip(), f"{fname}: empty material name"
            assert normalized.weight_mg > 0, f"{fname}: zero or negative weight for {normalized.material}"
            assert normalized.confidence > 0, f"{fname}: zero confidence for {normalized.material}"

        tested += 1

    assert tested == len(MATCHED_FILES), f"Only tested {tested}/{len(MATCHED_FILES)} files"
