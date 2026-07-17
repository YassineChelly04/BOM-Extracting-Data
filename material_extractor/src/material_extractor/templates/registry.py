"""Template registry and management."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import yaml

from material_extractor.models import (
    TemplateDefinition, TemplateRegistry, TemplateMetadata, SourceType,
    DetectionMethod
)
from material_extractor.core.detector import create_detector
from material_extractor.extractors import create_extractor


class TemplateManager:
    """Manage template registry and operations."""
    
    def __init__(self, registry_path: Path | None = None):
        self.registry = TemplateRegistry()
        self.registry_path = registry_path or Path("data/templates/registry.json")
        self._detectors: dict[str, Any] = {}
        self._extractors: dict[str, Any] = {}
    
    def load_registry(self) -> None:
        """Load registry from file."""
        if self.registry_path.exists():
            with open(self.registry_path) as f:
                data = json.load(f)
            self.registry = TemplateRegistry(**data)
    
    def save_registry(self) -> None:
        """Save registry to file."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, "w") as f:
            json.dump(self.registry.model_dump(mode="json"), f, indent=2)
    
    def load_from_yaml(self, yaml_path: Path) -> int:
        """Load templates from YAML directory."""
        count = 0
        for yaml_file in yaml_path.glob("*.yaml"):
            try:
                template = self._load_template_yaml(yaml_file)
                self.registry.register(template)
                count += 1
            except Exception as e:
                print(f"Failed to load {yaml_file}: {e}")
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


def create_template_yaml_template() -> str:
    """Generate template YAML template."""
    return """metadata:
  template_id: "unique_template_id"
  name: "Template Name"
  version: "1.0.0"
  description: "Description of what this template extracts"
  author: "Author Name"
  source_type: "pdf"  # pdf, excel, xlsx
  page_indices: [0]   # Pages to check (0-indexed)
  detection_method: "text_pattern"  # text_pattern, header_match, layout_analysis
  detection_keywords:
    - "keyword1"
    - "keyword2"
  detection_patterns:
    - "regex pattern"
  header_keywords:
    - "Material"
    - "Weight"
  validation_rules:
    min_rows: 2
    min_cols: 3
  priority: 0
  enabled: true

extraction:
  extractor_type: "pdf_table"  # pdf_table, pdf_text, excel, multi_sheet_excel
  target_size: "0402"  # For templates with multiple case sizes
  sheet_name: ""  # For Excel
  sheet_keywords: []  # Alternative to sheet_name
  # Custom extraction config
  custom_config: {}

normalization:
  # Override default normalization rules
  custom_rules: []
  # Force specific category for materials from this template
  force_category: ""

output:
  fields: ["material", "substance", "weight_mg", "case_size"]
  include_raw: false
  format: "csv"
"""


# --- Pre-defined template configurations ---

