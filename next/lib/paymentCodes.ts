import type { D1Database } from "@cloudflare/workers-types";
import type { PaidPlan } from "./plans";

export type PaymentCode = {
  code: string; plan: PaidPlan; amount_in_cents: number; lifetime: number; note: string | null;
  created_at: number; used_at: number | null; used_by: string | null; payment_id: string | null;
};

/** Lifetime access = 100 years from approval. */
export const LIFETIME_DAYS = 36_500;

export function normalizePaymentCode(raw: string | null | undefined): string | null {
  const c = (raw ?? "").trim().toUpperCase();
  return /^[A-Z0-9-]{8,40}$/.test(c) ? c : null;
}

export async function getPaymentCode(db: D1Database, raw: string | null | undefined): Promise<PaymentCode | null> {
  const code = normalizePaymentCode(raw);
  if (!code) return null;
  return db.prepare("SELECT * FROM payment_codes WHERE code = ?").bind(code).first<PaymentCode>();
}
