"use client";

import { useEffect, useRef, useState } from "react";
import data from "@/lib/data";
import ShaderBackground from "./ShaderBackground";

const CAT_COLORS = [
  "#0c7a3d", "#1fb35c", "#43bf6b", "#7fd08f", "#12924a",
  "#39b58f", "#2aa9a0", "#5cc98a", "#a7dfae", "#8fe9d2",
  "#0a5f30", "#6fd6a8", "#bfe9c6", "#2f9e6b", "#158a63",
];

function fmt(n) {
  return Number(n).toLocaleString("en-US", { maximumFractionDigits: n < 10 ? 3 : 1 });
}

const ICONS = {
  box: <><path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z" /><path d="M4 7.5l8 4.5 8-4.5" /><path d="M12 12v9" /></>,
  scale: <><path d="M12 3v18" /><path d="M6 7h12" /><path d="M8 21h8" /><path d="M6 7l-3 6a3 3 0 006 0l-3-6z" /><path d="M18 7l-3 6a3 3 0 006 0l-3-6z" /></>,
  layers: <><path d="M12 3l9 5-9 5-9-5 9-5z" /><path d="M3 13l9 5 9-5" /></>,
  chart: <><path d="M4 5v14h16" /><path d="M8 15l3-4 3 2 4-6" /></>,
  award: <><circle cx="12" cy="9" r="5" /><path d="M9 13l-1 8 4-2 4 2-1-8" /></>,
  clock: <><circle cx="12" cy="12" r="8" /><path d="M12 8v4l3 2" /></>,
};

function Icon({ name, size = 20 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      {ICONS[name]}
    </svg>
  );
}

