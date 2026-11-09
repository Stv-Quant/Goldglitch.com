import Link from "next/link";
import { Badge, ago, dt } from "@/components/admin/ui";
import { listUsers, type Segment } from "@/lib/admin";
import { formatCOP, PLANS } from "@/lib/plans";

const SEGMENTS: { key: Segment; label: string; hint: string }[] = [
  { key: "all", label: "Todos", hint: "Todas las cuentas" },
  { key: "paying", label: "Con plan activo", hint: "Pro o Elite vigente" },
  { key: "expiring", label: "Vencen en 7 días", hint: "Para recordarles renovar" },
  { key: "expired", label: "Vencidos", hint: "Tuvieron plan y no renovaron" },
  { key: "free", label: "Free", hint: "Sin plan vigente" },
  { key: "admin", label: "Admins", hint: "Con acceso a este panel" },
  { key: "suspended", label: "Suspendidos", hint: "Bloqueados" },
];

export default async function UsersPage({ searchParams }: { searchParams: Promise<{ q?: string; seg?: string; page?: string }> }) {
  const sp = await searchParams;
  const q = (sp.q ?? "").trim().slice(0, 100);
  const seg = (SEGMENTS.some((s) => s.key === sp.seg) ? sp.seg : "all") as Segment;
  const page = Math.max(0, Number(sp.page ?? 0) || 0);
  const { rows, total } = await listUsers(q, seg, page);
  const now = Date.now();
  const qs = (o: Record<string, string | number>) => new URLSearchParams({ q, seg, ...Object.fromEntries(Object.entries(o).map(([k, v]) => [k, String(v)])) }).toString();

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="num text-[11px] tracking-[0.22em] text-gold uppercase">CRM</p>
          <h1 className="display mt-2 text-[2.4rem]">Usuarios</h1>
          <p className="mt-1 text-sm text-lo">{total.toLocaleString("es-CO")} resultado(s)</p>
        </div>
        <a href={`/api/admin/export?what=users&${qs({})}`} className="btn-ghost px-4 py-2 text-sm">Exportar CSV</a>
      </div>

      <form className="flex flex-wrap gap-2" action="/admin/usuarios">
        <input type="hidden" name="seg" value={seg} />
        <input name="q" defaultValue={q} placeholder="Buscar por correo o etiqueta…" aria-label="Buscar"
          className="flex-1 min-w-[220px] rounded-[10px] bg-raise border border-line px-4 py-2.5 text-sm outline-none focus:border-[var(--border-glass)]" />
        <button className="btn-gold px-5 py-2.5 text-sm">Buscar</button>
      </form>

      <nav aria-label="Segmentos" className="flex flex-wrap gap-2">
        {SEGMENTS.map((s) => (
          <Link key={s.key} href={`/admin/usuarios?${new URLSearchParams({ q, seg: s.key })}`} title={s.hint}
            aria-current={seg === s.key ? "true" : undefined}
            className={`rounded-full border px-3 py-1 text-xs ${seg === s.key ? "border-[var(--border-glass)] bg-[var(--gold-faint)] text-hi" : "border-line text-lo hover:text-hi"}`}>
            {s.label}
          </Link>
        ))}
      </nav>

      <div className="card overflow-x-auto">
        <table className="w-full text-sm min-w-[860px]">
          <thead>
            <tr className="text-left text-[11px] text-lo border-b border-line">
              <th className="px-4 py-3 font-normal">Usuario</th>
              <th className="px-4 py-3 font-normal">Plan</th>
              <th className="px-4 py-3 font-normal">Vence</th>
              <th className="px-4 py-3 font-normal text-right">Pagado</th>
              <th className="px-4 py-3 font-normal">Registro</th>
              <th className="px-4 py-3 font-normal">Último ingreso</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((u) => {
              const active = !!u.current_period_end && u.current_period_end > now;
              const soon = active && u.current_period_end! - now < 7 * 86_400_000;
              return (
                <tr key={u.id} className="border-t border-line hover:bg-[rgba(237,230,214,0.02)]">
                  <td className="px-4 py-3">
                    <Link href={`/admin/usuarios/${u.id}`} className="text-hi hover:text-gold">{u.email}</Link>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {u.is_admin ? <Badge tone="flare">admin</Badge> : null}
                      {u.status === "suspended" && <Badge tone="down">suspendido</Badge>}
                      {u.tags?.split(",").map((t) => <Badge key={t}>{t}</Badge>)}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {active ? <Badge tone="gold">{PLANS[u.plan!].name}{u.provider === "admin" ? " · cortesía" : ""}</Badge> : u.plan ? <Badge tone="down">{PLANS[u.plan].name} vencido</Badge> : <Badge>Free</Badge>}
                  </td>
                  <td className="px-4 py-3 num text-xs" style={{ color: soon ? "var(--gold)" : "var(--text-mid)" }}>{u.current_period_end ? dt(u.current_period_end) : "—"}</td>
                  <td className="px-4 py-3 num text-right">{u.paid_cents ? formatCOP(u.paid_cents) : <span className="text-lo">—</span>}<div className="text-[11px] text-lo">{u.payments_n} pago(s)</div></td>
                  <td className="px-4 py-3 num text-xs text-mid">{dt(u.created_at)}</td>
                  <td className="px-4 py-3 num text-xs text-mid">{ago(u.last_login_at)}</td>
                </tr>
              );
            })}
            {!rows.length && (
              <tr><td colSpan={6} className="px-4 py-10 text-center text-lo">No hay usuarios en este segmento.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {total > 50 && (
        <div className="flex items-center justify-between text-sm">
          {page > 0 ? <Link href={`/admin/usuarios?${qs({ page: page - 1 })}`} className="btn-ghost px-4 py-2">← Anterior</Link> : <span />}
          <span className="num text-lo">Página {page + 1} de {Math.ceil(total / 50)}</span>
          {(page + 1) * 50 < total ? <Link href={`/admin/usuarios?${qs({ page: page + 1 })}`} className="btn-ghost px-4 py-2">Siguiente →</Link> : <span />}
        </div>
      )}
    </div>
  );
}
