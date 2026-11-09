import { pct } from "@/lib/format";

/**
 * Exact-score heatmap. 7×7 = 49 marks → SVG (accessible, crisp, no live updates).
 * Opacity encodes probability; the modal scoreline gets the gold outline.
 */
export function ScoreMatrix({
  matrix,
  homeLabel,
  awayLabel,
  maxGoals = 5,
}: {
  matrix: number[][];
  homeLabel: string;
  awayLabel: string;
  maxGoals?: number;
}) {
  const n = Math.min(maxGoals + 1, matrix.length);
  const cell = 44;
  const pad = 30;
  const size = pad + n * cell;
  let max = 0;
  let best: [number, number] = [0, 0];
  for (let h = 0; h < n; h++)
    for (let a = 0; a < n; a++) {
      const v = matrix[h]?.[a] ?? 0;
      if (v > max) { max = v; best = [h, a]; }
    }

  return (
    <figure className="w-full">
      <svg viewBox={`0 0 ${size} ${size + 6}`} className="w-full max-w-[360px] mx-auto block" role="img"
        aria-label={`Marcador más probable ${best[0]}-${best[1]} con ${pct(max, 1)}`}>
        <text x={pad + (n * cell) / 2} y={12} textAnchor="middle" fontSize="10" fill="var(--text-lo)">
          Goles {awayLabel} →
        </text>
        <text x={10} y={pad + (n * cell) / 2} textAnchor="middle" fontSize="10" fill="var(--text-lo)"
          transform={`rotate(-90 10 ${pad + (n * cell) / 2})`}>
          Goles {homeLabel} →
        </text>
        {Array.from({ length: n }, (_, i) => (
          <g key={`ax${i}`}>
            <text x={pad + i * cell + cell / 2} y={pad - 6} textAnchor="middle" fontSize="10" fill="var(--text-mid)" className="num">{i}</text>
            <text x={pad - 8} y={pad + i * cell + cell / 2 + 3} textAnchor="end" fontSize="10" fill="var(--text-mid)" className="num">{i}</text>
          </g>
        ))}
        {Array.from({ length: n }, (_, h) =>
          Array.from({ length: n }, (_, a) => {
            const v = matrix[h]?.[a] ?? 0;
            const o = max > 0 ? 0.06 + 0.94 * (v / max) : 0;
            const isBest = h === best[0] && a === best[1];
            const x = pad + a * cell;
            const y = pad + h * cell;
            return (
              <g key={`${h}-${a}`}>
                <rect x={x + 1} y={y + 1} width={cell - 2} height={cell - 2} rx={6}
                  fill="var(--gold)" fillOpacity={o * 0.85}
                  stroke={isBest ? "var(--text-hi)" : "none"} strokeWidth={isBest ? 1.5 : 0} />
                {v >= 0.015 && (
                  <text x={x + cell / 2} y={y + cell / 2 + 4} textAnchor="middle" fontSize="11"
                    fill={o > 0.55 ? "#020202" : "var(--text-hi)"} className="num">
                    {(v * 100).toFixed(v >= 0.1 ? 0 : 1)}
                  </text>
                )}
              </g>
            );
          }),
        )}
      </svg>
      <figcaption className="mt-2 text-center text-xs text-lo">
        Probabilidad (%) de cada marcador exacto · más probable{" "}
        <span className="num text-hi">{best[0]}–{best[1]}</span> ({pct(max, 1)})
      </figcaption>
    </figure>
  );
}
