"use client";

/**
 * Hand-rolled SVG chart primitives. No chart library — full control over marks,
 * spacing and the 2px surface gaps between adjacent fills.
 *
 * Every mark reports hover through `onHover(content, event)` so the page can
 * drive one shared tooltip.
 */

import { useMemo } from "react";

export const fmt = (n, d = 1) =>
  Number(n).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
export const usd = (n) =>
  n >= 0.01 ? `$${fmt(n, 2)}` : n > 0 ? `$${fmt(n, 4)}` : "$0";
export const pct = (n, d = 0) => `${fmt(n * 100, d)}%`;
export const mg = (n) => (n >= 0.01 ? fmt(n, 2) : n > 0 ? n.toExponential(1) : "0");

/* ============================================================ ARC GAUGE ==== */
/**
 * Recovery Value Score. A 240° arc with the low–high scenario band drawn as a
 * thick sweep, the expected value as a needle, and break-even as a hard tick.
 */
export function ArcGauge({ low, expected, high, threshold, size = 210 }) {
  const R = size * 0.4;
  const cx = size / 2;
  const cy = size * 0.54;
  const START = 150;
  const SWEEP = 240;
  /* Scale is capped so a runaway high case can't push break-even off the dial. */
  const max = Math.max(high, threshold * 2) * 1.05;
  const a = (v) => START + (Math.min(v, max) / max) * SWEEP;
  const pt = (deg, r) => {
    const rad = (deg * Math.PI) / 180;
    return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)];
  };
  const arc = (from, to, r) => {
    const [x1, y1] = pt(from, r);
    const [x2, y2] = pt(to, r);
    return `M ${x1} ${y1} A ${r} ${r} 0 ${to - from > 180 ? 1 : 0} 1 ${x2} ${y2}`;
  };
  const ok = expected >= threshold;
  const tone = ok ? "var(--g-forest)" : "var(--c-hazard)";
  const [tx, ty] = pt(a(threshold), R + 13);
  const [nx, ny] = pt(a(expected), R - 20);

  return (
    <svg viewBox={`0 0 ${size} ${size * 0.78}`} className="gauge" role="img"
      aria-label={`Recovery Value Score ${fmt(expected, 2)}, break-even ${fmt(threshold, 2)}`}>
      <path d={arc(START, START + SWEEP, R)} fill="none" stroke="var(--track)" strokeWidth="14" strokeLinecap="round" />
      <path d={arc(a(low), a(high), R)} fill="none" stroke={tone} strokeWidth="14" strokeLinecap="round" opacity="0.28" />
      <path d={arc(START, a(expected), R)} fill="none" stroke={tone} strokeWidth="6" strokeLinecap="round" />
      {/* break-even */}
      <line
        x1={pt(a(threshold), R - 11)[0]} y1={pt(a(threshold), R - 11)[1]}
        x2={pt(a(threshold), R + 11)[0]} y2={pt(a(threshold), R + 11)[1]}
        stroke="var(--ink)" strokeWidth="2.5"
      />
      <text x={tx} y={ty} className="gauge-tick" textAnchor={tx < cx ? "end" : "start"}>
        {fmt(threshold, 1)}
      </text>
      {/* needle */}
      <line x1={cx} y1={cy} x2={nx} y2={ny} stroke={tone} strokeWidth="3" strokeLinecap="round" />
      <circle cx={cx} cy={cy} r="5" fill={tone} />
      <text x={cx} y={cy - 34} className="gauge-val" textAnchor="middle" fill={tone}>
        {fmt(expected, 2)}
      </text>
      <text x={cx} y={cy + 26} className="gauge-lab" textAnchor="middle">
        {fmt(low, 2)} – {fmt(high, 2)} range
      </text>
    </svg>
  );
}

/* ============================================================== SCATTER ==== */
/**
 * The centrepiece: mass (x, log) against recoverable value (y, log).
 * Materials with no recoverable value sit in a pinned lane along the bottom so
 * "lots of mass, zero value" stays visible instead of being filtered away.
 */
