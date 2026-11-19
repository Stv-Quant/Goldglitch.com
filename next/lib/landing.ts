import "server-only";
import { getDB } from "./env";
import type { TodayFixture } from "./fixtures";

/** One real football 1X2 (free-plan data) shown openly on the landing: the product, not a promise. */
export type LandingSample = {
  matchId: string;
  league: string;
  home: string;
  away: string;
  homeLogo?: string;
  awayLogo?: string;
  kickoffAt: number;
  p: { home: number; draw: number; away: number };
  /** Picks ≥75% the model found in this match (count only; their content is Pro). */
  picks: number;
};

/** Public track record headline, same definition as /historial (featured picks, last 365 days). */
export type LandingRecord = { settled: number; won: number; expected: number | null; pending: number; matches: number };

export async function landingSample(fixtures: TodayFixture[], now = Date.now()): Promise<LandingSample | null> {
  try {
    const db = await getDB();
    const r = await db
      .prepare(
        `SELECT m.id, m.kickoff_at, c.name AS league, th.name AS home, ta.name AS away,
                json_extract(p.payload, '$.outcome.home') AS ph, json_extract(p.payload, '$.outcome.draw') AS pd,
                json_extract(p.payload, '$.outcome.away') AS pa,
                (SELECT count(*) FROM json_each(p.payload, '$.picks') WHERE json_extract(value, '$.p') >= 0.75) AS picks
           FROM matches m
           JOIN competitions c ON c.id = m.competition_id
           JOIN teams th ON th.id = m.home_team_id JOIN teams ta ON ta.id = m.away_team_id
           JOIN predictions p ON p.match_id = m.id
          WHERE m.sport = 'football' AND m.status = 'scheduled' AND m.kickoff_at > ? AND m.kickoff_at < ?
            AND json_extract(p.payload, '$.outcome.draw') IS NOT NULL
          ORDER BY abs(json_extract(p.payload, '$.outcome.home') - json_extract(p.payload, '$.outcome.away')) ASC, m.kickoff_at ASC
          LIMIT 1`,
      )
      .bind(now, now + 2 * 86_400_000)
      .first<{ id: string; kickoff_at: number; league: string; home: string; away: string; ph: number; pd: number; pa: number; picks: number }>();
    if (!r) return null;
    const ev = r.id.match(/espn-(\d+)$/)?.[1];
    const twin = fixtures.find((f) => ev && f.id.endsWith(`espn-${ev}`)) ?? fixtures.find((f) => f.id.endsWith(`:${ev}`));
    return {
      matchId: r.id,
      league: r.league,
      home: r.home,
      away: r.away,
      homeLogo: twin?.homeLogo,
      awayLogo: twin?.awayLogo,
      kickoffAt: r.kickoff_at,
      p: { home: r.ph, draw: r.pd, away: r.pa },
      picks: r.picks ?? 0,
    };
  } catch {
    return null;
  }
}

export async function landingRecord(): Promise<LandingRecord | null> {
  try {
    const db = await getDB();
    const since = Date.now() - 365 * 86_400_000;
    const [t, m] = await db.batch([
      db.prepare(
        `SELECT sum(status IN ('won','lost')) AS settled, sum(status = 'won') AS won, sum(status = 'pending') AS pending,
                sum(CASE WHEN status IN ('won','lost') THEN p END) AS p
           FROM tracked_picks WHERE kind = 'featured' AND kickoff_at >= ?`,
      ).bind(since),
      db.prepare(`SELECT count(DISTINCT match_id) AS n FROM predictions`),
    ]);
    const a = (t.results[0] ?? {}) as Record<string, number | null>;
    const settled = Number(a.settled ?? 0);
    return {
      settled,
      won: Number(a.won ?? 0),
      pending: Number(a.pending ?? 0),
      expected: settled ? Number(a.p) / settled : null,
      matches: Number((m.results[0] as { n?: number } | undefined)?.n ?? 0),
    };
  } catch {
    return null;
  }
}
