import type { D1Database, D1PreparedStatement } from "@cloudflare/workers-types";
import type { TrackedPick } from "./contracts";
import type { Sport } from "./sports";

/** Same DDL as migrations/0008_tracked_picks.sql, so the feature works even before the migration is applied. */
const DDL = [
  `CREATE TABLE IF NOT EXISTS tracked_picks (
    id TEXT PRIMARY KEY, kind TEXT NOT NULL CHECK (kind IN ('featured','value')), sport TEXT NOT NULL,
    competition_id TEXT NOT NULL, competition_name TEXT, match_id TEXT NOT NULL, home TEXT NOT NULL, away TEXT NOT NULL,
    kickoff_at INTEGER NOT NULL, group_name TEXT, label TEXT NOT NULL, p REAL NOT NULL, lo REAL, hi REAL, price REAL, ev REAL,
    status TEXT NOT NULL CHECK (status IN ('pending','won','lost','void')), result TEXT, picked_at INTEGER NOT NULL,
    settled_at INTEGER, profit REAL, updated_at INTEGER NOT NULL)`,
  "CREATE INDEX IF NOT EXISTS idx_tracked_picks_kickoff ON tracked_picks(kickoff_at)",
  "CREATE INDEX IF NOT EXISTS idx_tracked_picks_status ON tracked_picks(status, kind, kickoff_at)",
];

export async function ensureTrackedTable(db: D1Database): Promise<void> {
  await db.batch(DDL.map((q) => db.prepare(q)));
}

/**
 * Integrity rules, enforced in SQL:
 * - a pick is only accepted if it was made before kickoff;
 * - while pending, the selection may change only with a newer pre-kickoff version (the model updated before the match);
 * - a result is only accepted after kickoff;
 * - once settled (won / lost / void) the row never changes again.
 */
export function trackedPickStatements(db: D1Database, rows: TrackedPick[], now: number): D1PreparedStatement[] {
  return rows.map((t) =>
    db
      .prepare(
        `INSERT INTO tracked_picks (id, kind, sport, competition_id, competition_name, match_id, home, away, kickoff_at,
           group_name, label, p, lo, hi, price, ev, status, result, picked_at, settled_at, profit, updated_at)
         SELECT ?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14, ?15, ?16,
                CASE WHEN ?17 <> 'pending' AND ?9 > ?22 THEN 'pending' ELSE ?17 END,
                CASE WHEN ?9 > ?22 THEN NULL ELSE ?18 END, ?19,
                CASE WHEN ?9 > ?22 THEN NULL ELSE ?20 END, CASE WHEN ?9 > ?22 THEN NULL ELSE ?21 END, ?22
          WHERE ?19 < ?9
         ON CONFLICT(id) DO UPDATE SET
           label      = CASE WHEN excluded.picked_at > tracked_picks.picked_at AND excluded.picked_at < tracked_picks.kickoff_at THEN excluded.label ELSE tracked_picks.label END,
           group_name = CASE WHEN excluded.picked_at > tracked_picks.picked_at AND excluded.picked_at < tracked_picks.kickoff_at THEN excluded.group_name ELSE tracked_picks.group_name END,
           p          = CASE WHEN excluded.picked_at > tracked_picks.picked_at AND excluded.picked_at < tracked_picks.kickoff_at THEN excluded.p ELSE tracked_picks.p END,
           lo         = CASE WHEN excluded.picked_at > tracked_picks.picked_at AND excluded.picked_at < tracked_picks.kickoff_at THEN excluded.lo ELSE tracked_picks.lo END,
           hi         = CASE WHEN excluded.picked_at > tracked_picks.picked_at AND excluded.picked_at < tracked_picks.kickoff_at THEN excluded.hi ELSE tracked_picks.hi END,
           price      = CASE WHEN excluded.picked_at > tracked_picks.picked_at AND excluded.picked_at < tracked_picks.kickoff_at THEN excluded.price ELSE tracked_picks.price END,
           ev         = CASE WHEN excluded.picked_at > tracked_picks.picked_at AND excluded.picked_at < tracked_picks.kickoff_at THEN excluded.ev ELSE tracked_picks.ev END,
           picked_at  = CASE WHEN excluded.picked_at > tracked_picks.picked_at AND excluded.picked_at < tracked_picks.kickoff_at THEN excluded.picked_at ELSE tracked_picks.picked_at END,
           status     = CASE WHEN tracked_picks.kickoff_at < excluded.updated_at THEN excluded.status ELSE 'pending' END,
           result     = CASE WHEN tracked_picks.kickoff_at < excluded.updated_at THEN excluded.result ELSE NULL END,
           settled_at = CASE WHEN tracked_picks.kickoff_at < excluded.updated_at THEN excluded.settled_at ELSE NULL END,
           profit     = CASE WHEN tracked_picks.kickoff_at < excluded.updated_at THEN excluded.profit ELSE NULL END,
           updated_at = excluded.updated_at
         WHERE tracked_picks.status = 'pending'`,
      )
      .bind(
        t.id, t.kind, t.sport, t.competitionId, t.competitionName ?? null, t.matchId, t.home, t.away, t.kickoffAt,
        t.group, t.label, t.p, t.lo ?? null, t.hi ?? null, t.price ?? null, t.ev ?? null, t.status, t.result ?? null,
        t.pickedAt, t.settledAt ?? null, t.profit ?? null, now,
      ),
  );
}

