"""Core data models for material extraction."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class MaterialCategory(str, Enum):
    """Standardized material categories."""
    METAL = "Metal"
    METALLOID = "Metalloid"
    METAL_OXIDE = "Metal Oxide"
    CERAMIC = "Ceramic"
    COMPOUND_SEMICONDUCTOR = "Compound Semiconductor"
    SALT = "Salt"
    POLYMER = "Polymer"
    POLYMER_ADDITIVE = "Polymer Additive"
    COMPOSITE = "Composite"
    GLASS = "Glass"
    FILLER = "Filler"
    HYDROXIDE = "Hydroxide"
    HALOGEN = "Halogen"
    NON_METAL = "Non-Metal"
    SOLVENT = "Solvent"
    ADDITIVE = "Additive"
    OTHER = "Other"
    PASTE = "Paste"
    PLATING = "Plating"
    PIGMENT = "Pigment"
    UNKNOWN = "Unknown"


class SourceType(str, Enum):
    """Input file types."""
    PDF = "pdf"
    EXCEL = "excel"
    XLSX = "xlsx"
    XLS = "xls"
    CSV = "csv"
    UNKNOWN = "unknown"


class NormalizationMethod(str, Enum):
    """Material name normalization methods."""
    EXACT_MATCH = "exact_match"
    FUZZY_MATCH = "fuzzy_match"
    ALIAS_MAP = "alias_map"
    CAS_NUMBER = "cas_number"
    CHEMICAL_FORMULA = "chemical_formula"
    REGEX_MATCH = "regex_match"
    CUSTOM = "custom"


class NormalizationRule(BaseModel):
    """Normalization rule for material names."""
    pattern: str
    replacement: str
    category: MaterialCategory | None = None
    priority: int = Field(default=0, ge=0)
    case_sensitive: bool = False
    regex: bool = False
    description: str = ""


class NormalizationConfig(BaseModel):
    """Normalization configuration."""
    rules: list[NormalizationRule] = Field(default_factory=list)
    categories: dict[str, MaterialCategory] = Field(default_factory=dict)
    default_category: MaterialCategory = MaterialCategory.UNKNOWN
    fuzzy_threshold: float = Field(default=0.85, ge=0.0, le=1.0)


class NormalizationResult(BaseModel):
    """Result of normalization operation."""
    original: str
    normalized: str
    category: MaterialCategory
    method: NormalizationMethod
    confidence: float
    matched_alias: str = ""
    cas_number: str = ""
    chemical_formula: str = ""
    alternatives: list[str] = Field(default_factory=list)


class DetectionMethod(str, Enum):
    """Template detection methods."""
    TEXT_PATTERN = "text_pattern"
    HEADER_MATCH = "header_match"
    LAYOUT_ANALYSIS = "layout_analysis"
    KEYWORD_MATCH = "keyword_match"
    COMPOSITE = "composite"


class TemplateMetadata(BaseModel):
    """Template metadata and detection configuration."""
    template_id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_type: SourceType = SourceType.PDF
    page_indices: list[int] | None = None
    detection_method: DetectionMethod = DetectionMethod.TEXT_PATTERN
    detection_keywords: list[str] = Field(default_factory=list)
    detection_patterns: list[str] = Field(default_factory=list)
    header_keywords: list[str] = Field(default_factory=list)
    validation_rules: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=0, ge=0)
    enabled: bool = True


class TemplateDefinition(BaseModel):
    """Complete template definition."""
    metadata: TemplateMetadata
    extraction: dict[str, Any] = Field(default_factory=dict)
    normalization: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)


class MaterialRecord(BaseModel):
    """Normalized material record."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    material: str = Field(..., min_length=1)
    substance: str = Field(default="")
    weight_mg: Decimal = Field(default=Decimal("0"), ge=0)
    category: MaterialCategory = Field(default=MaterialCategory.UNKNOWN)
    case_size: str = Field(default="")
    part_number: str = Field(default="")
    manufacturer: str = Field(default="")
    template_id: str = Field(default="")
    source_file: str = Field(default="")
    page_number: int = Field(default=0, ge=0)
    row_index: int = Field(default=0, ge=0)
    raw_material: str = Field(default="")
    raw_substance: str = Field(default="")
    raw_weight: str = Field(default="")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    normalization_method: NormalizationMethod | None = None
    matched_alias: str = Field(default="")
    
    @field_validator("weight_mg", mode="before")
    @classmethod
    def parse_weight(cls, v: Any) -> Decimal:
        if isinstance(v, (int, float, Decimal)):
            return Decimal(str(v))
        if isinstance(v, str):
            cleaned = v.lower().strip()
            if not cleaned:
                return Decimal("0")
            try:
                if cleaned.endswith("kg"):
                    return Decimal(cleaned[:-2].strip()) * 1000000
                if cleaned.endswith("mg"):
                    return Decimal(cleaned[:-2].strip())
                if cleaned.endswith("ug"):
                    return Decimal(cleaned[:-2].strip()) / 1000
                if cleaned.endswith("g"):
                    return Decimal(cleaned[:-1].strip()) * 1000
                return Decimal(cleaned)
            except Exception:
                return Decimal("0")
        return Decimal("0")
    
    @model_validator(mode="after")
    def normalize_fields(self) -> MaterialRecord:
        self.material = self.material.strip()
        self.substance = self.substance.strip()
        self.case_size = self.case_size.strip()
        self.part_number = self.part_number.strip()
        self.manufacturer = self.manufacturer.strip()
        self.raw_material = self.raw_material.strip()
        self.raw_substance = self.raw_substance.strip()
        self.raw_weight = self.raw_weight.strip()
        return self
    
    def to_dict(self, include_raw: bool = False) -> dict[str, Any]:
        """Convert to dictionary for output serialization."""
        d: dict[str, Any] = {
            "material": self.material,
            "substance": self.substance,
            "weight_mg": float(self.weight_mg),
            "category": self.category.value,
            "case_size": self.case_size,
            "part_number": self.part_number,
            "manufacturer": self.manufacturer,
            "template_id": self.template_id,
            "source_file": self.source_file,
            "page_number": self.page_number,
            "row_index": self.row_index,
            "confidence": self.confidence,
        }
        if include_raw:
            d.update({
                "raw_material": self.raw_material,
                "raw_substance": self.raw_substance,
                "raw_weight": self.raw_weight,
            })
        return d


