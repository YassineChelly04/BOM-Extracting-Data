"""
generate_all_materials.py — Aggregate all materials across all template output CSVs.

Reads template1_output.csv .. template13_output.csv from the template_outputs folder,
normalizes material names, categorizes them, and writes a summary CSV.

Usage:
    python generate_all_materials.py
"""
import csv
import os
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "template_outputs")

NORM = {
    "copper": "Copper (Cu)", "cu": "Copper (Cu)", "copper (cu)": "Copper (Cu)",
    "copper(cu)": "Copper (Cu)",
    "nickel": "Nickel (Ni)", "ni": "Nickel (Ni)", "nickel (ni)": "Nickel (Ni)",
    "nickel(ni)": "Nickel (Ni)",
    "gold": "Gold (Au)", "au": "Gold (Au)", "gold (au)": "Gold (Au)",
    "gold(au)": "Gold (Au)",
    "silver": "Silver (Ag)", "ag": "Silver (Ag)", "silver (ag)": "Silver (Ag)",
    "tin": "Tin (Sn)", "sn": "Tin (Sn)", "tin (sn)": "Tin (Sn)",
    "zinc": "Zinc (Zn)", "zinc (metal)": "Zinc (Zn)",
    "lead": "Lead (Pb)", "lead (pb)": "Lead (Pb)",
    "palladium": "Palladium (Pd)", "pd": "Palladium (Pd)",
    "palladium (pd)": "Palladium (Pd)",
    "iron": "Iron (Fe)", "cobalt": "Cobalt (Co)",
    "chromium": "Chromium (Cr)", "bismuth": "Bismuth (Bi)",
    "bismuth (bi)": "Bismuth (Bi)",
    "aluminium": "Aluminum (Al)", "al": "Aluminum (Al)", "aluminum": "Aluminum (Al)",
    "indium": "Indium (In)", "in": "Indium (In)",
    "magnesium": "Magnesium (Mg)", "magnesium (mg)": "Magnesium (Mg)",
    "aluminum oxide": "Aluminum Oxide (Al2O3)", "al2o3": "Aluminum Oxide (Al2O3)",
    "aluminium oxide": "Aluminum Oxide (Al2O3)",
    "aluminum oxide(al2o3)": "Aluminum Oxide (Al2O3)",
    "silicon dioxide": "Silicon Dioxide (SiO2)", "sio2": "Silicon Dioxide (SiO2)",
    "silica": "Silicon Dioxide (SiO2)", "silica fused": "Fused Silica (SiO2)",
    "fused silica": "Fused Silica (SiO2)",
    "magnesium oxide": "Magnesium Oxide (MgO)", "mgo": "Magnesium Oxide (MgO)",
    "copper oxide": "Copper Oxide (CuO)", "zinc oxide": "Zinc Oxide (ZnO)",
    "barium oxide": "Barium Oxide (BaO)", "calcium oxide": "Calcium Oxide (CaO)",
    "tricobalt tetraoxide": "Tricobalt Tetraoxide (Co3O4)",
    "manganese dioxide": "Manganese Dioxide (MnO2)",
    "diantimony trioxide": "Antimony Trioxide (Sb2O3)",
    "strontium oxide": "Strontium Oxide (SrO)", "anatase": "Anatase (TiO2)",
    "yttrium oxide": "Yttrium Oxide (Y2O3)",
    "zirconium dioxide": "Zirconium Dioxide (ZrO2)",
    "sulphur trioxide": "Sulphur Trioxide (SO3)",
    "ruthenium oxide": "Ruthenium Oxide (RuO2)", "ruo2": "Ruthenium Oxide (RuO2)",
    "barium titanate(iv)": "Barium Titanate (BaTiO3)",
    "barium titanate": "Barium Titanate (BaTiO3)",
    "barium sulfate": "Barium Sulfate (BaSO4)",
    "gallium nitride(gan)": "Gallium Nitride (GaN)",
    "indium nitride(inn)": "Indium Nitride (InN)",
    "gaas": "Gallium Arsenide (GaAs)", "gap": "Gallium Phosphide (GaP)",
    "calcium zirconate": "Calcium Zirconate (CaZrO3)",
    "epoxy": "Epoxy Resin", "epoxy resin": "Epoxy Resin",
    "bisphenol a diglycidyl ether resin": "Epoxy Resin (Bisphenol A DGEBA)",
    "bisphenol a-bisphenol a diglycidyl ether polymer":
        "Epoxy Resin (Bisphenol A Polymer)",
    "o-cresol, formaldehyde, epichlorohydrin polymer":
        "Epoxy Resin (o-Cresol Novolac)",
    "formaldehyde, polymer with (chloromethyl)oxirane and phenol":
        "Epoxy Resin (Phenol-Formaldehyde)",
    "epidian": "Epoxy Resin (Epidian)", "triglycidyl isocyanurate": "Epoxy Resin (TGIC)",
    "tetrahydrophthalic anhydride": "Curing Agent (THPA)",
    "glass fiber": "Glass Fiber", "fiber class": "Glass Fiber",
    "gf-fibre": "Glass Fiber",
    "glass, oxide": "Glass Oxide",
    "glass frit( contain pb": "Lead-Containing Glass Frit",
    "glass (pb free) (contains bismuth, silicon & boron)":
        "Lead-Free Glass (Bi-Si-B)",
    "lead silicate [glass]": "Lead Silicate Glass",
    "lcp": "Liquid Crystal Polymer (LCP)", "carbon black": "Carbon Black",
    "poly(isobornyl) methacrylate": "Polymer (PIBMA)",
    "polysiloxanes": "Polymer (Polysiloxanes)",
    "further additives, not to declare": "Additives (Undisclosed)",
    "trade secret": "Additives (Trade Secret)",
    "doped silicon": "Doped Silicon (Si)", "silicon (si)": "Silicon (Si)",
    "eavy aromatic solvent naphth": "Solvent (Aromatic Naphtha)",
    "naphtha": "Solvent (Naphtha)",
    "miscellaneous": "Miscellaneous",
    "electrode paste": "Electrode Paste (Ni)",
    "base metal": "Base Metal (Cu)",
    "under layer": "Under Layer (Ni)",
    "finish plating": "Finish Plating (Sn)",
    "aluminium hydroxide (al(oh)3)": "Aluminum Hydroxide (Al(OH)3)",
    "pigment 1": "Pigment (Unknown 1)", "pigment 2": "Pigment (Unknown 2)",
    "chlorine": "Chlorine (Cl)", "phosphorus": "Phosphorus (P)",
}

