import { notFound } from "next/navigation";
import { CodeCheckout } from "@/components/app/CodeCheckout";
import { getDB } from "@/lib/env";
import { getPaymentCode } from "@/lib/paymentCodes";
import { PLANS, formatCOP } from "@/lib/plans";

export const dynamic = "force-dynamic";

export default async function SpecialPayment({ params }: { params: Promise<{ code: string }> }) {
  const pc = await getPaymentCode(await getDB(), (await params).code);
  if (!pc) notFound();
  return (
    <main className="mx-auto max-w-md px-4 py-12">
      <div className="card p-6">
        <p className="num text-[11px] tracking-[0.22em] text-gold uppercase">Pago especial</p>
        <h1 className="mt-3 text-2xl font-semibold">{PLANS[pc.plan].name} {pc.lifetime ? "de por vida" : ""}</h1>
        {pc.note && <p className="mt-1 text-sm text-lo">{pc.note}</p>}
        <p className="num mt-6 text-4xl gold-leaf">{formatCOP(pc.amount_in_cents)}</p>
        <p className="mt-2 text-xs text-lo">Pago único con Wompi. Este enlace sirve para una sola compra.</p>
        {pc.used_at
          ? <p role="alert" className="mt-6 text-sm" style={{ color: "var(--neon-down)" }}>Este código ya fue usado.</p>
          : <CodeCheckout code={pc.code} />}
      </div>
    </main>
  );
}
