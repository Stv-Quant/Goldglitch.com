import Link from "next/link";
import { CopyLink, InviteForm, RevokeInvite } from "@/components/admin/InviteForm";
import { Badge, dt } from "@/components/admin/ui";
import { getDB } from "@/lib/env";
import { inviteState, type Invite } from "@/lib/invites";
import { appUrl } from "@/lib/mail";

export const dynamic = "force-dynamic";

const STATE = {
  active: { label: "Activa", tone: "up" },
  full: { label: "Llena", tone: "gold" },
  expired: { label: "Vencida", tone: "line" },
  revoked: { label: "Desactivada", tone: "down" },
} as const;

export default async function InvitesPage() {
  const db = await getDB();
  const base = await appUrl();
  const invites = (await db.prepare("SELECT * FROM invites ORDER BY created_at DESC LIMIT 200").all<Invite>()).results;
  const people = (await db
    .prepare(
      `SELECT r.invite_id, r.redeemed_at, u.id, u.email FROM invite_redemptions r JOIN users u ON u.id = r.user_id
        ORDER BY r.redeemed_at DESC LIMIT 2000`,
    )
    .all<{ invite_id: string; redeemed_at: number; id: string; email: string }>()).results;
  const byInvite = Map.groupBy(people, (p) => p.invite_id);

  return (
    <div className="space-y-8">
      <div>
        <p className="num text-[11px] tracking-[0.22em] text-gold uppercase">Solo administradores</p>
        <h1 className="display mt-2 text-[2.4rem]">Invitaciones</h1>
        <p className="mt-2 max-w-2xl text-sm text-mid">
          Crea un enlace para que un grupo se registre: tú decides cuántas personas pueden usarlo, hasta qué fecha y si reciben un plan de regalo.
        </p>
      </div>

      <InviteForm base={base} />

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Enlaces creados</h2>
        {!invites.length && <div className="card p-6 text-sm text-lo">Aún no has creado invitaciones.</div>}
        <ul className="space-y-3">
          {invites.map((i) => {
            const st = STATE[inviteState(i)];
            const list = byInvite.get(i.id) ?? [];
            const pct = Math.min(100, (i.uses / i.max_uses) * 100);
            return (
              <li key={i.id} className="card p-4 sm:p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium text-hi">{i.label}</span>
                      <Badge tone={st.tone}>{st.label}</Badge>
                      {i.gift_plan && <Badge tone="gold">{i.gift_plan === "elite" ? "Elite" : "Pro"} {i.gift_days} días</Badge>}
                    </div>
                    <div className="mt-1.5"><CopyLink url={`${base}/i/${i.code}`} /></div>
                  </div>
                  {!i.revoked_at && <RevokeInvite id={i.id} />}
                </div>
                <div className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
                  <div>
                    <div className="text-xs text-lo">Registrados</div>
                    <div className="num"><span className="text-hi text-lg">{i.uses}</span> <span className="text-lo">/ {i.max_uses}</span></div>
                    <div className="mt-1 h-1.5 rounded-full bg-[var(--seg-3)]"><div className="h-full rounded-full bg-[var(--gold)]" style={{ width: `${pct}%` }} /></div>
                  </div>
                  <div><div className="text-xs text-lo">Registro hasta</div><div className="num">{dt(i.expires_at)}</div></div>
                  <div><div className="text-xs text-lo">Creada</div><div className="num">{dt(i.created_at)}</div></div>
                </div>
                {list.length > 0 && (
                  <details className="mt-4">
                    <summary className="cursor-pointer text-sm text-gold">Ver las {list.length} personas registradas</summary>
                    <ul className="mt-2 divide-y divide-[var(--border-soft)] text-sm">
                      {list.map((p) => (
                        <li key={p.id} className="flex flex-wrap justify-between gap-2 py-2">
                          <Link href={`/admin/usuarios/${p.id}`} className="break-all hover:text-gold">{p.email}</Link>
                          <span className="num text-xs text-lo">{dt(p.redeemed_at)}</span>
                        </li>
                      ))}
                    </ul>
                  </details>
                )}
              </li>
            );
          })}
        </ul>
      </section>
    </div>
  );
}
