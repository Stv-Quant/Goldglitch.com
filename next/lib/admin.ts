import "server-only";
import { getDB } from "./env";
import { dayKey } from "./format";

const DAY = 24 * 60 * 60 * 1000;

export type DailyPoint = { day: string; value: number };

function lastNDays(n: number, now: number): string[] {
  return Array.from({ length: n }, (_, i) => dayKey(now - (n - 1 - i) * DAY));
}

function bucket(rows: { at: number; v: number }[], days: string[]): DailyPoint[] {
  const m = new Map(days.map((d) => [d, 0]));
  for (const r of rows) {
    const k = dayKey(r.at);
    if (m.has(k)) m.set(k, (m.get(k) ?? 0) + r.v);
  }
  return days.map((day) => ({ day, value: m.get(day) ?? 0 }));
}

export async function getOverview() {
  const db = await getDB();
  const now = Date.now();
  const d7 = now - 7 * DAY;
  const d30 = now - 30 * DAY;
  const d60 = now - 60 * DAY;

  const [users, subs, rev30, revPrev30, revAll, payStatus, mrrRows, paidEver, signups, revenue, ingest, upcoming, metrics] = await db.batch([
    db.prepare(
      `SELECT COUNT(*) total, COALESCE(SUM(created_at >= ?1),0) new7, COALESCE(SUM(created_at >= ?2),0) new30,
              COALESCE(SUM(created_at >= ?3 AND created_at < ?2),0) newPrev30,
              COALESCE(SUM(last_login_at >= ?1),0) active7, COALESCE(SUM(last_login_at >= ?2),0) active30,
              COALESCE(SUM(status = 'suspended'),0) suspended, COALESCE(SUM(is_admin = 1),0) admins
         FROM users`,
    ).bind(d7, d30, d60),
    db.prepare(
      `SELECT COALESCE(SUM(current_period_end > ?1),0) active,
              COALESCE(SUM(current_period_end > ?1 AND plan = 'pro'),0) pro,
              COALESCE(SUM(current_period_end > ?1 AND plan = 'elite'),0) elite,
              COALESCE(SUM(current_period_end > ?1 AND provider = 'admin'),0) comps,
              COALESCE(SUM(current_period_end > ?1 AND current_period_end <= ?2),0) expiring7,
              COALESCE(SUM(current_period_end <= ?1 AND current_period_end > ?3),0) expired30
         FROM subscriptions`,
    ).bind(now, now + 7 * DAY, d30),
    db.prepare("SELECT COALESCE(SUM(amount_in_cents),0) cents, COUNT(*) n FROM payments WHERE status='APPROVED' AND updated_at >= ?").bind(d30),
    db.prepare("SELECT COALESCE(SUM(amount_in_cents),0) cents FROM payments WHERE status='APPROVED' AND updated_at >= ? AND updated_at < ?").bind(d60, d30),
    db.prepare("SELECT COALESCE(SUM(amount_in_cents),0) cents, COUNT(*) n FROM payments WHERE status='APPROVED'"),
    db.prepare("SELECT status, COUNT(*) n FROM payments WHERE created_at >= ? GROUP BY status").bind(d30),
    db.prepare(
      `SELECT p.amount_in_cents cents, p.period
         FROM subscriptions s
         JOIN payments p ON p.id = (SELECT id FROM payments WHERE user_id = s.user_id AND status = 'APPROVED' ORDER BY updated_at DESC LIMIT 1)
        WHERE s.current_period_end > ? AND s.provider != 'admin'`,
    ).bind(now),
    db.prepare("SELECT COUNT(DISTINCT user_id) n FROM payments WHERE status='APPROVED'"),
    db.prepare("SELECT created_at at, 1 v FROM users WHERE created_at >= ?").bind(d30),
    db.prepare("SELECT updated_at at, amount_in_cents v FROM payments WHERE status='APPROVED' AND updated_at >= ?").bind(d30),
    db.prepare("SELECT received_at, source, records FROM ingest_batches ORDER BY received_at DESC LIMIT 1"),
    db.prepare(
      `SELECT COUNT(*) n, COALESCE(SUM(EXISTS(SELECT 1 FROM predictions p WHERE p.match_id = m.id)),0) withPred
         FROM matches m WHERE m.kickoff_at >= ? AND m.kickoff_at < ?`,
    ).bind(now, now + 7 * DAY),
    db.prepare("SELECT model_version, brier, baseline_brier, n, generated_at FROM model_metrics ORDER BY generated_at DESC LIMIT 1"),
  ]);

  const u = users.results[0] as Record<string, number>;
  const s = subs.results[0] as Record<string, number>;
  const mrr = (mrrRows.results as { cents: number; period: string }[]).reduce((a, r) => a + (r.period === "annual" ? r.cents / 12 : r.cents), 0);
  const paying = (mrrRows.results as unknown[]).length;
  const status = Object.fromEntries((payStatus.results as { status: string; n: number }[]).map((r) => [r.status, r.n]));
  const finished = (status.APPROVED ?? 0) + (status.DECLINED ?? 0) + (status.ERROR ?? 0) + (status.VOIDED ?? 0);
  const days = lastNDays(30, now);
  const r30 = rev30.results[0] as { cents: number; n: number };
  const rPrev = revPrev30.results[0] as { cents: number };
  const rAll = revAll.results[0] as { cents: number; n: number };
  const up = upcoming.results[0] as { n: number; withPred: number };

  return {
    users: {
      total: u.total, new7: u.new7, new30: u.new30, newPrev30: u.newPrev30,
      active7: u.active7, active30: u.active30, suspended: u.suspended, admins: u.admins,
    },
    subs: {
      active: s.active, pro: s.pro, elite: s.elite, comps: s.comps,
      expiring7: s.expiring7, expired30: s.expired30, paying,
    },
    revenue: {
      last30: r30.cents, prev30: rPrev.cents, payments30: r30.n, allTime: rAll.cents, paymentsAll: rAll.n,
      mrr, arppu: paying ? mrr / paying : 0,
    },
    conversion: { paidEver: (paidEver.results[0] as { n: number }).n, rate: u.total ? (paidEver.results[0] as { n: number }).n / u.total : 0 },
    payments: { byStatus: status, approvalRate: finished ? (status.APPROVED ?? 0) / finished : null, pending: status.PENDING ?? 0 },
    series: {
      signups: bucket(signups.results as { at: number; v: number }[], days),
      revenue: bucket(revenue.results as { at: number; v: number }[], days),
    },
    data: {
      lastIngest: (ingest.results[0] as { received_at: number; source: string; records: number } | undefined) ?? null,
      upcoming7: up.n,
      upcomingWithPrediction: up.withPred,
      model: (metrics.results[0] as { model_version: string; brier: number; baseline_brier: number | null; n: number; generated_at: number } | undefined) ?? null,
    },
    generatedAt: now,
  };
}

