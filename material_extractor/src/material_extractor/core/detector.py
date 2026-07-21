"""Template detection interface and base classes."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from material_extractor.models import (
    SourceType, DetectionMethod, TemplateDefinition
)


class BaseDetector(ABC):
    """Abstract base for template detectors."""
    
    def __init__(self, template: TemplateDefinition):
        self.template = template
        self.metadata = template.metadata
    
    @property
    def template_id(self) -> str:
        return self.metadata.template_id
    
    @property
    def priority(self) -> int:
        return self.metadata.priority
    
    @abstractmethod
    def detect(self, file_path: Path, file_type: SourceType) -> bool:
        """Return True if this template matches the file."""
        pass
    
    # --- Common utilities ---
    
    def _read_pdf_text(self, file_path: Path, pages: list[int] | None = None) -> str:
        """Extract text from PDF pages."""
        import pdfplumber
        text_parts = []
        try:
            with pdfplumber.open(file_path) as pdf:
                page_indices = pages or self.metadata.page_indices or range(len(pdf.pages))
                for i in page_indices:
                    if i < len(pdf.pages):
                        text = pdf.pages[i].extract_text() or ""
                        text_parts.append(text)
        except Exception:
            pass
        return "\n".join(text_parts)
    
    def _read_excel_text(self, file_path: Path, sheet_name: str | int = 0) -> str:
        """Extract text representation from Excel sheet."""
        import pandas as pd
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=20)
            return df.to_string()
        except Exception:
            return ""
    
    def _check_keywords(self, text: str, keywords: list[str], all_required: bool = True) -> bool:
        """Check if keywords are present in text."""
        text_lower = text.lower()
        if all_required:
            return all(kw.lower() in text_lower for kw in keywords)
        return any(kw.lower() in text_lower for kw in keywords)
    
    def _check_patterns(self, text: str, patterns: list[str]) -> bool:
        """Check if any regex patterns match."""
        import re
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _detect_by_text(self, file_path: Path, file_type: SourceType) -> bool:
        """Generic text-based detection."""
        if file_type == SourceType.PDF:
            text = self._read_pdf_text(file_path)
        elif file_type == SourceType.EXCEL:
            text = self._read_excel_text(file_path)
        else:
            return False
        
        if self.metadata.detection_keywords and not self._check_keywords(text, self.metadata.detection_keywords):
            return False
        
        if self.metadata.detection_patterns and not self._check_patterns(text, self.metadata.detection_patterns):
            return False
        
        return True


class TextPatternDetector(BaseDetector):
    """Detector using text pattern matching."""
    
    def detect(self, file_path: Path, file_type: SourceType) -> bool:
        return self._detect_by_text(file_path, file_type)


class HeaderMatchDetector(BaseDetector):
    """Detector using table header matching."""
    
    def detect(self, file_path: Path, file_type: SourceType) -> bool:
        if file_type != SourceType.PDF:
            return False
        
        import pdfplumber
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_idx in self.metadata.page_indices or [0]:
                    if page_idx >= len(pdf.pages):
                        continue
                    tables = pdf.pages[page_idx].extract_tables()
                    if not tables:
                        continue
                    for table in tables:
                        if table and len(table) > 0:
                            header_row = [str(c).strip().lower() for c in table[0] if c]
                            if self._match_headers(header_row):
                                return True
        except Exception:
            pass
        return False
    
    def _match_headers(self, header_row: list[str]) -> bool:
        header_text = " ".join(header_row)
        required = self.metadata.header_keywords
        if not required:
            return True
        return all(kw.lower() in header_text for kw in required)


class LayoutAnalysisDetector(BaseDetector):
    """Detector using layout analysis."""
    
    def detect(self, file_path: Path, file_type: SourceType) -> bool:
        if file_type != SourceType.PDF:
            return False
        
        import pdfplumber
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_idx in self.metadata.page_indices or [0]:
                    if page_idx >= len(pdf.pages):
                        continue
                    page = pdf.pages[page_idx]
                    text = page.extract_text() or ""
                    tables = page.extract_tables() or []
                    
                    if self._check_layout(text, tables):
                        return True
        except Exception:
            pass
        return False
    
    def _check_layout(self, text: str, tables: list) -> bool:
        if not tables or len(text) < 100:
            return False
        rules = self.metadata.validation_rules
        if "min_rows" in rules and len(tables[0]) < rules["min_rows"]:
            return False
        if "min_cols" in rules and len(tables[0][0]) < rules["min_cols"]:
            return False
        if "cell_values" in rules:
            for (r, c), expected in rules["cell_values"].items():
                if r < len(tables[0]) and c < len(tables[0][r]):
                    if str(tables[0][r][c]).strip() != str(expected).strip():
                        return False
        return True


class KeywordMatchDetector(BaseDetector):
    """Simple keyword-based detector."""

    def detect(self, file_path: Path, file_type: SourceType) -> bool:
        if file_type == SourceType.PDF:
            text = self._read_pdf_text(file_path)
        elif file_type == SourceType.EXCEL:
            text = self._read_excel_text(file_path)
        else:
            return False

        keywords = self.metadata.detection_keywords
        if not keywords:
            return False

        text_lower = text.lower()
        return all(kw.lower() in text_lower for kw in keywords)


class CompositeDetector(BaseDetector):
    """Detector combining multiple detection methods."""
    
    def __init__(self, template: TemplateDefinition, detectors: list[BaseDetector]):
        super().__init__(template)
        self.detectors = detectors
    
    def detect(self, file_path: Path, file_type: SourceType) -> bool:
        return all(d.detect(file_path, file_type) for d in self.detectors)


def create_detector(template: TemplateDefinition) -> BaseDetector:
    """Factory to create appropriate detector for template."""
    method = template.metadata.detection_method
    
    if method == DetectionMethod.TEXT_PATTERN:
        return TextPatternDetector(template)
    elif method == DetectionMethod.HEADER_MATCH:
        return HeaderMatchDetector(template)
    elif method == DetectionMethod.LAYOUT_ANALYSIS:
        return LayoutAnalysisDetector(template)
    elif method == DetectionMethod.KEYWORD_MATCH:
        return KeywordMatchDetector(template)
    else:
        return TextPatternDetector(template)