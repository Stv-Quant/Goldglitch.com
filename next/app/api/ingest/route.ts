import type { D1PreparedStatement } from "@cloudflare/workers-types";
import { ingestBatchSchema } from "@/lib/contracts";
import { hmacSha256Hex, safeEqual, sha256Hex } from "@/lib/crypto";
import { getDB, getEnv } from "@/lib/env";

const MAX_SKEW_MS = 5 * 60 * 1000;
const MAX_BODY_BYTES = 5 * 1024 * 1024;
const CHUNK = 100;

/**
 * SQPC → PWA publishing endpoint.
 * Headers: X-GG-Timestamp (epoch ms), X-GG-Signature = hex HMAC-SHA256(secret, `${timestamp}.${rawBody}`).
 * Idempotent on batchId.
 */
export async function POST(request: Request) {
  const env = await getEnv();
  if (!env.INGEST_HMAC_SECRET) return Response.json({ ok: false, error: "not_configured" }, { status: 503 });

  const ts = Number(request.headers.get("x-gg-timestamp"));
  const sig = request.headers.get("x-gg-signature") ?? "";
  if (!Number.isFinite(ts) || Math.abs(Date.now() - ts) > MAX_SKEW_MS) {
    return Response.json({ ok: false, error: "stale_or_missing_timestamp" }, { status: 401 });
  }

  const raw = await request.text();
  if (raw.length > MAX_BODY_BYTES) return Response.json({ ok: false, error: "payload_too_large" }, { status: 413 });

  const expected = await hmacSha256Hex(env.INGEST_HMAC_SECRET, `${ts}.${raw}`);
  if (!safeEqual(expected, sig)) return Response.json({ ok: false, error: "bad_signature" }, { status: 401 });

  let json: unknown;
  try {
    json = JSON.parse(raw);
  } catch {
    return Response.json({ ok: false, error: "invalid_json" }, { status: 400 });
  }
  const parsed = ingestBatchSchema.safeParse(json);
  if (!parsed.success) {
    return Response.json(
      { ok: false, error: "invalid_batch", issues: parsed.error.issues.slice(0, 20) },
      { status: 422 },
    );
  }
  const b = parsed.data;
  const db = await getDB();
  const now = Date.now();

  const seen = await db.prepare("SELECT id FROM ingest_batches WHERE id = ?").bind(b.batchId).first();
  if (seen) return Response.json({ ok: true, duplicate: true });

  const stmts: D1PreparedStatement[] = [];

  for (const c of b.competitions) {
    stmts.push(
      db
        .prepare(
          `INSERT INTO competitions (id, sport, name, country, season) VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET sport=excluded.sport, name=excluded.name, country=excluded.country, season=excluded.season`,
        )
        .bind(c.id, c.sport, c.name, c.country ?? null, c.season ?? null),
    );
  }
  for (const t of b.teams) {
    stmts.push(
      db
        .prepare(
          `INSERT INTO teams (id, sport, name, short_name, country) VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET sport=excluded.sport, name=excluded.name, short_name=excluded.short_name, country=excluded.country`,
        )
        .bind(t.id, t.sport, t.name, t.shortName ?? null, t.country ?? null),
    );
  }
  for (const m of b.matches) {
    stmts.push(
      db
        .prepare(
          `INSERT INTO matches (id, sport, competition_id, home_team_id, away_team_id, kickoff_at, status, home_score, away_score, venue, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET sport=excluded.sport, competition_id=excluded.competition_id,
             home_team_id=excluded.home_team_id, away_team_id=excluded.away_team_id, kickoff_at=excluded.kickoff_at,
             status=excluded.status, home_score=excluded.home_score, away_score=excluded.away_score,
             venue=excluded.venue, updated_at=excluded.updated_at`,
        )
        .bind(
          m.id, m.sport, m.competitionId, m.homeTeamId, m.awayTeamId, m.kickoffAt, m.status,
          m.homeScore ?? null, m.awayScore ?? null, m.venue ?? null, now,
        ),
    );
  }
  // Seal rule: a prediction is only accepted if generated before kickoff, and an existing one can
  // only be replaced by a newer pre-kickoff version. After kickoff nothing — not even us — can edit it.
  const predStart = stmts.length;
  for (const p of b.predictions) {
    stmts.push(
      db
        .prepare(
          `INSERT INTO predictions (match_id, model_version, generated_at, p_home, p_draw, p_away, payload)
           SELECT ?1, ?2, ?3, ?4, ?5, ?6, ?7
            WHERE ?3 < (SELECT kickoff_at FROM matches WHERE id = ?1)
           ON CONFLICT(match_id, model_version) DO UPDATE SET generated_at=excluded.generated_at,
             p_home=excluded.p_home, p_draw=excluded.p_draw, p_away=excluded.p_away, payload=excluded.payload
           WHERE excluded.generated_at >= predictions.generated_at
             AND excluded.generated_at < (SELECT kickoff_at FROM matches WHERE id = excluded.match_id)`,
        )
        .bind(p.matchId, p.modelVersion, p.generatedAt, p.outcome.home, p.outcome.draw, p.outcome.away, JSON.stringify(p)),
    );
  }
  const predEnd = stmts.length;
  for (const k of b.metrics) {
    stmts.push(
      db
        .prepare(
          `INSERT INTO model_metrics (id, sport, competition_id, model_version, window_start, window_end, n, brier, log_loss, baseline_brier, calibration, generated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET n=excluded.n, brier=excluded.brier, log_loss=excluded.log_loss,
             baseline_brier=excluded.baseline_brier, calibration=excluded.calibration, generated_at=excluded.generated_at,
             window_start=excluded.window_start, window_end=excluded.window_end`,
        )
        .bind(
          k.id, k.sport, k.competitionId ?? null, k.modelVersion, k.windowStart, k.windowEnd, k.n,
          k.brier, k.logLoss, k.baselineBrier ?? null, JSON.stringify(k.calibration), k.generatedAt,
        ),
    );
  }

  // Order matters (FKs): competitions → teams → matches → predictions → metrics. Chunks run sequentially.
  let predictionsSealed = 0;
  try {
    for (let i = 0; i < stmts.length; i += CHUNK) {
      const res = await db.batch(stmts.slice(i, i + CHUNK));
      res.forEach((r, j) => {
        const idx = i + j;
        if (idx >= predStart && idx < predEnd) predictionsSealed += r.meta?.changes ? 1 : 0;
      });
    }
  } catch (e) {
    return Response.json({ ok: false, error: "db_write_failed", detail: String(e).slice(0, 300) }, { status: 500 });
  }

  await db
    .prepare("INSERT INTO ingest_batches (id, received_at, source, records, body_sha256) VALUES (?, ?, ?, ?, ?)")
    .bind(b.batchId, now, b.source, stmts.length, await sha256Hex(raw))
    .run();

  return Response.json({
    ok: true,
    written: {
      competitions: b.competitions.length,
      teams: b.teams.length,
      matches: b.matches.length,
      predictions: predictionsSealed,
      metrics: b.metrics.length,
    },
    // Predictions rejected because they were generated at/after kickoff or are older than the stored seal.
    rejectedPredictions: b.predictions.length - predictionsSealed,
  });
}
