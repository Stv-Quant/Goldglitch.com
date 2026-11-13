"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

const input = "w-full rounded-[10px] bg-raise border border-line px-3 py-2.5 text-hi outline-none focus:border-[var(--border-glass)]";

function todayPlus(days: number) {
  const d = new Date(Date.now() - 5 * 3_600_000 + days * 86_400_000);
  return d.toISOString().slice(0, 10);
}

export function InviteForm({ base }: { base: string }) {
  const router = useRouter();
  const [label, setLabel] = useState("");
  const [maxUses, setMaxUses] = useState("50");
  const [expiresOn, setExpiresOn] = useState(todayPlus(30));
  const [giftPlan, setGiftPlan] = useState<"" | "pro" | "elite">("");
  const [giftDays, setGiftDays] = useState("30");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true); setError(null); setCreated(null);
    const r = await fetch("/api/admin/invites", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ label, maxUses: Number(maxUses), expiresOn, giftPlan: giftPlan || null, giftDays: Number(giftDays) }),
    }).catch(() => null);
    const j = await r?.json().catch(() => null);
    setBusy(false);
    if (!j?.ok) return setError(j?.error ?? "No se pudo crear la invitación.");
    setCreated(`${base}/i/${j.invite.code}`);
    setLabel("");
    router.refresh();
  }

  return (
    <form onSubmit={submit} className="card p-5 sm:p-6 space-y-4">
      <h2 className="text-lg font-semibold">Nueva invitación</h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <label className="space-y-1.5 sm:col-span-2">
          <span className="text-sm text-mid">Nombre (solo lo ves tú)</span>
          <input required maxLength={80} value={label} onChange={(e) => setLabel(e.target.value)} placeholder="Ej. Grupo de WhatsApp de noviembre" className={input} />
        </label>
        <label className="space-y-1.5">
          <span className="text-sm text-mid">Máximo de personas</span>
          <input required type="number" min={1} max={100000} value={maxUses} onChange={(e) => setMaxUses(e.target.value)} className={`${input} num`} />
        </label>
        <label className="space-y-1.5">
          <span className="text-sm text-mid">Registro hasta (incluido)</span>
          <input required type="date" min={todayPlus(0)} value={expiresOn} onChange={(e) => setExpiresOn(e.target.value)} className={`${input} num`} />
        </label>
        <label className="space-y-1.5">
          <span className="text-sm text-mid">Regalo al registrarse</span>
          <select value={giftPlan} onChange={(e) => setGiftPlan(e.target.value as "" | "pro" | "elite")} className={input}>
            <option value="">Ninguno (plan gratis)</option>
            <option value="pro">Pro</option>
            <option value="elite">Elite</option>
          </select>
        </label>
        {giftPlan && (
          <label className="space-y-1.5">
            <span className="text-sm text-mid">Días de regalo</span>
            <input required type="number" min={1} max={365} value={giftDays} onChange={(e) => setGiftDays(e.target.value)} className={`${input} num`} />
          </label>
        )}
      </div>
      <p className="text-xs text-lo">
        Cuenta solo a personas que crean su cuenta nueva desde el enlace. Al llegar al máximo o pasar la fecha, el enlace deja de dar acceso a la invitación
        (la persona igual puede registrarse gratis, sin regalo).
      </p>
      {error && <p role="alert" className="text-sm" style={{ color: "var(--neon-down)" }}>{error}</p>}
      <div className="flex flex-wrap items-center gap-3">
        <button disabled={busy} className="btn-gold px-4 py-2 text-sm disabled:opacity-60">{busy ? "Creando…" : "Crear enlace"}</button>
        {created && <CopyLink url={created} />}
      </div>
    </form>
  );
}

export function CopyLink({ url }: { url: string }) {
  const [ok, setOk] = useState(false);
  return (
    <span className="inline-flex min-w-0 items-center gap-2">
      <code className="num truncate text-xs text-gold">{url}</code>
      <button type="button" onClick={() => navigator.clipboard.writeText(url).then(() => { setOk(true); setTimeout(() => setOk(false), 1500); })}
        className="rounded-lg border border-line px-2.5 py-1 text-xs text-mid hover:text-hi">{ok ? "Copiado ✓" : "Copiar"}</button>
    </span>
  );
}

export function RevokeInvite({ id }: { id: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  return (
    <button type="button" disabled={busy}
      onClick={async () => {
        setBusy(true);
        await fetch(`/api/admin/invites/${id}`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ action: "revoke" }) }).catch(() => null);
        setBusy(false);
        router.refresh();
      }}
      className="rounded-lg border border-line px-2.5 py-1 text-xs text-mid hover:text-[var(--neon-down)] disabled:opacity-50">
      {busy ? "…" : "Desactivar"}
    </button>
  );
}
