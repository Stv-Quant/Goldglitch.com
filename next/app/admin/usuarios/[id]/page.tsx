import Link from "next/link";
import { notFound } from "next/navigation";
import { UserActions } from "@/components/admin/UserActions";
import { Badge, STATUS_LABEL, STATUS_TONE, ago, dt } from "@/components/admin/ui";
import { getUserDetail } from "@/lib/admin";
import { getViewer } from "@/lib/auth";
import { formatCOP, PLANS } from "@/lib/plans";

const ACTION_LABEL: Record<string, string> = {
  grant_plan: "Otorgó plan", revoke_plan: "Terminó el plan", add_note: "Agregó nota", set_tags: "Cambió etiquetas",
  suspend: "Suspendió la cuenta", activate: "Reactivó la cuenta", make_admin: "Lo hizo administrador",
  remove_admin: "Le quitó el rol admin", logout_all: "Cerró sus sesiones", force_password_change: "Obligó cambio de contraseña",
};

function device(ua: string | null): string {
  if (!ua) return "Desconocido";
  const os = /iPhone|iPad/.test(ua) ? "iOS" : /Android/.test(ua) ? "Android" : /Windows/.test(ua) ? "Windows" : /Mac OS/.test(ua) ? "macOS" : /Linux/.test(ua) ? "Linux" : "Otro";
  const br = /Edg\//.test(ua) ? "Edge" : /Chrome\//.test(ua) ? "Chrome" : /Safari\//.test(ua) ? "Safari" : /Firefox\//.test(ua) ? "Firefox" : "Navegador";
  return `${br} · ${os}`;
}

export default async function UserDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [d, viewer] = await Promise.all([getUserDetail(id), getViewer()]);
  if (!d) notFound();
  const u = d.user;
  const now = Date.now();
  const active = !!u.current_period_end && u.current_period_end > now;
  const ltv = d.payments.filter((p) => p.status === "APPROVED").reduce((a, p) => a + p.amount_in_cents, 0);
  const liveSessions = d.sessions.filter((s) => s.expires_at > now).length;

  return (
    <div className="space-y-8">
      <Link href="/admin/usuarios" className="text-sm text-lo hover:text-hi">← Usuarios</Link>

      <header className="glass p-6 grid gap-6 md:grid-cols-[1fr_auto]">
        <div>
          <h1 className="text-2xl font-semibold break-all">{u.email}</h1>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {active ? <Badge tone="gold">{PLANS[u.plan!].name}{u.provider === "admin" ? " · cortesía" : ""}</Badge> : <Badge>Free</Badge>}
            {u.is_admin ? <Badge tone="flare">admin</Badge> : null}
            {u.status === "suspended" && <Badge tone="down">suspendido</Badge>}
            {u.must_change_password ? <Badge tone="gold">debe cambiar contraseña</Badge> : null}
            <Badge>{u.has_password ? "entra con contraseña" : "entra con enlace"}</Badge>
          </div>
          <p className="mt-3 text-xs text-lo num">ID {u.id}</p>
        </div>
        <dl className="grid grid-cols-2 gap-x-8 gap-y-3 text-sm">
          <div><dt className="text-[11px] text-lo">Valor total (LTV)</dt><dd className="num text-lg text-gold">{formatCOP(ltv)}</dd></div>
          <div><dt className="text-[11px] text-lo">Plan vence</dt><dd className="num">{u.current_period_end ? dt(u.current_period_end) : "—"}</dd></div>
          <div><dt className="text-[11px] text-lo">Registro</dt><dd className="num">{dt(u.created_at)}</dd></div>
          <div><dt className="text-[11px] text-lo">Último ingreso</dt><dd className="num">{ago(u.last_login_at)}</dd></div>
        </dl>
      </header>

      <div className="grid gap-8 xl:grid-cols-[1fr_380px]">
        <div className="space-y-8 min-w-0">
          <section>
            <h2 className="text-lg font-semibold">Pagos</h2>
            <div className="card mt-3 overflow-x-auto">
              <table className="w-full text-sm min-w-[620px]">
                <thead><tr className="text-left text-[11px] text-lo border-b border-line">
                  <th className="px-4 py-2.5 font-normal">Fecha</th><th className="px-4 py-2.5 font-normal">Plan</th>
                  <th className="px-4 py-2.5 font-normal text-right">Monto</th><th className="px-4 py-2.5 font-normal">Estado</th><th className="px-4 py-2.5 font-normal">Referencia</th>
                </tr></thead>
                <tbody>
                  {d.payments.map((p) => (
                    <tr key={p.id} className="border-t border-line">
                      <td className="px-4 py-2.5 num text-xs">{dt(p.created_at)}</td>
                      <td className="px-4 py-2.5">{PLANS[p.plan as "pro" | "elite"]?.name ?? p.plan} · {p.period === "annual" ? "anual" : "mensual"}</td>
                      <td className="px-4 py-2.5 num text-right">{formatCOP(p.amount_in_cents)}</td>
                      <td className="px-4 py-2.5"><Badge tone={STATUS_TONE[p.status]}>{STATUS_LABEL[p.status] ?? p.status}</Badge></td>
                      <td className="px-4 py-2.5 num text-[11px] text-lo">{p.id.slice(0, 14)}…</td>
                    </tr>
                  ))}
                  {!d.payments.length && <tr><td colSpan={5} className="px-4 py-6 text-center text-lo">Sin pagos.</td></tr>}
                </tbody>
              </table>
            </div>
          </section>

          <section>
            <h2 className="text-lg font-semibold">Notas internas</h2>
            <ul className="mt-3 space-y-2">
              {d.notes.map((nt) => (
                <li key={nt.id} className="card p-4">
                  <p className="text-sm whitespace-pre-wrap">{nt.body}</p>
                  <p className="mt-2 text-[11px] text-lo num">{nt.author} · {dt(nt.created_at)}</p>
                </li>
              ))}
              {!d.notes.length && <li className="text-sm text-lo">Aún no hay notas.</li>}
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold">Sesiones <span className="text-sm text-lo font-normal">· {liveSessions} activa(s)</span></h2>
            <ul className="card mt-3 divide-y divide-[var(--border-soft)] text-sm">
              {d.sessions.map((s, i) => (
                <li key={i} className="flex flex-wrap justify-between gap-2 px-4 py-2.5">
                  <span>{device(s.user_agent)}</span>
                  <span className="num text-xs text-lo">inició {dt(s.created_at)} · {s.expires_at > now ? "activa" : "expirada"}</span>
                </li>
              ))}
              {!d.sessions.length && <li className="px-4 py-4 text-lo">Sin sesiones registradas.</li>}
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold">Historial de cambios</h2>
            <ul className="mt-3 space-y-1.5 text-sm">
              {d.audit.map((a, i) => (
                <li key={i} className="flex flex-wrap gap-x-3 text-mid">
                  <span className="num text-xs text-lo">{dt(a.created_at)}</span>
                  <span>{a.admin ?? "—"} · {ACTION_LABEL[a.action] ?? a.action}</span>
                  {a.detail && <span className="num text-xs text-lo">{a.detail}</span>}
                </li>
              ))}
              {!d.audit.length && <li className="text-lo">Ningún administrador ha modificado esta cuenta.</li>}
            </ul>
          </section>
        </div>

        <aside>
          <UserActions userId={u.id} isAdmin={!!u.is_admin} suspended={u.status === "suspended"} hasPassword={!!u.has_password}
            isSelf={viewer?.userId === u.id} tags={u.tags ?? ""} />
        </aside>
      </div>
    </div>
  );
}
