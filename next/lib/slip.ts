/**
 * Combinadas: the same transparent scores SQPC uses (sqpc/slips.py), without any odds or multiplier.
 * Different matches are independent, so their joint probability is exact. Legs of the same match are correlated;
 * here they are multiplied as if independent and the page says so.
 */
export type Leg = {
  matchId: string;
  sport: string;
  competition: string;
  home: string;
  away: string;
  kickoffAt: number;
  label: string;
  group: string;
  p: number;
  lo?: number | null;
  hi?: number | null;
};

export type LegStatus = "pending" | "won" | "lost" | "void";

export const MAX_LEGS = 12;
const RISK_LABELS: [number, string][] = [[30, "Bajo"], [50, "Moderado"], [70, "Alto"], [101, "Muy alto"]];
const GRADES: [number, string][] = [[75, "A"], [60, "B"], [45, "C"], [30, "D"], [0, "E"]];

export type SlipScore = {
  p: number;                 // joint probability
  range: [number, number];   // conservative range from each leg's interval
  certainty: number;         // 0–100
  risk: number;              // 0–100
  riskLabel: string;
  grade: string;             // A–E
  weakest: number;           // index of the least likely leg
  hits: number[];            // P(exactly k legs right), k = 0..n
  expectedHits: number;
  sameMatch: boolean;        // some legs share a match (correlation not modelled)
};

export function scoreSlip(legs: Leg[]): SlipScore {
  const n = legs.length;
  const p = legs.reduce((a, l) => a * l.p, 1);
  let lo = p, hi = p;
  const widths: number[] = [];
  for (const l of legs) {
    if (l.lo != null && l.hi != null && l.hi > l.lo) {
      lo *= Math.max(l.lo, 1e-6) / l.p;
      hi *= Math.min(l.hi, 1) / l.p;
      widths.push((l.hi - l.lo) / Math.max(l.p, 1e-6));
    } else {
      // No interval published (actions, players): relative width as SQPC does for medium reliability.
      const w = (0.15 * (1 - l.p)) / Math.sqrt(Math.max(l.p, 0.05));
      lo *= 1 - w;
      hi *= Math.min(1 / l.p, 1 + w);
    }
  }
  const penUnc = widths.length ? 15 * (widths.reduce((a, b) => a + b, 0) / widths.length) : 5;
  const risk = Math.min(100, 0.85 * 100 * (1 - p) + penUnc);
  const certainty = 100 * p;
  // Overall grade as SQPC without the value term: 0.5·certainty + 0.3·confidence(medium = 50) + 0.2·50.
  const overall = 0.5 * certainty + 0.3 * 50 + 0.2 * 50;
  // Poisson-binomial distribution of the number of legs that come out right.
  let dist = [1];
  for (const l of legs) {
    const next = new Array(dist.length + 1).fill(0);
    dist.forEach((v, k) => { next[k] += v * (1 - l.p); next[k + 1] += v * l.p; });
    dist = next;
  }
  const ids = legs.map((l) => l.matchId);
  return {
    p,
    range: [Math.min(lo, p), Math.min(Math.max(hi, p), 1)],
    certainty,
    risk,
    riskLabel: RISK_LABELS.find(([t]) => risk < t)![1],
    grade: GRADES.find(([t]) => overall >= t)![1],
    weakest: legs.reduce((w, l, i) => (l.p < legs[w].p ? i : w), 0),
    hits: dist,
    expectedHits: legs.reduce((a, l) => a + l.p, 0),
    sameMatch: new Set(ids).size < n,
  };
}

/** Whole-slip result from its legs: one miss loses it; void legs drop out (if all void, it is void). */
export function slipStatus(st: LegStatus[]): LegStatus {
  if (st.includes("lost")) return "lost";
  if (st.includes("pending")) return "pending";
  return st.every((s) => s === "void") ? "void" : "won";
}
