"""Material extraction system.

Reads supplier PDFs / XLSXs and produces a unified material composition report.

One supplier format = one file in templates/. Add a format by dropping a new
templateN.py there; add a material by adding an entry to materials.yaml.
"""
from material_extractor.normalizer import Normalizer
from material_extractor.pipeline import Pipeline, Result, run

__all__ = ["Normalizer", "Pipeline", "Result", "run"]
__version__ = "2.0.0"