function useCountUp(target, duration = 1400) {
  const [v, setV] = useState(0);
  useEffect(() => {
    let raf, start;
    const step = (t) => {
      if (!start) start = t;
      const p = Math.min((t - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setV(target * eased);
      if (p < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);
  return v;
}

function Sparkline({ series, color }) {
  const pts = series.slice(0, 40);
  const max = Math.max(...pts), min = Math.min(...pts);
  const span = max - min || 1;
  const W = 220, H = 34;
  const coords = pts.map((y, i) => {
    const x = (i / (pts.length - 1)) * W;
    const yy = H - 3 - ((y - min) / span) * (H - 6);
    return `${x.toFixed(1)},${yy.toFixed(1)}`;
  }).join(" ");
  return (
    <svg className="spark" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
      <polyline points={coords} fill="none" stroke={color} strokeWidth="2"
        strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function Kpi({ icon, tone, label, value, suffix, decimals = 0, series, color }) {
  const v = useCountUp(value);
  return (
    <div className="kpi">
      <div className="top">
        <span className={`icon ${tone}`}><Icon name={icon} /></span>
        <span className="label">{label}</span>
      </div>
      <div className="value">
        {v.toLocaleString("en-US", { maximumFractionDigits: decimals })}
        {suffix ? <small> {suffix}</small> : null}
      </div>
      <Sparkline series={series} color={color} />
    </div>
  );
}

function Clock() {
  const [t, setT] = useState(null);
  useEffect(() => {
    const tick = () => setT(new Date().toLocaleTimeString("fr-FR"));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);
  return <span className="clock"><Icon name="clock" size={15} /> {t || "--:--:--"}</span>;
}

function BarList({ title, rows, max, unit }) {
  return (
    <div className="panel">
      <div className="p-title"><span className="dot" />{title}</div>
      {rows.map((r) => (
        <div className="bar" key={r.material}>
          <div className="row">
            <span className="name" title={r.material}>{r.material}</span>
            <span className="val">{fmt(r.weight)} {unit}</span>
          </div>
          <div className="track">
            <div className="fill" style={{ width: `${Math.max((r.weight / max) * 100, 1.5)}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function Donut() {
  const top = data.categories.slice(0, 6);
  const rest = data.categories.slice(6).reduce((s, c) => s + c.weight, 0);
  const slices = [...top, ...(rest > 0 ? [{ category: "Other", weight: rest }] : [])];
  const total = slices.reduce((s, c) => s + c.weight, 0);
  const R = 54, C = 2 * Math.PI * R;
  let offset = 0;
  const [ready, setReady] = useState(false);
  useEffect(() => { const t = setTimeout(() => setReady(true), 120); return () => clearTimeout(t); }, []);
  return (
    <div className="panel teal">
      <div className="p-title"><span className="dot" />Composition by Category</div>
      <div className="donut-wrap">
        <div style={{ position: "relative", width: 140, height: 140 }}>
          <svg className="donut" width="140" height="140" viewBox="0 0 140 140">
            <circle cx="70" cy="70" r={R} fill="none" stroke="rgba(12,122,61,0.10)" strokeWidth="18" />
            {slices.map((s, i) => {
              const len = ready ? (s.weight / total) * C : 0;
              const el = (
                <circle key={s.category} cx="70" cy="70" r={R} fill="none"
                  stroke={CAT_COLORS[i % CAT_COLORS.length]} strokeWidth="18"
                  strokeDasharray={`${len} ${C - len}`} strokeDashoffset={-offset} strokeLinecap="butt" />
              );
              offset += ready ? (s.weight / total) * C : 0;
              return el;
            })}
          </svg>
          <div className="donut-center" style={{ inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
            <div style={{ fontSize: 22, fontWeight: 900, color: "#0a5f30" }}>{data.categoryCount}</div>
            <div style={{ fontSize: 10, color: "#3c6b4c", letterSpacing: 1 }}>CATEGORIES</div>
          </div>
        </div>
        <div className="legend">
          {slices.map((s, i) => (
            <div className="li" key={s.category}>
              <span className="sw" style={{ background: CAT_COLORS[i % CAT_COLORS.length] }} />
              <span style={{ flex: 1 }}>{s.category}</span>
              <b>{Math.round((s.weight / total) * 100)}%</b>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function Page() {
  const maxWeight = data.topByWeight[0].weight;
  const maxCat = data.categories[0].weight;

  const catCounts = data.categories.map((c) => c.count);
  const catWeights = data.categories.map((c) => c.weight);
  const topWeights = data.topByWeight.map((m) => m.weight);
  const occ = data.topByOccurrence.map((m) => m.occurrences);

  return (
    <>
      <ShaderBackground />
      <header className="header">
        <div className="logo">
          <span className="word">ACTIA<sup>®</sup></span>
          <span className="grid">
            {Array.from({ length: 9 }).map((_, i) => <span key={i} />)}
          </span>
          <span className="stack"><span className="group">GROUP</span></span>
        </div>
        <div className="sub">Material Composition Report · <b>MCF8315C-Q1 · MC121EVM</b></div>
        <div className="right">
          <span className="status"><span className="led" /> Ligne active</span>
          <Clock />
        </div>
      </header>

      <div className="wrap">
        {/* KPI ROW */}
        <div className="kpi-row">
          <Kpi icon="box" tone="green" label="Total Materials" value={data.totalMaterials} series={catCounts} color="#1fb35c" />
          <Kpi icon="scale" tone="blue" label="Total Weight" value={data.totalWeight} suffix="mg" decimals={1} series={topWeights} color="#2f6bff" />
          <Kpi icon="layers" tone="teal" label="Categories" value={data.categoryCount} series={catWeights} color="#17a98f" />
          <Kpi icon="chart" tone="violet" label="Data Points" value={data.totalOccurrences} series={occ} color="#7048e8" />
          <Kpi icon="award" tone="amber" label="Heaviest Material" value={data.topByWeight[0].weight} suffix="mg" decimals={1} series={topWeights} color="#f0932b" />
        </div>

        <div className="divider" />

        {/* MAIN GRID */}
        <div className="main-grid">
          {/* LEFT — top categories as slanted panels */}
          <div className="col">
            {data.categories.slice(0, 4).map((c, i) => (
              <div className={`panel slant ${i === 0 ? "deep" : ""}`} key={c.category}>
                <div className="k-label">{c.category}</div>
                <div className="k-value" style={{ fontSize: 30 }}>{fmt(c.weight)}<small> mg</small></div>
                <div className="track" style={{ marginTop: 10, height: 8, borderRadius: 8, background: "rgba(255,255,255,0.35)", overflow: "hidden" }}>
                  <div className="fill" style={{ width: `${(c.weight / maxCat) * 100}%` }} />
                </div>
                <div className="k-foot">{c.count} material{c.count > 1 ? "s" : ""}</div>
              </div>
            ))}
          </div>

          {/* MIDDLE — main charts */}
          <div className="col">
            <BarList title="Top Materials by Weight" rows={data.topByWeight} max={maxWeight} unit="mg" />
            <Donut />
            <div className="panel">
              <div className="p-title"><span className="dot" />Most Frequently Declared</div>
              <table className="tbl">
                <thead><tr><th>Material</th><th>Category</th><th style={{ textAlign: "right" }}>Occurrences</th></tr></thead>
                <tbody>
                  {data.topByOccurrence.map((r) => (
                    <tr key={r.material}>
                      <td>{r.material}</td>
                      <td style={{ color: "#3c6b4c" }}>{r.category}</td>
                      <td className="num">{r.occurrences}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* RIGHT — category chips + heaviest table + coverage */}
          <div className="col">
            <div className="panel">
              <div className="p-title"><span className="dot" />Category Breakdown</div>
              <div className="chips">
                {data.categories.slice(0, 8).map((c, i) => (
                  <div className="chip" key={c.category}>
                    <span className="c-name"><span className="swatch" style={{ background: CAT_COLORS[i % CAT_COLORS.length] }} />{c.category}</span>
                    <span className="c-val">{fmt(c.weight)} mg</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="panel deep">
              <div className="p-title" style={{ color: "#eafaf0" }}><span className="dot" />Heaviest Contributors</div>
              <table className="tbl">
                <tbody>
                  {data.topByWeight.slice(0, 6).map((r) => (
                    <tr key={r.material}>
                      <td style={{ color: "#f2fff6", border: "none" }}>{r.material}</td>
                      <td className="num" style={{ color: "#ffffff", border: "none" }}>{fmt(r.weight)} mg</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="panel teal">
              <div className="k-label">Board Composition</div>
              <div className="k-value" style={{ fontSize: 34 }}>{fmt(data.totalWeight)}<small> mg</small></div>
              <div className="k-foot">across {data.totalMaterials} materials in {data.categoryCount} categories</div>
            </div>
          </div>
        </div>

        <div className="divider" />
        <div className="foot-note">
          Source: <b>materials_summary.csv</b> · ACTIA Material Extractor
        </div>
      </div>
    </>
  );
}
