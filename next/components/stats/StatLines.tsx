"use client";

import { useMemo, useState } from "react";
import type { StatLine } from "@/lib/contracts";

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
const fair = (p: number) => (p > 0.005 ? (1 / p).toFixed(2) : "—");
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

      <div className="mt-3 flex h-2 overflow-hidden rounded-full bg-[var(--seg-3)]" aria-hidden>
        <div className="h-full transition-[width] duration-200" style={{ width: `${u * 100}%`, background: favOver ? "var(--seg-2)" : "var(--gold)" }} />
        <div className="h-full flex-1 transition-[width] duration-200" style={{ background: favOver ? "var(--gold)" : "var(--seg-2)" }} />
      </div>
      <div className="mt-2 grid grid-cols-2 gap-2 text-sm" aria-live="polite">
        <div>
          <div className={`num font-semibold ${!favOver ? "text-gold" : ""}`}>{pct(u)}</div>
          <div className="text-[11px] text-lo">Menos de {fmtLine(line)} · cuota justa {fair(u)}</div>
        </div>
        <div className="text-right">
          <div className={`num font-semibold ${favOver ? "text-gold" : ""}`}>{pct(o)}</div>
          <div className="text-[11px] text-lo">Más de {fmtLine(line)} · cuota justa {fair(o)}</div>
        </div>
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
        <div className="flex flex-wrap gap-2 text-sm" role="tablist" aria-label="Tipo de estadística">
          {groups.map(([g]) => (
            <button key={g} type="button" role="tab" aria-selected={g === active} onClick={() => setActive(g)}
              className={`rounded-full border px-3 py-1 transition-colors ${g === active ? "border-[var(--border-glass)] bg-[var(--gold-faint)] text-hi" : "border-line text-lo hover:text-hi"}`}>
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
