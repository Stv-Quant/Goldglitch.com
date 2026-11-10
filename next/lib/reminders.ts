import "server-only";
import { getDB } from "./env";
import { sendRenewalReminder } from "./mail";
import type { PaidPlan } from "./plans";

const DAY = 86_400_000;

export type ReminderRun = { renewal_7d: number; renewal_1d: number; expired: number; checked: number; cleaned: number };

/**
 * Daily job. Paid memberships (not admin grants) get: a notice when ≤7 days remain, another when ≤1 day remains,
 * and one after expiry (within 3 days). email_log dedupe keys include the period end, so each stage goes out
 * once per period and a renewal starts a fresh cycle.
 */
export async function runRenewalReminders(now = Date.now()): Promise<ReminderRun> {
  const db = await getDB();
  const { results } = await db
    .prepare(
      `SELECT s.user_id, u.email, s.plan, s.current_period_end
         FROM subscriptions s JOIN users u ON u.id = s.user_id
        WHERE s.provider != 'admin' AND u.status != 'suspended'
          AND s.current_period_end > ? AND s.current_period_end <= ?`,
    )
    .bind(now - 3 * DAY, now + 7 * DAY)
    .all<{ user_id: string; email: string; plan: PaidPlan; current_period_end: number }>();

  const out: ReminderRun = { renewal_7d: 0, renewal_1d: 0, expired: 0, checked: results.length, cleaned: 0 };
  for (const r of results) {
    const left = r.current_period_end - now;
    const stage = left <= 0 ? "expired" : left <= DAY ? "renewal_1d" : "renewal_7d";
    const ok = await sendRenewalReminder({ id: r.user_id, email: r.email }, { plan: r.plan, periodEnd: r.current_period_end }, stage);
    if (ok) out[stage]++;
  }

  // Housekeeping: expired single-use tokens, old rate-limit rows and dead sessions.
  const cleaned = await db.batch([
    db.prepare("DELETE FROM login_tokens WHERE expires_at < ?").bind(now - DAY),
    db.prepare("DELETE FROM password_resets WHERE expires_at < ?").bind(now - DAY),
    db.prepare("DELETE FROM auth_attempts WHERE at < ?").bind(now - 7 * DAY),
    db.prepare("DELETE FROM sessions WHERE expires_at < ?").bind(now),
  ]);
  out.cleaned = cleaned.reduce((n, r) => n + (r.meta?.changes ?? 0), 0);
  return out;
}
