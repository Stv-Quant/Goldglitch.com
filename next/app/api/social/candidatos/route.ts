import { getDB } from "@/lib/env";
import { readSigned } from "@/lib/signed";

export const dynamic = "force-dynamic";

/**
 * Private report for the PC (signed): every pending football pick with p ≥ min (default 0.85) in the next `hours`
 * (default 48), all markets of each match, plus the settled history of picks ≥ min so the PC can check calibration
 * by market family. Never published.
 */
export async function POST(req: Request) {
  const raw = await readSigned(req, 10_000);
  if (raw instanceof Response) return raw;
  let body: { min?: number; hours?: number } = {};
  try {
    body = JSON.parse(raw || "{}");
  } catch {
    /* defaults */
  }
  const min = Math.min(0.99, Math.max(0.5, Number(body.min) || 0.85));
  const hours = Math.min(96, Math.max(1, Number(body.hours) || 48));
  const now = Date.now();
  const db = await getDB();
  const r = await db
    .prepare(
      `SELECT
         (SELECT COALESCE(json_group_array(json(x)), '[]') FROM (
            SELECT json_object('matchId', match_id, 'league', COALESCE(competition_name, competition_id), 'home', home,
                     'away', away, 'kickoffAt', kickoff_at, 'label', label, 'group', group_name, 'p', p) AS x
              FROM tracked_picks
             WHERE sport = 'football' AND status = 'pending' AND p >= ?2 AND kickoff_at > ?1 + 15 * 60000
               AND kickoff_at < ?1 + ?3 * 3600000
             ORDER BY kickoff_at, p DESC LIMIT 1500)) AS picks,
         (SELECT COALESCE(json_group_array(json(x)), '[]') FROM (
            SELECT json_object('label', label, 'group', group_name, 'p', p, 'won', status = 'won') AS x
              FROM tracked_picks
             WHERE sport = 'football' AND status IN ('won', 'lost') AND p >= ?2 AND kickoff_at > ?1 - 180 * 86400000
             LIMIT 6000)) AS history`,
    )
    .bind(now, min, hours)
    .first<{ picks: string; history: string }>();
  return new Response(`{"ok":true,"now":${now},"min":${min},"picks":${r?.picks ?? "[]"},"history":${r?.history ?? "[]"}}`, {
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}
