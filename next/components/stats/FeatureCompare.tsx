type Row = { label: string; home: number | string; away: number | string; better?: "higher" | "lower" };

/** Mirrored head-to-head bars. The better side per row is bright; the other recedes. */
export function FeatureCompare({ rows, homeShort, awayShort }: { rows: Row[]; homeShort: string; awayShort: string }) {
  if (!rows.length) return null;
  return (
    <div className="space-y-3">
      <div className="flex justify-between text-[11px] text-lo">
        <span className="num">{homeShort}</span>
        <span className="num">{awayShort}</span>
      </div>
      {rows.map((r) => {
        const h = typeof r.home === "number" ? r.home : NaN;
        const a = typeof r.away === "number" ? r.away : NaN;
        const numeric = Number.isFinite(h) && Number.isFinite(a) && h + a > 0;
        const hw = numeric ? (h / (h + a)) * 100 : 50;
        const homeBetter = numeric && r.better ? (r.better === "higher" ? h > a : h < a) : null;
        const better = (side: "home" | "away") => homeBetter !== null && (side === "home") === homeBetter;
        // Text keeps AA contrast on both sides; only the bar recedes for the weaker side.
        const tone = (side: "home" | "away") => (better(side) ? "var(--text-hi)" : "var(--text-lo)");
        const bar = (side: "home" | "away") => (better(side) ? "var(--text-hi)" : "var(--seg-2)");
        return (
          <div key={r.label}>
            <div className="flex items-baseline justify-between text-sm">
              <span className="num" style={{ color: tone("home") }}>{r.home}</span>
              <span className="text-xs text-lo">{r.label}</span>
              <span className="num" style={{ color: tone("away") }}>{r.away}</span>
            </div>
            <div className="mt-1 flex h-1 gap-[2px]" aria-hidden>
              <div className="rounded-l-full" style={{ width: `${hw}%`, background: bar("home"), opacity: 0.7 }} />
              <div className="rounded-r-full" style={{ width: `${100 - hw}%`, background: bar("away"), opacity: 0.7 }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
