/**
 * Criticality reference tables.
 *
 * Each extracted material is mapped to the element that carries its value or its
 * risk, then classified against two published critical-raw-material lists plus a
 * hazard list. Sources are named per material so the dashboard can show *why*
 * something was flagged rather than asserting it.
 *
 *   EU  — EU Critical Raw Materials Act, 2023 CRM list
 *   DOE — US DOE Critical Materials Assessment, 2023
 *   PM  — precious metal (not on either CRM list, but the dominant value carrier)
 *
 * These tables are the auditable part of the decision. Edit them here.
 */

export const CRM_LIST_LABEL = "EU CRM 2023 · US DOE 2023";

/** Value / risk carrier per extracted material name. */
const ELEMENT = {
  "Gold (Au)": "Au",
  "Silver (Ag)": "Ag",
  "Palladium (Pd)": "Pd",
  "Ruthenium Oxide (RuO2)": "Ru",
  "Copper (Cu)": "Cu",
  "Base Metal (Cu)": "Cu",
  "Copper Oxide (CuO)": "Cu",
  "Nickel (Ni)": "Ni",
  "Electrode Paste (Ni)": "Ni",
  "Under Layer (Ni)": "Ni",
  "Gallium (Ga)": "Ga",
  "Gallium Nitride (GaN)": "Ga",
  "Gallium Arsenide (GaAs)": "Ga",
  "Gallium Phosphide (GaP)": "Ga",
  "Indium (In)": "In",
  "Indium Nitride (InN)": "In",
  "Indium Oxide (In2O3)": "In",
  "Indium Tin Oxide (ITO)": "In",
  "Cobalt (Co)": "Co",
  "Tricobalt Tetraoxide (Co3O4)": "Co",
  "Doped Silicon (Si)": "Si",
  "Silicon (Si)": "Si",
  "Magnesium (Mg)": "Mg",
  "Magnesium Oxide (MgO)": "Mg",
  "Bismuth (Bi)": "Bi",
  "Lead-Free Glass (Bi-Si-B)": "Bi",
  "Antimony Trioxide (Sb2O3)": "Sb",
  "Phosphorus (P)": "P",
  "Barium (Ba)": "Ba",
  "Barium Sulfate (BaSO4)": "Ba",
  "Barium Titanate (BaTiO3)": "Ba",
  "Barium Oxide (BaO)": "Ba",
  "Strontium Oxide (SrO)": "Sr",
  "Anatase (TiO2)": "Ti",
  "Yttrium Oxide (Y2O3)": "Y",
  "Manganese Dioxide (MnO2)": "Mn",
  "Boron Zinc Hydroxide Oxide": "B",
  "Aluminum (Al)": "Al",
  "Aluminum Oxide (Al2O3)": "Al",
  "Aluminum Hydroxide (Al(OH)3)": "Al",
  "Aluminum Nitride (AlN)": "Al",
  "Lead (Pb)": "Pb",
  "Lead-Containing Glass Frit": "Pb",
  "Chromium (Cr)": "Cr",
  "Chromium Oxide (Cr2O3)": "Cr",
  "Tin (Sn)": "Sn",
  "Finish Plating (Sn)": "Sn",
  "Iron (Fe)": "Fe",
  "Zinc (Zn)": "Zn",
  "Zinc Oxide (ZnO)": "Zn",
  "Chlorine (Cl)": "Cl",
  "Carbon Black": "C",
};

/** Element -> which lists flag it, and the human-readable reason. */
const CRITICAL = {
  Au: { lists: ["PM"], why: "Precious metal — dominant recoverable value in e-scrap" },
  Ag: { lists: ["PM"], why: "Precious metal — contact plating and solder" },
  Pd: { lists: ["EU", "PM"], why: "Platinum-group metal on the EU CRM list" },
  Ru: { lists: ["EU", "PM"], why: "Platinum-group metal on the EU CRM list" },
  Cu: { lists: ["EU", "DOE"], why: "Listed by both the EU and US DOE (electrification demand)" },
  Ni: { lists: ["EU", "DOE"], why: "Listed by both the EU and US DOE (battery/alloy demand)" },
  Ga: { lists: ["EU", "DOE"], why: "Semiconductor feedstock, export-controlled supply" },
  In: { lists: ["EU"], why: "EU CRM — by-product-only supply chain" },
  Co: { lists: ["EU", "DOE"], why: "Listed by both the EU and US DOE" },
  Si: { lists: ["EU", "DOE"], why: "Silicon metal — EU CRM and DOE critical material" },
  Mg: { lists: ["EU", "DOE"], why: "EU CRM with highly concentrated supply" },
  Bi: { lists: ["EU"], why: "EU CRM — by-product of lead refining" },
  Sb: { lists: ["EU"], why: "EU CRM — flame-retardant synergist" },
  P: { lists: ["EU"], why: "EU CRM — phosphorus/phosphate rock" },
  Ba: { lists: ["EU"], why: "EU CRM — baryte" },
  Sr: { lists: ["EU"], why: "EU CRM — strontium" },
  Ti: { lists: ["EU"], why: "EU CRM — titanium metal" },
  Y: { lists: ["EU"], why: "EU CRM — heavy rare earth element" },
  Mn: { lists: ["EU"], why: "EU CRM — battery-grade manganese" },
  B: { lists: ["EU"], why: "EU CRM — borates" },
  Al: { lists: ["EU", "DOE"], why: "Bauxite/aluminium — EU CRM and DOE critical material" },
};

