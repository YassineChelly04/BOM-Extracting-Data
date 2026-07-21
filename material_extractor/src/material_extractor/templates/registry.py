"""Template registry and management."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml
from loguru import logger

from material_extractor.models import (
    TemplateDefinition, TemplateRegistry, TemplateMetadata, SourceType,
    DetectionMethod
)
from material_extractor.core.detector import create_detector
from material_extractor.extractors import create_extractor


class TemplateManager:
    """Manage template registry and operations."""

    def __init__(self, templates_dir: Path | None = None):
        self.registry = TemplateRegistry()
        self._detectors: dict[str, Any] = {}
        self._extractors: dict[str, Any] = {}
        if templates_dir:
            self.load_from_yaml(templates_dir)
    
    def load_from_yaml(self, yaml_path: Path) -> int:
        """Load templates from YAML directory."""
        count = 0
        if not yaml_path.exists():
            return 0

        for yaml_file in sorted(yaml_path.rglob("*.yaml")):
            try:
                template = self._load_template_yaml(yaml_file)
                self.registry.register(template)
                count += 1
            except Exception as e:
                logger.error(f"Failed to load {yaml_file}: {e}")
        return count
    
    def _load_template_yaml(self, path: Path) -> TemplateDefinition:
        """Load single template from YAML."""
        with open(path) as f:
            data = yaml.safe_load(f)
        
        metadata = TemplateMetadata(**data["metadata"])
        return TemplateDefinition(
            metadata=metadata,
            extraction=data.get("extraction", {}),
            normalization=data.get("normalization", {}),
            output=data.get("output", {})
        )
    
    def register_template(self, template: TemplateDefinition) -> None:
        """Register a template."""
        self.registry.register(template)
        self._detectors.pop(template.metadata.template_id, None)
        self._extractors.pop(template.metadata.template_id, None)
    
    def unregister_template(self, template_id: str) -> bool:
        """Unregister a template."""
        result = self.registry.unregister(template_id)
        self._detectors.pop(template_id, None)
        self._extractors.pop(template_id, None)
        return result
    
    def get_template(self, template_id: str) -> TemplateDefinition | None:
        return self.registry.get(template_id)
    
    def get_enabled_templates(self) -> list[TemplateDefinition]:
        return self.registry.get_enabled_templates()
    
    def get_detector(self, template_id: str):
        """Get or create detector for template."""
        if template_id not in self._detectors:
            template = self.registry.get(template_id)
            if template:
                self._detectors[template_id] = create_detector(template)
        return self._detectors.get(template_id)
    
    def get_extractor(self, template_id: str):
        """Get or create extractor for template."""
        if template_id not in self._extractors:
            template = self.registry.get(template_id)
            if template:
                self._extractors[template_id] = create_extractor(template)
        return self._extractors.get(template_id)
    
    def detect_template(self, file_path: Path, file_type: SourceType) -> TemplateDefinition | None:
        """Find matching template for file."""
        for template in self.get_enabled_templates():
            detector = self.get_detector(template.metadata.template_id)
            if detector and detector.detect(file_path, file_type):
                return template
        return None
    
    def export_template_yaml(self, template_id: str, output_path: Path) -> bool:
        """Export template to YAML."""
        template = self.registry.get(template_id)
        if not template:
            return False
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            yaml.dump(template.model_dump(), f, default_flow_style=False, sort_keys=False)
        return True