DEFAULT_TEMPLATES = {
    "molex_bom": {
        "metadata": {
            "template_id": "molex_bom",
            "name": "Molex/TE Connectivity BOM",
            "version": "1.0.0",
            "description": "Molex Annex 3 table format for MLCC materials",
            "author": "Material Extractor Team",
            "source_type": "pdf",
            "page_indices": [1],
            "detection_method": "text_pattern",
            "detection_keywords": ["Homogeneous Level Weight", "Total Weight", "0402"],
            "header_keywords": ["Level", "Material", "Substance", "CAS"],
            "validation_rules": {"min_rows": 3, "min_cols": 5},
            "priority": 10,
            "enabled": True
        },
        "extraction": {
            "extractor_type": "pdf_table",
            "target_size": "0402",
            "skip_rows": ["Homogeneous Level Weight", "Total Weight"],
            "case_sizes_row": 1,
            "header_row": 2
        },
        "normalization": {},
        "output": {
            "fields": ["material", "substance", "weight_mg"],
            "include_raw": True
        }
    },
    
    "wurth_md": {
        "metadata": {
            "template_id": "wurth_md",
            "name": "Würth Elektronik Material Declaration",
            "version": "1.0.0",
            "description": "Würth WL-SMCW layout with Semi-Component breakdown",
            "author": "Material Extractor Team",
            "source_type": "pdf",
            "page_indices": [0],
            "detection_method": "text_pattern",
            "detection_keywords": ["Semi-Component", "Average mass [%]", "Würth Elektronik"],
            "header_keywords": ["Semi-Component", "Substance", "Average mass"],
            "validation_rules": {"min_rows": 2, "min_cols": 5},
            "priority": 10,
            "enabled": True
        },
        "extraction": {
            "extractor_type": "pdf_table",
            "material_table_index": 1,
            "part_table_index": 2
        },
        "normalization": {},
        "output": {
            "fields": ["material", "weight_mg"],
            "include_raw": True
        }
    },
    
    "molex_compliance": {
        "metadata": {
            "template_id": "molex_compliance",
            "name": "Molex Product Compliance Declaration",
            "version": "1.0.0",
            "description": "Molex compliance declaration with substance rows",
            "author": "Material Extractor Team",
            "source_type": "pdf",
            "page_indices": [0, 1],
            "detection_method": "text_pattern",
            "detection_keywords": ["Product Compliance Declaration", "molex", "Product Composition"],
            "header_keywords": ["Name", "Type", "CAS", "Mass"],
            "validation_rules": {"min_rows": 2, "min_cols": 5},
            "priority": 10,
            "enabled": True
        },
        "extraction": {
            "extractor_type": "pdf_table",
            "pages": [0, 1]
        },
        "normalization": {},
        "output": {
            "fields": ["material", "substance", "weight_mg"],
            "include_raw": True
        }
    },
    
    "vishay_mlcc": {
        "metadata": {
            "template_id": "vishay_mlcc",
            "name": "Vishay MLCC Material Declaration",
            "version": "1.0.0",
            "description": "Vishay MLCC with material/substance/weight/unit columns",
            "author": "Material Extractor Team",
            "source_type": "pdf",
            "page_indices": [0],
            "detection_method": "header_match",
            "detection_keywords": ["Vishay", "Material Declaration"],
            "header_keywords": ["Material", "Substance", "Weight", "Unit"],
            "validation_rules": {"min_rows": 2, "min_cols": 4},
            "priority": 10,
            "enabled": True
        },
        "extraction": {
            "extractor_type": "pdf_table"
        },
        "normalization": {},
        "output": {
            "fields": ["material", "substance", "weight_mg"],
            "include_raw": True
        }
    },
    
    "samsung_mlcc": {
        "metadata": {
            "template_id": "samsung_mlcc",
            "name": "Samsung MLCC Excel Format",
            "version": "1.0.0",
            "description": "Samsung MLCC material declaration in Excel",
            "author": "Material Extractor Team",
            "source_type": "excel",
            "page_indices": [0],
            "detection_method": "keyword_match",
            "detection_keywords": ["Samsung", "MLCC", "Material"],
            "header_keywords": ["Material", "Substance", "Weight"],
            "validation_rules": {"min_rows": 2, "min_cols": 3},
            "priority": 10,
            "enabled": True
        },
        "extraction": {
            "extractor_type": "excel",
            "sheet_keywords": ["Material", "Declaration", "Composition"]
        },
        "normalization": {},
        "output": {
            "fields": ["material", "substance", "weight_mg"],
            "include_raw": True
        }
    },
    
    "yageo_mlcc": {
        "metadata": {
            "template_id": "yageo_mlcc",
            "name": "Yageo MLCC Excel Format",
            "version": "1.0.0",
            "description": "Yageo MLCC material declaration in Excel",
            "author": "Material Extractor Team",
            "source_type": "excel",
            "page_indices": [0],
            "detection_method": "keyword_match",
            "detection_keywords": ["Yageo", "MLCC", "Material"],
            "header_keywords": ["Material", "CAS", "Weight"],
            "validation_rules": {"min_rows": 2, "min_cols": 3},
            "priority": 10,
            "enabled": True
        },
        "extraction": {
            "extractor_type": "excel",
            "sheet_keywords": ["Material", "Declaration", "Composition"]
        },
        "normalization": {},
        "output": {
            "fields": ["material", "substance", "weight_mg"],
            "include_raw": True
        }
    }
}


def initialize_default_templates(manager: TemplateManager) -> None:
    """Initialize registry with default templates."""
    for template_id, data in DEFAULT_TEMPLATES.items():
        metadata = TemplateMetadata(**data["metadata"])
        template = TemplateDefinition(
            metadata=metadata,
            extraction=data["extraction"],
            normalization=data["normalization"],
            output=data["output"]
        )
        manager.register_template(template)