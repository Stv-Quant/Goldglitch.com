import { PROB_STEPS, isHot, probColor } from "@/lib/probScale";

/** A probability rendered in the scale colour. */
export function Prob({ p, className = "", digits = 0 }: { p: number; className?: string; digits?: number }) {
  return (
    <span className={`num ${isHot(p) ? "p-glow" : ""} ${className}`} style={{ color: probColor(p) }}>
      {(p * 100).toFixed(digits)}%
    </span>
  );
}

/** Thin bar filled to p in the scale colour. */
export function ProbMeter({ p, className = "h-1.5" }: { p: number; className?: string }) {
  return (
    <div className={`relative overflow-hidden rounded-full bg-[var(--seg-3)] ${className}`} aria-hidden>
      <div className={`p-fill absolute inset-y-0 left-0 rounded-full ${isHot(p) ? "p-fill-hot" : ""}`}
        style={{ width: `${Math.max(2, p * 100)}%`, ["--pc" as string]: probColor(p) }} />
    </div>
  );
}

/** Legend for the scale. Compact: one row of swatches. */
export function ProbLegend({ className = "" }: { className?: string }) {
  const steps = [...PROB_STEPS].reverse();
  return (
    <div className={`flex items-center gap-2 text-[10px] text-lo ${className}`} aria-label="Escala de probabilidad">
      <span className="uppercase tracking-[0.14em]">Escala</span>
      <div className="flex gap-0.5">
        {steps.map((s) => (
          <span key={s.label} title={`${s.name} · ${s.label}`} className="flex flex-col items-center gap-1">
            <span className="h-2 w-7 rounded-sm sm:w-9" style={{ background: s.color, boxShadow: `0 0 10px -3px ${s.color}` }} />
            <span className="num hidden text-[9px] sm:block" style={{ color: s.color }}>{s.label}</span>
          </span>
        ))}
      </div>
    </div>
  );
}
