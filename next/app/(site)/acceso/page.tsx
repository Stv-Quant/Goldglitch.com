import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { LoginForm } from "@/components/site/LoginForm";
import { getViewer } from "@/lib/auth";
import { INVITE_COOKIE, getInviteByCode, inviteState, normalizeCode } from "@/lib/invites";
import { cookies } from "next/headers";

export const metadata: Metadata = { title: "Entrar" };
export const dynamic = "force-dynamic";

const INVITE_MSG = {
  full: "Esta invitación ya alcanzó el máximo de personas. Puedes crear tu cuenta gratis igualmente.",
  expired: "Esta invitación ya venció. Puedes crear tu cuenta gratis igualmente.",
  revoked: "Esta invitación ya no está activa. Puedes crear tu cuenta gratis igualmente.",
  invalid: "No encontramos esa invitación. Puedes crear tu cuenta gratis igualmente.",
} as const;

export default async function AccesoPage({ searchParams }: { searchParams: Promise<{ error?: string; invitacion?: string }> }) {
  if (await getViewer().catch(() => null)) redirect("/app");
  const { error, invitacion } = await searchParams;
  const code = normalizeCode((await cookies()).get(INVITE_COOKIE)?.value);
  const invite = code ? await getInviteByCode(code).catch(() => null) : null;
  const active = invite && inviteState(invite) === "active" ? invite : null;
  const gift = active?.gift_plan ? `${active.gift_plan === "elite" ? "Elite" : "Pro"} gratis por ${active.gift_days} días` : null;

  return (
    <section className="mx-auto max-w-md px-4 py-20">
      <p className="eyebrow">Acceso</p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight">Entra sin contraseña</h1>
      <p className="mt-2 text-mid">Te enviamos un enlace al correo. Si no tienes cuenta, se crea al entrar — gratis.</p>
      {error === "link" && (
        <p role="alert" className="mt-6 card p-3 text-sm" style={{ borderColor: "rgba(255,77,109,.35)" }}>
          Ese enlace venció o ya se usó. Pide uno nuevo.
        </p>
      )}
      {active && (
        <div role="status" className="mt-6 card p-4 text-sm" style={{ borderColor: "var(--border-glass)" }}>
          <p className="text-gold">Tienes una invitación.</p>
          <p className="mt-1 text-mid">
            Crea tu cuenta con <b className="text-hi">Enlace al correo</b>{gift ? <> y recibes <b className="text-hi">{gift}</b></> : null}.
            Válida hasta el {new Intl.DateTimeFormat("es-CO", { dateStyle: "long", timeZone: "America/Bogota" }).format(active.expires_at)}.
          </p>
        </div>
      )}
      {!active && invitacion && invitacion in INVITE_MSG && (
        <p role="alert" className="mt-6 card p-3 text-sm text-mid">{INVITE_MSG[invitacion as keyof typeof INVITE_MSG]}</p>
      )}
      <div className="mt-8">
        <LoginForm defaultMode={active ? "link" : "password"} />
      </div>
    </section>
  );
}
