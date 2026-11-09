"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

type Props = { userId: string; isAdmin: boolean; suspended: boolean; hasPassword: boolean; isSelf: boolean; tags: string };

export function UserActions({ userId, isAdmin, suspended, hasPassword, isSelf, tags }: Props) {
  const router = useRouter();
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [plan, setPlan] = useState<"pro" | "elite">("pro");
  const [days, setDays] = useState(30);
  const [note, setNote] = useState("");
  const [tagStr, setTagStr] = useState(tags);
  const [confirming, setConfirming] = useState<string | null>(null);

  async function run(action: string, extra: Record<string, unknown> = {}, label = "Hecho.") {
    setBusy(action);
    setMsg(null);
    const r = await fetch(`/api/admin/users/${userId}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ action, ...extra }),
    }).catch(() => null);
    const j = await r?.json().catch(() => null);
    setBusy(null);
    setConfirming(null);
    if (j?.ok) {
      setMsg({ ok: true, text: label });
      if (action === "note") setNote("");
      router.refresh();
    } else setMsg({ ok: false, text: j?.error ?? "No se pudo completar." });
  }

  // Two-step confirmation for disruptive actions, without browser dialogs.
  function Danger({ action, label, done }: { action: string; label: string; done: string }) {
    if (confirming === action) {
      return (
        <span className="inline-flex gap-2">
          <button className="btn-ghost px-3 py-1.5 text-xs border-[var(--neon-down)] text-down" disabled={!!busy} onClick={() => run(action, {}, done)}>Confirmar</button>
          <button className="btn-ghost px-3 py-1.5 text-xs" onClick={() => setConfirming(null)}>Cancelar</button>
        </span>
      );
    }
    return <button className="btn-ghost px-3 py-1.5 text-xs" onClick={() => setConfirming(action)}>{label}</button>;
  }

  const input = "rounded-[8px] bg-raise border border-line px-3 py-2 text-sm text-hi outline-none focus:border-[var(--border-glass)]";

  return (
    <div className="space-y-5">
      <div className="card p-5">
        <h3 className="text-sm font-semibold">Membresía manual</h3>
        <p className="mt-1 text-xs text-lo">Otorga o extiende un plan sin pago (cortesías, soporte, alianzas). Queda marcado como «admin» y no suma al MRR.</p>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <select value={plan} onChange={(e) => setPlan(e.target.value as "pro" | "elite")} className={input} aria-label="Plan">
            <option value="pro">Pro</option>
            <option value="elite">Elite</option>
          </select>
          <input type="number" min={1} max={3650} value={days} onChange={(e) => setDays(Number(e.target.value))} className={`${input} w-24`} aria-label="Días" />
          <span className="text-xs text-lo">días</span>
          <button className="btn-gold px-4 py-2 text-sm" disabled={!!busy} onClick={() => run("grant", { plan, days }, `Plan ${plan} otorgado por ${days} días.`)}>
            {busy === "grant" ? "Guardando…" : "Otorgar"}
          </button>
          <Danger action="revoke" label="Terminar plan ahora" done="Plan terminado." />
        </div>
      </div>

      <div className="card p-5">
        <h3 className="text-sm font-semibold">Nota interna</h3>
        <textarea value={note} onChange={(e) => setNote(e.target.value)} rows={3} maxLength={4000} placeholder="Contexto de soporte, acuerdos, seguimiento…" className={`${input} mt-3 w-full`} />
        <button className="btn-ghost mt-2 px-4 py-2 text-sm" disabled={!note.trim() || !!busy} onClick={() => run("note", { body: note }, "Nota guardada.")}>Guardar nota</button>
      </div>

      <div className="card p-5">
        <h3 className="text-sm font-semibold">Etiquetas</h3>
        <p className="mt-1 text-xs text-lo">Separadas por comas, p. ej. «vip, afiliado, prueba». Se pueden buscar en la lista de usuarios.</p>
        <div className="mt-3 flex gap-2">
          <input value={tagStr} onChange={(e) => setTagStr(e.target.value)} className={`${input} flex-1`} aria-label="Etiquetas" />
          <button className="btn-ghost px-4 py-2 text-sm" disabled={!!busy} onClick={() => run("tags", { tags: tagStr }, "Etiquetas guardadas.")}>Guardar</button>
        </div>
      </div>

      <div className="card p-5">
        <h3 className="text-sm font-semibold">Cuenta y seguridad</h3>
        <div className="mt-3 flex flex-wrap gap-2">
          {!isSelf && <Danger action="logout" label="Cerrar todas sus sesiones" done="Sesiones cerradas." />}
          {hasPassword && <Danger action="force_password_change" label="Obligar cambio de contraseña" done="Deberá cambiarla al entrar." />}
          {!isSelf && (suspended
            ? <button className="btn-ghost px-3 py-1.5 text-xs" onClick={() => run("activate", {}, "Cuenta reactivada.")}>Reactivar cuenta</button>
            : <Danger action="suspend" label="Suspender cuenta" done="Cuenta suspendida." />)}
          {!isSelf && (isAdmin
            ? <Danger action="remove_admin" label="Quitar rol admin" done="Ya no es administrador." />
            : <Danger action="make_admin" label="Hacer administrador" done="Ahora es administrador." />)}
        </div>
        {isSelf && <p className="mt-2 text-xs text-lo">Es tu propia cuenta: no puedes suspenderla ni quitarte el rol desde aquí.</p>}
      </div>

      {msg && (
        <p role="status" className="text-sm" style={{ color: msg.ok ? "var(--neon-up)" : "var(--neon-down)" }}>{msg.text}</p>
      )}
    </div>
  );
}
