import { MailActions } from "@/components/admin/MailActions";
import { Badge, Metric, SectionTitle, ago, dt } from "@/components/admin/ui";
import { getViewer } from "@/lib/auth";
import { getDB, getEnv } from "@/lib/env";

export const dynamic = "force-dynamic";

const KIND: Record<string, { label: string; how: string }> = {
  welcome: { label: "Bienvenida", how: "Al crear la cuenta (primer ingreso con enlace). Una sola vez por persona." },
  magic_link: { label: "Enlace de acceso", how: "Cada vez que alguien pide entrar con «Enlace al correo»." },
  password_reset: { label: "Recuperar contraseña", how: "Desde «¿Olvidaste tu contraseña?». El enlace vence en 30 minutos." },
  password_changed: { label: "Contraseña cambiada", how: "Aviso de seguridad tras cambiar o restablecer la contraseña." },
  renewal_7d: { label: "Vence en 7 días", how: "Membresías pagas a las que les quedan 7 días o menos. Una vez por periodo." },
  renewal_1d: { label: "Vence mañana", how: "Membresías pagas a las que les queda 1 día o menos. Una vez por periodo." },
  expired: { label: "Plan vencido", how: "Hasta 3 días después del vencimiento, si no renovó. Una vez por periodo." },
  payment_approved: { label: "Pago aprobado", how: "Cuando Wompi confirma un pago. Incluye la nueva fecha de vencimiento." },
  test: { label: "Prueba", how: "Enviado desde este panel." },
};
const TONE = { sent: "up", failed: "down", skipped: "line" } as const;
const STATUS = { sent: "Enviado", failed: "Falló", skipped: "Omitido" } as const;

export default async function MailPage() {
  const [env, db, viewer] = await Promise.all([getEnv(), getDB(), getViewer()]);
  const since = Date.now() - 30 * 86_400_000;
  const [byKind, recent, upcoming] = await Promise.all([
    db.prepare("SELECT kind, status, COUNT(*) AS n FROM email_log WHERE created_at > ? GROUP BY kind, status").bind(since)
      .all<{ kind: string; status: keyof typeof TONE; n: number }>().then((r) => r.results).catch(() => []),
    db.prepare("SELECT kind, email, status, error, created_at FROM email_log ORDER BY created_at DESC LIMIT 60")
      .all<{ kind: string; email: string; status: keyof typeof TONE; error: string | null; created_at: number }>().then((r) => r.results).catch(() => []),
    db.prepare("SELECT COUNT(*) AS n FROM subscriptions WHERE provider != 'admin' AND current_period_end BETWEEN ? AND ?")
      .bind(Date.now(), Date.now() + 7 * 86_400_000).first<{ n: number }>().catch(() => null),
  ]);
  const totals = { sent: 0, failed: 0, skipped: 0 };
  for (const r of byKind) totals[r.status] += r.n;
  const configured = !!env.RESEND_API_KEY;

  return (
    <div className="space-y-8">
      <div>
        <p className="num text-[11px] tracking-[0.22em] text-gold uppercase">Resend</p>
        <h1 className="display mt-2 text-[2.4rem]">Correos automáticos</h1>
        <p className="mt-2 max-w-2xl text-sm text-mid">
          Bienvenida, recuperación de contraseña, avisos de seguridad, confirmación de pago y recordatorios de renovación.
          Los recordatorios corren solos todos los días a las 9:00 a. m. (hora Colombia).
        </p>
      </div>

      <section className="card p-5 sm:p-6 space-y-3">
        <p className="text-sm" style={{ color: configured ? "var(--neon-up)" : "var(--neon-down)" }}>
          ● {configured ? "Resend conectado." : "Falta RESEND_API_KEY: los correos se registran como «Omitido» y no salen."}
        </p>
        <p className="text-xs text-lo">Remitente: <span className="num">{env.MAIL_FROM ?? "Goldglitch <hola@easygoldglitch.com>"}</span></p>
        {viewer && <MailActions email={viewer.email} />}
      </section>

      <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 xl:grid-cols-4">
        <Metric label="Enviados (30 días)" value={String(totals.sent)} tone="up" how="Correos aceptados por Resend en los últimos 30 días." />
        <Metric label="Fallidos (30 días)" value={String(totals.failed)} tone={totals.failed ? "down" : undefined}
          how="Resend los rechazó (dominio sin verificar, clave inválida, dirección errónea). El motivo sale en el registro."
          why="Los recordatorios fallidos se reintentan en la siguiente ejecución diaria." />
        <Metric label="Omitidos (30 días)" value={String(totals.skipped)} how="No se enviaron porque Resend no estaba configurado en ese momento." />
        <Metric label="Vencen en 7 días" value={String(upcoming?.n ?? 0)} tone={upcoming?.n ? "gold" : undefined}
          how="Membresías pagas que recibirán (o ya recibieron) el aviso de renovación esta semana." />
      </div>

      <section className="space-y-3">
        <SectionTitle title="Qué se envía y cuándo" />
        <div className="card divide-y divide-[var(--border-soft)] text-sm">
          {Object.entries(KIND).filter(([k]) => k !== "test").map(([k, v]) => {
            const n = byKind.filter((r) => r.kind === k && r.status === "sent").reduce((a, r) => a + r.n, 0);
            return (
              <div key={k} className="flex flex-wrap items-start justify-between gap-2 px-4 py-3">
                <div className="min-w-0 flex-1"><div className="text-hi">{v.label}</div><div className="text-xs text-lo">{v.how}</div></div>
                <span className="num text-xs text-mid">{n} en 30 días</span>
              </div>
            );
          })}
        </div>
      </section>

      <section className="space-y-3">
        <SectionTitle title="Registro reciente" />
        <div className="card overflow-x-auto">
          <table className="w-full text-sm min-w-[640px]">
            <thead><tr className="text-left text-[11px] text-lo border-b border-line">
              <th className="px-4 py-2.5 font-normal">Fecha</th><th className="px-4 py-2.5 font-normal">Tipo</th>
              <th className="px-4 py-2.5 font-normal">Para</th><th className="px-4 py-2.5 font-normal">Estado</th>
            </tr></thead>
            <tbody>
              {recent.map((r, i) => (
                <tr key={i} className="border-t border-line align-top">
                  <td className="px-4 py-2.5 text-xs text-lo whitespace-nowrap" title={dt(r.created_at)}>{ago(r.created_at)}</td>
                  <td className="px-4 py-2.5">{KIND[r.kind]?.label ?? r.kind}</td>
                  <td className="px-4 py-2.5 num text-xs break-all">{r.email}</td>
                  <td className="px-4 py-2.5"><Badge tone={TONE[r.status]}>{STATUS[r.status]}</Badge>{r.error && <div className="mt-1 text-[11px] text-lo break-all">{r.error}</div>}</td>
                </tr>
              ))}
              {!recent.length && <tr><td colSpan={4} className="px-4 py-6 text-center text-lo">Aún no se ha enviado ningún correo.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
