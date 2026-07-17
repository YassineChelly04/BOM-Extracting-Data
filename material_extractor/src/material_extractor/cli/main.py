"""Main CLI entry point."""
from __future__ import annotations

import typer
from typing import Optional
from pathlib import Path

from material_extractor.cli.commands import extract, normalize, validate, list_templates
from material_extractor.config import get_settings

app = typer.Typer(
    name="material-extractor",
    help="Production-ready material declaration extraction and normalization system",
    add_completion=False,
)

# Add subcommands
app.add_typer(extract.app, name="extract")
app.add_typer(normalize.app, name="normalize")
app.add_typer(validate.app, name="validate")
app.add_typer(list_templates.app, name="templates")


@app.callback()
def main(
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Quiet mode"),
):
    """Material Extractor - Extract and normalize material declarations from BOM/MD documents."""
    settings = get_settings()
    
    if verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)


@app.command()
def init(
    data_dir: Path = typer.Option(Path("data"), "--data-dir", help="Data directory"),
    templates_dir: Path = typer.Option(Path("templates"), "--templates-dir", help="Templates directory"),
    output_dir: Path = typer.Option(Path("output"), "--output-dir", help="Output directory"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing"),
):
    """Initialize project structure and default templates."""
    
    dirs = [
        data_dir / "normalization",
        templates_dir / "pdf",
        templates_dir / "excel",
        output_dir / "individual",
        output_dir / "aggregated",
    ]
    
    for d in dirs:
        if d.exists() and not force:
            typer.echo(f"Directory exists (use --force): {d}")
            continue
        d.mkdir(parents=True, exist_ok=True)
        typer.echo(f"Created: {d}")
    
    # Create default normalization files
    _create_default_normalization(data_dir / "normalization")
    
    # Create default templates
    _create_default_templates(templates_dir)
    
    typer.echo("\n✓ Project initialized!")
    typer.echo(f"  Data: {data_dir}")
    typer.echo(f"  Templates: {templates_dir}")
    typer.echo(f"  Output: {output_dir}")


def _create_default_normalization(data_dir: Path):
    """Create default normalization YAML files."""
    
    # materials.yaml
    materials = {
        "Copper (Cu)": {"category": "Metal", "aliases": ["copper", "cu", "copper (cu)", "copper cu"]},
        "Nickel (Ni)": {"category": "Metal", "aliases": ["nickel", "ni", "nickel (ni)", "nickel ni"]},
        "Gold (Au)": {"category": "Metal", "aliases": ["gold", "au", "gold (au)", "gold au"]},
        "Silver (Ag)": {"category": "Metal", "aliases": ["silver", "ag", "silver (ag)", "silver ag"]},
        "Tin (Sn)": {"category": "Metal", "aliases": ["tin", "sn", "tin (sn)", "tin sn"]},
        "Zinc (Zn)": {"category": "Metal", "aliases": ["zinc", "zn", "zinc (zn)", "zinc zn"]},
        "Lead (Pb)": {"category": "Metal", "aliases": ["lead", "pb", "lead (pb)", "lead pb"]},
        "Palladium (Pd)": {"category": "Metal", "aliases": ["palladium", "pd", "palladium (pd)"]},
        "Iron (Fe)": {"category": "Metal", "aliases": ["iron", "fe", "iron (fe)"]},
        "Cobalt (Co)": {"category": "Metal", "aliases": ["cobalt", "co", "cobalt (co)"]},
        "Chromium (Cr)": {"category": "Metal", "aliases": ["chromium", "cr", "chromium (cr)"]},
        "Bismuth (Bi)": {"category": "Metal", "aliases": ["bismuth", "bi", "bismuth (bi)"]},
        "Aluminum (Al)": {"category": "Metal", "aliases": ["aluminum", "aluminium", "al", "aluminum (al)"]},
        "Indium (In)": {"category": "Metal", "aliases": ["indium", "in", "indium (in)"]},
        "Magnesium (Mg)": {"category": "Metal", "aliases": ["magnesium", "mg", "magnesium (mg)"]},
        "Silicon (Si)": {"category": "Metalloid", "aliases": ["silicon", "si", "silicon (si)"]},
        
        "Aluminum Oxide (Al2O3)": {"category": "Metal Oxide", "aliases": ["aluminum oxide", "al2o3", "aluminium oxide", "aluminum oxide (al2o3)"]},
        "Silicon Dioxide (SiO2)": {"category": "Metal Oxide", "aliases": ["silicon dioxide", "sio2", "silica", "silicon dioxide (sio2)"]},
        "Fused Silica (SiO2)": {"category": "Metal Oxide", "aliases": ["fused silica", "silica fused", "fused silica (sio2)"]},
        "Magnesium Oxide (MgO)": {"category": "Metal Oxide", "aliases": ["magnesium oxide", "mgo", "magnesium oxide (mgo)"]},
        "Copper Oxide (CuO)": {"category": "Metal Oxide", "aliases": ["copper oxide", "cuo"]},
        "Zinc Oxide (ZnO)": {"category": "Metal Oxide", "aliases": ["zinc oxide", "zno"]},
        "Barium Oxide (BaO)": {"category": "Metal Oxide", "aliases": ["barium oxide", "bao"]},
        "Calcium Oxide (CaO)": {"category": "Metal Oxide", "aliases": ["calcium oxide", "cao"]},
        "Tricobalt Tetraoxide (Co3O4)": {"category": "Metal Oxide", "aliases": ["tricobalt tetraoxide", "co3o4"]},
        "Manganese Dioxide (MnO2)": {"category": "Metal Oxide", "aliases": ["manganese dioxide", "mno2"]},
        "Antimony Trioxide (Sb2O3)": {"category": "Metal Oxide", "aliases": ["antimony trioxide", "diantimony trioxide", "sb2o3"]},
        "Strontium Oxide (SrO)": {"category": "Metal Oxide", "aliases": ["strontium oxide", "sro"]},
        "Anatase (TiO2)": {"category": "Metal Oxide", "aliases": ["anatase", "tio2", "titanium dioxide"]},
        "Yttrium Oxide (Y2O3)": {"category": "Metal Oxide", "aliases": ["yttrium oxide", "y2o3"]},
        "Zirconium Dioxide (ZrO2)": {"category": "Metal Oxide", "aliases": ["zirconium dioxide", "zro2"]},
        "Sulphur Trioxide (SO3)": {"category": "Metal Oxide", "aliases": ["sulphur trioxide", "so3"]},
        "Ruthenium Oxide (RuO2)": {"category": "Metal Oxide", "aliases": ["ruthenium oxide", "ruo2"]},
        
        "Barium Titanate (BaTiO3)": {"category": "Ceramic", "aliases": ["barium titanate", "batio3", "barium titanate(iv)"]},
        "Calcium Zirconate (CaZrO3)": {"category": "Ceramic", "aliases": ["calcium zirconate", "cazro3"]},
        
        "Barium Sulfate (BaSO4)": {"category": "Salt", "aliases": ["barium sulfate", "baso4"]},
        
        "Gallium Nitride (GaN)": {"category": "Compound Semiconductor", "aliases": ["gallium nitride", "gan", "gallium nitride(gan)"]},
        "Indium Nitride (InN)": {"category": "Compound Semiconductor", "aliases": ["indium nitride", "inn", "indium nitride(inn)"]},
        "Gallium Arsenide (GaAs)": {"category": "Compound Semiconductor", "aliases": ["gallium arsenide", "gaas"]},
        "Gallium Phosphide (GaP)": {"category": "Compound Semiconductor", "aliases": ["gallium phosphide", "gap"]},
        
        "Epoxy Resin": {"category": "Polymer", "aliases": ["epoxy", "epoxy resin", "epoxy resin (bisphenol a dgeba)"]},
        "Epoxy Resin (Bisphenol A DGEBA)": {"category": "Polymer", "aliases": ["bisphenol a diglycidyl ether resin", "bisphenol a-bisphenol a diglycidyl ether polymer"]},
        "Epoxy Resin (o-Cresol Novolac)": {"category": "Polymer", "aliases": ["o-cresol, formaldehyde, epichlorohydrin polymer"]},
        "Epoxy Resin (Phenol-Formaldehyde)": {"category": "Polymer", "aliases": ["formaldehyde, polymer with (chloromethyl)oxirane and phenol"]},
        "Epoxy Resin (TGIC)": {"category": "Polymer", "aliases": ["triglycidyl isocyanurate"]},
        "Liquid Crystal Polymer (LCP)": {"category": "Polymer", "aliases": ["lcp", "liquid crystal polymer"]},
        "Poly(isobornyl methacrylate) (PIBMA)": {"category": "Polymer", "aliases": ["poly(isobornyl) methacrylate", "pibma"]},
        "Polysiloxanes": {"category": "Polymer", "aliases": ["polysiloxanes"]},
        
        "Curing Agent (THPA)": {"category": "Polymer Additive", "aliases": ["tetrahydrophthalic anhydride", "thpa"]},
        
        "Glass Fiber": {"category": "Composite", "aliases": ["glass fiber", "fiber class", "gf-fibre"]},
        "Glass Oxide": {"category": "Glass", "aliases": ["glass, oxide", "glass oxide"]},
        "Lead-Containing Glass Frit": {"category": "Glass", "aliases": ["glass frit( contain pb", "lead silicate [glass]"]},
        "Lead-Free Glass (Bi-Si-B)": {"category": "Glass", "aliases": ["glass (pb free) (contains bismuth, silicon & boron)"]},
        
        "Carbon Black": {"category": "Filler", "aliases": ["carbon black"]},
        
        "Aluminum Hydroxide (Al(OH)3)": {"category": "Hydroxide", "aliases": ["aluminium hydroxide (al(oh)3)", "aluminum hydroxide"]},
        
        "Chlorine (Cl)": {"category": "Halogen", "aliases": ["chlorine", "cl"]},
        "Phosphorus (P)": {"category": "Non-Metal", "aliases": ["phosphorus", "p"]},
        
        "Solvent (Aromatic Naphtha)": {"category": "Solvent", "aliases": ["eavy aromatic solvent naphth", "naphtha", "solvent (aromatic naphtha)"]},
        
        "Additives (Trade Secret)": {"category": "Additive", "aliases": ["trade secret", "further additives, not to declare", "proprietary"]},
        "Additives (Undisclosed)": {"category": "Additive", "aliases": ["undisclosed", "miscellaneous"]},
        
        "Electrode Paste (Ni)": {"category": "Paste", "aliases": ["electrode paste", "electrode paste (ni)"]},
        "Base Metal (Cu)": {"category": "Metal", "aliases": ["base metal", "base metal (cu)"]},
        "Under Layer (Ni)": {"category": "Plating", "aliases": ["under layer", "underlayer", "under layer (ni)"]},
        "Finish Plating (Sn)": {"category": "Plating", "aliases": ["finish plating", "plating", "finish plating (sn)"]},
        
        "Pigment (Unknown 1)": {"category": "Pigment", "aliases": ["pigment 1"]},
        "Pigment (Unknown 2)": {"category": "Pigment", "aliases": ["pigment 2"]},
        
        "Doped Silicon (Si)": {"category": "Metalloid", "aliases": ["doped silicon", "doped silicon (si)"]},
    }
    
    import yaml
    with open(data_dir / "materials.yaml", "w") as f:
        yaml.dump(materials, f, default_flow_style=False, sort_keys=True)
    
    # substances.yaml
    substances = {
        "Copper (Cu)": {"aliases": ["cu", "copper"]},
        "Nickel (Ni)": {"aliases": ["ni", "nickel"]},
        "Gold (Au)": {"aliases": ["au", "gold"]},
        "Silver (Ag)": {"aliases": ["ag", "silver"]},
        "Tin (Sn)": {"aliases": ["sn", "tin"]},
        "Zinc (Zn)": {"aliases": ["zn", "zinc"]},
        "Lead (Pb)": {"aliases": ["pb", "lead"]},
        "Palladium (Pd)": {"aliases": ["pd", "palladium"]},
    }
    with open(data_dir / "substances.yaml", "w") as f:
        yaml.dump(substances, f, default_flow_style=False, sort_keys=True)
    
    # categories.yaml - not needed as categories are in materials


def _create_default_templates(templates_dir: Path):
    """Create default template YAML files."""
    
    pdf_dir = templates_dir / "pdf"
    excel_dir = templates_dir / "excel"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    excel_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a few example templates
    templates = {
        "molex_bom.yaml": {
            "metadata": {
                "template_id": "molex_bom",
                "name": "Molex/TE Connectivity BOM",
                "version": "1.0.0",
                "description": "Molex Annex 3 table format for MLCC materials with case sizes",
                "author": "Material Extractor Team",
                "source_type": "pdf",
                "page_indices": [1],
                "detection_method": "text_pattern",
                "detection_keywords": ["Homogeneous Level Weight", "Total Weight", "0402"],
                "header_keywords": ["Level", "Material", "Substance", "CAS"],
                "validation_rules": {"min_rows": 3, "min_cols": 5},
                "priority": 10,
                "enabled": True
            },
            "extraction": {
                "extractor_type": "pdf_table",
                "extractor_class": "MolexTemplateExtractor",
                "target_size": "0402",
                "skip_rows": ["Homogeneous Level Weight", "Total Weight"],
                "case_sizes_row": 1,
                "header_row": 2
            },
            "normalization": {},
            "output": {
                "fields": ["material", "substance", "weight_mg"],
                "include_raw": True
            }
        },
        "wurth_md.yaml": {
            "metadata": {
                "template_id": "wurth_md",
                "name": "Würth Elektronik Material Declaration",
                "version": "1.0.0",
                "description": "Würth WL-SMCW layout with Semi-Component breakdown",
                "author": "Material Extractor Team",
                "source_type": "pdf",
                "page_indices": [0],
                "detection_method": "text_pattern",
                "detection_keywords": ["Semi-Component", "Average mass [%]", "Würth Elektronik"],
                "header_keywords": ["Semi-Component", "Substance", "Average mass"],
                "validation_rules": {"min_rows": 2, "min_cols": 5},
                "priority": 10,
                "enabled": True
            },
            "extraction": {
                "extractor_type": "pdf_table",
                "extractor_class": "WurthTemplateExtractor",
                "material_table_index": 1,
                "part_table_index": 2
            },
            "normalization": {},
            "output": {
                "fields": ["material", "weight_mg"],
                "include_raw": True
            }
        },
        "molex_compliance.yaml": {
            "metadata": {
                "template_id": "molex_compliance",
                "name": "Molex Product Compliance Declaration",
                "version": "1.0.0",
                "description": "Molex compliance declaration with substance rows",
                "author": "Material Extractor Team",
                "source_type": "pdf",
                "page_indices": [0, 1],
                "detection_method": "text_pattern",
                "detection_keywords": ["Product Compliance Declaration", "molex", "Product Composition"],
                "header_keywords": ["Name", "Type", "CAS", "Mass"],
                "validation_rules": {"min_rows": 2, "min_cols": 5},
                "priority": 10,
                "enabled": True
            },
            "extraction": {
                "extractor_type": "pdf_table",
                "extractor_class": "MolexComplianceExtractor",
                "pages": [0, 1]
            },
            "normalization": {},
            "output": {
                "fields": ["material", "substance", "weight_mg"],
                "include_raw": True
            }
        }
    }
    
    import yaml
    for filename, data in templates.items():
        with open(pdf_dir / filename, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)


if __name__ == "__main__":
    app()