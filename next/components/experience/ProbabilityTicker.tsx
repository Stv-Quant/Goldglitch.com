"use client";

import { useEffect, useState } from "react";

type Item = { sport: string; home: string; away: string; p: number[] };

// Illustrative values only (labelled on screen). Real fixtures come from SQPC via /api/ingest.
const ROW_A: Item[] = [
  { sport: "FÚT", home: "AME", away: "CAL", p: [50, 27, 23] },
  { sport: "MLB", home: "NYY", away: "BOS", p: [58, 42] },
  { sport: "FÚT", home: "ARS", away: "LIV", p: [49, 27, 24] },
  { sport: "MLB", home: "LAD", away: "SFG", p: [61, 39] },
  { sport: "FÚT", home: "NAL", away: "MIL", p: [52, 29, 19] },
  { sport: "MLB", home: "HOU", away: "SEA", p: [54, 46] },
];
const ROW_B: Item[] = [
  { sport: "NBA", home: "BOS", away: "LAL", p: [62, 38] },
  { sport: "TEN", home: "J. A", away: "J. B", p: [57, 43] },
  { sport: "FÚT", home: "MCI", away: "CHE", p: [57, 24, 19] },
  { sport: "NBA", home: "DEN", away: "PHX", p: [55, 45] },
  { sport: "TEN", home: "J. C", away: "J. D", p: [71, 29] },
  { sport: "FÚT", home: "JUN", away: "TOL", p: [43, 32, 25] },
];

type Flash = { row: number; idx: number; dir: 1 | -1; id: number } | null;

/** Moves 1–3 points between two outcomes so every row still sums to 100. */
function nudge(items: Item[]): [Item[], number, 1 | -1] {
  const idx = Math.floor(Math.random() * items.length);
  const it = items[idx];
  const from = Math.floor(Math.random() * it.p.length);
  let to = Math.floor(Math.random() * it.p.length);
  if (to === from) to = (to + 1) % it.p.length;
  const d = Math.min(1 + Math.floor(Math.random() * 3), it.p[from] - 5);
  const p = [...it.p];
  p[from] -= d;
  p[to] += d;
  const next = items.map((x, i) => (i === idx ? { ...x, p } : x));
  return [next, idx, to === 0 ? 1 : -1];
}

function Row({ items, reverse, dur, flash, row }: { items: Item[]; reverse?: boolean; dur: string; flash: Flash; row: number }) {
  const doubled = [...items, ...items];
  return (
    <div className="ticker overflow-hidden py-3">
      <ul className="ticker-track" data-reverse={reverse ? "" : undefined} style={{ ["--ticker-dur" as string]: dur }}>
        {doubled.map((m, i) => {
          const max = Math.max(...m.p);
          const lit = flash && flash.row === row && flash.idx === i % items.length;
          return (
            <li key={i} className={`flex items-center gap-4 num text-sm whitespace-nowrap ${lit ? "tick-lit" : ""}`} aria-hidden={i >= items.length}>
              <span className="text-[10px] tracking-[0.2em] text-lo border border-line rounded px-1.5 py-0.5">{m.sport}</span>
              <span className="text-hi">{m.home}</span>
              <span className="flex gap-2">
                {m.p.map((v, j) => (
                  <span key={j} style={{ color: v === max ? "var(--gold)" : "var(--text-lo)" }}>{v}</span>
                ))}
              </span>
              <span className="text-hi">{m.away}</span>
              {lit && (
                <span key={flash!.id} className="tick-delta text-[10px]" style={{ color: flash!.dir > 0 ? "var(--neon-up)" : "var(--neon-down)" }}>
                  {flash!.dir > 0 ? "▲" : "▼"}
                </span>
              )}
              <span className="text-line">/</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export function ProbabilityTicker() {
  const [a, setA] = useState(ROW_A);
  const [b, setB] = useState(ROW_B);
  const [flash, setFlash] = useState<Flash>(null);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let n = 0;
    const id = setInterval(() => {
      const row = n++ % 2;
      if (row === 0) setA((cur) => { const [next, idx, dir] = nudge(cur); setFlash({ row, idx, dir, id: n }); return next; });
      else setB((cur) => { const [next, idx, dir] = nudge(cur); setFlash({ row, idx, dir, id: n }); return next; });
    }, 1400);
    return () => clearInterval(id);
  }, []);

  return (
    <section aria-label="Ejemplos de probabilidades" className="relative border-y border-line bg-[var(--bg-raise)]/60 py-2 my-10">
      <div className="px-5 sm:px-6 pt-2 flex items-center gap-2 num text-[10px] tracking-[0.2em] uppercase text-lo">
        <span className="live-dot" aria-hidden /> Recalculando
      </div>
      <Row items={a} dur="55s" flash={flash} row={0} />
      <Row items={b} dur="70s" reverse flash={flash} row={1} />
      <p className="px-5 sm:px-6 pb-2 text-[10px] num tracking-[0.18em] uppercase text-lo">
        Ejemplos ilustrativos · el número dorado es el resultado más probable, no una garantía
      </p>
    </section>
  );
}
