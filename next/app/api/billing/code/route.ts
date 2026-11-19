import { getViewer } from "@/lib/auth";
import { getDB, getEnv } from "@/lib/env";
import { getPaymentCode } from "@/lib/paymentCodes";
import { CURRENCY } from "@/lib/plans";
import { buildCheckoutUrl } from "@/lib/wompi";

/** Checkout for a special one-time payment code (fixed plan and price). The code is spent when Wompi approves. */
export async function POST(request: Request) {
  const viewer = await getViewer();
  if (!viewer) return Response.json({ ok: false, error: "unauthenticated" }, { status: 401 });
  const body = await request.json().catch(() => null);

  const env = await getEnv();
  if (!env.WOMPI_PUBLIC_KEY || !env.WOMPI_INTEGRITY_SECRET) {
    return Response.json({ ok: false, error: "billing_not_configured" }, { status: 503 });
  }
  const db = await getDB();
  const pc = await getPaymentCode(db, body?.code);
  if (!pc) return Response.json({ ok: false, error: "invalid_code" }, { status: 404 });
  if (pc.used_at) return Response.json({ ok: false, error: "code_used" }, { status: 409 });

  const reference = `gg_${crypto.randomUUID().replace(/-/g, "")}`;
  const now = Date.now();
  await db
    .prepare(
      `INSERT INTO payments (id, user_id, plan, period, amount_in_cents, currency, provider, status, created_at, updated_at, code, note)
       VALUES (?, ?, ?, 'annual', ?, ?, 'wompi', 'PENDING', ?, ?, ?, ?)`,
    )
    .bind(reference, viewer.userId, pc.plan, pc.amount_in_cents, CURRENCY, now, now, pc.code, pc.note)
    .run();

  const origin = env.APP_URL ?? new URL(request.url).origin;
  const url = await buildCheckoutUrl({
    publicKey: env.WOMPI_PUBLIC_KEY,
    integritySecret: env.WOMPI_INTEGRITY_SECRET,
    reference,
    amountInCents: pc.amount_in_cents,
    currency: CURRENCY,
    redirectUrl: `${origin}/app/cuenta?pago=${reference}`,
    email: viewer.email,
  });
  return Response.json({ ok: true, url, reference });
}
