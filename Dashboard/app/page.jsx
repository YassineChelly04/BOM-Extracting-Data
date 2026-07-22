"use client";

import { useEffect, useState } from "react";
import data from "@/lib/data";
import ShaderBackground from "./ShaderBackground";

/* ---------- helpers ---------- */
function fmt(n, dec = 1) {
  return Number(n).toLocaleString("en-US", {
    minimumFractionDigits: dec,
    maximumFractionDigits: dec,
  });
}
function fmtInt(n) {
  return Math.round(n).toLocaleString("en-US");
}

/* modern SVG icons live as real files in /public/svg — tinted via CSS mask */
function Svg({ name, size = 20, className = "" }) {
  return (
    <span
      className={`svgi ${className}`}
      aria-hidden="true"
      style={{
        width: size,
        height: size,
        WebkitMaskImage: `url(/svg/${name}.svg)`,
        maskImage: `url(/svg/${name}.svg)`,
      }}
    />
  );
}

/* one icon per material category, reused for badges + breakdown rows */
const CAT_ICON = {
  Metal: "metal",
  Polymer: "polymer",
  "Metal Oxide": "metal-oxide",
  Composite: "composite",
  "Polymer Additive": "polymer-additive",
  Ceramic: "ceramic",
  Additive: "additive",
  Metalloid: "metalloid",
};
const catIcon = (cat) => CAT_ICON[cat] || "materials";

/* ---------- count-up ---------- */
function useCountUp(target, { dec = 0, duration = 1400 } = {}) {
  const [v, setV] = useState(0);
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) { setV(target); return; }
    let raf, start;
    const step = (t) => {
      if (!start) start = t;
      const p = Math.min((t - start) / duration, 1);
      setV(target * (1 - Math.pow(1 - p, 3)));
      if (p < 1) raf = requestAnimationFrame(step);
      else setV(target);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, dec, duration]);
  return dec > 0 ? fmt(v, dec) : fmtInt(v);
}

/* ---------- KPI card ---------- */
function Kpi({ icon, accent, name, value, unit, dec = 0, note }) {
  const v = useCountUp(value, { dec });
  return (
    <div className="card kpi" style={{ "--accent": accent }}>
      <div className="top">
        <span className="icon"><Svg name={icon} size={19} /></span>
        <span className="name">{name}</span>
      </div>
      <div className="value">
        <span>{v}</span>
        {unit ? <span className="unit">{unit}</span> : null}
      </div>
      {note ? <div className="note"><span className="swatch" />{note}</div> : null}
    </div>
  );
}

/* ---------- left stat card ---------- */
function StatCard({ icon, accent, label, value, count, pct, delay }) {
  const v = useCountUp(value, { dec: 1 });
  const [w, setW] = useState(0);
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) { setW(pct); return; }
    const t = setTimeout(() => setW(pct), 200);
    return () => clearTimeout(t);
  }, [pct]);
  return (
    <div className="card stat" style={{ "--accent": accent, animationDelay: `${delay}s` }}>
      <div className="top">
        <div>
          <div className="s-label">{label}</div>
          <div className="s-value"><span>{v}</span><span className="unit">mg</span></div>
        </div>
        <span className="s-ic"><Svg name={icon} size={22} /></span>
      </div>
      <div className="bar-track"><div className="bar-fill" style={{ width: `${w}%` }} /></div>
      <div className="s-foot">{count} materials</div>
    </div>
  );
}

/* ---------- top materials row ---------- */
function MatRow({ m, pct }) {
  const [w, setW] = useState(0);
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) { setW(pct); return; }
    const t = setTimeout(() => setW(pct), 250);
    return () => clearTimeout(t);
  }, [pct]);
  return (
    <div className="mat-row">
      <span className="badge" title={m.category}><Svg name={catIcon(m.category)} size={18} /></span>
      <div className="mat-mid">
        <div className="mat-name" title={m.material}>{m.material}</div>
        <div className="mat-bar"><span style={{ width: `${w}%` }} /></div>
      </div>
      <div className="mat-val">{fmt(m.weight, 1)}<small>mg</small></div>
    </div>
  );
}

/* ---------- category row ---------- */
function CatRow({ c, totalWeight }) {
  const v = useCountUp(c.weight, { dec: 1 });
  const share = ((c.weight / totalWeight) * 100).toFixed(1);
  return (
    <div className="cat-row">
      <span className="cat-ic"><Svg name={catIcon(c.category)} size={17} /></span>
      <span className="cat-name">{c.category}</span>
      <span className="cat-share">{share}%</span>
      <span className="cat-val">{v}<small>mg</small></span>
    </div>
  );
}

