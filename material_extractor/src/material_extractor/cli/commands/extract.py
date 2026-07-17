"""Extract command - extract materials from files."""
from __future__ import annotations

import typer
from pathlib import Path
from typing import Optional
import json

from material_extractor.core.pipeline import ExtractionPipeline
from material_extractor.templates.registry import TemplateManager
from material_extractor.normalization import get_normalizer
from material_extractor.config import get_settings
from material_extractor.models import SourceType

app = typer.Typer(name="extract", help="Extract materials from PDF/Excel files")


@app.command()
def extract_cmd(
    input_file: Path = typer.Argument(..., help="Input PDF or Excel file"),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="Output CSV file"),
    template_id: Optional[str] = typer.Option(None, "--template", "-t", help="Force specific template ID"),
    output_format: str = typer.Option("csv", "--format", "-f", help="Output format (csv, json)"),
    include_raw: bool = typer.Option(False, "--raw", help="Include raw extracted fields"),
    no_normalize: bool = typer.Option(False, "--no-normalize", help="Skip normalization"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Extract materials from a single file."""
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    # Initialize
    template_manager = TemplateManager()
    template_manager.load_registry()
    
    normalizer = get_normalizer()
    normalizer.load()
    
    pipeline = ExtractionPipeline(template_manager, normalizer)
    
    # Detect file type
    file_type = _detect_file_type(input_file)
    
    # Find template
    if template_id:
        template = template_manager.get_template(template_id)
        if not template:
            console.print(f"[red]Template not found: {template_id}[/red]")
            raise typer.Exit(1)
    else:
        template = template_manager.detect_template(input_file, file_type)
        if not template:
            console.print(f"[red]No matching template for: {input_file.name}[/red]")
            console.print("Available templates:")
            for t in template_manager.registry.get_enabled_templates():
                console.print(f"  - {t.metadata.template_id}: {t.metadata.name}")
            raise typer.Exit(1)
    
    if verbose:
        console.print(f"Using template: [cyan]{template.metadata.template_id}[/cyan] ({template.metadata.name})")
    
    # Extract
    extractor = template_manager.get_extractor(template.metadata.template_id)
    if not extractor:
        console.print(f"[red]No extractor for template: {template.metadata.template_id}[/red]")
        raise typer.Exit(1)
    
    result = extractor.extract(input_file)
    result.source_file = str(input_file)
    
    if not result.success:
        console.print(f"[red]Extraction failed:[/red]")
        for e in result.errors:
            console.print(f"  - {e}")
        raise typer.Exit(1)
    
    # Normalize
    records = result.records
    if not no_normalize:
        records = [normalizer.normalize_record(r) for r in records]
        for r in records:
            r.source_file = str(input_file)
    
    # Output
    if not output_file:
        output_file = input_file.with_suffix(f"_extracted.{output_format}")
    
    _write_output(records, output_file, output_format, include_raw)
    
    # Summary
    console.print(f"\n[green]Success![/green] Extracted {len(records)} records")
    console.print(f"Template: {template.metadata.name}")
    console.print(f"Output: {output_file}")
    
    if verbose and records:
        table = Table(title="Extracted Materials")
        table.add_column("Material", style="cyan")
        table.add_column("Substance", style="green")
        table.add_column("Weight (mg)", style="yellow", justify="right")
        table.add_column("Category", style="magenta")
        table.add_column("Confidence", style="blue", justify="right")
        
        for r in records[:20]:
            table.add_row(
                r.material[:50], r.substance[:30],
                f"{float(r.weight_mg):.4f}", r.category.value,
                f"{r.confidence:.2f}"
            )
        
        if len(records) > 20:
            table.add_row(f"... and {len(records) - 20} more", "", "", "", "")
        
        console.print(table)


def _detect_file_type(file_path: Path) -> SourceType:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return SourceType.PDF
    elif suffix in [".xlsx", ".xls"]:
        return SourceType.EXCEL
    elif suffix == ".csv":
        return SourceType.CSV
    return SourceType.UNKNOWN


def _write_output(records: list, output_file: Path, fmt: str, include_raw: bool) -> None:
    import csv
    import json
    
    if fmt == "csv":
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            if records:
                fieldnames = records[0].to_dict(include_raw=include_raw).keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in records:
                    writer.writerow(r.to_dict(include_raw=include_raw))
    elif fmt == "json":
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump([r.to_dict(include_raw=include_raw) for r in records], f, indent=2)
    else:
        raise ValueError(f"Unknown format: {fmt}")


if __name__ == "__main__":
    app()