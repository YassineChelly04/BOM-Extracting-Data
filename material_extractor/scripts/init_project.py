#!/usr/bin/env python3
"""Project initialization script."""
from __future__ import annotations

import argparse
import yaml
from pathlib import Path


def create_directories(dirs: list[Path]) -> None:
    """Create directories if they don't exist."""
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"Created: {d}")


def create_normalization_files(data_dir: Path) -> None:
    """Create default normalization YAML files."""
    
    # materials.yaml
    materials = {
        "Copper (Cu)": {"category": "Metal", "aliases": ["copper", "cu", "copper (cu)"]},
        "Nickel (Ni)": {"category": "Metal", "aliases": ["nickel", "ni", "nickel (ni)"]},
        "Gold (Au)": {"category": "Metal", "aliases": ["gold", "au", "gold (au)"]},
        "Silver (Ag)": {"category": "Metal", "aliases": ["silver", "ag", "silver (ag)"]},
        "Tin (Sn)": {"category": "Metal", "aliases": ["tin", "sn", "tin (sn)"]},
        "Zinc (Zn)": {"category": "Metal", "aliases": ["zinc", "zn", "zinc (zn)"]},
        "Lead (Pb)": {"category": "Metal", "aliases": ["lead", "pb", "lead (pb)"]},
        "Palladium (Pd)": {"category": "Metal", "aliases": ["palladium", "pd"]},
        "Iron (Fe)": {"category": "Metal", "aliases": ["iron", "fe"]},
        "Cobalt (Co)": {"category": "Metal", "aliases": ["cobalt", "co"]},
        "Chromium (Cr)": {"category": "Metal", "aliases": ["chromium", "cr"]},
        "Bismuth (Bi)": {"category": "Metal", "aliases": ["bismuth", "bi"]},
        "Aluminum (Al)": {"category": "Metal", "aliases": ["aluminum", "aluminium", "al"]},
        "Indium (In)": {"category": "Metal", "aliases": ["indium", "in"]},
        "Magnesium (Mg)": {"category": "Metal", "aliases": ["magnesium", "mg"]},
        "Silicon (Si)": {"category": "Metalloid", "aliases": ["silicon", "si"]},
        
        "Aluminum Oxide (Al2O3)": {"category": "Metal Oxide", "aliases": ["aluminum oxide", "al2o3", "aluminium oxide"]},
        "Silicon Dioxide (SiO2)": {"category": "Metal Oxide", "aliases": ["silicon dioxide", "sio2", "silica"]},
        "Fused Silica (SiO2)": {"category": "Metal Oxide", "aliases": ["fused silica", "silica fused"]},
        "Magnesium Oxide (MgO)": {"category": "Metal Oxide", "aliases": ["magnesium oxide", "mgo"]},
        "Copper Oxide (CuO)": {"category": "Metal Oxide", "aliases": ["copper oxide", "cuo"]},
        "Zinc Oxide (ZnO)": {"category": "Metal Oxide", "aliases": ["zinc oxide", "zno"]},
        "Barium Oxide (BaO)": {"category": "Metal Oxide", "aliases": ["barium oxide", "bao"]},
        "Calcium Oxide (CaO)": {"category": "Metal Oxide", "aliases": ["calcium oxide", "cao"]},
        "Tricobalt Tetraoxide (Co3O4)": {"category": "Metal Oxide", "aliases": ["tricobalt tetraoxide", "co3o4"]},
        "Manganese Dioxide (MnO2)": {"category": "Metal Oxide", "aliases": ["manganese dioxide", "mno2"]},
        "Antimony Trioxide (Sb2O3)": {"category": "Metal Oxide", "aliases": ["antimony trioxide", "diantimony trioxide", "sb2o3"]},
        "Strontium Oxide (SrO)": {"category": "Metal Oxide", "aliases": ["strontium oxide", "sro"]},
        "Anatase (TiO2)": {"category": "Metal Oxide", "aliases": ["anatase", "tio2"]},
        "Yttrium Oxide (Y2O3)": {"category": "Metal Oxide", "aliases": ["yttrium oxide", "y2o3"]},
        "Zirconium Dioxide (ZrO2)": {"category": "Metal Oxide", "aliases": ["zirconium dioxide", "zro2"]},
        "Sulphur Trioxide (SO3)": {"category": "Metal Oxide", "aliases": ["sulphur trioxide", "so3"]},
        "Ruthenium Oxide (RuO2)": {"category": "Metal Oxide", "aliases": ["ruthenium oxide", "ruo2"]},
        
        "Barium Titanate (BaTiO3)": {"category": "Ceramic", "aliases": ["barium titanate", "batio3"]},
        "Calcium Zirconate (CaZrO3)": {"category": "Ceramic", "aliases": ["calcium zirconate", "cazro3"]},
        
        "Barium Sulfate (BaSO4)": {"category": "Salt", "aliases": ["barium sulfate", "baso4"]},
        
        "Gallium Nitride (GaN)": {"category": "Compound Semiconductor", "aliases": ["gallium nitride", "gan"]},
        "Indium Nitride (InN)": {"category": "Compound Semiconductor", "aliases": ["indium nitride", "inn"]},
        "Gallium Arsenide (GaAs)": {"category": "Compound Semiconductor", "aliases": ["gallium arsenide", "gaas"]},
        "Gallium Phosphide (GaP)": {"category": "Compound Semiconductor", "aliases": ["gallium phosphide", "gap"]},
        
        "Epoxy Resin": {"category": "Polymer", "aliases": ["epoxy", "epoxy resin"]},
        "Epoxy Resin (Bisphenol A DGEBA)": {"category": "Polymer", "aliases": ["bisphenol a diglycidyl ether resin"]},
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
        
        "Solvent (Aromatic Naphtha)": {"category": "Solvent", "aliases": ["eavy aromatic solvent naphth", "naphtha"]},
        
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
    
    with open(data_dir / "materials.yaml", "w") as f:
        yaml.dump(materials, f, default_flow_style=False, sort_keys=True)
    
    # substances.yaml
    substances = {
        "Copper (Cu)": {"aliases": ["cu", "copper"], "cas_number": "7440-50-8"},
        "Nickel (Ni)": {"aliases": ["ni", "nickel"], "cas_number": "7440-02-0"},
        "Gold (Au)": {"aliases": ["au", "gold"], "cas_number": "7440-57-5"},
        "Silver (Ag)": {"aliases": ["ag", "silver"], "cas_number": "7440-22-4"},
        "Tin (Sn)": {"aliases": ["sn", "tin"], "cas_number": "7440-31-5"},
        "Zinc (Zn)": {"aliases": ["zn", "zinc"], "cas_number": "7440-66-6"},
        "Lead (Pb)": {"aliases": ["pb", "lead"], "cas_number": "7439-92-1"},
        "Palladium (Pd)": {"aliases": ["pd", "palladium"], "cas_number": "7440-05-3"},
    }
    
    with open(data_dir / "substances.yaml", "w") as f:
        yaml.dump(substances, f, default_flow_style=False, sort_keys=True)
    
    print(f"Created normalization files in {data_dir}")


def create_template_files(templates_dir: Path) -> None:
    """Create default template YAML files."""
    
    pdf_dir = templates_dir / "pdf"
    excel_dir = templates_dir / "excel"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    excel_dir.mkdir(parents=True, exist_ok=True)
    
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
    
    for filename, data in templates.items():
        with open(pdf_dir / filename, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    print(f"Created template files in {templates_dir}")


def init_project(
    data_dir: Path = Path("data"),
    templates_dir: Path = Path("templates"),
    output_dir: Path = Path("output"),
    force: bool = False
) -> None:
    """Initialize the project structure."""
    
    # Create directories
    dirs = [
        data_dir / "normalization",
        templates_dir / "pdf",
        templates_dir / "excel",
        output_dir / "individual",
        output_dir / "aggregated",
    ]
    
    create_directories(dirs)
    
    # Create normalization files
    norm_dir = data_dir / "normalization"
    if force or not (norm_dir / "materials.yaml").exists():
        create_normalization_files(norm_dir)
    else:
        print(f"Normalization files already exist (use --force to overwrite)")
    
    # Create template files
    if force or not (templates_dir / "pdf" / "molex_bom.yaml").exists():
        create_template_files(templates_dir)
    else:
        print(f"Template files already exist (use --force to overwrite)")
    
    # Create .gitkeep files
    for d in [output_dir / "individual", output_dir / "aggregated"]:
        (d / ".gitkeep").touch()
    
    print("\n[OK] Project initialized successfully!")
    print(f"  Data: {data_dir}")
    print(f"  Templates: {templates_dir}")
    print(f"  Output: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Initialize Material Extractor project")
    parser.add_argument("--data-dir", type=Path, default=Path("data"), help="Data directory")
    parser.add_argument("--templates-dir", type=Path, default=Path("templates"), help="Templates directory")
    parser.add_argument("--output-dir", type=Path, default=Path("output"), help="Output directory")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    
    args = parser.parse_args()
    init_project(args.data_dir, args.templates_dir, args.output_dir, args.force)


if __name__ == "__main__":
    main()