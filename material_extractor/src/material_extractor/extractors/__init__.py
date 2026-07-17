"""Extractor factory and template-specific extractors."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from material_extractor.core.extractor import (
    PDFTableExtractor, ExcelSheetExtractor, BaseExtractor
)
from material_extractor.models import (
    TemplateDefinition, ExtractionResult, MaterialRecord, SourceType
)


# --- Factory ---

def create_extractor(template: TemplateDefinition) -> BaseExtractor:
    """Create appropriate extractor for template."""
    extractor_type = template.extraction.get("extractor_type", "pdf_table")
    
    if extractor_type == "pdf_table":
        return _create_pdf_table_extractor(template)
    elif extractor_type == "pdf_text":
        return _create_pdf_text_extractor(template)
    elif extractor_type == "excel":
        return _create_excel_extractor(template)
    elif extractor_type == "excel_multi":
        return _create_multi_sheet_extractor(template)
    else:
        return _create_pdf_table_extractor(template)


def _create_pdf_table_extractor(template: TemplateDefinition) -> BaseExtractor:
    """Create PDF table extractor based on template config."""
    extractor_class = template.extraction.get("extractor_class")
    
    if extractor_class == "MolexTemplateExtractor":
        return MolexTemplateExtractor(template)
    elif extractor_class == "WurthTemplateExtractor":
        return WurthTemplateExtractor(template)
    elif extractor_class == "TIEMCTemplateExtractor":
        return TIEMCTemplateExtractor(template)
    elif extractor_class == "VishayTemplateExtractor":
        return VishayTemplateExtractor(template)
    elif extractor_class == "SamsungTemplateExtractor":
        return SamsungTemplateExtractor(template)
    elif extractor_class == "MurataTemplateExtractor":
        return MurataTemplateExtractor(template)
    elif extractor_class == "TDKTemplateExtractor":
        return TDKTemplateExtractor(template)
    elif extractor_class == "KemetTemplateExtractor":
        return KemetTemplateExtractor(template)
    elif extractor_class == "AVXTemplateExtractor":
        return AVXTemplateExtractor(template)
    elif extractor_class == "YageoTemplateExtractor":
        return YageoTemplateExtractor(template)
    elif extractor_class == "KyoceraTemplateExtractor":
        return KyoceraTemplateExtractor(template)
    elif extractor_class == "GenericPDFTableExtractor":
        return GenericPDFTableExtractor(template)
    else:
        # Default generic extractor
        return GenericPDFTableExtractor(template)


def _create_pdf_text_extractor(template: TemplateDefinition) -> BaseExtractor:
    return GenericPDFTextExtractor(template)


def _create_excel_extractor(template: TemplateDefinition) -> BaseExtractor:
    return GenericExcelExtractor(template)


def _create_multi_sheet_extractor(template: TemplateDefinition) -> BaseExtractor:
    return GenericMultiSheetExtractor(template)


# --- Template-Specific Extractors ---

class MolexTemplateExtractor(PDFTableExtractor):
    """Template 1: Molex/TE Connectivity BOM with case sizes."""
    
    def _process_table(self, table: list[list[str]], page: int, table_idx: int) -> list[MaterialRecord]:
        if len(table) < 3:
            return []
        
        records = []
        case_sizes = [c for c in table[1][4:] if c]
        skip_rows = {"Homogeneous Level Weight", "Total Weight"}
        current_level = None
        
        for row_idx, row in enumerate(table[3:], start=3):
            if not row or len(row) < 5:
                continue
            
            level, material, substance, cas, *weights = row
            
            if level and level not in skip_rows:
                current_level = level
            
            if not material or level in skip_rows:
                continue
            
            weight_dict = dict(zip(case_sizes, weights))
            target_size = self.config.get("target_size", "0402")
            weight_str = weight_dict.get(target_size, "0")
            
            records.append(self._create_record(
                material=material.strip(),
                substance=substance.strip() if substance else "",
                weight_mg=weight_str,
                case_size=target_size,
                raw_material=material,
                raw_substance=substance or "",
                raw_weight=weight_str,
                page_number=page,
                row_index=row_idx
            ))
        
        return records


class WurthTemplateExtractor(PDFTableExtractor):
    """Template 2: Würth Elektronik material declaration."""
    
    def _process_table(self, table: list[list[str]], page: int, table_idx: int) -> list[MaterialRecord]:
        if table_idx != 1:
            return []
        
        records = []
        
        # Get total mass from part table (table index 2)
        total_mass_g = 0.0
        # This would need access to all tables - simplified for now
        
        for row_idx, row in enumerate(table[1:], start=1):
            if len(row) < 5:
                continue
            _, _, substance, _, avg_mass, _ = row
            if not substance or not avg_mass:
                continue
            
            weight_mg = round(float(avg_mass) / 100 * total_mass_g * 1000, 4)
            
            records.append(self._create_record(
                material=substance.replace("\n", " ").strip(),
                substance="",
                weight_mg=weight_mg,
                raw_material=substance,
                raw_substance="",
                raw_weight=str(weight_mg),
                page_number=page,
                row_index=row_idx
            ))
        
        return records


class TIEMCTemplateExtractor(PDFTableExtractor):
    """Template 3: TI EMC material declaration."""
    
    def _process_table(self, table: list[list[str]], page: int, table_idx: int) -> list[MaterialRecord]:
        records = []
        
        for row_idx, row in enumerate(table[1:], start=1):
            if len(row) < 5:
                continue
            name, type_, cas, _, mass_g = row
            if type_ != "Substance" or not mass_g:
                continue
            
            weight_mg = float(mass_g) * 1000
            
            records.append(self._create_record(
                material=name.strip(),
                substance=cas.strip() if cas else "",
                weight_mg=weight_mg,
                raw_material=name,
                raw_substance=cas or "",
                raw_weight=str(weight_mg),
                page_number=page,
                row_index=row_idx
            ))
        
        return records


class VishayTemplateExtractor(PDFTableExtractor):
    """Template 4: Vishay material declaration."""
    
    def _process_table(self, table: list[list[str]], page: int, table_idx: int) -> list[MaterialRecord]:
        # Vishay specific parsing
        records = []
        for row_idx, row in enumerate(table[1:], start=1):
            if len(row) < 3:
                continue
            material, cas, weight = row[0], row[1], row[2]
            if not material or not weight:
                continue
            
            records.append(self._create_record(
                material=material.strip(),
                substance=cas.strip() if cas else "",
                weight_mg=weight,
                raw_material=material,
                raw_substance=cas or "",
                raw_weight=weight,
                page_number=page,
                row_index=row_idx
            ))
        return records


class SamsungTemplateExtractor(PDFTableExtractor):
    """Template 5: Samsung Electro-Mechanics."""
    
    def _process_table(self, table: list[list[str]], page: int, table_idx: int) -> list[MaterialRecord]:
        records = []
        for row_idx, row in enumerate(table[1:], start=1):
            if len(row) < 4:
                continue
            # Samsung specific column mapping
            records.append(self._create_record(
                material=row[0].strip() if row[0] else "",
                substance=row[1].strip() if row[1] else "",
                weight_mg=row[2] if len(row) > 2 else "0",
                case_size=row[3] if len(row) > 3 else "",
                raw_material=row[0] or "",
                raw_substance=row[1] or "",
                raw_weight=row[2] if len(row) > 2 else "",
                page_number=page,
                row_index=row_idx
            ))
        return records


class MurataTemplateExtractor(PDFTableExtractor):
    """Template 6: Murata Manufacturing."""
    
    def _process_table(self, table: list[list[str]], page: int, table_idx: int) -> list[MaterialRecord]:
        records = []
        for row_idx, row in enumerate(table[1:], start=1):
            if len(row) < 3:
                continue
            records.append(self._create_record(
                material=row[0].strip(),
                substance=row[1].strip() if len(row) > 1 else "",
                weight_mg=row[2] if len(row) > 2 else "0",
                raw_material=row[0],
                raw_substance=row[1] if len(row) > 1 else "",
                raw_weight=row[2] if len(row) > 2 else "",
                page_number=page,
                row_index=row_idx
            ))
        return records


class TDKTemplateExtractor(PDFTableExtractor):
    """Template 7: TDK Corporation."""
    
    def _process_table(self, table: list[list[str]], page: int, table_idx: int) -> list[MaterialRecord]:
        records = []
        for row_idx, row in enumerate(table[1:], start=1):
            if len(row) < 3:
                continue
            records.append(self._create_record(
                material=row[0].strip(),
                substance=row[1].strip() if len(row) > 1 else "",
                weight_mg=row[2] if len(row) > 2 else "0",
                raw_material=row[0],
                raw_substance=row[1] if len(row) > 1 else "",
                raw_weight=row[2] if len(row) > 2 else "",
                page_number=page,
                row_index=row_idx
            ))
        return records


class KemetTemplateExtractor(PDFTableExtractor):
    """Template 8: KEMET Corporation."""
    
    def _process_table(self, table: list[list[str]], page: int, table_idx: int) -> list[MaterialRecord]:
        records = []
        for row_idx, row in enumerate(table[1:], start=1):
            if len(row) < 3:
                continue
            records.append(self._create_record(
                material=row[0].strip(),
                substance=row[1].strip() if len(row) > 1 else "",
                weight_mg=row[2] if len(row) > 2 else "0",
                raw_material=row[0],
                raw_substance=row[1] if len(row) > 1 else "",
                raw_weight=row[2] if len(row) > 2 else "",
                page_number=page,
                row_index=row_idx
            ))
        return records


class AVXTemplateExtractor(PDFTableExtractor):
    """Template 9: AVX/Kyocera."""
    
    def _process_table(self, table: list[list[str]], page: int, table_idx: int) -> list[MaterialRecord]:
        records = []
        for row_idx, row in enumerate(table[1:], start=1):
            if len(row) < 3:
                continue
            records.append(self._create_record(
                material=row[0].strip(),
                substance=row[1].strip() if len(row) > 1 else "",
                weight_mg=row[2] if len(row) > 2 else "0",
                raw_material=row[0],
                raw_substance=row[1] if len(row) > 1 else "",
                raw_weight=row[2] if len(row) > 2 else "",
                page_number=page,
                row_index=row_idx
            ))
        return records


class YageoTemplateExtractor(PDFTableExtractor):
    """Template 10: Yageo."""
    
    def _process_table(self, table: list[list[str]], page: int, table_idx: int) -> list[MaterialRecord]:
        records = []
        for row_idx, row in enumerate(table[1:], start=1):
            if len(row) < 3:
                continue
            records.append(self._create_record(
                material=row[0].strip(),
                substance=row[1].strip() if len(row) > 1 else "",
                weight_mg=row[2] if len(row) > 2 else "0",
                raw_material=row[0],
                raw_substance=row[1] if len(row) > 1 else "",
                raw_weight=row[2] if len(row) > 2 else "",
                page_number=page,
                row_index=row_idx
            ))
        return records


class KyoceraTemplateExtractor(PDFTableExtractor):
    """Template 11: Kyocera."""
    
    def _process_table(self, table: list[list[str]], page: int, table_idx: int) -> list[MaterialRecord]:
        records = []
        for row_idx, row in enumerate(table[1:], start=1):
            if len(row) < 3:
                continue
            records.append(self._create_record(
                material=row[0].strip(),
                substance=row[1].strip() if len(row) > 1 else "",
                weight_mg=row[2] if len(row) > 2 else "0",
                raw_material=row[0],
                raw_substance=row[1] if len(row) > 1 else "",
                raw_weight=row[2] if len(row) > 2 else "",
                page_number=page,
                row_index=row_idx
            ))
        return records


class GenericPDFTableExtractor(PDFTableExtractor):
    """Generic fallback extractor for PDF tables."""
    
    def _process_table(self, table: list[list[str]], page: int, table_idx: int) -> list[MaterialRecord]:
        records = []
        
        # Try to detect header
        header = [str(c).lower() for c in table[0] if c]
        header_text = " ".join(header)
        
        # Find material, substance, weight columns
        mat_col = self._find_column(header, ["material", "substance", "component", "name"])
        sub_col = self._find_column(header, ["cas", "substance", "chemical", "formula"])
        wt_col = self._find_column(header, ["weight", "mass", "mg", "g", "amount", "%"])
        
        if mat_col is None:
            return records
        
        for row_idx, row in enumerate(table[1:], start=1):
            if not row or len(row) <= mat_col:
                continue
            
            material = row[mat_col] if row[mat_col] else ""
            if not material.strip():
                continue
            
            substance = row[sub_col] if sub_col is not None and len(row) > sub_col else ""
            weight = row[wt_col] if wt_col is not None and len(row) > wt_col else "0"
            
            records.append(self._create_record(
                material=material.strip(),
                substance=substance.strip() if substance else "",
                weight_mg=weight,
                raw_material=material,
                raw_substance=substance or "",
                raw_weight=weight,
                page_number=page,
                row_index=row_idx
            ))
        
        return records
    
    def _find_column(self, headers: list[str], keywords: list[str]) -> int | None:
        for i, h in enumerate(headers):
            for kw in keywords:
                if kw in h:
                    return i
        return None


class GenericPDFTextExtractor:
    """Generic text-based extractor for PDFs."""
    
    def __init__(self, template: TemplateDefinition):
        self.template = template
        self.config = template.extraction
    
    def extract(self, file_path: Path) -> ExtractionResult:
        # Implementation for text-based extraction
        return ExtractionResult(
            success=False,
            template_id=self.template.metadata.template_id,
            source_file=str(file_path),
            errors=["Not implemented"]
        )


class GenericExcelExtractor(ExcelSheetExtractor):
    """Generic Excel extractor."""
    
    def _process_dataframe(self, df) -> list[MaterialRecord]:
        records = []
        for row_idx, row in df.iterrows():
            material = str(row.get("Material", row.get("material", ""))).strip()
            if not material:
                continue
            
            records.append(self._create_record(
                material=material,
                substance=str(row.get("CAS", row.get("Substance", ""))).strip(),
                weight_mg=str(row.get("Weight", row.get("Weight_mg", "0"))),
                raw_material=material,
                raw_substance=str(row.get("CAS", row.get("Substance", ""))),
                raw_weight=str(row.get("Weight", row.get("Weight_mg", "0"))),
                row_index=row_idx
            ))
        return records


class GenericMultiSheetExtractor:
    """Generic multi-sheet Excel extractor."""
    
    def __init__(self, template: TemplateDefinition):
        self.template = template
        self.config = template.extraction
    
    def extract(self, file_path: Path) -> ExtractionResult:
        return ExtractionResult(
            success=False,
            template_id=self.template.metadata.template_id,
            source_file=str(file_path),
            errors=["Not implemented"]
        )