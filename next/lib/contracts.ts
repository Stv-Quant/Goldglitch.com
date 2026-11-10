import { z } from "zod";
import { SPORTS } from "./sports";

/**
 * Data contract between SQPC (Python engine) and the PWA.
 * SQPC publishes batches to POST /api/ingest; the PWA never computes model outputs itself.
 */

const id = z.string().min(1).max(128);
const prob = z.number().min(0).max(1);
const interval = z.tuple([prob, prob]);
const sport = z.enum(SPORTS);

export const competitionSchema = z.object({
  id,
  sport,
  name: z.string().min(1).max(120),
  country: z.string().max(60).optional(),
  season: z.string().max(20).optional(),
});

export const teamSchema = z.object({
  id,
  sport,
  name: z.string().min(1).max(120),
  shortName: z.string().max(12).optional(),
  country: z.string().max(60).optional(),
});

export const matchSchema = z.object({
  id,
  sport,
  competitionId: id,
  homeTeamId: id,
  awayTeamId: id,
  kickoffAt: z.number().int().positive(), // epoch ms UTC
  status: z.enum(["scheduled", "live", "finished", "postponed", "canceled"]),
  homeScore: z.number().int().min(0).nullable().optional(),
  awayScore: z.number().int().min(0).nullable().optional(),
  venue: z.string().max(120).optional(),
});

const featureRow = z.object({
  label: z.string().max(60),
  home: z.union([z.number(), z.string()]),
  away: z.union([z.number(), z.string()]),
  /** "higher" | "lower" is better — drives which side is highlighted. */
  better: z.enum(["higher", "lower"]).optional(),
});

const marketRow = z.object({
  key: z.string().max(40), // e.g. "over_2_5", "btts_yes"
  label: z.string().max(60),
  p: prob,
  interval: interval.optional(),
});

const playerRow = z.object({
  name: z.string().max(80),
  side: z.enum(["home", "away"]),
  role: z.string().max(30).optional(),
  expectedMinutes: z.number().min(0).max(120).optional(),
  pScore: prob.optional(),
  pAssist: prob.optional(),
  xg90: z.number().min(0).optional(),
});

const edgeRow = z.object({
  market: z.string().max(40),
  selection: z.string().max(60),
  modelP: prob,
  bookmaker: z.string().max(40),
  odds: z.number().gt(1),
  /** EV per unit staked: modelP * odds - 1 */
  ev: z.number(),
  capturedAt: z.number().int().positive(),
});

/** Full distribution of a count (goals, corners, points…): pmf[i] = P(X = start + i). Lets the site price any .5 line. */
const statLine = z.object({
  key: z.string().max(40),
  label: z.string().max(60),
  group: z.string().max(30),
  mean: z.number().min(0),
  start: z.number().int().min(0),
  pmf: z.array(z.number().min(0).max(1)).min(2).max(400),
  /** Visible on the free plan. */
  free: z.boolean().optional(),
});
export type StatLine = z.infer<typeof statLine>;

export const predictionSchema = z.object({
  matchId: id,
  modelVersion: z.string().min(1).max(40),
  generatedAt: z.number().int().positive(),
  outcome: z.object({
    home: prob,
    draw: prob.nullable(), // null for sports without draws (MLB, NBA, NHL moneyline)
    away: prob,
    interval: z
      .object({ home: interval, draw: interval.nullable(), away: interval })
      .optional(),
  }),
  features: z.array(featureRow).max(40).default([]),
  xg: z.object({ home: z.number().min(0), away: z.number().min(0) }).optional(),
  /** scoreMatrix[h][a] = P(home scores h, away scores a), typically 0..6 */
  scoreMatrix: z.array(z.array(prob).max(11)).max(11).optional(),
  markets: z.array(marketRow).max(40).default([]),
  players: z.array(playerRow).max(60).default([]),
  edges: z.array(edgeRow).max(40).default([]),
  lines: z.array(statLine).max(80).default([]),
});

export const metricsSchema = z.object({
  id,
  sport,
  competitionId: id.optional(),
  modelVersion: z.string().min(1).max(40),
  windowStart: z.number().int().positive(),
  windowEnd: z.number().int().positive(),
  n: z.number().int().min(1),
  brier: z.number().min(0),
  logLoss: z.number().min(0),
  baselineBrier: z.number().min(0).optional(),
  calibration: z
    .array(z.object({ bin: z.number(), predicted: prob, observed: prob, n: z.number().int().min(0) }))
    .max(50),
  generatedAt: z.number().int().positive(),
});

export const ingestBatchSchema = z.object({
  batchId: id,
  source: z.string().min(1).max(40),
  competitions: z.array(competitionSchema).max(200).default([]),
  teams: z.array(teamSchema).max(2000).default([]),
  matches: z.array(matchSchema).max(2000).default([]),
  predictions: z.array(predictionSchema).max(2000).default([]),
  metrics: z.array(metricsSchema).max(200).default([]),
});

export type Competition = z.infer<typeof competitionSchema>;
export type Team = z.infer<typeof teamSchema>;
export type Match = z.infer<typeof matchSchema>;
export type Prediction = z.infer<typeof predictionSchema>;
export type ModelMetrics = z.infer<typeof metricsSchema>;
export type IngestBatch = z.infer<typeof ingestBatchSchema>;
