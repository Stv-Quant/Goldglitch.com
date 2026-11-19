import { useId } from "react";

/**
 * A count distribution drawn as a bell: a smooth density through the model's real probabilities (a sum of narrow
 * Gaussians centred on each value), so skew is kept and nothing spills below zero. With `line`, the area left of it
 * takes `under` and the right `over`; without, the curve is gold and the most likely value is marked.
 */
export function Bell({ pmf, start = 0, line, under, over, dimUnder = false, dimOver = false, height = 56, tail = 0.003, plusLast = false, labels }: {
  pmf: number[]; start?: number; line?: number; under?: string; over?: string;
  dimUnder?: boolean; dimOver?: boolean; height?: number; tail?: number; plusLast?: boolean;
  /** Optional value labels under the curve (e.g. ["0","1",…,"5+"]); default: first, line and last. */
  labels?: React.ReactNode[];
}) {
  const id = useId().replace(/:/g, "");
  let lo = 0, hi = pmf.length - 1, acc = 0;
  while (lo < hi && acc + pmf[lo] < tail) acc += pmf[lo++];
  acc = 0;
  while (hi > lo && acc + pmf[hi] < tail) acc += pmf[hi--];

  const W = 300, H = height, pad = 3;
  const x0 = start + lo - 0.55, x1 = start + hi + 0.55;
  const sx = (x: number) => ((x - x0) / (x1 - x0)) * W;
  const mean = pmf.reduce((s, p, i) => s + p * (start + i), 0) / (pmf.reduce((s, p) => s + p, 0) || 1);
  const h = Math.max(0.42, Math.min(0.9, 0.5 + (hi - lo) * 0.02));
  const dens = (x: number) => pmf.reduce((s, p, i) => s + p * Math.exp(-0.5 * ((x - (start + i)) / h) ** 2), 0);
  const N = 96;
  const pts = Array.from({ length: N + 1 }, (_, i) => { const x = x0 + ((x1 - x0) * i) / N; return [x, dens(x)] as const; });
  const max = Math.max(...pts.map((p) => p[1])) || 1;
  const sy = (y: number) => H - pad - (y / max) * (H - pad * 2);
  const curve = pts.map(([x, y], i) => `${i ? "L" : "M"}${sx(x).toFixed(1)} ${sy(y).toFixed(1)}`).join(" ");
  const area = `${curve} L${W} ${H} L0 ${H} Z`;
  const mode = start + pmf.indexOf(Math.max(...pmf));
  const lx = line !== undefined ? Math.max(0, Math.min(W, sx(line))) : null;
  const gold = "var(--gold)";

  return (
    <div aria-hidden>
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="block w-full" style={{ height: H }}>
        <defs>
          <linearGradient id={`g${id}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#fff" stopOpacity="0.9" />
            <stop offset="1" stopColor="#fff" stopOpacity="0.15" />
          </linearGradient>
          <mask id={`m${id}`}><path d={area} fill={`url(#g${id})`} /></mask>
          {lx !== null && (
            <>
              <clipPath id={`u${id}`}><rect x="0" y="0" width={W} height={H} className="bell-clip" style={{ transform: `translateX(${lx - W}px)` }} /></clipPath>
              <clipPath id={`o${id}`}><rect x="0" y="0" width={W} height={H} className="bell-clip" style={{ transform: `translateX(${lx}px)` }} /></clipPath>
            </>
          )}
        </defs>
        {lx !== null ? (
          <>
            <g clipPath={`url(#u${id})`} opacity={dimUnder ? 0.35 : 1}>
              <rect width={W} height={H} fill={under ?? gold} mask={`url(#m${id})`} />
              <path d={curve} fill="none" stroke={under ?? gold} strokeWidth="1.6" vectorEffect="non-scaling-stroke" />
            </g>
            <g clipPath={`url(#o${id})`} opacity={dimOver ? 0.35 : 1}>
              <rect width={W} height={H} fill={over ?? gold} mask={`url(#m${id})`} />
              <path d={curve} fill="none" stroke={over ?? gold} strokeWidth="1.6" vectorEffect="non-scaling-stroke" />
            </g>
            <line x1={lx} x2={lx} y1="0" y2={H} stroke="var(--text-hi)" strokeOpacity="0.55" strokeDasharray="3 3" vectorEffect="non-scaling-stroke" className="bell-clip" />
          </>
        ) : (
          <>
            <rect width={W} height={H} fill={gold} mask={`url(#m${id})`} opacity="0.55" />
            <path d={curve} fill="none" stroke={gold} strokeWidth="1.8" vectorEffect="non-scaling-stroke" />
            <line x1={sx(mode)} x2={sx(mode)} y1={sy(dens(mode))} y2={H} stroke="var(--gold)" strokeOpacity="0.7" strokeDasharray="2 3" vectorEffect="non-scaling-stroke" />
          </>
        )}
      </svg>
      <div className={`relative mt-1 num text-[10px] text-lo ${labels ? "h-9" : "h-3.5"}`}>
        {labels
          ? labels.map((t, i) => (
              <span key={i} className="absolute -translate-x-1/2 text-center" style={{ left: `${(sx(start + i) / W) * 100}%` }}>{t}</span>
            ))
          : (
            <>
              <span className="absolute left-0">{start + lo}</span>
              {line === undefined && (
                <span className="absolute -translate-x-1/2 text-mid" style={{ left: `${(sx(mean) / W) * 100}%` }}>media {mean.toFixed(1)}</span>
              )}
              <span className="absolute right-0">{start + hi}{plusLast || hi < pmf.length - 1 ? "+" : ""}</span>
            </>
          )}
      </div>
    </div>
  );
}
