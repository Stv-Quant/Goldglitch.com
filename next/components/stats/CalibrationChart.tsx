/**
 * Reliability diagram: predicted probability (x) vs observed frequency (y).
 * Points on the diagonal = the model means what it says. Point area ∝ sample size.
 */
export function CalibrationChart({
  bins,
}: {
  bins: { bin: number; predicted: number; observed: number; n: number }[];
}) {
  const W = 320;
  const H = 320;
  const m = { l: 40, r: 12, t: 12, b: 36 };
  const iw = W - m.l - m.r;
  const ih = H - m.t - m.b;
  const x = (p: number) => m.l + p * iw;
  const y = (p: number) => m.t + (1 - p) * ih;
  const maxN = Math.max(1, ...bins.map((b) => b.n));
  const ticks = [0, 0.25, 0.5, 0.75, 1];
  const path = bins
    .slice()
    .sort((a, b) => a.predicted - b.predicted)
    .map((b, i) => `${i ? "L" : "M"}${x(b.predicted).toFixed(1)},${y(b.observed).toFixed(1)}`)
    .join(" ");

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full max-w-[420px] block" role="img"
      aria-label="Gráfico de calibración: probabilidad pronosticada frente a frecuencia observada">
      {ticks.map((t) => (
        <g key={t}>
          <line x1={x(0)} x2={x(1)} y1={y(t)} y2={y(t)} stroke="var(--border-soft)" />
          <line x1={x(t)} x2={x(t)} y1={y(0)} y2={y(1)} stroke="var(--border-soft)" />
          <text x={m.l - 6} y={y(t) + 3} textAnchor="end" fontSize="10" fill="var(--text-lo)" className="num">{t * 100}%</text>
          <text x={x(t)} y={H - m.b + 14} textAnchor="middle" fontSize="10" fill="var(--text-lo)" className="num">{t * 100}%</text>
        </g>
      ))}
      <line x1={x(0)} y1={y(0)} x2={x(1)} y2={y(1)} stroke="var(--text-lo)" strokeDasharray="4 4" />
      <path d={path} fill="none" stroke="var(--gold)" strokeWidth={1.5} />
      {bins.map((b) => (
        <circle key={b.bin} cx={x(b.predicted)} cy={y(b.observed)} r={3 + 5 * Math.sqrt(b.n / maxN)}
          fill="var(--gold)" fillOpacity={0.85} stroke="var(--bg-void)" strokeWidth={1}>
          <title>{`Pronosticado ${(b.predicted * 100).toFixed(0)}% · ocurrió ${(b.observed * 100).toFixed(0)}% · ${b.n} casos`}</title>
        </circle>
      ))}
      <text x={m.l + iw / 2} y={H - 4} textAnchor="middle" fontSize="10" fill="var(--text-mid)">Probabilidad pronosticada</text>
      <text x={10} y={m.t + ih / 2} textAnchor="middle" fontSize="10" fill="var(--text-mid)"
        transform={`rotate(-90 10 ${m.t + ih / 2})`}>Frecuencia real</text>
    </svg>
  );
}
