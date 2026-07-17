"""Main processing pipeline."""
from __future__ import annotations

import concurrent.futures
from pathlib import Path
from typing import Any
from datetime import datetime
from decimal import Decimal
import pandas as pd

from material_extractor.models import (
    MaterialRecord, MaterialCategory, ProcessingStats, ExtractionResult,
    SourceType, AggregatedMaterial
)
from material_extractor.normalization import MaterialNormalizer, get_normalizer
from material_extractor.templates.registry import TemplateManager
from material_extractor.config import get_settings


class ExtractionPipeline:
    """Main pipeline for material extraction and normalization."""
    
    def __init__(self, template_manager: TemplateManager | None = None,
                 normalizer: MaterialNormalizer | None = None,
                 config: dict | None = None):
        self.template_manager = template_manager or TemplateManager()
        self.normalizer = normalizer or get_normalizer()
        self.config = config or {}
        self.stats = ProcessingStats()
    
    def process_file(self, file_path: Path) -> ProcessingStats:
        """Process a single file."""
        import time
        start = time.perf_counter()
        
        self.stats.total_files += 1
        
        try:
            # Detect file type
            file_type = self._detect_file_type(file_path)
            
            # Find matching template
            template = self.template_manager.detect_template(file_path, file_type)
            if not template:
                self.stats.skipped_files += 1
                self.stats.warnings.append(f"No template matched: {file_path.name}")
                return self.stats
            
            # Extract
            extractor = self.template_manager.get_extractor(template.metadata.template_id)
            if not extractor:
                self.stats.failed_files += 1
                self.stats.errors.append(f"No extractor for template: {template.metadata.template_id}")
                return self.stats
            
            result = extractor.extract(file_path)
            result.source_file = str(file_path)
            
            if not result.success or not result.records:
                self.stats.failed_files += 1
                self.stats.errors.extend(result.errors)
                return self.stats
            
            # Normalize
            normalized = self.normalizer.normalize_records(result.records)
            for rec in normalized:
                rec.source_file = str(file_path)
            
            # Update stats
            self.stats.processed_files += 1
            self.stats.total_records += len(normalized)
            self.stats.total_templates_matched += 1
            self.stats.total_weight_mg += sum(r.weight_mg for r in normalized)
            
            # Save individual output
            self._save_output(normalized, file_path, template.metadata.template_id)
            
            # Track materials for aggregation
            for rec in normalized:
                self._track_material(rec)
                
        except Exception as e:
            self.stats.failed_files += 1
            self.stats.errors.append(f"{file_path.name}: {str(e)}")
        
        self.stats.processing_time_ms += (time.perf_counter() - start) * 1000
        return self.stats
    
    def process_directory(self, input_dir: Path, pattern: str = "*",
                          parallel: bool = False, max_workers: int = 4) -> ProcessingStats:
        """Process all matching files in directory."""
        files = list(input_dir.glob(pattern))
        self.stats.total_files = len(files)
        
        if parallel and len(files) > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(self.process_file, f) for f in files]
                for future in concurrent.futures.as_completed(futures):
                    future.result()
        else:
            for f in files:
                self.process_file(f)
        
        # Generate aggregated output
        self._generate_aggregated_output()
        
        return self.stats
    
    def _detect_file_type(self, file_path: Path) -> SourceType:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            return SourceType.PDF
        elif suffix in (".xlsx", ".xls"):
            return SourceType.EXCEL
        elif suffix == ".csv":
            return SourceType.CSV
        return SourceType.UNKNOWN
    
    def _save_output(self, records: list[MaterialRecord], 
                     source_file: Path, template_id: str) -> None:
        """Save individual file output."""
        settings = get_settings()
        output_dir = settings.output_dir / "individual"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{source_file.stem}_{template_id}.csv"
        
        df = pd.DataFrame([r.to_dict() for r in records])
        df.to_csv(output_file, index=False, encoding=settings.output_encoding)
    
    def _track_material(self, record: MaterialRecord) -> None:
        """Track material for aggregation."""
        # This would build up aggregation data
        pass
    
    def _generate_aggregated_output(self) -> None:
        """Generate aggregated CSV across all processed files."""
        settings = get_settings()
        output_dir = settings.output_dir / "aggregated"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Read all individual outputs
        individual_dir = settings.output_dir / "individual"
        if not individual_dir.exists():
            return
        
        all_records = []
        for csv_file in individual_dir.glob("*.csv"):
            try:
                df = pd.read_csv(csv_file)
                all_records.append(df)
            except Exception:
                continue
        
        if not all_records:
            return
        
        combined = pd.concat(all_records, ignore_index=True)
        
        # Aggregate by material
        agg = combined.groupby("material").agg(
            category=("category", "first"),
            total_weight_mg=("weight_mg", "sum"),
            templates=("template_id", lambda x: ", ".join(sorted(set(x)))),
            files=("source_file", lambda x: ", ".join(sorted(set(x))))
        ).reset_index()
        
        agg["template_count"] = agg["templates"].apply(lambda x: len(x.split(", ")))
        agg["file_count"] = agg["files"].apply(lambda x: len(x.split(", ")))
        
        # Sort by category then material
        category_order = [c.value for c in MaterialCategory]
        cat_map = {c: i for i, c in enumerate(category_order)}
        agg["category_sort"] = agg["category"].map(lambda x: cat_map.get(x, 999))
        agg = agg.sort_values(["category_sort", "material"]).drop("category_sort", axis=1)
        
        output_file = output_dir / "all_materials_aggregated.csv"
        agg.to_csv(output_file, index=False, encoding=settings.output_encoding)
        
        # Also save detailed
        detail_file = output_dir / "all_materials_detailed.csv"
        combined.to_csv(detail_file, index=False, encoding=settings.output_encoding)
        
        self.stats.unique_materials = len(agg)


def run_pipeline(input_path: Path, template_dir: Path | None = None,
                 output_dir: Path | None = None, **kwargs) -> ProcessingStats:
    """Convenience function to run pipeline."""
    settings = get_settings()
    
    if output_dir:
        settings.output_dir = output_dir
    
    template_manager = TemplateManager()
    if template_dir:
        template_manager.load_from_yaml(template_dir)
    else:
        template_manager.load_registry()
    
    pipeline = ExtractionPipeline(template_manager=template_manager)
    
    if input_path.is_file():
        return pipeline.process_file(input_path)
    else:
        return pipeline.process_directory(input_path, **kwargs)