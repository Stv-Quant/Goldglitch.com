/**
 * Statistics derived from the score matrix SQPC publishes. No new model output is invented:
 * every number here is a sum over P(home = h, away = a).
 */
export type ScoreStats = {
  top: { h: number; a: number; p: number }[];
  cleanSheet: { home: number; away: number };
  winToNil: { home: number; away: number };
  btts: number;
  totalGoals: { label: string; p: number }[];
  expectedTotal: number;
};

export function scoreStats(matrix: number[][], topN = 6): ScoreStats | null {
  const cells: { h: number; a: number; p: number }[] = [];
  let sum = 0;
  matrix.forEach((row, h) => row.forEach((p, a) => { if (p > 0) { cells.push({ h, a, p }); sum += p; } }));
  if (sum <= 0) return null;
  const n = (p: number) => p / sum;
  const pick = (f: (c: { h: number; a: number }) => boolean) => n(cells.filter(f).reduce((s, c) => s + c.p, 0));

  const totals = new Map<number, number>();
  for (const c of cells) totals.set(Math.min(c.h + c.a, 6), (totals.get(Math.min(c.h + c.a, 6)) ?? 0) + c.p);

  return {
    top: [...cells].sort((x, y) => y.p - x.p).slice(0, topN).map((c) => ({ ...c, p: n(c.p) })),
    cleanSheet: { home: pick((c) => c.a === 0), away: pick((c) => c.h === 0) },
    winToNil: { home: pick((c) => c.h > 0 && c.a === 0), away: pick((c) => c.a > 0 && c.h === 0) },
    btts: pick((c) => c.h > 0 && c.a > 0),
    totalGoals: Array.from({ length: 7 }, (_, g) => ({ label: g === 6 ? "6+" : String(g), p: n(totals.get(g) ?? 0) })),
    expectedTotal: cells.reduce((s, c) => s + (c.h + c.a) * n(c.p), 0),
  };
}
