import { pct } from "@/lib/format";

type Outcome = { key: "home" | "draw" | "away"; label: string; p: number; interval?: [number, number] | null };

/**
 * 1X2 probability strip. The most likely outcome is the only gold element (first fixation);
 * the others step down in luminance. Uncertainty ranges render as brackets under each value.
 */
export function ProbabilityBar({
  home,
  draw,
  away,
  labels,
  interval,
  size = "md",
}: {
  home: number;
  draw: number | null;
  away: number;
  labels: { home: string; away: string };
  interval?: { home: [number, number]; draw: [number, number] | null; away: [number, number] };
  size?: "sm" | "md";
}) {
  const outcomes: Outcome[] = [
    { key: "home", label: labels.home, p: home, interval: interval?.home },
    ...(draw !== null ? [{ key: "draw" as const, label: "Empate", p: draw, interval: interval?.draw }] : []),
    { key: "away", label: labels.away, p: away, interval: interval?.away },
  ];
  const total = outcomes.reduce((s, o) => s + o.p, 0) || 1;
  const ranked = [...outcomes].sort((a, b) => b.p - a.p).map((o) => o.key);
  const fill = (k: Outcome["key"]) =>
    k === ranked[0] ? "var(--gold)" : k === ranked[1] ? "var(--seg-2)" : "var(--seg-3)";

  const h = size === "sm" ? "h-1.5" : "h-2.5";

  return (
    <div className="w-full">
      <div
        className={`flex ${h} w-full overflow-hidden rounded-full gap-[2px]`}
        role="img"
        aria-label={outcomes.map((o) => `${o.label} ${pct(o.p)}`).join(", ")}
      >
        {outcomes.map((o) => (
          <div key={o.key} style={{ width: `${(o.p / total) * 100}%`, background: fill(o.key) }} />
        ))}
      </div>
      <div className={`mt-2 grid ${draw !== null ? "grid-cols-3" : "grid-cols-2"}`}>
        {outcomes.map((o, i) => {
          const align = i === 0 ? "text-left" : i === outcomes.length - 1 ? "text-right" : "text-center";
          const lead = o.key === ranked[0];
          return (
            <div key={o.key} className={align}>
              <div className={`num ${size === "sm" ? "text-sm" : "text-lg"} ${lead ? "text-gold font-semibold" : "text-mid"}`}>
                {pct(o.p)}
              </div>
              {size === "md" && (
                <div className="text-[11px] text-lo truncate">
                  {o.label}
                  {o.interval && (
                    <span className="num ml-1 text-lo" title="Rango de incertidumbre del modelo (80%)">
                      [{pct(o.interval[0])}–{pct(o.interval[1])}]
                    </span>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
