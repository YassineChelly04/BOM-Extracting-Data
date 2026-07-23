"use client";

import { useEffect, useMemo, useState } from "react";
import ShaderBackground from "./ShaderBackground";
import {
  ArcGauge, MassValueScatter, Treemap, StackBar, Legend, Meter, Tooltip,
  fmt, usd, pct, mg,
} from "./charts";
import { buildModel, PRODUCT, CONVEYOR_TONE } from "@/lib/model";
import { BUCKETS, CRM_LIST_LABEL } from "@/lib/criticality";
import { DEFAULTS, BREAK_EVEN, ELEMENT_ECONOMICS, PRICES_AS_OF, PRICE_SOURCE } from "@/lib/config";

function Svg({ name, size = 18 }) {
  return (
    <span className="svgi" aria-hidden="true"
      style={{ width: size, height: size, WebkitMaskImage: `url(/svg/${name}.svg)`, maskImage: `url(/svg/${name}.svg)` }} />
  );
}

function Panel({ title, sub, aside, children, className = "", span }) {
  return (
    <section className={`panel ${className}`} style={span ? { gridColumn: `span ${span}` } : undefined}>
      {title && (
        <header className="panel-h">
          <div>
            <h2>{title}</h2>
            {sub ? <p>{sub}</p> : null}
          </div>
          {aside}
        </header>
      )}
      <div className="panel-b">{children}</div>
    </section>
  );
}

function Kpi({ label, value, unit, foot, tone }) {
  return (
    <div className={`kpi ${tone || ""}`}>
      <span className="kpi-k">{label}</span>
      <span className="kpi-v">
        {value}
        {unit ? <small>{unit}</small> : null}
      </span>
      <span className="kpi-f">{foot}</span>
    </div>
  );
}

/* ======================================================= VERDICT PANEL ==== */
function Verdict({ m, cfg, setCfg, alt }) {
  const t = CONVEYOR_TONE[m.decision.tone];
  const flip = alt && alt.decision.conveyor !== m.decision.conveyor;
  return (
    <section className="verdict" style={{ "--tone": t.color, "--wash": t.wash, "--tone-ink": t.ink }}>
      <div className="verdict-top">
        <span className="verdict-k">Conveyor</span>
        <span className="verdict-n">{m.decision.conveyor}</span>
      </div>
      <div className="verdict-tone">{t.label}</div>
      <div className="verdict-level">{m.decision.level}</div>
      <h1>{m.decision.title}</h1>
      <p className="verdict-why">{m.decision.rationale}</p>

      <div className="verdict-guard">
        <label className="switch">
          <input type="checkbox" checked={cfg.excludeSuspect}
            onChange={(e) => setCfg({ ...cfg, excludeSuspect: e.target.checked })} />
          <span className="track"><span className="thumb" /></span>
          <span className="switch-l">Data-quality guard</span>
        </label>
        {alt && (
          <div className="verdict-delta">
            <span>RVS {fmt(m.rvs.expected, 2)}</span>
            <em>→</em>
            <span className={flip ? "flip" : ""}>
              {fmt(alt.rvs.expected, 2)} · Conveyor {alt.decision.conveyor}
            </span>
            <small>if {cfg.excludeSuspect ? "suspect rows are trusted" : "suspect rows are removed"}</small>
          </div>
        )}
      </div>
    </section>
  );
}