export type Segment = "all" | "paying" | "free" | "expiring" | "expired" | "admin" | "suspended";

const SEGMENT_SQL: Record<Segment, string> = {
  all: "1=1",
  paying: "s.current_period_end > ?3",
  free: "(s.user_id IS NULL OR s.current_period_end <= ?3)",
  expiring: "s.current_period_end > ?3 AND s.current_period_end <= ?3 + 604800000",
  expired: "s.current_period_end <= ?3",
  admin: "u.is_admin = 1",
  suspended: "u.status = 'suspended'",
};

export type UserRow = {
  id: string; email: string; is_admin: number; status: string; created_at: number; last_login_at: number | null;
  tags: string | null; plan: "pro" | "elite" | null; current_period_end: number | null; provider: string | null;
  paid_cents: number; payments_n: number; has_password: number;
};

export async function listUsers(q: string, segment: Segment, page: number, pageSize = 50) {
  const db = await getDB();
  const now = Date.now();
  // ?3 (now) is referenced in every variant: D1 rejects statements with unused bound parameters.
  const where = `(?1 = '' OR u.email LIKE ?2 OR COALESCE(u.tags,'') LIKE ?2) AND ?3 > 0 AND ${SEGMENT_SQL[segment] ?? "1=1"}`;
  const like = `%${q.replace(/[%_]/g, "")}%`;
  const [rows, count] = await db.batch([
    db.prepare(
      `SELECT u.id, u.email, u.is_admin, u.status, u.created_at, u.last_login_at, u.tags,
              s.plan, s.current_period_end, s.provider, (u.password_hash IS NOT NULL) has_password,
              (SELECT COALESCE(SUM(amount_in_cents),0) FROM payments p WHERE p.user_id = u.id AND p.status = 'APPROVED') paid_cents,
              (SELECT COUNT(*) FROM payments p WHERE p.user_id = u.id) payments_n
         FROM users u LEFT JOIN subscriptions s ON s.user_id = u.id
        WHERE ${where}
        ORDER BY u.created_at DESC LIMIT ?4 OFFSET ?5`,
    ).bind(q, like, now, pageSize, page * pageSize),
    db.prepare(`SELECT COUNT(*) n FROM users u LEFT JOIN subscriptions s ON s.user_id = u.id WHERE ${where}`).bind(q, like, now),
  ]);
  return { rows: rows.results as UserRow[], total: (count.results[0] as { n: number }).n };
}

