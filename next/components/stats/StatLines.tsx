"use client";

import { useMemo, useState } from "react";
import type { StatLine } from "@/lib/contracts";
import { isHot, probColor } from "@/lib/probScale";

/** P(X > line) from a pmf that starts at `start`. */
function over(l: StatLine, line: number): number {
  let p = 0;
  for (let i = 0; i < l.pmf.length; i++) if (l.start + i > line) p += l.pmf[i];
  return Math.min(1, Math.max(0, p));
}

const FAV_MIN = 0.65;

/**
 * Default line: the one whose favoured side (Más or Menos) is the most likely to hit while staying meaningful —
 * the smallest favourite probability that is still ≥ 65%. Ties go to the line nearest the expected value.
 */
export function defaultLine(l: StatLine): number {
  const lo = l.start - 0.5;
  const hi = l.start + l.pmf.length - 1.5;
  let best: { line: number; fav: number } | null = null;
  for (let line = Math.max(0.5, lo); line <= hi; line += 1) {
    const o = over(l, line);
    const fav = Math.max(o, 1 - o);
    if (fav < FAV_MIN) continue;
    if (!best || fav < best.fav - 1e-9 || (Math.abs(fav - best.fav) < 1e-9 && Math.abs(line - l.mean) < Math.abs(best.line - l.mean))) {
      best = { line, fav };
    }
  }
  return best?.line ?? Math.max(0.5, Math.round(l.mean - 0.5) + 0.5);
}

const pct = (p: number) => `${Math.round(p * 100)}%`;
const fmtLine = (n: number) => n.toLocaleString("es-CO", { minimumFractionDigits: 1, maximumFractionDigits: 1 });

function LineCard({ l }: { l: StatLine }) {
  const first = Math.max(0.5, l.start - 0.5);
  const last = l.start + l.pmf.length - 1.5;
  const [line, setLine] = useState(() => defaultLine(l));
  const o = over(l, line);
  const u = 1 - o;
  const favOver = o >= u;
  const step = (d: number) => setLine((x) => Math.min(last, Math.max(first, x + d)));

  return (
    <div className="rounded-[12px] border border-line p-4">
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="text-sm text-hi">{l.label}</h3>
        <span className="num text-[11px] text-lo whitespace-nowrap">esperado {l.mean.toLocaleString("es-CO", { maximumFractionDigits: 2 })}</span>
      </div>

      <div className="mt-3 flex items-center gap-2">
        <button type="button" onClick={() => step(-0.5)} disabled={line <= first} aria-label="Bajar la línea 0.5"
          className="grid h-9 w-9 place-items-center rounded-lg border border-line text-mid hover:text-hi disabled:opacity-30">−</button>
        <div className="flex-1 text-center">
          <div className="num text-xl font-semibold">{fmtLine(line)}</div>
          <div className="text-[11px] text-lo">línea</div>
        </div>
        <button type="button" onClick={() => step(0.5)} disabled={line >= last} aria-label="Subir la línea 0.5"
          className="grid h-9 w-9 place-items-center rounded-lg border border-line text-mid hover:text-hi disabled:opacity-30">+</button>
      </div>

      <Histogram l={l} line={line} over={o} />
      <div className="mt-3 grid grid-cols-2 gap-2 text-sm" aria-live="polite">
        <div className={`rounded-lg px-2.5 py-2 ${!favOver ? "bg-[var(--gold-faint)]" : ""}`}>
          <div className={`num text-lg font-semibold ${isHot(u) ? "p-glow" : ""}`} style={{ color: probColor(u) }}>{pct(u)}</div>
          <div className="text-[11px] text-lo">Menos de {fmtLine(line)}</div>
        </div>
        <div className={`rounded-lg px-2.5 py-2 text-right ${favOver ? "bg-[var(--gold-faint)]" : ""}`}>
          <div className={`num text-lg font-semibold ${isHot(o) ? "p-glow" : ""}`} style={{ color: probColor(o) }}>{pct(o)}</div>
          <div className="text-[11px] text-lo">Más de {fmtLine(line)}</div>
        </div>
      </div>
    </div>
  );
}

/** The full distribution as bars; the ones above the line take the "Más" colour, the rest the "Menos" colour. */
function Histogram({ l, line, over: o }: { l: StatLine; line: number; over: number }) {
  // Trim the long tail so the bars stay readable.
  let lo = 0, hi = l.pmf.length - 1, acc = 0;
  while (lo < hi && acc + l.pmf[lo] < 0.003) acc += l.pmf[lo++];
  acc = 0;
  while (hi > lo && acc + l.pmf[hi] < 0.003) acc += l.pmf[hi--];
  const bars = l.pmf.slice(lo, hi + 1);
  const max = Math.max(...bars) || 1;
  const cOver = probColor(o), cUnder = probColor(1 - o);
  return (
    <div className="mt-3" aria-hidden>
      <div className="flex h-12 items-end gap-[2px]">
        {bars.map((v, i) => {
          const x = l.start + lo + i;
          const isOver = x > line;
          return (
            <div key={x} className="flex-1 rounded-t-[2px] transition-colors duration-200"
              style={{ height: `${Math.max(4, (v / max) * 100)}%`, background: isOver ? cOver : cUnder, opacity: isOver === o >= 0.5 ? 1 : 0.35 }} />
          );
        })}
      </div>
      <div className="mt-1 flex justify-between num text-[10px] text-lo">
        <span>{l.start + lo}</span>
        <span>{l.start + hi}{hi < l.pmf.length - 1 ? "+" : ""}</span>
      </div>
    </div>
  );
}

/** Every count the model prices (goals, corners, cards, shots, points, player props) with a ±0.5 line stepper. */
export function StatLines({ lines }: { lines: StatLine[] }) {
  const groups = useMemo(() => {
    const m = new Map<string, StatLine[]>();
    for (const l of lines) m.set(l.group, [...(m.get(l.group) ?? []), l]);
    return Array.from(m.entries());
  }, [lines]);
  const [active, setActive] = useState(groups[0]?.[0] ?? "");
  const shown = groups.find(([g]) => g === active)?.[1] ?? [];

  return (
    <div>
      {groups.length > 1 && (
        <div className="scroll-x -mx-1 flex gap-2 px-1 text-sm" role="tablist" aria-label="Tipo de estadística">
          {groups.map(([g]) => (
            <button key={g} type="button" role="tab" aria-selected={g === active} onClick={() => setActive(g)}
              className={`whitespace-nowrap rounded-full border px-3 py-1 transition-colors ${g === active ? "border-[var(--border-glass)] bg-[var(--gold-faint)] text-hi" : "border-line text-lo hover:text-hi"}`}>
              {g}
            </button>
          ))}
        </div>
      )}
      <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {shown.map((l) => <LineCard key={l.key} l={l} />)}
      </div>
    </div>
  );
}
