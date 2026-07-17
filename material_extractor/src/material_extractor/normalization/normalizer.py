"""Scalable normalization system with YAML data files."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml
from rapidfuzz import fuzz, process

from material_extractor.models import (
    MaterialRecord, MaterialCategory, NormalizationMethod, NormalizationResult,
    NormalizationConfig, NormalizationRule
)
from material_extractor.config import get_settings


class ScalableNormalizer:
    """Production-ready normalizer with external data files."""
    
    def __init__(self, config: NormalizationConfig | None = None, data_dir: Path | None = None):
        self.settings = get_settings()
        self.data_dir = data_dir or self.settings.data_dir / "normalization"
        self.config = config or NormalizationConfig()
        self._material_map: dict[str, tuple[str, MaterialCategory]] = {}
        self._substance_map: dict[str, str] = {}
        self._alias_index: dict[str, str] = {}
        self._built = False
    
    def load(self) -> None:
        """Load normalization data from YAML files."""
        self._material_map.clear()
        self._substance_map.clear()
        self._alias_index.clear()
        
        # Load materials
        materials_file = self.data_dir / "materials.yaml"
        if materials_file.exists():
            with open(materials_file) as f:
                data = yaml.safe_load(f) or {}
            for normalized, info in data.items():
                category = MaterialCategory(info.get("category", "Unknown"))
                aliases = info.get("aliases", [])
                self._material_map[normalized.lower()] = (normalized, category)
                for alias in aliases:
                    self._alias_index[alias.lower()] = normalized
                self._alias_index[normalized.lower()] = normalized
        
        # Load substances
        substances_file = self.data_dir / "substances.yaml"
        if substances_file.exists():
            with open(substances_file) as f:
                data = yaml.safe_load(f) or {}
            for normalized, info in data.items():
                aliases = info.get("aliases", [])
                self._substance_map[normalized.lower()] = normalized
                for alias in aliases:
                    self._substance_map[alias.lower()] = normalized
                    self._alias_index[alias.lower()] = normalized
        
        # Load categories
        categories_file = self.data_dir / "categories.yaml"
        if categories_file.exists():
            with open(categories_file) as f:
                data = yaml.safe_load(f) or {}
            for cat_name, materials in data.items():
                try:
                    category = MaterialCategory(cat_name)
                    for mat in materials:
                        self._material_map[mat.lower()] = (mat, category)
                        self._alias_index[mat.lower()] = mat
                except ValueError:
                    pass
        
        self._built = True
    
    def normalize(self, material_name: str, substance: str = "") -> NormalizationResult:
        """Normalize material and substance names."""
        if not self._built:
            self.load()
        
        original = material_name.strip()
        if not original:
            return NormalizationResult(
                original=original,
                normalized="",
                category=MaterialCategory.UNKNOWN,
                method=NormalizationMethod.EXACT_MATCH,
                confidence=0.0
            )
        
        # Try exact alias match
        lower = original.lower()
        if lower in self._alias_index:
            normalized = self._alias_index[lower]
            category = self._material_map.get(normalized.lower(), (normalized, MaterialCategory.UNKNOWN))[1]
            return NormalizationResult(
                original=original,
                normalized=normalized,
                category=category,
                method=NormalizationMethod.ALIAS_MAP,
                confidence=1.0,
                matched_alias=original
            )
        
        # Try exact substance match
        if substance and substance.strip().lower() in self._substance_map:
            norm_sub = self._substance_map[substance.strip().lower()]
            return NormalizationResult(
                original=original,
                normalized=norm_sub,
                category=MaterialCategory.UNKNOWN,
                method=NormalizationMethod.CAS_NUMBER,
                confidence=0.95,
                matched_alias=substance
            )
        
        # Fuzzy match
        all_known = list(self._alias_index.keys())
        if all_known:
            match = process.extractOne(lower, all_known, scorer=fuzz.WRatio,
                                       score_cutoff=self.config.fuzzy_threshold * 100)
            if match:
                matched_alias, score, _ = match
                normalized = self._alias_index[matched_alias]
                category = self._material_map.get(normalized.lower(), (normalized, MaterialCategory.UNKNOWN))[1]
                return NormalizationResult(
                    original=original,
                    normalized=normalized,
                    category=category,
                    method=NormalizationMethod.FUZZY_MATCH,
                    confidence=score / 100.0,
                    matched_alias=matched_alias,
                    is_fuzzy=True
                )
        
        # Default: return as-is
        return NormalizationResult(
            original=original,
            normalized=original,
            category=MaterialCategory.UNKNOWN,
            method=NormalizationMethod.EXACT_MATCH,
            confidence=0.5
        )
    
    def normalize_record(self, record: MaterialRecord) -> MaterialRecord:
        """Normalize a material record in place."""
        result = self.normalize(record.raw_material or record.material, record.raw_substance or record.substance)
        
        record.material = result.normalized
        record.category = result.category
        record.normalization_method = result.method
        record.matched_alias = result.matched_alias
        record.confidence = min(record.confidence, result.confidence)
        
        # Normalize substance too
        if record.substance:
            sub_result = self.normalize("", record.substance)
            if sub_result.normalized != sub_result.original:
                record.substance = sub_result.normalized
        
        return record
    
    def add_material(self, normalized: str, aliases: list[str], category: MaterialCategory) -> None:
        """Add new material mapping (runtime)."""
        self._material_map[normalized.lower()] = (normalized, category)
        self._alias_index[normalized.lower()] = normalized
        for alias in aliases:
            self._alias_index[alias.lower()] = normalized
    
    def add_substance(self, normalized: str, aliases: list[str]) -> None:
        """Add new substance mapping."""
        self._substance_map[normalized.lower()] = normalized
        for alias in aliases:
            self._alias_index[alias.lower()] = normalized
    
    def save_material(self, normalized: str, aliases: list[str], category: MaterialCategory) -> None:
        """Persist material to YAML."""
        materials_file = self.data_dir / "materials.yaml"
        data = {}
        if materials_file.exists():
            with open(materials_file) as f:
                data = yaml.safe_load(f) or {}
        
        data[normalized] = {
            "category": category.value,
            "aliases": aliases
        }
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(materials_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=True)
        
        # Reload
        self.load()
    
    def stats(self) -> dict[str, int]:
        """Get normalization statistics."""
        unique_substances = set()
        for key, val in self._substance_map.items():
            unique_substances.add(val)
        return {
            "materials": len(self._material_map),
            "substances": len(unique_substances),
            "total_aliases": len(self._alias_index)
        }


# Global instance
_normalizer: ScalableNormalizer | None = None


def get_normalizer() -> ScalableNormalizer:
    """Get global normalizer instance."""
    global _normalizer
    if _normalizer is None:
        _normalizer = ScalableNormalizer()
        _normalizer.load()
    return _normalizer