CATEGORY = {
    "Copper (Cu)": "Metal", "Nickel (Ni)": "Metal", "Gold (Au)": "Metal",
    "Silver (Ag)": "Metal", "Tin (Sn)": "Metal", "Zinc (Zn)": "Metal",
    "Lead (Pb)": "Metal", "Palladium (Pd)": "Metal", "Iron (Fe)": "Metal",
    "Cobalt (Co)": "Metal", "Chromium (Cr)": "Metal", "Bismuth (Bi)": "Metal",
    "Aluminum (Al)": "Metal", "Indium (In)": "Metal", "Magnesium (Mg)": "Metal",
    "Silicon (Si)": "Metalloid", "Doped Silicon (Si)": "Metalloid",
    "Aluminum Oxide (Al2O3)": "Metal Oxide", "Silicon Dioxide (SiO2)": "Metal Oxide",
    "Fused Silica (SiO2)": "Metal Oxide", "Magnesium Oxide (MgO)": "Metal Oxide",
    "Copper Oxide (CuO)": "Metal Oxide", "Zinc Oxide (ZnO)": "Metal Oxide",
    "Barium Oxide (BaO)": "Metal Oxide", "Calcium Oxide (CaO)": "Metal Oxide",
    "Tricobalt Tetraoxide (Co3O4)": "Metal Oxide",
    "Manganese Dioxide (MnO2)": "Metal Oxide",
    "Antimony Trioxide (Sb2O3)": "Metal Oxide",
    "Strontium Oxide (SrO)": "Metal Oxide",
    "Anatase (TiO2)": "Metal Oxide", "Yttrium Oxide (Y2O3)": "Metal Oxide",
    "Zirconium Dioxide (ZrO2)": "Metal Oxide",
    "Sulphur Trioxide (SO3)": "Metal Oxide",
    "Ruthenium Oxide (RuO2)": "Metal Oxide",
    "Barium Titanate (BaTiO3)": "Ceramic",
    "Calcium Zirconate (CaZrO3)": "Ceramic",
    "Barium Sulfate (BaSO4)": "Salt",
    "Gallium Nitride (GaN)": "Compound Semiconductor",
    "Indium Nitride (InN)": "Compound Semiconductor",
    "Gallium Arsenide (GaAs)": "Compound Semiconductor",
    "Gallium Phosphide (GaP)": "Compound Semiconductor",
    "Epoxy Resin": "Polymer",
    "Epoxy Resin (Bisphenol A DGEBA)": "Polymer",
    "Epoxy Resin (Bisphenol A Polymer)": "Polymer",
    "Epoxy Resin (o-Cresol Novolac)": "Polymer",
    "Epoxy Resin (Phenol-Formaldehyde)": "Polymer",
    "Epoxy Resin (Epidian)": "Polymer",
    "Epoxy Resin (TGIC)": "Polymer",
    "Curing Agent (THPA)": "Polymer Additive",
    "Liquid Crystal Polymer (LCP)": "Polymer",
    "Polymer (PIBMA)": "Polymer",
    "Polymer (Polysiloxanes)": "Polymer",
    "Glass Fiber": "Composite", "Glass Oxide": "Glass",
    "Lead-Containing Glass Frit": "Glass",
    "Lead-Free Glass (Bi-Si-B)": "Glass",
    "Lead Silicate Glass": "Glass",
    "Carbon Black": "Filler",
    "Aluminum Hydroxide (Al(OH)3)": "Hydroxide",
    "Chlorine (Cl)": "Halogen", "Phosphorus (P)": "Non-Metal",
    "Solvent (Aromatic Naphtha)": "Solvent", "Solvent (Naphtha)": "Solvent",
    "Additives (Undisclosed)": "Additive",
    "Additives (Trade Secret)": "Additive",
    "Miscellaneous": "Other", "Electrode Paste (Ni)": "Paste",
    "Base Metal (Cu)": "Metal", "Under Layer (Ni)": "Plating",
    "Finish Plating (Sn)": "Plating",
    "Pigment (Unknown 1)": "Pigment", "Pigment (Unknown 2)": "Pigment",
}


