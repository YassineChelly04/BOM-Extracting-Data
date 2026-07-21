"""List templates command."""
from __future__ import annotations

import typer
from pathlib import Path

from material_extractor.templates.registry import TemplateManager

app = typer.Typer(name="list-templates", help="List available templates")


def _find_templates_dir(path: Path | None) -> Path | None:
    if path and path.exists():
        return path
    for p in (Path("templates"), Path("material_extractor/templates")):
        if p.exists():
            return p
    return path


@app.command()
def list_templates_cmd(
    template_dir: Path = typer.Option(None, "--templates", "-t", help="Template directory"),
    show_details: bool = typer.Option(False, "--details", "-d", help="Show template details"),
    enabled_only: bool = typer.Option(False, "--enabled-only", help="Show only enabled templates"),
):
    """List all registered templates."""
    
    manager = TemplateManager(templates_dir=_find_templates_dir(template_dir))
    
    templates = manager.get_enabled_templates() if enabled_only else list(manager.registry.templates.values())
    
    if not templates:
        typer.echo("No templates found.")
        return
    
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    table = Table(title="Available Templates")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Version", justify="center")
    table.add_column("Type", justify="center")
    table.add_column("Method", justify="center")
    table.add_column("Priority", justify="right")
    table.add_column("Enabled", justify="center")
    
    for t in sorted(templates, key=lambda x: (-x.metadata.priority, x.metadata.template_id)):
        table.add_row(
            t.metadata.template_id,
            t.metadata.name,
            t.metadata.version,
            t.metadata.source_type.value,
            t.metadata.detection_method.value,
            str(t.metadata.priority),
            "✓" if t.metadata.enabled else "✗"
        )
    
    console.print(table)
    
    if show_details:
        for t in templates:
            console.print(f"\n[bold]{t.metadata.template_id}[/bold] - {t.metadata.name}")
            console.print(f"  Description: {t.metadata.description}")
            console.print(f"  Author: {t.metadata.author}")
            console.print(f"  Keywords: {', '.join(t.metadata.detection_keywords) if t.metadata.detection_keywords else 'N/A'}")
            console.print(f"  Patterns: {', '.join(t.metadata.detection_patterns) if t.metadata.detection_patterns else 'N/A'}")
            console.print(f"  Page indices: {t.metadata.page_indices}")
            if t.extraction:
                console.print(f"  Extraction: {t.extraction}")


@app.command()
def show(
    template_id: str = typer.Argument(..., help="Template ID to show"),
    template_dir: Path = typer.Option(None, "--templates", "-t", help="Template directory"),
):
    """Show detailed template configuration."""
    
    manager = TemplateManager(templates_dir=_find_templates_dir(template_dir))
    
    template = manager.get_template(template_id)
    if not template:
        typer.echo(f"Template not found: {template_id}")
        raise typer.Exit(1)
    
    import json
    typer.echo(json.dumps(template.model_dump(mode="json"), indent=2, default=str))


@app.command()
def export(
    template_id: str = typer.Argument(..., help="Template ID to export"),
    output_dir: Path = typer.Option(Path("templates"), "--output", "-o", help="Output directory"),
    template_dir: Path = typer.Option(None, "--templates", "-t", help="Source template directory"),
):
    """Export template to YAML file."""
    
    manager = TemplateManager(templates_dir=_find_templates_dir(template_dir))
    
    if manager.export_template_yaml(template_id, output_dir / f"{template_id}.yaml"):
        typer.echo(f"Exported {template_id} to {output_dir / f'{template_id}.yaml'}")
    else:
        typer.echo(f"Template not found: {template_id}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()