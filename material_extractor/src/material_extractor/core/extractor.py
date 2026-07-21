"""Extraction interfaces and base classes."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from material_extractor.models import (
    SourceType, MaterialRecord, ExtractionResult, TemplateDefinition
)


class BaseExtractor(ABC):
    """Abstract base extractor."""
    
    def __init__(self, template: TemplateDefinition):
        self.template = template
        self.metadata = template.metadata
    
    @abstractmethod
    def extract(self, file_path: Path) -> ExtractionResult:
        """Extract material records from file."""
        pass
    
    def _create_result(self, success: bool = True) -> ExtractionResult:
        """Create extraction result with metadata."""
        return ExtractionResult(
            success=success,
            template_id=self.metadata.template_id,
            source_file="",
            file_type=self.metadata.source_type,
        )
    
    def _create_record(self, **kwargs) -> MaterialRecord:
        """Create material record with template info."""
        return MaterialRecord(
            template_id=self.metadata.template_id,
            **kwargs
        )


class PDFExtractorMixin:
    """Mixin for PDF extraction utilities."""
    
    def _open_pdf(self, file_path: Path):
        import pdfplumber
        return pdfplumber.open(file_path)
    
    def _extract_tables(self, pdf, page_index: int, settings: dict | None = None) -> list:
        page = pdf.pages[page_index]
        return page.extract_tables(settings) or []
    
    def _extract_text(self, pdf, page_index: int) -> str:
        page = pdf.pages[page_index]
        return page.extract_text() or ""
    
    def _find_data_table(self, tables: list[list[list[str]]], 
                         header_keywords: list[str]) -> list[list[str]] | None:
        """Find the main data table by header keywords."""
        for table in tables:
            if not table:
                continue
            header = [str(c).lower() for c in table[0] if c]
            header_text = " ".join(header)
            if any(kw.lower() in header_text for kw in header_keywords):
                return table
        return None


class ExcelExtractorMixin:
    """Mixin for Excel extraction utilities."""
    
    def _read_excel(self, file_path: Path, **kwargs):
        import pandas as pd
        return pd.read_excel(file_path, **kwargs)
    
    def _read_all_sheets(self, file_path: Path) -> dict[str, Any]:
        import pandas as pd
        return pd.read_excel(file_path, sheet_name=None, engine="openpyxl")
    
    def _find_data_sheet(self, sheets: dict, keywords: list[str]) -> tuple[str, Any] | None:
        """Find sheet containing data by name or content."""
        for name, df in sheets.items():
            name_lower = name.lower()
            if any(kw.lower() in name_lower for kw in keywords):
                return name, df
            # Check first few rows
            for _, row in df.head(5).iterrows():
                row_text = " ".join(str(v).lower() for v in row if pd.notna(v))
                if any(kw.lower() in row_text for kw in keywords):
                    return name, df
        return None
    
    def _find_header_row(self, df, keywords: list[str], max_rows: int = 10) -> int | None:
        """Find row index containing header keywords."""
        import pandas as pd
        for i in range(min(max_rows, len(df))):
            row_vals = [str(v).lower() for v in df.iloc[i] if pd.notna(v)]
            row_text = " ".join(row_vals)
            if any(kw.lower() in row_text for kw in keywords):
                return i
        return None


class PDFTableExtractor(BaseExtractor, PDFExtractorMixin):
    """Extract from PDF tables using pdfplumber."""
    
    def extract(self, file_path: Path) -> ExtractionResult:
        result = self._create_result()
        result.source_file = str(file_path)
        
        import pdfplumber
        try:
            with pdfplumber.open(file_path) as pdf:
                pages = self.metadata.page_indices or [0]
                for page_idx in pages:
                    if page_idx >= len(pdf.pages):
                        continue
                    
                    page = pdf.pages[page_idx]
                    result.pages_processed += 1
                    
                    tables = self._extract_tables(pdf, page_idx)
                    result.tables_found += len(tables)
                    
                    for table_idx, table in enumerate(tables):
                        records = self._process_table(table, page_idx, table_idx)
                        result.records.extend(records)
                        if records:
                            result.tables_processed += 1
            
            result.success = len(result.records) > 0
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
        
        return result
    
    def _process_table(self, table: list[list[str]], page_num: int, table_idx: int) -> list[MaterialRecord]:
        """Override in subclasses to process specific table format."""
        return []


class ExcelSheetExtractor(BaseExtractor, ExcelExtractorMixin):
    """Extract from Excel sheets."""
    
    def extract(self, file_path: Path) -> ExtractionResult:
        result = self._create_result()
        result.source_file = str(file_path)
        
        import pandas as pd
        try:
            sheets = self._read_all_sheets(file_path)
            target = self._find_data_sheet(sheets, 
                self.template.extraction.get("sheet_keywords", ["material", "substance", "composition"]))
            
            if target:
                sheet_name, df = target
                header_row = self._find_header_row(df, 
                    self.template.extraction.get("header_keywords", ["material", "substance"]))
                
                if header_row is not None:
                    df.columns = df.iloc[header_row]
                    df = df.iloc[header_row + 1:].reset_index(drop=True)
                    records = self._process_dataframe(df)
                    result.records.extend(records)
                    result.tables_processed = 1
                    result.success = len(records) > 0
            else:
                result.errors.append("No matching sheet found")
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
        
        return result
    
    def _process_dataframe(self, df) -> list[MaterialRecord]:
        """Override in subclasses to process specific DataFrame format."""
        return []

