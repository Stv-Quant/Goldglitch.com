import Link from "next/link";
import { dt } from "@/components/admin/ui";
import { listAudit } from "@/lib/admin";

const LABEL: Record<string, string> = {
  grant_plan: "Otorgó plan", revoke_plan: "Terminó plan", add_note: "Agregó nota", set_tags: "Cambió etiquetas",
  suspend: "Suspendió cuenta", activate: "Reactivó cuenta", make_admin: "Hizo administrador", remove_admin: "Quitó rol admin",
  logout_all: "Cerró sesiones", force_password_change: "Obligó cambio de contraseña",
  export_usuarios: "Exportó usuarios (CSV)", export_pagos: "Exportó pagos (CSV)",
};

export default async function AuditPage() {
  const rows = await listAudit();
  return (
    <div className="space-y-6">
      <div>
        <p className="num text-[11px] tracking-[0.22em] text-gold uppercase">Registro</p>
        <h1 className="display mt-2 text-[2.4rem]">Auditoría</h1>
        <p className="mt-2 max-w-2xl text-sm text-mid">
          Cada acción hecha desde este panel queda registrada con quién, cuándo y sobre qué cuenta. No se puede editar ni borrar
          desde la aplicación.
        </p>
      </div>
      <div className="card overflow-x-auto">
        <table className="w-full text-sm min-w-[720px]">
          <thead><tr className="text-left text-[11px] text-lo border-b border-line">
            <th className="px-4 py-3 font-normal">Fecha</th><th className="px-4 py-3 font-normal">Administrador</th>
            <th className="px-4 py-3 font-normal">Acción</th><th className="px-4 py-3 font-normal">Cuenta</th><th className="px-4 py-3 font-normal">Detalle</th>
          </tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-t border-line">
                <td className="px-4 py-2.5 num text-xs">{dt(r.created_at)}</td>
                <td className="px-4 py-2.5">{r.admin ?? "—"}</td>
                <td className="px-4 py-2.5">{LABEL[r.action] ?? r.action}</td>
                <td className="px-4 py-2.5">{r.target_user_id ? <Link href={`/admin/usuarios/${r.target_user_id}`} className="hover:text-gold">{r.target ?? r.target_user_id}</Link> : "—"}</td>
                <td className="px-4 py-2.5 num text-[11px] text-lo">{r.detail ?? ""}</td>
              </tr>
            ))}
            {!rows.length && <tr><td colSpan={5} className="px-4 py-10 text-center text-lo">Aún no hay acciones registradas.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
