/**
 * The decision model: extracted materials -> recovery value -> conveyor verdict.
 *
 * Everything the dashboard renders below the header comes from `buildModel`, so
 * editing a config value in the Config panel re-derives the whole story,
 * including the Decision Banner.
 */

import data from "./data.js";
import parts from "./parts.js";
import { classify, bucketOf } from "./criticality.js";
import { ELEMENT_ECONOMICS, DEFAULTS, BREAK_EVEN } from "./config.js";

/** Identity of the unit under test. */
export const PRODUCT = {
  id: "MC121EVM-D-001",
  name: "MCF8315C-Q1 Sensorless FOC Motor Driver EVM",
  ecuType: "Motor Control ECU",
  revision: "Rev D",
  bomLineItems: 88,
  extractedParts: parts.partCount,
  /**
   * Confidence in the identification of the materials that WERE extracted — all
   * rows originate from manufacturer material declarations rather than vision.
   * Distinct from coverage, which is reported separately and is much lower.
   */
  extractionConfidence: 0.94,
};

const clamp01 = (n) => Math.max(0, Math.min(1, n));

/**
 * Recovered value in USD for one material row under a scenario.
 * weight is the compound weight in mg; economics are per kg of element.
 */
function valueOf(weightMg, element, fraction, priceMul, recoveryMul) {
  const econ = ELEMENT_ECONOMICS[element];
  if (!econ) return 0;
  const kg = (weightMg * fraction) / 1e6;
  return kg * (econ.price * priceMul) * clamp01(econ.recovery * recoveryMul);
}

