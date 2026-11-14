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
  /** Heading the market is listed under (Resultado, Goles, Hándicap…). */
  group: z.string().max(30).optional(),
});

const count = z.number().int().min(0).max(100000);
const statNums = z.record(z.string().max(20), z.number().min(0).max(1000));

/** One of the player's last games against this opponent. */
const vsGame = z.object({
  date: z.string().max(10),
  comp: z.string().max(20).optional(),
  minutes: count.optional(),
  starter: z.boolean().optional(),
  goals: count.optional(),
  assists: count.optional(),
  shots: count.optional(),
  sot: count.optional(),
  fouls: count.optional(),
  yellow: count.optional(),
});

const playerRow = z.object({
  name: z.string().max(80),
  side: z.enum(["home", "away"]),
  role: z.string().max(30).optional(),
  /** Chance of starting / of playing at all. */
  pStart: prob.optional(),
  pPlay: prob.optional(),
  expectedMinutes: z.number().min(0).max(120).optional(),
  pScore: prob.optional(),
  pAssist: prob.optional(),
  xg90: z.number().min(0).optional(),
  /** Expected count for this match: goals, assists, shots, sot, fouls, fouled, yellow, offsides, saves. */
  exp: statNums.optional(),
  /** SQPC's own probabilities for this match: goal2, shots1..3, sot1..2, fouls1..2, fouled1, card, offside1, saves2..4. */
  probs: z.record(z.string().max(20), prob).optional(),
  /** Season totals as SQPC has them. */
  season: z.object({
    apps: count.optional(),
    starts: count.optional(),
    minutes: count.optional(),
    goals: count.optional(),
    assists: count.optional(),
    shots: count.optional(),
    sot: count.optional(),
    fouls: count.optional(),
    fouled: count.optional(),
    yellow: count.optional(),
    offsides: count.optional(),
    saves: count.optional(),
  }).optional(),
  /** History against today's opponent. */
  vsOpp: z.object({
    games: count,
    minutes: count.optional(),
    totals: z.record(z.string().max(20), count).optional(),
    recent: z.array(vsGame).max(10).optional(),
  }).optional(),
});
export type PlayerRow = z.infer<typeof playerRow>;

/** A selection SQPC itself ranked, with its uncertainty band and (when known) the best price found. */
const sqpcPick = z.object({
  group: z.string().max(30),
  market: z.string().max(80),
  selection: z.string().max(100),
  p: prob,
  lo: prob.nullish(),
  hi: prob.nullish(),
  price: z.number().gt(1).nullish(),
  book: z.string().max(40).nullish(),
  ev: z.number().nullish(),
  grade: z.string().max(20).nullish(),
});
export type SqpcPick = z.infer<typeof sqpcPick>;

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

/** One side of "what each team plays for": current table, end-of-season chances and how much this match moves them. */
const stakeSide = z.object({
  team: z.string().max(120),
  pos: z.number().int().min(1).max(60),
  pts: z.number().int().min(0).max(200),
  gp: z.number().int().min(0).max(80),
  gd: z.number().int().min(-200).max(200),
  pTop: prob,
  pZone: prob,
  pReleg: prob,
  /** Win instead of lose: change in P(title or top places) and in P(relegation). */
  levTop: z.number().min(-1).max(1),
  levZone: z.number().min(-1).max(1),
  levDown: z.number().min(-1).max(1),
  dead: z.boolean(),
  need: z.string().max(120),
});
const moodSide = z.object({
  /** Points per game over what the model expected, last 5 league matches. */
  form: z.number().min(-3).max(3),
  slump: z.boolean(),
  last: z.string().max(10),
});
export const stakesSchema = z.object({
  format: z.object({
    teams: z.number().int().min(2).max(60),
    games: z.number().int().min(1).max(80),
    top: z.number().int().min(1).max(10),
    zone: z.number().int().min(1).max(30),
    releg: z.number().int().min(0).max(10),
    topLabel: z.string().max(40),
    zoneLabel: z.string().max(40),
  }).optional(),
  progress: prob.optional(),
  home: stakeSide.optional(),
  away: stakeSide.optional(),
  mood: z.object({ home: moodSide.optional(), away: moodSide.optional() }).optional(),
  /** Goal multipliers already applied to the model (1 = no effect). */
  effect: z.object({ home: z.number().min(0.5).max(2), away: z.number().min(0.5).max(2), applied: z.boolean() }).optional(),
});
export type Stakes = z.infer<typeof stakesSchema>;

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
  markets: z.array(marketRow).max(120).default([]),
  players: z.array(playerRow).max(60).default([]),
  edges: z.array(edgeRow).max(40).default([]),
  lines: z.array(statLine).max(80).default([]),
  picks: z.array(sqpcPick).max(80).default([]),
  /** Football: table position, what each side plays for and recent mood (SQPC models/stakes.py). */
  stakes: stakesSchema.optional(),
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

/**
 * A pick SQPC chose before kickoff and then settled against the real result. "featured" = the strongest selection
 * (≥80%) of a match, the one shown in "Picks destacados"; "value" = a validated value bet with its price.
 */
export const trackedPickSchema = z.object({
  id,
  kind: z.enum(["featured", "value"]),
  sport,
  competitionId: id,
  competitionName: z.string().max(120).optional(),
  matchId: id,
  home: z.string().min(1).max(120),
  away: z.string().min(1).max(120),
  kickoffAt: z.number().int().positive(),
  group: z.string().max(30),
  label: z.string().min(1).max(140),
  p: prob,
  lo: prob.nullish(),
  hi: prob.nullish(),
  price: z.number().gt(1).nullish(),
  ev: z.number().nullish(),
  status: z.enum(["pending", "won", "lost", "void"]),
  result: z.string().max(60).nullish(),
  /** When this selection was made (must be before kickoff). */
  pickedAt: z.number().int().positive(),
  updatedAt: z.number().int().min(0).optional(),
  settledAt: z.number().int().positive().nullish(),
  /** Units won/lost at `price` with stake 1 (value bets). */
  profit: z.number().nullish(),
});
export type TrackedPick = z.infer<typeof trackedPickSchema>;

export const ingestBatchSchema = z.object({
  batchId: id,
  source: z.string().min(1).max(40),
  competitions: z.array(competitionSchema).max(200).default([]),
  teams: z.array(teamSchema).max(2000).default([]),
  matches: z.array(matchSchema).max(2000).default([]),
  predictions: z.array(predictionSchema).max(2000).default([]),
  metrics: z.array(metricsSchema).max(200).default([]),
  trackedPicks: z.array(trackedPickSchema).max(3000).default([]),
});

export type Competition = z.infer<typeof competitionSchema>;
export type Team = z.infer<typeof teamSchema>;
export type Match = z.infer<typeof matchSchema>;
export type Prediction = z.infer<typeof predictionSchema>;
export type ModelMetrics = z.infer<typeof metricsSchema>;
export type IngestBatch = z.infer<typeof ingestBatchSchema>;
