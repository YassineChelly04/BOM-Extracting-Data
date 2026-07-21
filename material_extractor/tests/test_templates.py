"""End-to-end test: every sample file in templates/test_files should be
detected by exactly one template and yield material records."""
from pathlib import Path

import pytest

from material_extractor.pipeline import Pipeline

TEST_FILES = sorted((Path(__file__).parent.parent / "templates" / "test_files").glob("template*.*"))


@pytest.mark.parametrize("sample", TEST_FILES, ids=lambda p: p.name)
def test_sample_file_extracts(sample):
    result = Pipeline().process_file(sample)
    assert result.error is None, result.error
    assert result.matched, f"no template matched {sample.name}"
    assert result.records, f"{result.template} extracted 0 records from {sample.name}"
    for record in result.records:
        assert record["material"]
        assert float(record["weight_mg"]) >= 0


def test_normalizer_resolves_common_metals():
    from material_extractor.normalizer import Normalizer

    norm = Normalizer()
    assert norm.normalize_name("copper") == ("Copper (Cu)", "Metal")
    assert norm.normalize_name("ni")[1] == "Metal"
    assert norm.normalize_name("totally-unknown-thing") == ("totally-unknown-thing", "Unknown")