export function MassValueScatter({ materials, buckets, onHover, w = 620, h = 360 }) {
  const P = { l: 54, r: 18, t: 16, b: 52 };
  const iw = w - P.l - P.r;
  const ih = h - P.t - P.b;
  const zeroLane = 26;

  const pts = materials.filter((m) => m.weight > 0);
  const valued = pts.filter((m) => m.value > 0);

  const xs = pts.map((m) => Math.log10(m.weight));
  const x0 = Math.floor(Math.min(...xs));
  const x1 = Math.ceil(Math.max(...xs));
  const X = (v) => P.l + ((Math.log10(v) - x0) / (x1 - x0)) * iw;

  const ys = valued.map((m) => Math.log10(m.value));
  const y0 = Math.floor(Math.min(...ys));
  const y1 = Math.ceil(Math.max(...ys));
  const plotH = ih - zeroLane;
  const Y = (v) => P.t + plotH - ((Math.log10(v) - y0) / (y1 - y0)) * plotH;
  const yZero = P.t + ih - zeroLane / 2;

  const ticks = (a, b) => Array.from({ length: b - a + 1 }, (_, i) => a + i);
  const label = (e) =>
    e >= 3 ? `${10 ** (e - 3)}k` : e >= 0 ? `${10 ** e}` : `0.${"0".repeat(-e - 1)}1`;

  /* Direct-label the few that matter; the rest speak through hover. */
  const named = [...valued].sort((a, b) => b.value - a.value).slice(0, 4);
  const heavy = [...pts].filter((m) => m.value === 0).sort((a, b) => b.weight - a.weight).slice(0, 2);
  const labelled = new Set([...named, ...heavy].map((m) => m.material));

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="chart" role="img"
      aria-label="Material mass against recoverable value">
      {ticks(y0, y1).map((e) => (
        <g key={`y${e}`}>
          <line x1={P.l} x2={w - P.r} y1={Y(10 ** e)} y2={Y(10 ** e)} className="grid" />
          <text x={P.l - 9} y={Y(10 ** e) + 3.5} className="ax" textAnchor="end">
            ${label(e)}
          </text>
        </g>
      ))}
      {ticks(x0, x1).map((e) => (
        <text key={`x${e}`} x={X(10 ** e)} y={h - P.b + 18} className="ax" textAnchor="middle">
          {label(e)}
        </text>
      ))}
      <text x={P.l + iw / 2} y={h - 8} className="ax-title" textAnchor="middle">
        mass in the unit (mg, log)
      </text>
      <text x={14} y={P.t + plotH / 2} className="ax-title" textAnchor="middle"
        transform={`rotate(-90 14 ${P.t + plotH / 2})`}>
        recoverable value (log)
      </text>

      {/* zero-value lane */}
      <line x1={P.l} x2={w - P.r} y1={yZero - zeroLane / 2} y2={yZero - zeroLane / 2} className="grid dash" />
      <text x={P.l - 9} y={yZero + 3.5} className="ax" textAnchor="end">$0</text>

      {pts.map((m) => {
        const cy = m.value > 0 ? Y(m.value) : yZero;
        const r = m.value > 0 ? 6 : 4.5;
        return (
          <circle
            key={m.material}
            cx={X(m.weight)} cy={cy} r={r}
            fill={buckets[m.bucket].color}
            fillOpacity={m.value > 0 ? 0.9 : 0.45}
            stroke="var(--solid)" strokeWidth="2"
            className="dot-mark"
            onMouseEnter={(e) =>
              onHover(
                {
                  title: m.material,
                  rows: [
                    ["Mass", `${mg(m.weight)} mg`],
                    ["Value", usd(m.value)],
                    ["Location", m.primaryLocation],
                    ["Class", buckets[m.bucket].label],
                  ],
                  color: buckets[m.bucket].color,
                },
                e
              )
            }
            onMouseLeave={() => onHover(null)}
          />
        );
      })}
      {pts
        .filter((m) => labelled.has(m.material))
        .map((m) => (
          <text
            key={`l${m.material}`}
            x={X(m.weight) + 10}
            y={(m.value > 0 ? Y(m.value) : yZero) + 3.5}
            className="mark-label"
          >
            {m.material.replace(/\s*\(.*$/, "")}
          </text>
        ))}
    </svg>
  );
}

/* ============================================================== TREEMAP ==== */
function squarify(items, x, y, w, h) {
  const out = [];
  let rest = items.filter((i) => i.value > 0);
  let rx = x, ry = y, rw = w, rh = h;
  let guard = 0;
  while (rest.length && guard++ < 200) {
    const total = rest.reduce((s, i) => s + i.value, 0);
    if (total <= 0 || rw <= 0 || rh <= 0) break;
    const vertical = rw >= rh;
    const side = vertical ? rh : rw;
    let row = [rest[0]];
    let best = Infinity;
    for (let k = 1; k <= rest.length; k++) {
      const cand = rest.slice(0, k);
      const sum = cand.reduce((s, i) => s + i.value, 0);
      const len = (sum / total) * (vertical ? rw : rh);
      const worst = Math.max(
        ...cand.map((i) => {
          const thick = (i.value / sum) * side;
          return thick > 0 && len > 0 ? Math.max(len / thick, thick / len) : Infinity;
        })
      );
      if (worst <= best) { best = worst; row = cand; } else break;
    }
    const sum = row.reduce((s, i) => s + i.value, 0);
    const len = (sum / total) * (vertical ? rw : rh);
    let off = 0;
    for (const i of row) {
      const thick = (i.value / sum) * side;
      out.push(
        vertical
          ? { ...i, x: rx, y: ry + off, w: len, h: thick }
          : { ...i, x: rx + off, y: ry, w: thick, h: len }
      );
      off += thick;
    }
    if (vertical) { rx += len; rw -= len; } else { ry += len; rh -= len; }
    rest = rest.slice(row.length);
  }
  return out;
}

