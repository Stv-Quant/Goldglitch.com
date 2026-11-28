import { redirect } from "next/navigation";
import { LogoutButton } from "@/components/app/LogoutButton";
import { getViewer } from "@/lib/auth";
import { getDB } from "@/lib/env";
import { dateLabel } from "@/lib/format";

export const dynamic = "force-dynamic";

const PAYMENT_MSG: Record<string, { text: string; tone: string }> = {
  APPROVED: { text: "Pago aprobado. Tu plan ya está activo.", tone: "var(--neon-up)" },
  PENDING: { text: "Estamos esperando la confirmación de Wompi. Puede tardar unos minutos (PSE a veces más).", tone: "var(--gold)" },
  DECLINED: { text: "El pago fue rechazado. No se hizo ningún cobro.", tone: "var(--neon-down)" },
  VOIDED: { text: "El pago fue anulado.", tone: "var(--neon-down)" },
  ERROR: { text: "Hubo un error con el pago. Si se debitó, escríbenos con la referencia.", tone: "var(--neon-down)" },
};

export default async function CuentaPage({ searchParams }: { searchParams: Promise<{ pago?: string }> }) {
  const viewer = await getViewer();
  if (!viewer) redirect("/acceso?entrar");
  const { pago } = await searchParams;

  let paymentStatus: string | null = null;
  if (pago) {
    const db = await getDB();
    const row = await db
      .prepare("SELECT status FROM payments WHERE id = ? AND user_id = ?")
      .bind(pago, viewer.userId)
      .first<{ status: string }>();
    paymentStatus = row?.status ?? null;
  }
  const msg = paymentStatus ? PAYMENT_MSG[paymentStatus] : null;

  return (
    <div className="space-y-8">
      <div>
        <p className="eyebrow">Cuenta</p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">{viewer.email}</h1>
      </div>

      {msg && (
        <p role="status" className="card p-4 text-sm" style={{ borderColor: msg.tone }}>
          <span style={{ color: msg.tone }}>●</span> {msg.text}
          <span className="block text-[11px] text-lo num mt-1">Ref. {pago}</span>
        </p>
      )}

      <section className="glass p-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="text-xs text-lo">Tu cuenta</div>
          <div className="text-xl font-semibold text-gold">Gratis · todo incluido</div>
          <div className="text-sm text-mid mt-0.5">Goldglitch no cobra nada: tienes todas las estadísticas, picks y alertas.</div>
        </div>
        <LogoutButton />
      </section>
    </div>
  );
}