export async function getUserDetail(id: string) {
  const db = await getDB();
  const [user, payments, sessions, notes, audit] = await db.batch([
    db.prepare(
      `SELECT u.*, (u.password_hash IS NOT NULL) has_password, s.plan, s.current_period_end, s.provider, s.updated_at sub_updated_at
         FROM users u LEFT JOIN subscriptions s ON s.user_id = u.id WHERE u.id = ?`,
    ).bind(id),
    db.prepare("SELECT * FROM payments WHERE user_id = ? ORDER BY created_at DESC LIMIT 100").bind(id),
    db.prepare("SELECT created_at, expires_at, user_agent FROM sessions WHERE user_id = ? ORDER BY created_at DESC LIMIT 20").bind(id),
    db.prepare(
      `SELECT n.id, n.body, n.created_at, a.email author FROM crm_notes n JOIN users a ON a.id = n.author_id
        WHERE n.user_id = ? ORDER BY n.created_at DESC LIMIT 100`,
    ).bind(id),
    db.prepare(
      `SELECT x.action, x.detail, x.created_at, a.email admin FROM admin_audit x LEFT JOIN users a ON a.id = x.admin_id
        WHERE x.target_user_id = ? ORDER BY x.created_at DESC LIMIT 50`,
    ).bind(id),
  ]);
  const u = user.results[0] as (Record<string, unknown> & { password_hash?: string }) | undefined;
  if (!u) return null;
  delete u.password_hash;
  return {
    user: u as unknown as UserRow & { display_name: string | null; must_change_password: number; sub_updated_at: number | null },
    payments: payments.results as PaymentRow[],
    sessions: sessions.results as { created_at: number; expires_at: number; user_agent: string | null }[],
    notes: notes.results as { id: string; body: string; created_at: number; author: string }[],
    audit: audit.results as { action: string; detail: string | null; created_at: number; admin: string | null }[],
  };
}

export type PaymentRow = {
  id: string; user_id: string; plan: string; period: string; amount_in_cents: number; currency: string;
  provider: string; provider_tx_id: string | null; status: string; applied_at: number | null; created_at: number; updated_at: number;
  email?: string;
};

export async function listPayments(status: string, q: string) {
  const db = await getDB();
  const like = `%${q.replace(/[%_]/g, "")}%`;
  const valid = ["PENDING", "APPROVED", "DECLINED", "VOIDED", "ERROR"].includes(status) ? status : "";
  const r = await db
    .prepare(
      `SELECT p.*, u.email FROM payments p JOIN users u ON u.id = p.user_id
        WHERE (?1 = '' OR p.status = ?1) AND (?2 = '' OR u.email LIKE ?3 OR p.id LIKE ?3 OR COALESCE(p.provider_tx_id,'') LIKE ?3)
        ORDER BY p.created_at DESC LIMIT 200`,
    )
    .bind(valid, q, like)
    .all<PaymentRow>();
  return r.results;
}

export async function getDataHealth() {
  const db = await getDB();
  const now = Date.now();
  const [batches, matchStatus, preds, missing, metrics, comps] = await db.batch([
    db.prepare("SELECT id, received_at, source, records FROM ingest_batches ORDER BY received_at DESC LIMIT 30"),
    db.prepare("SELECT status, COUNT(*) n FROM matches GROUP BY status"),
    db.prepare("SELECT COUNT(*) n, MAX(generated_at) last FROM predictions"),
    db.prepare(
      `SELECT m.id, m.kickoff_at, c.name comp, th.name home, ta.name away FROM matches m
         JOIN competitions c ON c.id = m.competition_id JOIN teams th ON th.id = m.home_team_id JOIN teams ta ON ta.id = m.away_team_id
        WHERE m.kickoff_at >= ? AND m.kickoff_at < ? AND NOT EXISTS (SELECT 1 FROM predictions p WHERE p.match_id = m.id)
        ORDER BY m.kickoff_at LIMIT 30`,
    ).bind(now, now + 7 * DAY),
    db.prepare("SELECT id, sport, model_version, n, brier, log_loss, baseline_brier, window_start, window_end, generated_at FROM model_metrics ORDER BY generated_at DESC LIMIT 20"),
    db.prepare(
      `SELECT c.name, c.sport, COUNT(m.id) n, COALESCE(SUM(m.kickoff_at >= ?),0) upcoming FROM competitions c
         LEFT JOIN matches m ON m.competition_id = c.id GROUP BY c.id ORDER BY n DESC`,
    ).bind(now),
  ]);
  return {
    batches: batches.results as { id: string; received_at: number; source: string; records: number }[],
    matchStatus: matchStatus.results as { status: string; n: number }[],
    predictions: preds.results[0] as { n: number; last: number | null },
    missing: missing.results as { id: string; kickoff_at: number; comp: string; home: string; away: string }[],
    metrics: metrics.results as {
      id: string; sport: string; model_version: string; n: number; brier: number; log_loss: number;
      baseline_brier: number | null; window_start: number; window_end: number; generated_at: number;
    }[],
    competitions: comps.results as { name: string; sport: string; n: number; upcoming: number }[],
  };
}

export async function listAudit() {
  const db = await getDB();
  const r = await db
    .prepare(
      `SELECT x.id, x.action, x.detail, x.created_at, a.email admin, t.email target, x.target_user_id
         FROM admin_audit x LEFT JOIN users a ON a.id = x.admin_id LEFT JOIN users t ON t.id = x.target_user_id
        ORDER BY x.created_at DESC LIMIT 300`,
    )
    .all<{ id: string; action: string; detail: string | null; created_at: number; admin: string | null; target: string | null; target_user_id: string | null }>();
  return r.results;
}