/** Sub-assembly value treemap — area is value, colour is the dominant class. */
export function Treemap({ items, buckets, onHover, onSelect, selected, w = 620, h = 300 }) {
  const cells = useMemo(
    () => squarify([...items].sort((a, b) => b.value - a.value), 0, 0, w, h),
    [items, w, h]
  );
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="chart treemap" role="img"
      aria-label="Sub-assemblies sized by recoverable value">
      {cells.map((c, i) => {
        const dom = Object.entries(c.mix || {}).sort((a, b) => b[1] - a[1])[0];
        const color = buckets[dom ? dom[0] : "common"].color;
        const big = c.w > 92 && c.h > 46;
        const on = selected === c.id;
        return (
          <g key={c.id}
            onMouseEnter={(e) =>
              onHover(
                {
                  title: c.name,
                  rows: [
                    ["Value", usd(c.value)],
                    ["Share of unit", pct(c.valueShare, 1)],
                    ["Mass", `${fmt(c.weight, 0)} mg`],
                    ["Critical mass", `${fmt(c.criticalWeight, 1)} mg`],
                    ["Parts", String(c.partCount)],
                  ],
                  color,
                },
                e
              )
            }
            onMouseLeave={() => onHover(null)}
            onClick={() => onSelect(on ? null : c.id)}
            className="tm-cell"
          >
            {/* 2px inset creates the surface gap between adjacent fills */}
            <rect x={c.x + 1} y={c.y + 1} width={Math.max(0, c.w - 2)} height={Math.max(0, c.h - 2)}
              rx="6" fill={color} fillOpacity={on ? 1 : 0.85}
              stroke={on ? "var(--ink)" : "transparent"} strokeWidth="2" />
            {i === 0 && (
              <rect x={c.x + 7} y={c.y + 7} width="20" height="16" rx="4" fill="var(--solid)" opacity=".9" />
            )}
            {i === 0 && (
              <text x={c.x + 17} y={c.y + 19} className="tm-rank" textAnchor="middle">1st</text>
            )}
            {big && (
              <>
                <text x={c.x + 10} y={c.y + (i === 0 ? 42 : 24)} className="tm-name">
                  {c.name}
                </text>
                <text x={c.x + 10} y={c.y + (i === 0 ? 62 : 43)} className="tm-val">
                  {usd(c.value)} · {pct(c.valueShare, 0)}
                </text>
              </>
            )}
          </g>
        );
      })}
    </svg>
  );
}

/* ========================================================== STACKED BAR ==== */
/** Horizontal 100% stack with 2px surface gaps. Used for mass and value mix. */
export function StackBar({ segments, onHover, height = 30 }) {
  const total = segments.reduce((s, x) => s + x.value, 0) || 1;
  return (
    <div className="stack" style={{ height }}>
      {segments
        .filter((s) => s.value > 0)
        .map((s) => (
          <div
            key={s.key}
            className="stack-seg"
            style={{ width: `${(s.value / total) * 100}%`, background: s.color }}
            onMouseEnter={(e) =>
              onHover({ title: s.label, rows: [[s.unit || "Value", s.display], ["Share", pct(s.value / total, 1)]], color: s.color }, e)
            }
            onMouseLeave={() => onHover(null)}
          />
        ))}
    </div>
  );
}

export function Legend({ items }) {
  return (
    <ul className="legend">
      {items.map((i) => (
        <li key={i.key}>
          <span className="sw" style={{ background: i.color }} />
          {i.label}
        </li>
      ))}
    </ul>
  );
}

/* ================================================================ METER ==== */
export function Meter({ label, value, of, color, display }) {
  const p = of > 0 ? Math.min(1, value / of) : 0;
  return (
    <div className="meter">
      <div className="meter-k">
        <span>{label}</span>
        <b>{display}</b>
      </div>
      <div className="meter-track">
        <span style={{ width: `${p * 100}%`, background: color }} />
      </div>
    </div>
  );
}

/* ============================================================== TOOLTIP ==== */
export function Tooltip({ tip }) {
  if (!tip) return null;
  const { x, y, data } = tip;
  return (
    <div className="tip" style={{ left: x, top: y }} role="tooltip">
      <div className="tip-t">
        <span className="sw" style={{ background: data.color }} />
        {data.title}
      </div>
      <dl>
        {data.rows.map(([k, v]) => (
          <div key={k}>
            <dt>{k}</dt>
            <dd>{v}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
