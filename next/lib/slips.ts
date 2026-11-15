import "server-only";
import { LABEL } from "./appList";
import { getDB } from "./env";
import { MAX_LEGS, scoreSlip, slipStatus, type Leg, type LegStatus } from "./slip";

export const MAX_SAVED = 200;

export type SavedSlip = {
  id: string;
  name: string | null;
  createdAt: number;
  legs: (Leg & { status: LegStatus })[];
  status: LegStatus;
  score: ReturnType<typeof scoreSlip>;
};

/**
 * Rebuilds each requested leg from the model's current picks (never trusts the probability sent by the browser).
 * Only picks at 75%+ of matches that have not started qualify: those are the ones SQPC tracks and settles.
 */
export async function resolveLegs(wanted: { matchId: string; label: string }[]): Promise<Leg[] | string> {
  if (wanted.length < 2) return "Una combinada necesita al menos 2 selecciones.";
  if (wanted.length > MAX_LEGS) return `Máximo ${MAX_LEGS} selecciones.`;
  const keys = new Set(wanted.map((w) => `${w.matchId}\u0000${w.label}`));
  if (keys.size !== wanted.length) return "Hay selecciones repetidas.";
  const ids = [...new Set(wanted.map((w) => w.matchId))];
  const db = await getDB();
  const { results } = await db
    .prepare(
      `SELECT m.id AS matchId, m.sport, m.kickoff_at AS kickoffAt, c.name AS competition, th.name AS home, ta.name AS away,
              (SELECT json_group_array(json_object('label', ${LABEL}, 'group', json_extract(value, '$.group'),
                        'p', json_extract(value, '$.p'), 'lo', json_extract(value, '$.lo'), 'hi', json_extract(value, '$.hi')))
                 FROM predictions p, json_each(p.payload, '$.picks')
                WHERE p.match_id = m.id
                  AND p.generated_at = (SELECT max(generated_at) FROM predictions WHERE match_id = m.id)
                  AND json_extract(value, '$.p') >= 0.75 AND json_extract(value, '$.p') < 0.995) AS picks
         FROM matches m
         JOIN competitions c ON c.id = m.competition_id
         JOIN teams th ON th.id = m.home_team_id
         JOIN teams ta ON ta.id = m.away_team_id
        WHERE m.id IN (${ids.map(() => "?").join(",")})`,
    )
    .bind(...ids)
    .all<{ matchId: string; sport: string; kickoffAt: number; competition: string; home: string; away: string; picks: string | null }>();
  const byId = new Map(results.map((r) => [r.matchId, r]));
  const now = Date.now();
  const legs: Leg[] = [];
  for (const w of wanted) {
    const m = byId.get(w.matchId);
    if (!m) return "Uno de los partidos ya no está publicado.";
    if (m.kickoffAt <= now) return `${m.home} vs ${m.away} ya empezó: quita esa selección.`;
    const picks = JSON.parse(m.picks ?? "[]") as { label: string; group: string; p: number; lo: number | null; hi: number | null }[];
    const k = picks.filter((x) => x.label === w.label).sort((a, b) => b.p - a.p)[0];
    if (!k) return `“${w.label}” ya no es un pick de 75% o más: quítala.`;
    legs.push({
      matchId: m.matchId, sport: m.sport, competition: m.competition, home: m.home, away: m.away, kickoffAt: m.kickoffAt,
      label: k.label, group: k.group ?? "Otros", p: k.p, lo: k.lo, hi: k.hi,
    });
  }
  return legs.sort((a, b) => a.kickoffAt - b.kickoffAt);
}

export async function saveSlip(userId: string, name: string | null, legs: Leg[]): Promise<string | null> {
  const db = await getDB();
  const n = await db.prepare("SELECT count(*) AS n FROM slips WHERE user_id = ?").bind(userId).first<{ n: number }>();
  if ((n?.n ?? 0) >= MAX_SAVED) return null;
  const id = crypto.randomUUID();
  await db
    .prepare("INSERT INTO slips (id, user_id, name, legs, p, first_kickoff, last_kickoff, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)")
    .bind(id, userId, name, JSON.stringify(legs), scoreSlip(legs).p, legs[0].kickoffAt, legs[legs.length - 1].kickoffAt, Date.now())
    .run();
  return id;
}

/** The viewer's slips, newest first, with each leg's result taken from the tracked picks. */
export async function listSlips(userId: string): Promise<SavedSlip[]> {
  const db = await getDB();
  const { results } = await db
    .prepare("SELECT id, name, legs, created_at FROM slips WHERE user_id = ? ORDER BY created_at DESC LIMIT ?")
    .bind(userId, MAX_SAVED)
    .all<{ id: string; name: string | null; legs: string; created_at: number }>();
  const slips = results.map((r) => ({ ...r, legs: JSON.parse(r.legs) as Leg[] }));
  const pairs = slips.flatMap((s) => s.legs.map((l) => [l.matchId, l.label] as const));
  const status = new Map<string, LegStatus>();
  for (let i = 0; i < pairs.length; i += 40) {
    const chunk = pairs.slice(i, i + 40);
    const { results: rows } = await db
      .prepare(
        `SELECT match_id, label, status FROM tracked_picks
          WHERE kind = 'featured' AND (${chunk.map(() => "(match_id = ? AND label = ?)").join(" OR ")})`,
      )
      .bind(...chunk.flat())
      .all<{ match_id: string; label: string; status: LegStatus }>();
    for (const r of rows) status.set(`${r.match_id}\u0000${r.label}`, r.status);
  }
  return slips.map((s) => {
    const legs = s.legs.map((l) => ({ ...l, status: status.get(`${l.matchId}\u0000${l.label}`) ?? ("pending" as LegStatus) }));
    return { id: s.id, name: s.name, createdAt: s.created_at, legs, status: slipStatus(legs.map((l) => l.status)), score: scoreSlip(s.legs) };
  });
}

export async function deleteSlip(userId: string, id: string): Promise<boolean> {
  const db = await getDB();
  const r = await db.prepare("DELETE FROM slips WHERE id = ? AND user_id = ?").bind(id, userId).run();
  return (r.meta?.changes ?? 0) > 0;
}