class ExtractionResult(BaseModel):
    """Result of extraction operation."""
    success: bool = False
    records: list[MaterialRecord] = Field(default_factory=list)
    template_id: str = ""
    source_file: str = ""
    file_type: SourceType = SourceType.UNKNOWN
    pages_processed: int = 0
    tables_found: int = 0
    tables_processed: int = 0
    extraction_time_ms: float = 0.0
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    @property
    def record_count(self) -> int:
        return len(self.records)
    
    @property
    def total_weight_mg(self) -> Decimal:
        return sum(r.weight_mg for r in self.records)


class TemplateRegistry(BaseModel):
    """Registry of all templates."""
    templates: dict[str, TemplateDefinition] = Field(default_factory=dict)
    version: str = "1.0.0"
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    def get(self, template_id: str) -> TemplateDefinition | None:
        return self.templates.get(template_id)
    
    def get_enabled(self) -> list[TemplateDefinition]:
        return sorted(
            [t for t in self.templates.values() if t.metadata.enabled],
            key=lambda t: (-t.metadata.priority, t.metadata.template_id)
        )
    
    def register(self, template: TemplateDefinition) -> None:
        self.templates[template.metadata.template_id] = template
        self.updated_at = datetime.now(timezone.utc)
    
    def unregister(self, template_id: str) -> bool:
        if template_id in self.templates:
            del self.templates[template_id]
            self.updated_at = datetime.now(timezone.utc)
            return True
        return False
    
    def get_enabled_templates(self) -> list[TemplateDefinition]:
        """Alias for get_enabled()."""
        return self.get_enabled()


class ProcessingStats(BaseModel):
    """Processing statistics."""
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0
    total_records: int = 0
    total_templates_matched: int = 0
    unique_materials: int = 0
    total_weight_mg: Decimal = Field(default=Decimal("0"))
    processing_time_ms: float = 0.0
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    template_stats: dict[str, dict[str, Any]] = Field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "failed_files": self.failed_files,
            "skipped_files": self.skipped_files,
            "total_records": self.total_records,
            "total_templates_matched": self.total_templates_matched,
            "unique_materials": self.unique_materials,
            "total_weight_mg": float(self.total_weight_mg),
            "processing_time_ms": self.processing_time_ms,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }


class AggregatedMaterial(BaseModel):
    """Aggregated material across multiple templates/files."""
    material: str
    category: MaterialCategory
    total_weight_mg: Decimal = Field(default=Decimal("0"))
    templates: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    record_count: int = 0
    min_weight_mg: Decimal | None = None
    max_weight_mg: Decimal | None = None
    avg_weight_mg: Decimal | None = None
    
    @property
    def template_count(self) -> int:
        return len(set(self.templates))
    
    @property
    def file_count(self) -> int:
        return len(set(self.files))