"""CLI commands package."""
from __future__ import annotations

# Import commands to register them
from material_extractor.cli.commands import extract, normalize, validate, list_templates

__all__ = ["extract", "normalize", "validate", "list_templates"]