/** Elements carrying a regulatory hazard, shown with separate visual treatment. */
const HAZARD = {
  Pb: "RoHS restricted substance — lead, 0.1 % w/w limit",
  Cr: "RoHS restricted if hexavalent — Cr(VI), 0.1 % w/w limit",
  Sb: "Antimony trioxide — IARC 2B suspected carcinogen",
  Cl: "Halogen content — restricts halogen-free recycling routes",
  C: "Carbon black — IARC 2B suspected carcinogen (respirable)",
};

/**
 * Mass fraction of the carrier element in the extracted compound. Extraction
 * reports compound weight; value and critical-mass figures need element weight.
 * Anything absent is treated as the pure element (fraction 1.0).
 */
const FRACTION = {
  "Copper Oxide (CuO)": 0.799,
  "Magnesium Oxide (MgO)": 0.603,
  "Aluminum Oxide (Al2O3)": 0.529,
  "Aluminum Hydroxide (Al(OH)3)": 0.346,
  "Aluminum Nitride (AlN)": 0.658,
  "Barium Titanate (BaTiO3)": 0.589,
  "Barium Oxide (BaO)": 0.897,
  "Barium Sulfate (BaSO4)": 0.588,
  "Antimony Trioxide (Sb2O3)": 0.835,
  "Strontium Oxide (SrO)": 0.845,
  "Anatase (TiO2)": 0.599,
  "Yttrium Oxide (Y2O3)": 0.787,
  "Manganese Dioxide (MnO2)": 0.632,
  "Zinc Oxide (ZnO)": 0.803,
  "Chromium Oxide (Cr2O3)": 0.684,
  "Ruthenium Oxide (RuO2)": 0.759,
  "Tricobalt Tetraoxide (Co3O4)": 0.734,
  "Indium Oxide (In2O3)": 0.827,
  "Indium Tin Oxide (ITO)": 0.74,
  "Indium Nitride (InN)": 0.891,
  "Gallium Nitride (GaN)": 0.833,
  "Gallium Arsenide (GaAs)": 0.482,
  "Gallium Phosphide (GaP)": 0.692,
  "Lead-Containing Glass Frit": 0.6,
  "Lead-Free Glass (Bi-Si-B)": 0.5,
  "Boron Zinc Hydroxide Oxide": 0.12,
};

/**
 * Classify one extracted material.
 * @returns {{element: string|null, lists: string[], why: string|null,
 *            hazard: string|null, critical: boolean}}
 */
export function classify(materialName) {
  const element = ELEMENT[materialName] || null;
  const crit = element ? CRITICAL[element] : null;
  const hazard = element ? HAZARD[element] || null : null;
  return {
    element,
    fraction: FRACTION[materialName] ?? 1,
    lists: crit ? crit.lists : [],
    why: crit ? crit.why : null,
    hazard,
    critical: Boolean(crit),
  };
}

/**
 * Visual bucket used by the decomposition chart. Four categorical hues plus a
 * reserved neutral for the non-critical remainder — the neutral is deliberately
 * an "Other" bucket, not a fifth series slot.
 */
export function bucketOf(materialName, category) {
  const { critical, hazard } = classify(materialName);
  if (hazard) return "hazard";
  if (critical) return "crm";
  if (/Polymer|Additive|Composite|Filler|Solvent|Pigment/.test(category)) return "organic";
  if (/Oxide|Ceramic|Glass|Salt|Hydroxide|Metalloid|Semiconductor/.test(category)) return "mineral";
  return "common";
}

export const BUCKETS = {
  crm: { label: "Critical / precious", color: "#C6A02C" },
  organic: { label: "Polymer & organic", color: "#2a78d6" },
  mineral: { label: "Ceramic & oxide", color: "#1baf7a" },
  hazard: { label: "Hazardous", color: "#d03b3b" },
  common: { label: "Common metal (other)", color: "#8B978E" },
};
