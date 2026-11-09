import type { Prediction } from "./contracts";
import { hasTier, type Tier } from "./plans";

/**
 * What a viewer is allowed to receive. Redaction happens on the server so locked data
 * never reaches the client bundle, HTML or network tab.
 */
export type RedactedPrediction = {
  matchId: string;
  modelVersion: string;
  generatedAt: number;
  outcome: { home: number; draw: number | null; away: number };
  features: Prediction["features"];
  // Pro
  interval?: NonNullable<Prediction["outcome"]["interval"]>;
  xg?: Prediction["xg"];
  scoreMatrix?: Prediction["scoreMatrix"];
  markets?: Prediction["markets"];
  players?: Prediction["players"];
  // Elite
  edges?: Prediction["edges"];
  locked: { pro: boolean; elite: boolean };
};

export function canViewSport(tier: Tier, sport: "football" | "baseball"): boolean {
  return sport === "football" || hasTier(tier, "elite");
}

export function redactPrediction(p: Prediction, tier: Tier): RedactedPrediction {
  const out: RedactedPrediction = {
    matchId: p.matchId,
    modelVersion: p.modelVersion,
    generatedAt: p.generatedAt,
    outcome: { home: p.outcome.home, draw: p.outcome.draw, away: p.outcome.away },
    features: p.features,
    locked: { pro: !hasTier(tier, "pro"), elite: !hasTier(tier, "elite") },
  };
  if (hasTier(tier, "pro")) {
    out.interval = p.outcome.interval;
    out.xg = p.xg;
    out.scoreMatrix = p.scoreMatrix;
    out.markets = p.markets;
    out.players = p.players;
  }
  if (hasTier(tier, "elite")) {
    out.edges = p.edges;
  }
  return out;
}
