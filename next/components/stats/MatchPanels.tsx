import type { RedactedPrediction } from "@/lib/entitlements";
import type { Pick } from "@/lib/picks";
import { PICK_FEATURED, PICK_MIN } from "@/lib/picks";
import { probColor } from "@/lib/probScale";
import { Prob, ProbMeter } from "./Prob";

/** One pick: what, how likely (scale colour), confidence and fair price. */
export function PickCard({ k }: { k: Pick }) {
  const featured = k.p >= PICK_FEATURED;
  return (
    <div className="relative h-full overflow-hidden rounded-[12px] border border-line bg-[var(--bg-raise)] p-4"
      style={featured ? { borderColor: `color-mix(in srgb, ${probColor(k.p)} 45%, transparent)` } : undefined}>
      <span aria-hidden className="absolute inset-y-0 left-0 w-1" style={{ background: probColor(k.p) }} />
      <div className="flex items-center justify-between gap-2 text-[10px] uppercase tracking-[0.16em] text-lo">
        <span className="truncate">{k.source}</span>
        {k.grade && <span style={{ color: probColor(k.p) }}>{k.grade}</span>}
      </div>
      <div className="mt-1.5 text-sm leading-snug text-hi">{k.label}</div>
      <div className="mt-2 flex items-baseline justify-between gap-2">
        <Prob p={k.p} className="text-3xl font-semibold" />
        <span className="num text-[11px] text-lo">cuota justa {(1 / k.p).toFixed(2)}</span>
      </div>
      {(k.lo != null && k.hi != null) || k.price ? (
        <div className="mt-1 flex justify-between gap-2 num text-[11px] text-lo">
          <span>{k.lo != null && k.hi != null ? `rango ${Math.round(k.lo * 100)}–${Math.round(k.hi * 100)}%` : ""}</span>
          <span>{k.price ? `${k.book ?? "casa"} ${k.price.toFixed(2)}` : ""}</span>
        </div>
      ) : null}
    </div>
  );
}

/** Top picks visible; the rest one tap away so the page stays short. */
export function PicksList({ picks, visible = 6 }: { picks: Pick[]; visible?: number }) {
  const head = picks.slice(0, visible);
  const rest = picks.slice(visible);
  const grid = "grid gap-3 sm:grid-cols-2 lg:grid-cols-3";
  return (
    <div>
      {/* Phones: one swipeable row keeps the page short. */}
      <ul className="scroll-x -mx-4 flex snap-x gap-3 px-4 sm:hidden">
        {picks.map((k) => <li key={k.key} className="w-[76%] shrink-0 snap-start"><PickCard k={k} /></li>)}
      </ul>
      {picks.length > 1 && <p className="mt-2 text-[11px] text-lo sm:hidden">Desliza para ver los {picks.length} picks →</p>}
      <div className="hidden sm:block">
      <ul className={grid}>{head.map((k) => <li key={k.key}><PickCard k={k} /></li>)}</ul>
      {rest.length > 0 && (
        <details className="group mt-3">
          <summary className="cursor-pointer list-none text-sm text-gold">
            <span className="group-open:hidden">Ver {rest.length} pick{rest.length === 1 ? "" : "s"} más</span>
            <span className="hidden group-open:inline">Ver menos</span>
          </summary>
          <ul className={`${grid} mt-3`}>{rest.map((k) => <li key={k.key}><PickCard k={k} /></li>)}</ul>
        </details>
      )}
      </div>
    </div>
  );
}

export function MarketsPanel({ markets }: { markets: NonNullable<RedactedPrediction["markets"]> }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {Array.from(Map.groupBy(markets, (mk) => mk.group ?? "Otros")).map(([g, rows]) => (
        <div key={g} className="card p-4">
          <h3 className="mb-3 text-[11px] uppercase tracking-[0.16em] text-lo">{g}</h3>
          <ul className="space-y-3">
            {[...rows].sort((a, b) => b.p - a.p).map((mk) => (
              <li key={mk.key}>
                <div className="flex items-baseline justify-between gap-2 text-sm">
                  <span className="min-w-0 text-mid">
                    {mk.label}
                    {mk.p >= PICK_MIN && <span className="ml-2 rounded px-1.5 py-px text-[9px] font-semibold uppercase tracking-[0.12em]" style={{ background: probColor(mk.p), color: "#0a0907" }}>Pick</span>}
                  </span>
                  <span className="whitespace-nowrap">
                    <Prob p={mk.p} className="font-semibold" />
                    {mk.interval && <span className="num ml-1 text-[10px] text-lo">{Math.round(mk.interval[0] * 100)}–{Math.round(mk.interval[1] * 100)}</span>}
                  </span>
                </div>
                <ProbMeter p={mk.p} className="mt-1.5 h-1" />
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