/* ================================================================ PAGE ==== */
function Clock() {
  const [t, setT] = useState(null);
  useEffect(() => {
    const tick = () => setT(new Date().toTimeString().slice(0, 8));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);
  return <span className="clock">{t || "--:--:--"}</span>;
}

export default function Page() {
  const [cfg, setCfg] = useState({ ...DEFAULTS });
  const [drawer, setDrawer] = useState(false);
  const [tip, setTip] = useState(null);
  const [pick, setPick] = useState(null);

  const m = useMemo(() => buildModel(cfg), [cfg]);
  /* The counterfactual: same unit, guard inverted. Drives the delta readout. */
  const alt = useMemo(
    () => (m.suspectRows.length ? buildModel({ ...cfg, excludeSuspect: !cfg.excludeSuspect }) : null),
    [cfg, m.suspectRows.length]
  );

  const onHover = (data, e) =>
    setTip(data ? { data, x: e.clientX + 16, y: e.clientY + 16 } : null);

  const totalMass = m.materials.reduce((s, x) => s + x.weight, 0);

  /* mass composition by class */
  const massMix = Object.keys(BUCKETS).map((b) => {
    const v = m.materials.filter((x) => x.bucket === b).reduce((s, x) => s + x.weight, 0);
    return { key: b, label: BUCKETS[b].label, color: BUCKETS[b].color, value: v,
      display: `${fmt(v, 1)} mg`, unit: "Mass" };
  });
  /* value composition */
  const valueMix = [
    ...m.contributors.map((c) => ({
      key: c.material, label: c.material.replace(/\s*\(.*$/, ""), color: BUCKETS[c.bucket].color,
      value: c.value, display: usd(c.value), unit: "Value",
    })),
    ...(m.otherValue > 0
      ? [{ key: "_o", label: "Other", color: BUCKETS.common.color, value: m.otherValue, display: usd(m.otherValue), unit: "Value" }]
      : []),
  ];

  const selected = pick ? m.subassemblies.find((s) => s.id === pick) : null;
  const tableRows = (selected ? selected.materials : m.flagged)
    .filter((r) => r.weight > 0)
    .slice(0, 60);

  return (
    <>
      <ShaderBackground tone={m.decision.tone} />
      <div className="bg-veil" />
      <Tooltip tip={tip} />

      <header className="header">
        <div className="header-inner">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img className="brand-logo" src="/actia-logo.png" alt="ACTIA Group" width="150" height="32" />
          <div className="idbar">
            <b>{PRODUCT.id}</b>
            <span>{PRODUCT.name}</span>
            <span className="tagline">{PRODUCT.ecuType} · {PRODUCT.revision}</span>
          </div>
          <div className="spacer" />
          <div className="live-pill"><span className="led" /> Live</div>
          <div className="updated"><Svg name="clock" size={12} /> <Clock /></div>
          <button className="icon-btn" onClick={() => setDrawer(true)} title="Configuration">
            <Svg name="categories" size={17} />
          </button>
        </div>
      </header>

      <main className="grid">
        {/* ---- row 1: verdict + KPIs + gauge ---- */}
        <Verdict m={m} cfg={cfg} setCfg={setCfg} alt={alt} />

        <div className="kpi-strip">
          <Kpi label="Recoverable" value={usd(m.value.expected)} foot={`${usd(m.value.low)} – ${usd(m.value.high)}`} />
          <Kpi label="Processing cost" value={usd(m.cost.expected)} foot="per unit" />
          <Kpi label="Critical materials" value={m.criticalFlags.length} foot={CRM_LIST_LABEL} tone="crm" />
          <Kpi label="Hazardous" value={m.hazardFlags.length} foot="RoHS / IARC flagged" tone="haz" />
          <Kpi label="Unit mass" value={fmt(totalMass, 0)} unit="mg" foot={`${m.materials.length} materials`} />
          <Kpi label="BOM coverage" value={pct(m.coverage, 1)} foot={`${PRODUCT.extractedParts}/${PRODUCT.bomLineItems} parts`}
            tone={m.coverage < 0.7 ? "warn" : ""} />
        </div>

        <Panel className="p-gauge" title="Recovery Value Score" sub="value ÷ cost · break-even 1.00">
          <ArcGauge low={m.rvs.low} expected={m.rvs.expected} high={m.rvs.high} threshold={BREAK_EVEN} />
          <div className={`gauge-verdict ${m.rvs.expected >= BREAK_EVEN ? "ok" : "under"}`}>
            {m.rvs.expected >= BREAK_EVEN
              ? `${fmt(m.rvs.expected, 1)}× return on processing`
              : `returns ${pct(m.rvs.expected, 0)} of processing cost`}
          </div>
        </Panel>

        {/* ---- row 2: the centrepiece ---- */}
        <Panel className="p-scatter" title="Material map" sub="mass vs recoverable value — every material in the unit"
          aside={<Legend items={Object.entries(BUCKETS).map(([k, v]) => ({ key: k, ...v }))} />}>
          <MassValueScatter materials={m.materials} buckets={BUCKETS} onHover={onHover} />
        </Panel>

        <Panel className="p-mix" title="Composition">
          <div className="mixblock">
            <span className="mix-k">By mass · {fmt(totalMass, 0)} mg</span>
            <StackBar segments={massMix} onHover={onHover} />
          </div>
          <div className="mixblock">
            <span className="mix-k">By value · {usd(m.value.expected)}</span>
            <StackBar segments={valueMix} onHover={onHover} />
          </div>
          <div className="meters">
            <Meter label="Critical mass" value={m.criticalWeight} of={totalMass}
              color={BUCKETS.crm.color} display={`${fmt(m.criticalWeight, 0)} mg · ${pct(m.criticalWeight / totalMass, 0)}`} />
            <Meter label="Hazardous mass" value={m.hazardFlags.reduce((s, x) => s + x.weight, 0)} of={totalMass}
              color={BUCKETS.hazard.color}
              display={`${fmt(m.hazardFlags.reduce((s, x) => s + x.weight, 0), 0)} mg · ${pct(m.hazardFlags.reduce((s, x) => s + x.weight, 0) / totalMass, 0)}`} />
            <Meter label="BOM characterised" value={m.coverage} of={1} color="var(--g-forest)" display={pct(m.coverage, 1)} />
          </div>
        </Panel>

        {/* ---- row 3: decomposition ---- */}
        <Panel className="p-tree" title="Sub-assembly value" sub="area = recoverable value · click to filter the table"
          aside={pick ? <button className="chipbtn" onClick={() => setPick(null)}>Clear filter ✕</button> : null}>
          <Treemap items={m.subassemblies} buckets={BUCKETS} onHover={onHover}
            onSelect={setPick} selected={pick} />
        </Panel>

        <Panel className="p-table"
          title={selected ? selected.name : "Flagged materials"}
          sub={selected ? `${selected.partCount} parts · ${fmt(selected.weight, 0)} mg` : `${m.flagged.length} critical or hazardous`}>
          <div className="tablewrap">
            <table className="tbl">
              <thead>
                <tr>
                  <th scope="col">Material</th>
                  <th scope="col">Class</th>
                  <th scope="col" className="num">Mass</th>
                  <th scope="col" className="num">Value</th>
                </tr>
              </thead>
              <tbody>
                {tableRows.map((r) => (
                  <tr key={r.material}>
                    <th scope="row">
                      <span className="dot" style={{ background: BUCKETS[r.bucket].color }} />
                      {r.material}
                      {r.suspectWeight > 0 ? <em className="susp" title="suspect rows held out">⚑</em> : null}
                    </th>
                    <td>
                      <span className="tags">
                        {r.lists.map((l) => (
                          <span key={l} className={`tag tag-${l.toLowerCase()}`}>{l === "PM" ? "Precious" : l}</span>
                        ))}
                        {r.hazard ? <span className="tag tag-haz">Hazard</span> : null}
                        {!r.lists.length && !r.hazard ? <span className="tag tag-none">{r.category}</span> : null}
                      </span>
                    </td>
                    <td className="num">{mg(r.weight)}</td>
                    <td className="num strong">{r.value > 0 ? usd(r.value) : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        {/* ---- data quality, compact ---- */}
        {m.suspectRows.length > 0 && (
          <Panel className="p-dq" title="Data-quality flags"
            sub={`${m.suspectRows.length} rows report a precious metal above ${pct(cfg.suspectPreciousShare)} of part mass`}>
            <div className="dqrows">
              {m.suspectRows.map((r) => (
                <div key={r.material + r.part} className="dqrow">
                  <b>{r.material.replace(/\s*\(.*$/, "")}</b>
                  <span>{r.part}</span>
                  <span className="dqbar"><span style={{ width: `${Math.min(100, r.share * 100 * 3)}%` }} /></span>
                  <em>{pct(r.share, 1)} of part</em>
                </div>
              ))}
            </div>
            <p className="dqnote">
              Signature of a composition-percentage table parsed as milligrams. Worth {usd(m.suspectValue)} if trusted.
            </p>
          </Panel>
        )}
      </main>

      <footer className="foot">
        material_extractor · {PRODUCT.extractedParts}/{PRODUCT.bomLineItems} BOM items characterised ·
        criticality per {CRM_LIST_LABEL} · prices {PRICES_AS_OF}
      </footer>

      <ConfigDrawer cfg={cfg} setCfg={setCfg} open={drawer} setOpen={setDrawer} />
    </>
  );
}

/* ============================================================== DRAWER ==== */
function Slider({ label, value, min, max, step, onChange, format }) {
  return (
    <label className="fld">
      <span className="fld-k">{label}<b>{format(value)}</b></span>
      <input type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(Number(e.target.value))} />
    </label>
  );
}

function ConfigDrawer({ cfg, setCfg, open, setOpen }) {
  const set = (k) => (v) => setCfg({ ...cfg, [k]: v });
  const priced = Object.entries(ELEMENT_ECONOMICS)
    .filter(([, e]) => e.recovery > 0)
    .sort((a, b) => b[1].price - a[1].price);
  return (
    <>
      <div className={`scrim ${open ? "on" : ""}`} onClick={() => setOpen(false)} />
      <aside className={`drawer ${open ? "on" : ""}`} aria-hidden={!open}>
        <div className="drawer-h">
          <h2>Configuration</h2>
          <button className="icon-btn" onClick={() => setOpen(false)} aria-label="Close">✕</button>
        </div>
        <div className="drawer-b">
          <h3>Economics</h3>
          <label className="fld">
            <span className="fld-k">Processing cost<b>{usd(cfg.processingCost)}/unit</b></span>
            <input type="number" step="0.05" min="0.01" value={cfg.processingCost}
              onChange={(e) => set("processingCost")(Number(e.target.value) || 0.01)} />
          </label>
          <Slider label="Price spread" value={cfg.priceSpread} min={0} max={0.6} step={0.05}
            onChange={set("priceSpread")} format={(v) => `±${pct(v)}`} />
          <Slider label="Recovery spread" value={cfg.recoverySpread} min={0} max={0.5} step={0.05}
            onChange={set("recoverySpread")} format={(v) => `±${pct(v)}`} />
          <Slider label="Cost spread" value={cfg.costSpread} min={0} max={0.6} step={0.05}
            onChange={set("costSpread")} format={(v) => `±${pct(v)}`} />

          <h3>Thresholds</h3>
          <Slider label="Min. critical materials" value={cfg.minCriticalMaterials} min={1} max={20} step={1}
            onChange={set("minCriticalMaterials")} format={(v) => `${v}`} />
          <Slider label="Confidence floor" value={cfg.confidenceFloor} min={0.3} max={0.99} step={0.01}
            onChange={set("confidenceFloor")} format={(v) => pct(v)} />
          <Slider label="Sub-component value share" value={cfg.subComponentValueShare} min={0.5} max={1} step={0.05}
            onChange={set("subComponentValueShare")} format={(v) => pct(v)} />

          <h3>Data-quality guard</h3>
          <label className="fld fld-check">
            <input type="checkbox" checked={cfg.excludeSuspect}
              onChange={(e) => set("excludeSuspect")(e.target.checked)} />
            <span>Hold suspect precious-metal rows out</span>
          </label>
          <Slider label="Suspect above" value={cfg.suspectPreciousShare} min={0.01} max={0.5} step={0.01}
            onChange={set("suspectPreciousShare")} format={(v) => `${pct(v)} of part mass`} />

          <h3>Prices &amp; recovery</h3>
          <p className="drawer-note">As of {PRICES_AS_OF}. {PRICE_SOURCE}.</p>
          <div className="tablewrap">
            <table className="tbl compact">
              <thead><tr><th scope="col">Element</th><th scope="col" className="num">$/kg</th><th scope="col" className="num">Rec.</th></tr></thead>
              <tbody>
                {priced.map(([sym, e]) => (
                  <tr key={sym}>
                    <th scope="row">{e.name} <em>({sym})</em></th>
                    <td className="num">{fmt(e.price, 2)}</td>
                    <td className="num">{pct(e.recovery)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button className="reset" onClick={() => setCfg({ ...DEFAULTS })}>Reset to defaults</button>
        </div>
      </aside>
    </>
  );
}
