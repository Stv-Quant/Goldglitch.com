import "server-only";
import { getDB } from "./env";

export type TodayFixture = {
  id: string;
  sport: "FÚT" | "NBA" | "NFL" | "NHL" | "MLB";
  league: string;
  home: string;
  away: string;
  kickoffAt: number;
  state: "pre" | "in" | "post";
  outcomes: 2 | 3;
};

// Public ESPN scoreboards: the schedule only (teams + kickoff). Probabilities never come from here.
const FEEDS: { path: string; sport: TodayFixture["sport"]; league: string }[] = [
  { path: "soccer/col.1", sport: "FÚT", league: "Liga BetPlay" },
  { path: "soccer/eng.1", sport: "FÚT", league: "Premier League" },
  { path: "soccer/esp.1", sport: "FÚT", league: "LaLiga" },
  { path: "soccer/ita.1", sport: "FÚT", league: "Serie A" },
  { path: "soccer/ger.1", sport: "FÚT", league: "Bundesliga" },
  { path: "soccer/fra.1", sport: "FÚT", league: "Ligue 1" },
  { path: "soccer/arg.1", sport: "FÚT", league: "Liga Argentina" },
  { path: "soccer/mex.1", sport: "FÚT", league: "Liga MX" },
  { path: "soccer/bra.1", sport: "FÚT", league: "Brasileirão" },
  { path: "soccer/uefa.champions", sport: "FÚT", league: "Champions" },
  { path: "soccer/conmebol.libertadores", sport: "FÚT", league: "Libertadores" },
  { path: "basketball/nba", sport: "NBA", league: "NBA" },
  { path: "football/nfl", sport: "NFL", league: "NFL" },
  { path: "hockey/nhl", sport: "NHL", league: "NHL" },
  { path: "baseball/mlb", sport: "MLB", league: "MLB" },
];

const TZ_OFFSET_MS = -5 * 3_600_000; // Colombia, no DST

/** Today's calendar day in Colombia as [startMs, endMs) and YYYYMMDD. */
export function bogotaDay(now = Date.now()): { start: number; end: number; ymd: string } {
  const local = new Date(now + TZ_OFFSET_MS);
  const start = Date.UTC(local.getUTCFullYear(), local.getUTCMonth(), local.getUTCDate()) - TZ_OFFSET_MS;
  const ymd = local.toISOString().slice(0, 10).replaceAll("-", "");
  return { start, end: start + 86_400_000, ymd };
}

type EspnEvent = {
  id: string;
  date: string;
  status?: { type?: { state?: string } };
  competitions?: { competitors?: { homeAway?: string; team?: { abbreviation?: string; shortDisplayName?: string } }[] }[];
};

async function fromEspn(ymd: string, start: number, end: number): Promise<TodayFixture[]> {
  const out = await Promise.all(
    FEEDS.map(async (f) => {
      try {
        const res = await fetch(`https://site.api.espn.com/apis/site/v2/sports/${f.path}/scoreboard?dates=${ymd}`, {
          signal: AbortSignal.timeout(3500),
          headers: { accept: "application/json" },
        });
        if (!res.ok) return [];
        const data = (await res.json()) as { events?: EspnEvent[] };
        return (data.events ?? []).flatMap((e): TodayFixture[] => {
          const c = e.competitions?.[0]?.competitors ?? [];
          const h = c.find((x) => x.homeAway === "home")?.team;
          const a = c.find((x) => x.homeAway === "away")?.team;
          const kickoffAt = Date.parse(e.date);
          if (!h || !a || !Number.isFinite(kickoffAt) || kickoffAt < start || kickoffAt >= end) return [];
          const st = e.status?.type?.state;
          return [{
            id: `${f.path}:${e.id}`,
            sport: f.sport,
            league: f.league,
            home: (h.abbreviation ?? h.shortDisplayName ?? "").slice(0, 4).toUpperCase(),
            away: (a.abbreviation ?? a.shortDisplayName ?? "").slice(0, 4).toUpperCase(),
            kickoffAt,
            state: st === "in" || st === "post" ? st : "pre",
            outcomes: f.sport === "FÚT" ? 3 : 2,
          }];
        });
      } catch {
        return [];
      }
    }),
  );
  return out.flat();
}

async function fromSqpc(start: number, end: number): Promise<TodayFixture[]> {
  try {
    const db = await getDB();
    const { results } = await db
      .prepare(
        `SELECT m.id, m.sport, m.kickoff_at, m.status, c.name AS league,
                COALESCE(th.short_name, substr(th.name,1,3)) AS home, COALESCE(ta.short_name, substr(ta.name,1,3)) AS away
           FROM matches m JOIN competitions c ON c.id = m.competition_id
           JOIN teams th ON th.id = m.home_team_id JOIN teams ta ON ta.id = m.away_team_id
          WHERE m.kickoff_at >= ? AND m.kickoff_at < ? ORDER BY m.kickoff_at LIMIT 60`,
      )
      .bind(start, end)
      .all<{ id: string; sport: string; kickoff_at: number; status: string; league: string; home: string; away: string }>();
    return results.map((r) => ({
      id: `sqpc:${r.id}`,
      sport: r.sport === "baseball" ? "MLB" : "FÚT",
      league: r.league,
      home: r.home.toUpperCase(),
      away: r.away.toUpperCase(),
      kickoffAt: r.kickoff_at,
      state: r.status === "live" ? "in" : r.status === "finished" ? "post" : "pre",
      outcomes: r.sport === "baseball" ? 2 : 3,
    }));
  } catch {
    return [];
  }
}

/**
 * Upcoming fixtures for today and tomorrow (Colombia), live ones included, finished ones dropped.
 * Our own fixtures (SQPC) first; the public schedule fills the rest so it is never empty on a match day.
 */
export async function getTodayFixtures(now = Date.now()): Promise<TodayFixture[]> {
  const today = bogotaDay(now);
  const tomorrow = bogotaDay(now + 86_400_000);
  const [own, pubA, pubB] = await Promise.all([
    fromSqpc(today.start, tomorrow.end),
    fromEspn(today.ymd, today.start, today.end),
    fromEspn(tomorrow.ymd, tomorrow.start, tomorrow.end),
  ]);
  const pub = [...pubA, ...pubB].filter((f) => f.state !== "post");
  const seen = new Set(own.map((f) => `${f.home}-${f.away}`));
  const all = [...own, ...pub.filter((f) => !seen.has(`${f.home}-${f.away}`))];
  const rank = { in: 0, pre: 1, post: 2 } as const;
  return all
    .filter((f) => f.state !== "post")
    .sort((a, b) => rank[a.state] - rank[b.state] || a.kickoffAt - b.kickoffAt)
    .slice(0, 40);
}
