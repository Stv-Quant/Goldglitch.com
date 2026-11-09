import { getViewer } from "@/lib/auth";
import { getDB, getEnv } from "@/lib/env";
import { CURRENCY, PLANS, type BillingPeriod, type PaidPlan } from "@/lib/plans";
import { buildCheckoutUrl } from "@/lib/wompi";

const PAID: PaidPlan[] = ["pro", "elite"];
const PERIODS: BillingPeriod[] = ["monthly", "annual"];

export async function POST(request: Request) {
  const viewer = await getViewer();
  if (!viewer) return Response.json({ ok: false, error: "unauthenticated" }, { status: 401 });

  const body = await request.json().catch(() => null);
  const plan = body?.plan as PaidPlan;
  const period = body?.period as BillingPeriod;
  if (!PAID.includes(plan) || !PERIODS.includes(period)) {
    return Response.json({ ok: false, error: "invalid_plan" }, { status: 400 });
  }

  const env = await getEnv();
  if (!env.WOMPI_PUBLIC_KEY || !env.WOMPI_INTEGRITY_SECRET) {
    return Response.json({ ok: false, error: "billing_not_configured" }, { status: 503 });
  }

  const amountInCents = PLANS[plan].price[period];
  const reference = `gg_${crypto.randomUUID().replace(/-/g, "")}`;
  const now = Date.now();

  const db = await getDB();
  await db
    .prepare(
      `INSERT INTO payments (id, user_id, plan, period, amount_in_cents, currency, provider, status, created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, 'wompi', 'PENDING', ?, ?)`,
    )
    .bind(reference, viewer.userId, plan, period, amountInCents, CURRENCY, now, now)
    .run();

  const origin = env.APP_URL ?? new URL(request.url).origin;
  const url = await buildCheckoutUrl({
    publicKey: env.WOMPI_PUBLIC_KEY,
    integritySecret: env.WOMPI_INTEGRITY_SECRET,
    reference,
    amountInCents,
    currency: CURRENCY,
    redirectUrl: `${origin}/app/cuenta?pago=${reference}`,
    email: viewer.email,
  });

  return Response.json({ ok: true, url, reference });
}
