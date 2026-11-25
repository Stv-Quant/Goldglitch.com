import "server-only";
import type { Tier } from "./plans";
import { SPORTS } from "./sports";
import { canViewSport } from "./entitlements";
import { hasTier } from "./plans";
import { getDB } from "./env";

/**
 * Compact match list for the app home, built entirely by SQLite (D1) as one JSON string.
 * The Worker never parses predictions here: it forwards the text. On the Workers free plan (10 ms of CPU per
 * request) parsing and rendering hundreds of matches on the server was what caused error 1102.
 *
 * Per match: id, sport, ko (kickoff ms), st (status), hs/as (score), c/cn (competition), h/hn/a/an (names, shorts),
 * o {h,d,a} (1X2), k {n: picks at 80%+, l/p: strongest pick — Pro only}.
 */
// Same wording as pickLabel() / SQPC's label_of.
export const LABEL = `CASE WHEN COALESCE(json_extract(value, '$.market'), '') = ''
                     OR instr(lower(json_extract(value, '$.selection')), lower(json_extract(value, '$.market'))) > 0
                    THEN json_extract(value, '$.selection')
                    WHEN COALESCE(json_extract(value, '$.selection'), '') <> ''
                     AND instr(lower(json_extract(value, '$.market')), lower(json_extract(value, '$.selection'))) > 0
                    THEN json_extract(value, '$.market')
                    ELSE json_extract(value, '$.market') || ': ' || json_extract(value, '$.selection') END`;
const NO_PICKS = `COALESCE(json_array_length(pr.payload, '$.picks'), 0) = 0`;
// Same sources as picksFor(): SQPC's own picks; without them, the 1X2 and the published markets.
// k is built in one pass over the candidates: count, and (SQLite bare-column rule) the label of the max-probability row.
const CAND = `SELECT lbl, pp FROM (
    SELECT ${LABEL} AS lbl, json_extract(value, '$.p') AS pp FROM json_each(pr.payload, '$.picks')
    UNION ALL SELECT 'Gana ' || th.name, pr.p_home WHERE ${NO_PICKS}
    UNION ALL SELECT 'Gana ' || ta.name, pr.p_away WHERE ${NO_PICKS}
    UNION ALL SELECT 'Empate', pr.p_draw WHERE ${NO_PICKS} AND pr.p_draw IS NOT NULL
    UNION ALL SELECT json_extract(value, '$.label'), json_extract(value, '$.p') FROM json_each(pr.payload, '$.markets') WHERE ${NO_PICKS}
  ) WHERE pp >= 0.8 AND pp < 0.995`;

export async function compactList(tier: Tier, fromMs: number, toMs: number): Promise<string> {
  const db = await getDB();
  const sports = SPORTS.filter((s) => canViewSport(tier, s));
  const pro = hasTier(tier, "pro") ? 1 : 0;
  const ph = sports.map((_, i) => `?${i + 4}`).join(",");
  const row = await db
    .prepare(
      `WITH ms AS (
         SELECT * FROM matches WHERE kickoff_at >= ?1 AND kickoff_at < ?2 AND sport IN (${ph}) ORDER BY kickoff_at LIMIT 1500
       ), latest AS (
         SELECT p.match_id, max(p.generated_at) AS g FROM predictions p WHERE p.match_id IN (SELECT id FROM ms) GROUP BY p.match_id
       )
       SELECT COALESCE(json_group_array(json(x)), '[]') AS list FROM (
         SELECT json_object(
           'id', m.id, 'sport', m.sport, 'ko', m.kickoff_at, 'st', m.status, 'hs', m.home_score, 'as', m.away_score,
           'c', c.id, 'cn', c.name,
           'h', th.name, 'hn', COALESCE(th.short_name, upper(substr(th.name, 1, 3))),
           'a', ta.name, 'an', COALESCE(ta.short_name, upper(substr(ta.name, 1, 3))),
           'o', CASE WHEN pr.match_id IS NULL THEN NULL ELSE json_object('h', pr.p_home, 'd', pr.p_draw, 'a', pr.p_away) END,
           'k', CASE WHEN pr.match_id IS NULL THEN NULL
                     WHEN ?3 = 0 THEN json((SELECT json_object('n', count(DISTINCT lbl)) FROM (${CAND})))
                     ELSE json((SELECT json_object('n', count(DISTINCT lbl), 'l', lbl, 'p', max(pp)) FROM (${CAND}))) END
         ) AS x
         FROM ms m
         JOIN competitions c ON c.id = m.competition_id
         JOIN teams th ON th.id = m.home_team_id
         JOIN teams ta ON ta.id = m.away_team_id
         LEFT JOIN latest l ON l.match_id = m.id
         LEFT JOIN predictions pr ON pr.match_id = l.match_id AND pr.generated_at = l.g
         GROUP BY m.id
         ORDER BY m.kickoff_at
       )`,
    )
    .bind(fromMs, toMs, pro, ...sports)
    .first<{ list: string }>();
  return row?.list ?? "[]";
}

/** Matches still to be played in a window (to pick the default day without loading anything). */
export async function openCount(tier: Tier, fromMs: number, toMs: number): Promise<number> {
  const db = await getDB();
  const sports = SPORTS.filter((s) => canViewSport(tier, s));
  const r = await db
    .prepare(`SELECT count(*) AS n FROM matches WHERE kickoff_at >= ? AND kickoff_at < ? AND status <> 'finished' AND sport IN (${sports.map(() => "?").join(",")})`)
    .bind(fromMs, toMs, ...sports)
    .first<{ n: number }>();
  return r?.n ?? 0;
}