def main():
    mat_templates = defaultdict(set)
    mat_weights = defaultdict(float)

    for i in range(1, 14):
        fname = os.path.join(OUTPUT_DIR, f"template{i}_output.csv")
        if not os.path.exists(fname):
            continue
        with open(fname, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw = row.get("material", "").strip()
                if not raw:
                    continue
                key = NORM.get(raw.lower(), raw)
                mat_templates[key].add(i)
                try:
                    mat_weights[key] += float(row.get("weight_mg", 0))
                except (ValueError, TypeError):
                    pass

    sorted_mats = sorted(
        mat_templates.items(),
        key=lambda x: (CATEGORY.get(x[0], "ZZZ"), x[0]),
    )

    out_path = os.path.join(OUTPUT_DIR, "all_materials_across_templates.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Material", "Category", "Total Weight (mg)",
            "Found In Templates", "Template Count",
        ])
        for mat, temps in sorted_mats:
            cat = CATEGORY.get(mat, "Unknown")
            tlist = ", ".join(f"T{i}" for i in sorted(temps))
            writer.writerow([
                mat, cat, round(mat_weights[mat], 6), tlist, len(temps),
            ])

    print(f"Wrote {len(sorted_mats)} unique materials -> {out_path}")

    cats = defaultdict(list)
    for mat, _temps in sorted_mats:
        cats[CATEGORY.get(mat, "Unknown")].append(mat)
    for cat in sorted(cats.keys()):
        print(f"  {cat} ({len(cats[cat])}):")
        for m in cats[cat]:
            print(f"    - {m}")


if __name__ == "__main__":
    main()
