import { getDB } from "@/lib/env";
import { readSigned } from "@/lib/signed";

export const dynamic = "force-dynamic";

/**
 * Facts for the social agents, built in SQL (the Worker only forwards the text):
 * - upcoming: the strongest pick (≥80%) of each match in the next 36 h, best first
 * - intl: NBA / NHL strongest pick (≥60%) per game in the next 36 h, for the international audience
 * - results: picks settled in the last 36 h (won / lost)
 * - record: hit rate of settled picks over 7 days, 30 days and all time
 * Every number the agents publish comes from here; they never make one up.
 */
export async function POST(req: Request) {
  const raw = await readSigned(req, 10_000);
  if (raw instanceof Response) return raw;
  const now = Date.now();
  const db = await getDB();
  const r = await db
    .prepare(
      `SELECT
         (SELECT COALESCE(json_group_array(json(x)), '[]') FROM (
            SELECT json_object('matchId', match_id, 'sport', sport, 'league', COALESCE(competition_name, competition_id),
                     'home', home, 'away', away, 'kickoffAt', kickoff_at, 'label', label, 'group', group_name, 'p', p,
                     'x12', (SELECT json_array(pr.p_home, pr.p_draw, pr.p_away) FROM predictions pr
                              WHERE pr.match_id = s.match_id ORDER BY pr.generated_at DESC LIMIT 1),
                     'more', (SELECT count(*) FROM tracked_picks t2 WHERE t2.match_id = s.match_id AND t2.status = 'pending'
                              AND t2.p >= 0.7)) AS x
              FROM (SELECT t.*, row_number() OVER (PARTITION BY match_id ORDER BY p DESC) AS rk FROM tracked_picks t
                     WHERE kind = 'featured' AND status = 'pending' AND kickoff_at > ?1 AND kickoff_at < ?1 + 36 * 3600000 AND p >= 0.8) s
             WHERE rk = 1 ORDER BY p DESC LIMIT 200)) AS upcoming,
         (SELECT COALESCE(json_group_array(json(x)), '[]') FROM (
            SELECT json_object('matchId', match_id, 'sport', sport, 'league', COALESCE(competition_name, competition_id),
                     'home', home, 'away', away, 'kickoffAt', kickoff_at, 'label', label, 'group', group_name, 'p', p,
                     'x12', (SELECT json_array(pr.p_home, pr.p_draw, pr.p_away) FROM predictions pr
                              WHERE pr.match_id = s.match_id ORDER BY pr.generated_at DESC LIMIT 1),
                     'more', (SELECT count(*) FROM tracked_picks t2 WHERE t2.match_id = s.match_id AND t2.status = 'pending'
                              AND t2.p >= 0.7)) AS x
              FROM (SELECT t.*, row_number() OVER (PARTITION BY match_id ORDER BY p DESC) AS rk FROM tracked_picks t
                     WHERE status = 'pending' AND sport IN ('basketball', 'hockey') AND kickoff_at > ?1
                       AND kickoff_at < ?1 + 36 * 3600000 AND p >= 0.6) s
             WHERE rk = 1 ORDER BY p DESC LIMIT 40)) AS intl,
         (SELECT COALESCE(json_group_array(json(x)), '[]') FROM (
            SELECT json_object('matchId', match_id, 'sport', sport, 'league', COALESCE(competition_name, competition_id),
                     'home', home, 'away', away, 'kickoffAt', kickoff_at, 'label', label, 'p', p, 'status', status, 'result', result) AS x
              FROM tracked_picks WHERE kind = 'featured' AND status IN ('won', 'lost')
               AND COALESCE(settled_at, kickoff_at) > ?1 - 36 * 3600000 ORDER BY p DESC LIMIT 200)) AS results,
         (SELECT json_object(
            'd7', json_object('won', sum(status = 'won' AND kickoff_at > ?1 - 7 * 86400000), 'n', sum(status IN ('won','lost') AND kickoff_at > ?1 - 7 * 86400000)),
            'd30', json_object('won', sum(status = 'won' AND kickoff_at > ?1 - 30 * 86400000), 'n', sum(status IN ('won','lost') AND kickoff_at > ?1 - 30 * 86400000)),
            'all', json_object('won', sum(status = 'won'), 'n', sum(status IN ('won','lost'))))
            FROM tracked_picks WHERE kind = 'featured') AS record,
         (SELECT count(*) FROM matches WHERE kickoff_at > ?1 AND kickoff_at < ?1 + 36 * 3600000) AS matches36h`,
    )
    .bind(now)
    .first<{ upcoming: string; intl: string; results: string; record: string; matches36h: number }>();
  return new Response(
    `{"ok":true,"now":${now},"matches36h":${r?.matches36h ?? 0},"upcoming":${r?.upcoming ?? "[]"},"intl":${r?.intl ?? "[]"},"results":${r?.results ?? "[]"},"record":${r?.record ?? "{}"}}`,
    { headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } },
  );
}
