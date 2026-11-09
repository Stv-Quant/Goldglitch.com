import Link from "next/link";
import { Badge, STATUS_LABEL, STATUS_TONE, dt } from "@/components/admin/ui";
import { listPayments } from "@/lib/admin";
import { formatCOP, PLANS } from "@/lib/plans";

export default async function PaymentsPage({ searchParams }: { searchParams: Promise<{ status?: string; q?: string }> }) {
  const sp = await searchParams;
  const status = sp.status ?? "";
  const q = (sp.q ?? "").trim().slice(0, 100);
  const rows = await listPayments(status, q);
  const approved = rows.filter((p) => p.status === "APPROVED");
  const sum = approved.reduce((a, p) => a + p.amount_in_cents, 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="num text-[11px] tracking-[0.22em] text-gold uppercase">Wompi</p>
          <h1 className="display mt-2 text-[2.4rem]">Pagos</h1>
          <p className="mt-1 text-sm text-lo">{rows.length} pago(s) mostrados · {approved.length} aprobados por {formatCOP(sum)}</p>
        </div>
        <a href={`/api/admin/export?what=payments&${new URLSearchParams({ status, q })}`} className="btn-ghost px-4 py-2 text-sm">Exportar CSV</a>
      </div>

      <div className="card p-4 text-[13px] text-mid leading-relaxed">
        <span className="text-hi">Cómo leer esta tabla.</span> Cada vez que alguien abre el pago se crea un registro <Badge tone="gold">Pendiente</Badge>.
        Wompi nos avisa el resultado por webhook firmado y el estado cambia a <Badge tone="up">Aprobado</Badge>, <Badge tone="down">Rechazado</Badge>,
        anulado o error. Solo los aprobados activan la membresía. Un pendiente antiguo suele ser alguien que abrió el pago y no lo terminó.
      </div>

      <form className="flex flex-wrap gap-2" action="/admin/pagos">
        <select name="status" defaultValue={status} aria-label="Estado"
          className="rounded-[10px] bg-raise border border-line px-3 py-2.5 text-sm outline-none">
          <option value="">Todos los estados</option>
          {Object.entries(STATUS_LABEL).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
        </select>
        <input name="q" defaultValue={q} placeholder="Correo, referencia o ID de Wompi…" aria-label="Buscar"
          className="flex-1 min-w-[220px] rounded-[10px] bg-raise border border-line px-4 py-2.5 text-sm outline-none focus:border-[var(--border-glass)]" />
        <button className="btn-gold px-5 py-2.5 text-sm">Filtrar</button>
      </form>

      <div className="card overflow-x-auto">
        <table className="w-full text-sm min-w-[900px]">
          <thead><tr className="text-left text-[11px] text-lo border-b border-line">
            <th className="px-4 py-3 font-normal">Fecha</th><th className="px-4 py-3 font-normal">Usuario</th><th className="px-4 py-3 font-normal">Plan</th>
            <th className="px-4 py-3 font-normal text-right">Monto</th><th className="px-4 py-3 font-normal">Estado</th>
            <th className="px-4 py-3 font-normal">Referencia</th><th className="px-4 py-3 font-normal">Transacción Wompi</th>
          </tr></thead>
          <tbody>
            {rows.map((p) => (
              <tr key={p.id} className="border-t border-line">
                <td className="px-4 py-3 num text-xs">{dt(p.created_at)}</td>
                <td className="px-4 py-3"><Link href={`/admin/usuarios/${p.user_id}`} className="hover:text-gold">{p.email}</Link></td>
                <td className="px-4 py-3">{PLANS[p.plan as "pro" | "elite"]?.name ?? p.plan} · {p.period === "annual" ? "anual" : "mensual"}</td>
                <td className="px-4 py-3 num text-right">{formatCOP(p.amount_in_cents)}</td>
                <td className="px-4 py-3"><Badge tone={STATUS_TONE[p.status]}>{STATUS_LABEL[p.status] ?? p.status}</Badge></td>
                <td className="px-4 py-3 num text-[11px] text-lo">{p.id}</td>
                <td className="px-4 py-3 num text-[11px] text-lo">{p.provider_tx_id ?? "—"}</td>
              </tr>
            ))}
            {!rows.length && <tr><td colSpan={7} className="px-4 py-10 text-center text-lo">Todavía no hay pagos con estos filtros.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
