"""Unit tests for models."""
import pytest
from decimal import Decimal
from material_extractor.models import (
    MaterialRecord, MaterialCategory, SourceType, ExtractionResult,
    NormalizationRule, NormalizationConfig, TemplateRegistry, TemplateDefinition,
    TemplateMetadata, DetectionMethod
)


class TestMaterialRecord:
    """Tests for MaterialRecord model."""
    
    def test_create_record(self):
        record = MaterialRecord(
            material="Copper (Cu)",
            substance="Cu",
            weight_mg="1.5",
            category=MaterialCategory.METAL
        )
        
        assert record.material == "Copper (Cu)"
        assert record.substance == "Cu"
        assert record.weight_mg == Decimal("1.5")
        assert record.category == MaterialCategory.METAL
    
    def test_weight_parsing(self):
        """Test various weight formats."""
        assert MaterialRecord(material="Test", weight_mg="1.5").weight_mg == Decimal("1.5")
        assert MaterialRecord(material="Test", weight_mg=2.5).weight_mg == Decimal("2.5")
        assert MaterialRecord(material="Test", weight_mg="0").weight_mg == Decimal("0")
    
    def test_to_dict(self):
        record = MaterialRecord(
            material="Test",
            substance="Sub",
            weight_mg="1.0",
            category=MaterialCategory.METAL
        )
        d = record.to_dict()
        
        assert d["material"] == "Test"
        assert d["substance"] == "Sub"
        assert d["weight_mg"] == 1.0
        assert d["category"] == "Metal"


class TestNormalizationConfig:
    """Tests for normalization configuration."""
    
    def test_add_rule(self):
        config = NormalizationConfig()
        rule = NormalizationRule(
            pattern="copper",
            replacement="Copper (Cu)",
            category=MaterialCategory.METAL,
            priority=10
        )
        config.rules.append(rule)
        
        assert len(config.rules) == 1
        assert config.rules[0].pattern == "copper"
    
    def test_category_mapping(self):
        config = NormalizationConfig()
        config.categories["copper (cu)"] = MaterialCategory.METAL
        
        assert config.categories.get("copper (cu)") == MaterialCategory.METAL


class TestTemplateRegistry:
    """Tests for template registry."""
    
    def test_register_and_get(self):
        registry = TemplateRegistry()
        
        template = TemplateDefinition(
            metadata=TemplateMetadata(
                template_id="test_template",
                name="Test Template",
                source_type=SourceType.PDF,
                detection_method=DetectionMethod.TEXT_PATTERN,
                detection_keywords=["test"]
            ),
            extraction={}
        )
        
        registry.register(template)
        
        assert registry.get("test_template") == template
        assert len(registry.templates) == 1
    
    def test_get_enabled(self):
        registry = TemplateRegistry()
        
        t1 = TemplateDefinition(
            metadata=TemplateMetadata(
                template_id="enabled",
                name="Enabled",
                source_type=SourceType.PDF,
                enabled=True
            ),
            extraction={}
        )
        t2 = TemplateDefinition(
            metadata=TemplateMetadata(
                template_id="disabled",
                name="Disabled",
                source_type=SourceType.PDF,
                enabled=False
            ),
            extraction={}
        )
        
        registry.register(t1)
        registry.register(t2)
        
        enabled = registry.get_enabled()
        assert len(enabled) == 1
        assert enabled[0].metadata.template_id == "enabled"
    
    def test_priority_sorting(self):
        registry = TemplateRegistry()
        
        t1 = TemplateDefinition(
            metadata=TemplateMetadata(
                template_id="low_priority",
                name="Low",
                source_type=SourceType.PDF,
                priority=1
            ),
            extraction={}
        )
        t2 = TemplateDefinition(
            metadata=TemplateMetadata(
                template_id="high_priority",
                name="High",
                source_type=SourceType.PDF,
                priority=100
            ),
            extraction={}
        )
        
        registry.register(t1)
        registry.register(t2)
        
        enabled = registry.get_enabled()
        assert enabled[0].metadata.template_id == "high_priority"
        assert enabled[1].metadata.template_id == "low_priority"


class TestExtractionResult:
    """Tests for ExtractionResult."""
    
    def test_total_weight(self):
        result = ExtractionResult(
            success=True,
            records=[
                MaterialRecord(material="A", weight_mg="1.0"),
                MaterialRecord(material="B", weight_mg="2.5"),
            ]
        )
        
        assert result.total_weight_mg == Decimal("3.5")
        assert result.record_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])