export function buildModel(cfg = DEFAULTS) {
  const {
    processingCost,
    priceSpread,
    recoverySpread,
    costSpread,
    minCriticalMaterials,
    traceThresholdMg,
    confidenceFloor,
    subComponentValueShare,
  } = { ...DEFAULTS, ...cfg };

  const { suspectPreciousShare, suspectPriceFloor, excludeSuspect } = {
    ...DEFAULTS,
    ...cfg,
  };

  /* ---- where each material lives, so a flag can name its sub-assembly ---- */
  const locations = new Map();
  for (const sub of parts.subassemblies) {
    for (const m of sub.materials) {
      const list = locations.get(m.material) || [];
      list.push({ sub: sub.name, weight: m.weight });
      locations.set(m.material, list);
    }
  }

  /* ---- data-quality guard ------------------------------------------------
   * A high-value element occupying an implausible share of a part's mass is
   * the signature of a percentage table parsed as milligrams. Collect the
   * offending weight per material so it can be held out of the score.        */
  const suspectWeight = new Map();
  const suspectBySub = new Map();
  const suspectRows = [];
  for (const sub of parts.subassemblies) {
    const perSub = new Map();
    suspectBySub.set(sub.id, perSub);
    for (const part of sub.parts) {
      if (!part.weight) continue;
      for (const row of part.materials) {
        const c = classify(row.material);
        const econ = c.element ? ELEMENT_ECONOMICS[c.element] : null;
        if (!econ || econ.price < suspectPriceFloor) continue;
        const share = row.weight / part.weight;
        if (share <= suspectPreciousShare) continue;
        suspectWeight.set(
          row.material,
          (suspectWeight.get(row.material) || 0) + row.weight
        );
        perSub.set(row.material, (perSub.get(row.material) || 0) + row.weight);
        suspectRows.push({
          material: row.material,
          part: part.part,
          designators: part.designators,
          sub: sub.name,
          weight: row.weight,
          partWeight: part.weight,
          share,
        });
      }
    }
  }
  suspectRows.sort((a, b) => b.weight - a.weight);

  /* ---- enrich every extracted material ---------------------------------- */
  const materials = data.materials.map((m) => {
    const c = classify(m.material);
    const econ = c.element ? ELEMENT_ECONOMICS[c.element] : null;
    const here = (locations.get(m.material) || []).sort((a, b) => b.weight - a.weight);
    const suspect = suspectWeight.get(m.material) || 0;
    const w = excludeSuspect ? Math.max(0, m.weight - suspect) : m.weight;
    return {
      ...m,
      ...c,
      bucket: bucketOf(m.material, m.category),
      elementWeight: m.weight * c.fraction,
      suspectWeight: suspect,
      effectiveWeight: w,
      price: econ ? econ.price : 0,
      recovery: econ ? econ.recovery : 0,
      value: valueOf(w, c.element, c.fraction, 1, 1),
      valueLow: valueOf(w, c.element, c.fraction, 1 - priceSpread, 1 - recoverySpread),
      valueHigh: valueOf(w, c.element, c.fraction, 1 + priceSpread, 1 + recoverySpread),
      locations: here,
      primaryLocation: here.length ? here[0].sub : "—",
      trace: m.weight < traceThresholdMg,
    };
  });

  const byValue = [...materials].sort((a, b) => b.value - a.value);
  const flagged = materials
    .filter((m) => (m.critical || m.hazard) && !m.trace)
    .sort((a, b) => b.value - a.value || b.weight - a.weight);
  const criticalFlags = flagged.filter((m) => m.critical);
  const hazardFlags = flagged.filter((m) => m.hazard);
  const nonCritical = materials
    .filter((m) => !m.critical && !m.hazard)
    .sort((a, b) => b.weight - a.weight);

  const criticalWeight = materials
    .filter((m) => m.critical)
    .reduce((s, m) => s + m.elementWeight, 0);

  /* ---- Recovery Value Score --------------------------------------------- */
  const sum = (k) => materials.reduce((s, m) => s + m[k], 0);
  const value = { low: sum("valueLow"), expected: sum("value"), high: sum("valueHigh") };
  const cost = {
    low: processingCost * (1 + costSpread),
    expected: processingCost,
    high: processingCost * (1 - costSpread),
  };
  const rvs = {
    low: cost.low > 0 ? value.low / cost.low : 0,
    expected: cost.expected > 0 ? value.expected / cost.expected : 0,
    high: cost.high > 0 ? value.high / cost.high : 0,
  };

  /* Materials driving the score, with the remainder folded into "Other". */
  const contributors = [];
  let other = 0;
  for (const m of byValue) {
    if (m.value <= 0) continue;
    const share = m.value / value.expected;
    if (contributors.length < 4 && share >= 0.01) contributors.push(m);
    else other += m.value;
  }

  /* ---- Decomposition: value and bucket mix per sub-assembly ------------- */
  const subassemblies = parts.subassemblies
    .map((sub) => {
      const perSub = suspectBySub.get(sub.id) || new Map();
      const mats = sub.materials.map((m) => {
        const c = classify(m.material);
        const suspect = perSub.get(m.material) || 0;
        const w = excludeSuspect ? Math.max(0, m.weight - suspect) : m.weight;
        return {
          ...m,
          ...c,
          bucket: bucketOf(m.material, m.category),
          suspectWeight: suspect,
          effectiveWeight: w,
          value: valueOf(w, c.element, c.fraction, 1, 1),
        };
      });
      const mix = {};
      for (const m of mats) mix[m.bucket] = (mix[m.bucket] || 0) + m.value;
      return {
        id: sub.id,
        name: sub.name,
        description: sub.description,
        partCount: sub.partCount,
        parts: sub.parts,
        weight: sub.weight,
        criticalWeight: mats
          .filter((m) => m.critical)
          .reduce((s, m) => s + m.weight * m.fraction, 0),
        value: mats.reduce((s, m) => s + m.value, 0),
        mix,
        materials: mats.sort((a, b) => b.value - a.value || b.weight - a.weight),
      };
    })
    .sort((a, b) => b.value - a.value);

  const unitValue = subassemblies.reduce((s, x) => s + x.value, 0) || 1;
  let cumulative = 0;
  for (const sub of subassemblies) {
    sub.valueShare = sub.value / unitValue;
    cumulative += sub.valueShare;
    sub.cumulativeShare = cumulative;
  }
  /* Sub-assemblies that together hold the configured share of unit value. */
  const targets = [];
  for (const sub of subassemblies) {
    targets.push(sub);
    if (sub.cumulativeShare >= subComponentValueShare) break;
  }

  /* ---- Verdict ---------------------------------------------------------- */
  const criticalCount = criticalFlags.length;
  const commonShare =
    materials.filter((m) => m.bucket === "common").reduce((s, m) => s + m.weight, 0) /
    data.totalWeight;

  const decision = decide({
    confidence: PRODUCT.extractionConfidence,
    confidenceFloor,
    criticalCount,
    minCriticalMaterials,
    rvs,
    commonShare,
    targets,
    hazardCount: hazardFlags.length,
  });

  return {
    materials,
    flagged,
    criticalFlags,
    hazardFlags,
    nonCritical,
    criticalWeight,
    criticalCount,
    value,
    cost,
    rvs,
    contributors,
    otherValue: other,
    subassemblies,
    targets,
    commonShare,
    decision,
    suspectRows,
    suspectValue: suspectRows.reduce((s, r) => {
      const c = classify(r.material);
      return s + valueOf(r.weight, c.element, c.fraction, 1, 1);
    }, 0),
    coverage: PRODUCT.extractedParts / PRODUCT.bomLineItems,
    cfg: { ...DEFAULTS, ...cfg },
  };
}

