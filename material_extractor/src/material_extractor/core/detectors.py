"""Concrete detector implementations."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from material_extractor.core.detector import BaseDetector, create_detector
from material_extractor.models import (
    SourceType, TemplateDefinition, DetectionMethod, TemplateMetadata
)


class TextPatternDetector(BaseDetector):
    """Detector using text pattern matching."""
    
    def detect(self, file_path: Path, file_type: SourceType) -> bool:
        text = self._extract_text(file_path, file_type)
        if not text:
            return False
        
        # Check required keywords
        required = self.template.metadata.detection_keywords
        if required and not all(kw.lower() in text.lower() for kw in required):
            return False
        
        # Check patterns
        patterns = self.template.metadata.detection_patterns
        if patterns:
            return any(re.search(p, text, re.IGNORECASE) for p in patterns)
        
        return bool(required)  # If only keywords, they all matched


class HeaderMatchDetector(BaseDetector):
    """Detector matching table headers."""
    
    def detect(self, file_path: Path, file_type: SourceType) -> bool:
        if file_type == SourceType.PDF:
            return self._detect_pdf_headers(file_path)
        elif file_type == SourceType.EXCEL:
            return self._detect_excel_headers(file_path)
        return False
    
    def _detect_pdf_headers(self, file_path: Path) -> bool:
        import pdfplumber
        try:
            with pdfplumber.open(file_path) as pdf:
                pages = self.template.metadata.page_indices or [0]
                for page_idx in pages:
                    if page_idx >= len(pdf.pages):
                        continue
                    tables = pdf.pages[page_idx].extract_tables() or []
                    for table in tables:
                        if table and self._match_headers(table[0]):
                            return True
        except Exception:
            pass
        return False
    
    def _detect_excel_headers(self, file_path: Path) -> bool:
        import pandas as pd
        try:
            sheets = pd.read_excel(file_path, sheet_name=None, nrows=5, engine="openpyxl")
            for df in sheets.values():
                if self._match_headers(df.columns.tolist()):
                    return True
                # Check first few rows
                for _, row in df.head(3).iterrows():
                    if self._match_headers(row.dropna().tolist()):
                        return True
        except Exception:
            pass
        return False
    
    def _match_headers(self, headers: list[Any]) -> bool:
        header_text = " ".join(str(h).lower() for h in headers if h)
        keywords = self.template.metadata.header_keywords
        if not keywords:
            return False
        return any(kw.lower() in header_text for kw in keywords)


class KeywordMatchDetector(BaseDetector):
    """Simple keyword-based detector."""
    
    def detect(self, file_path: Path, file_type: SourceType) -> bool:
        text = self._extract_text(file_path, file_type)
        if not text:
            return False
        
        keywords = self.template.metadata.detection_keywords
        if not keywords:
            return False
        
        text_lower = text.lower()
        return all(kw.lower() in text_lower for kw in keywords)


class LayoutAnalysisDetector(BaseDetector):
    """Detector using layout analysis."""
    
    def detect(self, file_path: Path, file_type: SourceType) -> bool:
        if file_type != SourceType.PDF:
            return False
        
        import pdfplumber
        try:
            with pdfplumber.open(file_path) as pdf:
                pages = self.template.metadata.page_indices or [0]
                for page_idx in pages:
                    if page_idx >= len(pdf.pages):
                        continue
                    page = pdf.pages[page_idx]
                    text = page.extract_text() or ""
                    tables = page.extract_tables() or []
                    
                    # Check for specific layout patterns
                    if self._check_layout(text, tables):
                        return True
        except Exception:
            pass
        return False
    
    def _check_layout(self, text: str, tables: list) -> bool:
        # Override in subclasses for specific layouts
        return bool(tables) and len(text) > 100


class CompositeDetector(BaseDetector):
    """Detector combining multiple detection methods."""
    
    def __init__(self, template: TemplateDefinition):
        super().__init__(template)
        self.detectors = []
        for method in self.template.metadata.detection_method:
            if isinstance(method, DetectionMethod):
                temp_template = self.template.model_copy()
                temp_template.metadata.detection_method = method
                self.detectors.append(create_detector(temp_template))
    
    def detect(self, file_path: Path, file_type: SourceType) -> bool:
        return all(d.detect(file_path, file_type) for d in self.detectors)


# Factory function
def create_detector(template: TemplateDefinition) -> BaseDetector:
    """Create appropriate detector for template."""
    method = template.metadata.detection_method
    
    if method == DetectionMethod.TEXT_PATTERN:
        return TextPatternDetector(template)
    elif method == DetectionMethod.HEADER_MATCH:
        return HeaderMatchDetector(template)
    elif method == DetectionMethod.KEYWORD_MATCH:
        return KeywordMatchDetector(template)
    elif method == DetectionMethod.LAYOUT_ANALYSIS:
        return LayoutAnalysisDetector(template)
    else:
        return TextPatternDetector(template)