export type TrackedRow = {
  id: string; kind: "featured" | "value"; sport: Sport; competition: string; home: string; away: string;
  kickoffAt: number; group: string; label: string; p: number; price: number | null; ev: number | null;
  status: "pending" | "won" | "lost" | "void"; result: string | null; profit: number | null;
};

export type Bucket = { key: string; n: number; won: number; hitRate: number; expected: number };
export type KindSummary = {
  settled: number; won: number; lost: number; void: number; pending: number;
  hitRate: number | null; expected: number | null; brier: number | null;
  profit: number | null; roi: number | null; priced: number;
  bySport: Bucket[]; byBand: Bucket[]; byGroup: Bucket[];
  /** Cumulative (hits − expected hits), oldest first: stays near 0 when the model is honest. */
  curve: { t: number; diff: number }[];
};

export function bandOf(p: number): string {
  return p < 0.85 ? "80–85%" : p < 0.9 ? "85–90%" : p < 0.95 ? "90–95%" : "95%+";
}

function bucket(rows: TrackedRow[], key: (r: TrackedRow) => string): Bucket[] {
  const m = new Map<string, { n: number; won: number; p: number }>();
  for (const r of rows) {
    const k = key(r);
    const x = m.get(k) ?? { n: 0, won: 0, p: 0 };
    x.n += 1;
    x.won += r.status === "won" ? 1 : 0;
    x.p += r.p;
    m.set(k, x);
  }
  return [...m.entries()]
    .map(([k, v]) => ({ key: k, n: v.n, won: v.won, hitRate: v.won / v.n, expected: v.p / v.n }))
    .sort((a, b) => b.n - a.n);
}

/** Pure aggregation (tested): pending and void rows never count toward the hit rate. */
export function summarize(all: TrackedRow[], kind: TrackedRow["kind"]): KindSummary {
  const rows = all.filter((r) => r.kind === kind);
  const done = rows.filter((r) => r.status === "won" || r.status === "lost");
  const won = done.filter((r) => r.status === "won").length;
  const priced = done.filter((r) => typeof r.profit === "number");
  const profit = priced.reduce((s, r) => s + (r.profit as number), 0);
  const ordered = [...done].sort((a, b) => a.kickoffAt - b.kickoffAt);
  let c = 0;
  const curve = ordered.map((r) => ((c += (r.status === "won" ? 1 : 0) - r.p), { t: r.kickoffAt, diff: c }));
  return {
    settled: done.length,
    won,
    lost: done.length - won,
    void: rows.filter((r) => r.status === "void").length,
    pending: rows.filter((r) => r.status === "pending").length,
    hitRate: done.length ? won / done.length : null,
    expected: done.length ? done.reduce((s, r) => s + r.p, 0) / done.length : null,
    brier: done.length ? done.reduce((s, r) => s + (r.p - (r.status === "won" ? 1 : 0)) ** 2, 0) / done.length : null,
    profit: priced.length ? profit : null,
    roi: priced.length ? profit / priced.length : null,
    priced: priced.length,
    bySport: bucket(done, (r) => r.sport),
    byBand: bucket(done, (r) => bandOf(r.p)).sort((a, b) => a.key.localeCompare(b.key)),
    byGroup: bucket(done, (r) => r.group),
    curve: curve.slice(-400),
  };
}

export async function trackedPicks(db: D1Database, days = 365): Promise<TrackedRow[]> {
  await ensureTrackedTable(db);
  const sinceMs = Date.now() - days * 86_400_000;
  const { results } = await db
    .prepare(
      `SELECT id, kind, sport, COALESCE(competition_name, competition_id) AS competition, home, away, kickoff_at, group_name,
              label, p, price, ev, status, result, profit
         FROM tracked_picks WHERE kickoff_at >= ? ORDER BY kickoff_at DESC LIMIT 5000`,
    )
    .bind(sinceMs)
    .all<{
      id: string; kind: "featured" | "value"; sport: Sport; competition: string; home: string; away: string; kickoff_at: number;
      group_name: string | null; label: string; p: number; price: number | null; ev: number | null;
      status: TrackedRow["status"]; result: string | null; profit: number | null;
    }>();
  return results.map((r) => ({
    id: r.id, kind: r.kind, sport: r.sport, competition: r.competition, home: r.home, away: r.away, kickoffAt: r.kickoff_at,
    group: r.group_name ?? "Otros", label: r.label, p: r.p, price: r.price, ev: r.ev, status: r.status, result: r.result, profit: r.profit,
  }));
}
