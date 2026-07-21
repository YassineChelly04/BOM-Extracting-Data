"""Integration tests for extraction pipeline."""
import pytest
from pathlib import Path
from material_extractor.core.pipeline import ExtractionPipeline
from material_extractor.templates.registry import TemplateManager
from material_extractor.normalization import get_normalizer


class TestPipeline:
    """Integration tests for the extraction pipeline."""
    
    @pytest.fixture
    def pipeline(self):
        """Create a test pipeline."""
        tm = TemplateManager(templates_dir=Path("templates"))
        normalizer = get_normalizer()
        return ExtractionPipeline(template_manager=tm, normalizer=normalizer)
    
    def test_template_manager_has_templates(self, pipeline):
        """Test that templates are loaded from YAML."""
        templates = pipeline.template_manager.get_enabled_templates()
        assert len(templates) > 0
        assert any(t.metadata.template_id == "molex_bom" for t in templates)