/* ---------- total weight + donut (share of heaviest category) ---------- */
function TotalCard() {
  const v = useCountUp(data.totalWeight, { dec: 0 });
  const C = 2 * Math.PI * 50;
  const topCat = data.categories[0];
  const topPct = Math.round((topCat.weight / data.totalWeight) * 100);
  const [ready, setReady] = useState(false);
  const [pct, setPct] = useState(0);
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) { setReady(true); setPct(topPct); return; }
    const t = setTimeout(() => setReady(true), 300);
    let p = 0;
    const id = setInterval(() => { p += 1; if (p >= topPct) { p = topPct; clearInterval(id); } setPct(p); }, 22);
    return () => { clearTimeout(t); clearInterval(id); };
  }, [topPct]);
  const dash = ready ? C * (1 - topPct / 100) : C;
  return (
    <div className="card total-card" style={{ animationDelay: "0.3s" }}>
      <div className="total-left">
        <div className="k">Total Weight</div>
        <div className="v"><span>{v}</span><span className="unit">mg</span></div>
        <div className="foot">across <b>{data.totalMaterials}</b> materials in <b>{data.categoryCount}</b> categories</div>
      </div>
      <div className="donut">
        <svg viewBox="0 0 120 120" width="108" height="108">
          <circle cx="60" cy="60" r="50" fill="none" stroke="var(--track)" strokeWidth="12" />
          <circle className="ring" cx="60" cy="60" r="50" fill="none" stroke="url(#dg)" strokeWidth="12"
            strokeLinecap="round" strokeDasharray={C} strokeDashoffset={dash}
            transform="rotate(-90 60 60)" />
          <defs>
            <linearGradient id="dg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#3BA35A" />
              <stop offset="1" stopColor="#2E7D32" />
            </linearGradient>
          </defs>
        </svg>
        <div className="pct"><span className="pn">{pct}%</span><span className="pl">{topCat.category}</span></div>
      </div>
    </div>
  );
}

/* ---------- live clock ---------- */
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

/* ---------- page ---------- */
export default function Page() {
  const stats = data.categories.slice(0, 3);
  const statMax = Math.max(...stats.map((s) => s.weight));
  const statAccents = { Metal: "var(--g-signal)", Polymer: "var(--g-emerald)", "Metal Oxide": "var(--g-forest)" };

  const top = data.topByWeight.slice(0, 10);
  const matMax = top[0].weight;
  const cats = data.categories.slice(0, 8);

  const heaviest = data.topByWeight[0];
  const goldWeight = (data.materials.find((m) => m.material === "Gold (Au)") || {}).weight || 0;
  const share = (w) => (w / data.totalWeight) * 100;
  const shortName = (m) => m.replace(/\s*\(.*$/, "");

  /* every note below is derived from the data — no invented trends */
  const KPI = [
    {
      icon: "materials", accent: "#34A853", name: "Total Materials", value: data.totalMaterials,
      note: <>in <b>{data.categoryCount}</b> categories</>,
    },
    {
      icon: "gold", accent: "#C6A02C", name: "Weight of Gold", value: goldWeight, unit: "mg", dec: 1,
      note: <><b>{fmt(share(goldWeight), 1)}%</b> of total weight</>,
    },
    {
      icon: "categories", accent: "#2E7D32", name: "Categories", value: data.categoryCount,
      note: <><b>{data.categories[0].category}</b> is the largest</>,
    },
    {
      icon: "datapoints", accent: "#1E7A45", name: "Material Appearances", value: data.totalOccurrences,
      note: <>across <b>{data.totalMaterials}</b> materials</>,
    },
    {
      icon: "heaviest", accent: "#7CB342", name: "Heaviest Material", value: heaviest.weight, unit: "mg", dec: 1,
      note: <><b>{shortName(heaviest.material)}</b> · {Math.round(share(heaviest.weight))}% of weight</>,
    },
  ];

  return (
    <>
      <ShaderBackground />
      <div className="bg-veil" />

      <header className="header">
        <div className="header-inner">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img className="brand-logo" src="/actia-logo.png" alt="ACTIA Group" width="156" height="34" />
          <div className="sub">
            Material Composition Report
            <span className="sep">·</span><b>MCF8315C-Q1</b>
            <span className="sep">·</span><b>MC121EVM</b>
          </div>
          <div className="spacer" />
          <div className="live-pill"><span className="led" /> Live Data</div>
          <div className="updated">
            <div className="k">Last updated</div>
            <div className="v"><Svg name="clock" size={12} /> <Clock /></div>
          </div>
          <button className="icon-btn" title="Export report" aria-label="Export report">
            <Svg name="export" size={18} />
          </button>
        </div>
      </header>

      <div className="wrap">
        {/* KPI ROW */}
        <div className="kpi-row">
          {KPI.map((k) => <Kpi key={k.name} {...k} />)}
        </div>

        {/* BODY */}
        <div className="body-grid">
          {/* left — category stat cards */}
          <div className="col left">
            {stats.map((s, i) => (
              <StatCard
                key={s.category}
                icon={catIcon(s.category)}
                accent={statAccents[s.category] || "var(--g-signal)"}
                label={s.category}
                value={s.weight}
                count={s.count}
                pct={(s.weight / statMax) * 100}
                delay={0.1 + i * 0.08}
              />
            ))}
          </div>

          {/* center — top materials */}
          <div className="col center">
            <div className="card" style={{ animationDelay: "0.15s" }}>
              <div className="sec-head"><span className="led" /> Top Materials by Weight</div>
              <div className="mat-list">
                {top.map((m) => <MatRow key={m.material} m={m} pct={(m.weight / matMax) * 100} />)}
              </div>
              <button className="view-all" type="button">
                View all {data.totalMaterials} materials  &rarr;
              </button>
            </div>
          </div>

          {/* right — total + category breakdown */}
          <div className="col right">
            <TotalCard />
            <div className="card" style={{ animationDelay: "0.28s" }}>
              <div className="sec-head"><span className="led" /> Category Breakdown</div>
              <div className="cat-list">
                {cats.map((c) => <CatRow key={c.category} c={c} totalWeight={data.totalWeight} />)}
              </div>
            </div>
          </div>
        </div>

        <div className="foot-note">
          Source: <b>materials_summary.csv</b> · ACTIA Material Extractor · {data.totalMaterials} materials · {data.categoryCount} categories
        </div>
      </div>
    </>
  );
}
