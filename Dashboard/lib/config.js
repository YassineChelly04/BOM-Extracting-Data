/**
 * Operational parameters for the recovery decision. Everything here is an
 * assumption, not extracted data — the Config panel edits these live and the
 * Recovery Value Score recomputes from them.
 */

/** Spot prices are placeholders pending a live feed. Shown with this date. */
export const PRICES_AS_OF = "2026-07-01";
export const PRICE_SOURCE = "Placeholder desk estimates — replace with live feed";

/**
 * Refinery payable price in USD per kg of recovered element, and the fraction of
 * the contained element a commercial e-scrap route actually recovers.
 */
export const ELEMENT_ECONOMICS = {
  Au: { price: 85000, recovery: 0.95, name: "Gold" },
  Pd: { price: 32000, recovery: 0.92, name: "Palladium" },
  Ru: { price: 20000, recovery: 0.3, name: "Ruthenium" },
  Ag: { price: 1000, recovery: 0.9, name: "Silver" },
  Ga: { price: 400, recovery: 0.05, name: "Gallium" },
  In: { price: 300, recovery: 0.1, name: "Indium" },
  Co: { price: 25, recovery: 0.7, name: "Cobalt" },
  Y: { price: 30, recovery: 0.0, name: "Yttrium" },
  Sn: { price: 31, recovery: 0.6, name: "Tin" },
  Ni: { price: 16, recovery: 0.75, name: "Nickel" },
  Sb: { price: 13, recovery: 0.0, name: "Antimony" },
  Cu: { price: 9.5, recovery: 0.9, name: "Copper" },
  Bi: { price: 10, recovery: 0.2, name: "Bismuth" },
  Ti: { price: 8, recovery: 0.0, name: "Titanium" },
  Zn: { price: 2.9, recovery: 0.5, name: "Zinc" },
  Al: { price: 2.5, recovery: 0.5, name: "Aluminium" },
  Si: { price: 2.5, recovery: 0.0, name: "Silicon" },
  Pb: { price: 2.0, recovery: 0.8, name: "Lead" },
  Mg: { price: 3.0, recovery: 0.0, name: "Magnesium" },
  Mn: { price: 1.8, recovery: 0.0, name: "Manganese" },
  Fe: { price: 0.5, recovery: 0.85, name: "Iron" },
  Cr: { price: 3.0, recovery: 0.3, name: "Chromium" },
  Ba: { price: 0.2, recovery: 0.0, name: "Barium" },
  Sr: { price: 1.5, recovery: 0.0, name: "Strontium" },
  B: { price: 1.0, recovery: 0.0, name: "Boron" },
  P: { price: 1.0, recovery: 0.0, name: "Phosphorus" },
  C: { price: 0.8, recovery: 0.0, name: "Carbon" },
  Cl: { price: 0.0, recovery: 0.0, name: "Chlorine" },
};

export const DEFAULTS = {
  /** USD to disassemble, shred and refine one unit. */
  processingCost: 0.85,
  /** Scenario spread applied to the three RVS cases. */
  priceSpread: 0.2,
  /** Recovery-rate spread applied to the three RVS cases. */
  recoverySpread: 0.15,
  /** Cost spread applied to the three RVS cases (inverted for the high case). */
  costSpread: 0.25,
  /**
   * A unit goes to Conveyor 1 only if at least this many distinct critical
   * materials are present above the trace threshold.
   */
  minCriticalMaterials: 3,
  /** Weight below this (mg) is treated as trace and does not raise a flag. */
  traceThresholdMg: 0.01,
  /** Vision/extraction confidence below this routes to Conveyor 3. */
  confidenceFloor: 0.7,
  /**
   * Data-quality guard. A high-value element (see suspectPriceFloor) cannot
   * plausibly make up more than this share of a part's mass; when it does, the
   * row is almost always a composition-percentage table misread as milligrams.
   * Such rows are marked suspect and, by default, excluded from the score.
   */
  suspectPreciousShare: 0.08,
  suspectPriceFloor: 1000,
  excludeSuspect: true,
  /**
   * If RVS_expected clears break-even but RVS_low does not, recovery is limited
   * to the sub-assemblies that together hold this share of unit value.
   */
  subComponentValueShare: 0.9,
};

/** Break-even. RVS is value / cost, so 1.0 is the line. */
export const BREAK_EVEN = 1.0;
