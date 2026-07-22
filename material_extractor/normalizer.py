"""Material name normalization.

Loads a single YAML file (materials.yaml) that maps a canonical material name
to a category and a list of aliases. Normalizing a raw name is a plain
lowercase alias lookup -- no fuzzy matching, no models, no magic.

To teach the system a new material, add one entry to materials.yaml:

    Copper (Cu):
      category: Metal
      aliases:
      - copper
      - cu
"""
from __future__ import annotations

from pathlib import Path

import yaml

DEFAULT_DATA_FILE = Path(__file__).parent / "materials.yaml"


class Normalizer:
    """Map raw supplier material names to canonical names + categories."""

    def __init__(self, data_file: Path | None = None):
        self.data_file = data_file or DEFAULT_DATA_FILE
        self._alias_to_canonical: dict[str, str] = {}
        self._category: dict[str, str] = {}
        self._load()

    @staticmethod
    def _key(text: str) -> str:
        """Match key: lowercase with all whitespace removed, so 'Nickel(Ni)'
        and 'nickel (ni)' collapse to the same thing."""
        return "".join(str(text).lower().split())

    def _load(self) -> None:
        if not self.data_file.exists():
            return
        with open(self.data_file, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        for canonical, info in data.items():
            category = (info or {}).get("category", "Unknown")
            self._category[canonical] = category
            self._alias_to_canonical[self._key(canonical)] = canonical
            for alias in (info or {}).get("aliases", []):
                self._alias_to_canonical[self._key(alias)] = canonical

    def normalize_name(self, name: str) -> tuple[str, str]:
        """Return (canonical_name, category). Falls back to (name, 'Unknown')."""
        canonical = self._alias_to_canonical.get(self._key(name))
        if canonical:
            return canonical, self._category.get(canonical, "Unknown")
        return name, "Unknown"

    def normalize_record(self, record: dict) -> dict:
        """Add canonical 'material' and 'category' to an extracted record."""
        canonical, category = self.normalize_name(record.get("material", ""))
        record["raw_material"] = record.get("material", "")
        record["material"] = canonical
        record["category"] = category
        return record

    @property
    def material_count(self) -> int:
        return len(self._category)
