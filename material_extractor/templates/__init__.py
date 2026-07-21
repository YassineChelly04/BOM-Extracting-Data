"""Supplier format templates.

Each templateN.py in this folder handles exactly one supplier document format
and exposes two functions:

    detect(path: str) -> bool          # is this file my format?
    extract(path: str) -> list[dict]   # rows of {material, substance?, weight_mg}

The pipeline discovers every module here automatically. To support a new
supplier, add a new templateN.py -- nothing else needs editing.
"""