function decide(x) {
  if (x.confidence < x.confidenceFloor) {
    return {
      conveyor: 3,
      tone: "unknown",
      level: "Manual review",
      title: "Route to manual review",
      rationale: `Material identification confidence ${(x.confidence * 100).toFixed(0)} % is below the ${(
        x.confidenceFloor * 100
      ).toFixed(0)} % floor — the unit cannot be classified automatically.`,
    };
  }
  const enough = x.criticalCount >= x.minCriticalMaterials;
  if (enough && x.rvs.low >= BREAK_EVEN) {
    return {
      conveyor: 1,
      tone: "rare",
      level: "Full unit",
      title: "Recover the whole unit",
      rationale: `${x.criticalCount} critical materials detected and the worst-case Recovery Value Score of ${x.rvs.low.toFixed(
        2
      )} still clears break-even — the entire unit is worth processing.`,
    };
  }
  if (enough && x.rvs.expected >= BREAK_EVEN) {
    const names = x.targets.map((t) => t.name).join(" + ");
    return {
      conveyor: 1,
      tone: "rare",
      level: "Sub-component only",
      title: `Harvest ${x.targets.length === 1 ? x.targets[0].name : "priority sub-components"}`,
      rationale: `${x.criticalCount} critical materials detected, but only the expected case clears break-even (${x.rvs.expected.toFixed(
        2
      )} vs ${x.rvs.low.toFixed(2)} worst case) — recover ${names} and route the remainder to Conveyor 2.`,
    };
  }
  if (x.commonShare >= 0.4) {
    return {
      conveyor: 2,
      tone: "common",
      level: "Bulk stream",
      title: "Common recyclables",
      rationale: `Only ${x.criticalCount} critical material${
        x.criticalCount === 1 ? "" : "s"
      } above threshold and a Recovery Value Score of ${x.rvs.expected.toFixed(
        2
      )} — below break-even for selective recovery. ${(x.commonShare * 100).toFixed(
        0
      )} % of mass is common metal, so route to the bulk stream.`,
    };
  }
  return {
    conveyor: 3,
    tone: "unknown",
    level: "Manual review",
    title: "Route to manual review",
    rationale: `Recovery Value Score ${x.rvs.expected.toFixed(
      2
    )} is below break-even and the unit has no dominant recyclable fraction.`,
  };
}

export const CONVEYOR_TONE = {
  rare: { color: "#B8860B", wash: "#FBF3DC", ink: "#5C430A", label: "Rare / high value" },
  common: { color: "#2a78d6", wash: "#E7F0FC", ink: "#123B6C", label: "Common recyclables" },
  unknown: { color: "#6B7A70", wash: "#EDF1EE", ink: "#33403A", label: "Unknown / review" },
};
