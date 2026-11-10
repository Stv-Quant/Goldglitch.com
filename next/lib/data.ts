import "server-only";
import type { ModelMetrics, Prediction } from "./contracts";
import { canViewSport, redactPrediction, type RedactedPrediction } from "./entitlements";
import { getDB } from "./env";
import type { Tier } from "./plans";
import { SPORTS, type Sport } from "./sports";

export type MatchView = {
  id: string;
  sport: Sport;
  kickoffAt: number;
  status: string;
  homeScore: number | null;
  awayScore: number | null;
  venue: string | null;
  competition: { id: string; name: string; country: string | null };
  home: { id: string; name: string; short: string };
  away: { id: string; name: string; short: string };
  prediction: RedactedPrediction | null;
};

type Row = {
  id: string; sport: Sport; kickoff_at: number; status: string;
  home_score: number | null; away_score: number | null; venue: string | null;
  competition_id: string; competition_name: string; competition_country: string | null;
  home_id: string; home_name: string; home_short: string | null;
  away_id: string; away_name: string; away_short: string | null;
  payload: string | null;
};

const BASE_SELECT = `
  SELECT m.id, m.sport, m.kickoff_at, m.status, m.home_score, m.away_score, m.venue,
         c.id AS competition_id, c.name AS competition_name, c.country AS competition_country,
         th.id AS home_id, th.name AS home_name, th.short_name AS home_short,
         ta.id AS away_id, ta.name AS away_name, ta.short_name AS away_short,
         (SELECT p.payload FROM predictions p WHERE p.match_id = m.id ORDER BY p.generated_at DESC LIMIT 1) AS payload
    FROM matches m
    JOIN competitions c ON c.id = m.competition_id
    JOIN teams th ON th.id = m.home_team_id
    JOIN teams ta ON ta.id = m.away_team_id`;

function short(name: string, s: string | null): string {
  return s ?? name.slice(0, 3).toUpperCase();
}

function toView(r: Row, tier: Tier): MatchView {
  let prediction: RedactedPrediction | null = null;
  if (r.payload) {
    try {
      prediction = redactPrediction(JSON.parse(r.payload) as Prediction, tier);
    } catch {
      prediction = null;
    }
  }
  return {
    id: r.id,
    sport: r.sport,
    kickoffAt: r.kickoff_at,
    status: r.status,
    homeScore: r.home_score,
    awayScore: r.away_score,
    venue: r.venue,
    competition: { id: r.competition_id, name: r.competition_name, country: r.competition_country },
    home: { id: r.home_id, name: r.home_name, short: short(r.home_name, r.home_short) },
    away: { id: r.away_id, name: r.away_name, short: short(r.away_name, r.away_short) },
    prediction,
  };
}

export async function listMatches(tier: Tier, fromMs: number, toMs: number): Promise<MatchView[]> {
  const db = await getDB();
  const sports = SPORTS.filter((s) => canViewSport(tier, s));
  const { results } = await db
    .prepare(
      `${BASE_SELECT}
       WHERE m.kickoff_at >= ? AND m.kickoff_at < ? AND m.sport IN (${sports.map(() => "?").join(",")})
       ORDER BY m.kickoff_at ASC LIMIT 200`,
    )
    .bind(fromMs, toMs, ...sports)
    .all<Row>();
  return results.map((r) => toView(r, tier));
}

/** Returns null when not found; `{ locked: true }` when the sport requires a higher tier. */
export async function getMatch(id: string, tier: Tier): Promise<MatchView | { locked: true; sport: Sport } | null> {
  const db = await getDB();
  const r = await db.prepare(`${BASE_SELECT} WHERE m.id = ?`).bind(id).first<Row>();
  if (!r) return null;
  if (!canViewSport(tier, r.sport)) return { locked: true, sport: r.sport };
  return toView(r, tier);
}

export async function latestMetrics(): Promise<ModelMetrics[]> {
  const db = await getDB();
  const { results } = await db
    .prepare(
      `SELECT id, sport, competition_id, model_version, window_start, window_end, n, brier, log_loss, baseline_brier, calibration, generated_at
         FROM model_metrics ORDER BY generated_at DESC LIMIT 12`,
    )
    .all<{
      id: string; sport: Sport; competition_id: string | null; model_version: string;
      window_start: number; window_end: number; n: number; brier: number; log_loss: number;
      baseline_brier: number | null; calibration: string; generated_at: number;
    }>();
  return results.map((r) => ({
    id: r.id,
    sport: r.sport,
    competitionId: r.competition_id ?? undefined,
    modelVersion: r.model_version,
    windowStart: r.window_start,
    windowEnd: r.window_end,
    n: r.n,
    brier: r.brier,
    logLoss: r.log_loss,
    baselineBrier: r.baseline_brier ?? undefined,
    calibration: JSON.parse(r.calibration),
    generatedAt: r.generated_at,
  }));
}
