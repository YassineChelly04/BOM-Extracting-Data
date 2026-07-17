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
        tm = TemplateManager()
        tm.load_registry()
        
        if not tm.registry.templates:
            from material_extractor.templates.registry import initialize_default_templates
            initialize_default_templates(tm)
        
        normalizer = get_normalizer()
        
        return ExtractionPipeline(template_manager=tm, normalizer=normalizer)
    
    def test_pipeline_initialization(self, pipeline):
        """Test pipeline initializes correctly."""
        assert pipeline.template_manager is not None
        assert pipeline.normalizer is not None
    
    def test_template_manager_has_templates(self, pipeline):
        """Test that templates are loaded."""
        templates = pipeline.template_manager.get_enabled_templates()
        assert len(templates) > 0
        assert any(t.metadata.template_id == "molex_bom" for t in templates)


class TestNormalizer:
    """Tests for the normalizer."""
    
    def test_normalizer_loads_data(self):
        """Test normalizer loads YAML data."""
        normalizer = get_normalizer()
        normalizer.load()
        
        stats = normalizer.stats()
        assert stats["materials"] > 0
        assert stats["total_aliases"] > 0
    
    def test_normalize_common_materials(self):
        """Test normalization of common materials."""
        normalizer = get_normalizer()
        normalizer.load()
        
        # Test copper
        result = normalizer.normalize("copper")
        assert result.normalized == "Copper (Cu)"
        assert result.category.value == "Metal"
        assert result.confidence > 0.9
        
        # Test nickel
        result = normalizer.normalize("nickel")
        assert result.normalized == "Nickel (Ni)"
        
        # Test gold
        result = normalizer.normalize("gold")
        assert result.normalized == "Gold (Au)"
        
        # Test epoxy
        result = normalizer.normalize("epoxy")
        assert result.normalized == "Epoxy Resin"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])