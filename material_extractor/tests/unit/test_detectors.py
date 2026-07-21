"""Unit tests for detectors."""
import pytest
from pathlib import Path
from material_extractor.core.detector import (
    TextPatternDetector, HeaderMatchDetector, create_detector
)
from material_extractor.models import (
    TemplateDefinition, TemplateMetadata, SourceType, DetectionMethod
)


class TestTextPatternDetector:
    """Tests for TextPatternDetector."""
    
    def test_create_detector(self):
        template = TemplateDefinition(
            metadata=TemplateMetadata(
                template_id="test",
                name="Test",
                source_type=SourceType.PDF,
                detection_method=DetectionMethod.TEXT_PATTERN,
                detection_keywords=["test keyword"],
                detection_patterns=[r"test.*pattern"]
            ),
            extraction={}
        )
        
        detector = create_detector(template)
        assert isinstance(detector, TextPatternDetector)
    
    def test_keyword_detection(self):
        template = TemplateDefinition(
            metadata=TemplateMetadata(
                template_id="test",
                name="Test",
                source_type=SourceType.PDF,
                detection_method=DetectionMethod.TEXT_PATTERN,
                detection_keywords=["material", "declaration"]
            ),
            extraction={}
        )
        
        detector = TextPatternDetector(template)
        
        # Should match
        assert detector._check_keywords("This is a material declaration", ["material", "declaration"], True)
        
        # Should not match - missing one keyword
        assert not detector._check_keywords("This is a material", ["material", "declaration"], True)
        
        # Should match with any
        assert detector._check_keywords("This is a material", ["material", "declaration"], False)


class TestHeaderMatchDetector:
    """Tests for HeaderMatchDetector."""
    
    def test_create_detector(self):
        template = TemplateDefinition(
            metadata=TemplateMetadata(
                template_id="test",
                name="Test",
                source_type=SourceType.PDF,
                detection_method=DetectionMethod.HEADER_MATCH,
                header_keywords=["material", "weight"]
            ),
            extraction={}
        )
        
        detector = create_detector(template)
        assert isinstance(detector, HeaderMatchDetector)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])