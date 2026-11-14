import type { D1Database } from "@cloudflare/workers-types";
import type { IngestBatch } from "./contracts";
import type { Sport } from "./sports";

/** Sports the live D1 CHECK constraints accept (a sport added in code needs its migration, e.g. 0009 for e-sports). */
export async function acceptedSports(db: D1Database): Promise<Set<Sport> | null> {
  const row = await db.prepare("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'matches'").first<{ sql: string }>();
  if (!row?.sql) return null;
  const m = row.sql.match(/sport\s+TEXT[^,]*CHECK\s*\(\s*sport\s+IN\s*\(([^)]*)\)/i);
  if (!m) return null;
  return new Set(m[1].split(",").map((s) => s.trim().replace(/^'|'$/g, "")) as Sport[]);
}

/**
 * Drops rows of sports the database does not accept yet, so one pending migration never blocks the rest of a batch.
 * Tracked picks have no sport constraint and always pass.
 */
export function filterBySport(b: IngestBatch, ok: Set<Sport> | null): { batch: IngestBatch; skipped: Record<string, number> } {
  if (!ok) return { batch: b, skipped: {} };
  const skipped: Record<string, number> = {};
  const keep = <T extends { sport: Sport }>(rows: T[]) =>
    rows.filter((r) => ok.has(r.sport) || ((skipped[r.sport] = (skipped[r.sport] ?? 0) + 1), false));
  const matches = keep(b.matches);
  const ids = new Set(matches.map((m) => m.id));
  const dropped = new Set(b.matches.filter((m) => !ids.has(m.id)).map((m) => m.id));
  return {
    batch: {
      ...b,
      competitions: b.competitions.filter((c) => ok.has(c.sport)),
      teams: b.teams.filter((t) => ok.has(t.sport)),
      matches,
      predictions: b.predictions.filter((p) => !dropped.has(p.matchId)),
      metrics: b.metrics.filter((k) => ok.has(k.sport)),
    },
    skipped,
  };
}
