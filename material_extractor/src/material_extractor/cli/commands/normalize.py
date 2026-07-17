"""Normalize command - normalize material names."""
from __future__ import annotations

import typer
from pathlib import Path
import pandas as pd

from material_extractor.normalization import get_normalizer
from material_extractor.config import get_settings

app = typer.Typer(name="normalize", help="Normalize material names")


@app.command()
def normalize_cmd(
    input_file: Path = typer.Argument(..., help="Input CSV file with materials"),
    output_file: Path = typer.Option(None, "--output", "-o", help="Output CSV file"),
    material_col: str = typer.Option("material", "--material-col", help="Material column name"),
    substance_col: str = typer.Option("substance", "--substance-col", help="Substance column name"),
    add_category: bool = typer.Option(True, "--add-category/--no-category", help="Add category column"),
    fuzzy_threshold: float = typer.Option(0.85, "--threshold", help="Fuzzy match threshold"),
):
    """Normalize material names in CSV file."""
    
    normalizer = get_normalizer()
    normalizer.config.fuzzy_threshold = fuzzy_threshold
    
    df = pd.read_csv(input_file)
    
    if material_col not in df.columns:
        typer.echo(f"Column '{material_col}' not found. Available: {list(df.columns)}")
        raise typer.Exit(1)
    
    # Normalize each row
    results = []
    for _, row in df.iterrows():
        mat = str(row.get(material_col, "")).strip()
        sub = str(row.get(substance_col, "")).strip() if substance_col in df.columns else ""
        
        if not mat:
            results.append({"normalized": "", "category": "", "confidence": 0.0, "method": ""})
            continue
        
        result = normalizer.normalize(mat, sub)
        results.append({
            "normalized": result.normalized,
            "category": result.category.value,
            "confidence": result.confidence,
            "method": result.method.value,
            "matched_alias": result.matched_alias
        })
    
    # Add results to dataframe
    for col in ["normalized", "category", "confidence", "method", "matched_alias"]:
        df[f"norm_{col}"] = [r[col] for r in results]
    
    # Output
    if not output_file:
        output_file = input_file.with_stem(input_file.stem + "_normalized")
    
    df.to_csv(output_file, index=False)
    
    # Stats
    from rich.console import Console
    console = Console()
    console.print(f"Normalized {len(df)} records")
    console.print(f"Output: {output_file}")
    
    # Method distribution
    method_counts = df["norm_method"].value_counts()
    console.print("\nNormalization methods:")
    for method, count in method_counts.items():
        console.print(f"  {method}: {count}")
    
    # Low confidence
    low_conf = df[df["norm_confidence"] < 0.8]
    if len(low_conf) > 0:
        console.print(f"\n[yellow]Warning: {len(low_conf)} records with confidence < 0.8[/yellow]")
        for _, row in low_conf.head(10).iterrows():
            console.print(f"  {row[material_col]} -> {row['norm_normalized']} ({row['norm_confidence']:.2f})")


@app.command()
def add_material(
    name: str = typer.Argument(..., help="Normalized material name"),
    category: str = typer.Argument(..., help="Material category"),
    aliases: str = typer.Option("", "--aliases", "-a", help="Comma-separated aliases"),
    data_dir: Path = typer.Option(None, "--data-dir", help="Data directory"),
):
    """Add new material to normalization database."""
    from material_extractor.models import MaterialCategory
    
    normalizer = get_normalizer()
    
    try:
        cat = MaterialCategory(category)
    except ValueError:
        typer.echo(f"Invalid category: {category}")
        typer.echo(f"Valid: {[c.value for c in MaterialCategory]}")
        raise typer.Exit(1)
    
    alias_list = [a.strip() for a in aliases.split(",") if a.strip()] if aliases else []
    
    normalizer.add_material(name, alias_list, cat)
    
    # Save
    if data_dir:
        normalizer.data_dir = data_dir
    normalizer.save_material(name, alias_list, cat)
    
    typer.echo(f"Added material: {name}")
    typer.echo(f"  Category: {cat.value}")
    typer.echo(f"  Aliases: {alias_list}")


@app.command()
def stats():
    """Show normalization database statistics."""
    normalizer = get_normalizer()
    normalizer.load()
    
    s = normalizer.stats()
    
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    table = Table(title="Normalization Database Stats")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="green", justify="right")
    
    table.add_row("Materials", str(s["materials"]))
    table.add_row("Substances", str(s["substances"]))
    table.add_row("Total Aliases", str(s["total_aliases"]))
    
    console.print(table)


if __name__ == "__main__":
    app()