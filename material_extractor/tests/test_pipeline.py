"""Tests for the material extraction pipeline.

Four things worth guaranteeing:
  1. auto-discovery finds templates and each honors the detect/extract contract
  2. end-to-end: every sample file is handled by exactly one template
  3. the normalizer maps aliases -> canonical names and passes unknowns through
  4. weights are coerced to a uniform float
"""
from pathlib import Path

import pytest

from material_extractor.normalizer import Normalizer
from material_extractor.pipeline import Pipeline, _to_mg, discover_templates

SAMPLE_FILES = sorted((Path(__file__).parent.parent / "templates" / "test_files").glob("template*.*"))


@pytest.fixture(scope="module")
def pipeline():
    """Build the pipeline once (discovery/imports are expensive)."""
    return Pipeline()


# --- 1. auto-discovery contract ---

def test_templates_are_discovered_and_follow_contract():
    templates = discover_templates()
    assert templates, "no templates discovered"
    for template in templates:
        assert callable(getattr(template, "detect", None)), f"{template.__name__} missing detect()"
        assert callable(getattr(template, "extract", None)), f"{template.__name__} missing extract()"


# --- 2. end-to-end per sample file ---

@pytest.mark.parametrize("sample", SAMPLE_FILES, ids=lambda p: p.name)
def test_sample_file_extracts(pipeline, sample):
    result = pipeline.process_file(sample)
    assert result.error is None, result.error
    assert result.matched, f"no template matched {sample.name}"
    assert result.records, f"{result.template} extracted 0 records from {sample.name}"
    for record in result.records:
        assert record["material"]
        assert record["category"]  # always set — "Unknown" at worst
        assert isinstance(record["weight_mg"], float)
        assert record["weight_mg"] >= 0


# --- 3. normalizer ---

def test_normalizer_resolves_aliases_case_insensitively():
    norm = Normalizer()
    assert norm.normalize_name("copper") == ("Copper (Cu)", "Metal")
    assert norm.normalize_name("CU") == ("Copper (Cu)", "Metal")


def test_normalizer_passes_unknown_through():
    norm = Normalizer()
    assert norm.normalize_name("xyz-not-a-material") == ("xyz-not-a-material", "Unknown")


def test_normalize_record_keeps_raw_name_and_adds_category():
    record = Normalizer().normalize_record({"material": "copper", "weight_mg": 5})
    assert record["material"] == "Copper (Cu)"
    assert record["category"] == "Metal"
    assert record["raw_material"] == "copper"


# --- 4. weight coercion ---

@pytest.mark.parametrize("value,expected", [
    ("0.89", 0.89),
    (5, 5.0),
    (2.5, 2.5),
    ("  1.20 ", 1.2),
    ("not-a-number", 0.0),
    (None, 0.0),
])
def test_to_mg_coerces_to_float(value, expected):
    result = _to_mg(value)
    assert isinstance(result, float)
    assert result == expected
