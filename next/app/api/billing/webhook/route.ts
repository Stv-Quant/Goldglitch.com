import { getDB, getEnv } from "@/lib/env";
import { later, sendPaymentApproved } from "@/lib/mail";
import { PERIOD_DAYS, type BillingPeriod } from "@/lib/plans";
import { verifyEventChecksum, type WompiEvent } from "@/lib/wompi";

const DAY_MS = 24 * 60 * 60 * 1000;
const FINAL = new Set(["APPROVED", "DECLINED", "VOIDED", "ERROR"]);

// Wompi retries on non-2xx, so only return errors when a retry could succeed.
export async function POST(request: Request) {
  const env = await getEnv();
  if (!env.WOMPI_EVENTS_SECRET) return new Response("not configured", { status: 503 });

  const evt = (await request.json().catch(() => null)) as WompiEvent | null;
  if (!evt || typeof evt !== "object") return new Response("bad request", { status: 400 });

  const authentic = await verifyEventChecksum(evt, env.WOMPI_EVENTS_SECRET, request.headers.get("x-event-checksum"));
  if (!authentic) return new Response("invalid checksum", { status: 401 });

  if (evt.event !== "transaction.updated" || !evt.data?.transaction) return Response.json({ ok: true, ignored: true });
  const tx = evt.data.transaction;
  if (!FINAL.has(tx.status)) return Response.json({ ok: true, ignored: true });

  const db = await getDB();
  const now = Date.now();

  const payment = await db
    .prepare("SELECT id, user_id, plan, period, amount_in_cents, currency, applied_at FROM payments WHERE id = ?")
    .bind(tx.reference)
    .first<{ id: string; user_id: string; plan: "pro" | "elite"; period: BillingPeriod; amount_in_cents: number; currency: string; applied_at: number | null }>();
  if (!payment) return Response.json({ ok: true, ignored: "unknown_reference" });

  if (tx.status !== "APPROVED") {
    await db
      .prepare("UPDATE payments SET status = ?, provider_tx_id = ?, updated_at = ? WHERE id = ? AND applied_at IS NULL")
      .bind(tx.status, tx.id, now, payment.id)
      .run();
    return Response.json({ ok: true });
  }

  // Never trust amount/currency from the client: they must match what we priced.
  if (tx.amount_in_cents !== payment.amount_in_cents || tx.currency !== payment.currency) {
    await db
      .prepare("UPDATE payments SET status = 'ERROR', provider_tx_id = ?, updated_at = ? WHERE id = ? AND applied_at IS NULL")
      .bind(tx.id, now, payment.id)
      .run();
    console.error("wompi amount mismatch", { reference: payment.id, tx: tx.id });
    return Response.json({ ok: true, flagged: "amount_mismatch" });
  }

  // Idempotent claim: only the first delivery of this approval flips applied_at.
  const claimed = await db
    .prepare(
      "UPDATE payments SET status = 'APPROVED', provider_tx_id = ?, applied_at = ?, updated_at = ? WHERE id = ? AND applied_at IS NULL RETURNING id",
    )
    .bind(tx.id, now, now, payment.id)
    .first();
  if (!claimed) return Response.json({ ok: true, duplicate: true });

  const extension = PERIOD_DAYS[payment.period] * DAY_MS;
  // Same plan: stack on top of remaining time. Plan change: new period starts now (no proration in v1).
  await db
    .prepare(
      `INSERT INTO subscriptions (user_id, plan, current_period_end, provider, updated_at)
       VALUES (?1, ?2, ?3 + ?4, 'wompi', ?3)
       ON CONFLICT(user_id) DO UPDATE SET
         current_period_end = CASE
           WHEN subscriptions.plan = excluded.plan AND subscriptions.current_period_end > ?3
             THEN subscriptions.current_period_end + ?4
           ELSE ?3 + ?4 END,
         plan = excluded.plan,
         provider = excluded.provider,
         updated_at = excluded.updated_at`,
    )
    .bind(payment.user_id, payment.plan, now, extension)
    .run();

  const after = await db
    .prepare("SELECT u.email, s.current_period_end FROM users u JOIN subscriptions s ON s.user_id = u.id WHERE u.id = ?")
    .bind(payment.user_id)
    .first<{ email: string; current_period_end: number }>();
  if (after) {
    await later(sendPaymentApproved({ id: payment.user_id, email: after.email }, {
      reference: payment.id, plan: payment.plan, period: payment.period,
      amountInCents: payment.amount_in_cents, periodEnd: after.current_period_end,
    }));
  }
  return Response.json({ ok: true, applied: true });
}
