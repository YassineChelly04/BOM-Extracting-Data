"""Normalization package exports."""
from material_extractor.normalization.normalizer import (
    ScalableNormalizer,
    get_normalizer,
)

# Alias for backward compatibility
MaterialNormalizer = ScalableNormalizer

__all__ = ["ScalableNormalizer", "MaterialNormalizer", "get_normalizer"]