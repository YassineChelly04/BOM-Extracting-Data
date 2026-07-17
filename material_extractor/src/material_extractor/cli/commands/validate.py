"""Validate command - validate extracted data."""
from __future__ import annotations

import typer
from pathlib import Path
import pandas as pd

from material_extractor.models import MaterialCategory

app = typer.Typer(name="validate", help="Validate extraction output")


@app.command()
def validate_cmd(
    input_file: Path = typer.Argument(..., help="Input CSV file to validate"),
    check_weights: bool = typer.Option(True, "--weights/--no-weights", help="Check weight values"),
    check_categories: bool = typer.Option(True, "--categories/--no-categories", help="Check categories"),
    check_duplicates: bool = typer.Option(True, "--duplicates/--no-duplicates", help="Check duplicates"),
    output_report: Path = typer.Option(None, "--report", "-r", help="Validation report output"),
):
    """Validate extraction output CSV."""
    
    df = pd.read_csv(input_file)
    
    issues = []
    warnings = []
    
    # Check required columns
    required = ["material", "weight_mg"]
    for col in required:
        if col not in df.columns:
            issues.append(f"Missing required column: {col}")
    
    if issues:
        _print_results(issues, warnings)
        raise typer.Exit(1)
    
    # Check for empty materials
    empty_mats = df[df["material"].isna() | (df["material"].str.strip() == "")]
    if len(empty_mats) > 0:
        issues.append(f"Found {len(empty_mats)} rows with empty material name")
    
    # Check weights
    if check_weights:
        neg_weights = df[df["weight_mg"] < 0]
        if len(neg_weights) > 0:
            issues.append(f"Found {len(neg_weights)} rows with negative weight")
        
        zero_weights = df[df["weight_mg"] == 0]
        if len(zero_weights) > 0:
            warnings.append(f"Found {len(zero_weights)} rows with zero weight")
        
        # Check for non-numeric
        try:
            pd.to_numeric(df["weight_mg"])
        except Exception:
            issues.append("Weight column contains non-numeric values")
    
    # Check categories
    if check_categories and "category" in df.columns:
        valid_cats = [c.value for c in MaterialCategory]
        invalid_cats = df[~df["category"].isin(valid_cats)]
        if len(invalid_cats) > 0:
            warnings.append(f"Found {len(invalid_cats)} rows with invalid category")
    
    # Check duplicates
    if check_duplicates:
        dup_cols = ["material"]
        if "substance" in df.columns:
            dup_cols.append("substance")
        if "source_file" in df.columns:
            dup_cols.append("source_file")
        
        dupes = df.duplicated(subset=dup_cols, keep=False)
        if dupes.any():
            warnings.append(f"Found {dupes.sum()} potentially duplicate rows")
    
    _print_results(issues, warnings)
    
    if output_report:
        report = {
            "file": str(input_file),
            "rows": len(df),
            "columns": list(df.columns),
            "issues": issues,
            "warnings": warnings,
            "passed": len(issues) == 0
        }
        import json
        with open(output_report, "w") as f:
            json.dump(report, f, indent=2)
        typer.echo(f"\nReport saved to: {output_report}")
    
    if issues:
        raise typer.Exit(1)


@app.command()
def validate_dir(
    input_dir: Path = typer.Argument(..., help="Directory with CSV files"),
    pattern: str = typer.Option("*.csv", "--pattern", "-p", help="File pattern"),
):
    """Validate all CSV files in directory."""
    
    files = list(input_dir.glob(pattern))
    if not files:
        typer.echo(f"No files matching {pattern} in {input_dir}")
        raise typer.Exit(1)
    
    all_passed = True
    
    for f in files:
        typer.echo(f"\nValidating: {f.name}")
        try:
            df = pd.read_csv(f)
            # Quick checks
            if "material" not in df.columns or "weight_mg" not in df.columns:
                typer.echo("  [red]FAIL[/red] - Missing required columns")
                all_passed = False
                continue
            
            if df["material"].isna().any():
                typer.echo("  [yellow]WARN[/yellow] - Empty material names")
            
            if (df["weight_mg"] < 0).any():
                typer.echo("  [red]FAIL[/red] - Negative weights")
                all_passed = False
                continue
            
            typer.echo(f"  [green]OK[/green] - {len(df)} records")
        except Exception as e:
            typer.echo(f"  [red]ERROR[/red] - {e}")
            all_passed = False
    
    typer.echo(f"\n{'All passed!' if all_passed else 'Some failed!'}")
    if not all_passed:
        raise typer.Exit(1)


def _print_results(issues: list, warnings: list) -> None:
    from rich.console import Console
    console = Console()
    
    if issues:
        console.print("\n[red]Issues:[/red]")
        for i in issues:
            console.print(f"  ✗ {i}")
    
    if warnings:
        console.print("\n[yellow]Warnings:[/yellow]")
        for w in warnings:
            console.print(f"  ⚠ {w}")
    
    if not issues and not warnings:
        console.print("\n[green]All checks passed![/green]")


if __name__ == "__main__":
    app()