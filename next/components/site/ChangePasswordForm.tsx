"use client";

import { useState } from "react";

const input =
  "w-full rounded-[10px] bg-raise border border-line px-4 py-3 text-hi placeholder:text-lo focus:border-[var(--border-glass)] outline-none";

function strength(pw: string): { score: number; label: string } {
  let s = 0;
  if (pw.length >= 12) s++;
  if (pw.length >= 16) s++;
  s += [/[a-z]/, /[A-Z]/, /[0-9]/, /[^A-Za-z0-9]/].filter((r) => r.test(pw)).length >= 3 ? 1 : 0;
  if (pw.length >= 20) s++;
  return { score: s, label: ["Muy débil", "Débil", "Aceptable", "Fuerte", "Muy fuerte"][s] };
}

/** Change the password (signed in) or, with `resetToken`, set a new one from a recovery email. */
export function ChangePasswordForm({ resetToken }: { resetToken?: string } = {}) {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const st = strength(next);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (next !== confirm) return setError("Las contraseñas nuevas no coinciden.");
    setBusy(true);
    const r = await fetch(resetToken ? "/api/auth/reset" : "/api/auth/change-password", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(resetToken ? { token: resetToken, password: next } : { current, next }),
    }).catch(() => null);
    const j = await r?.json().catch(() => null);
    if (j?.ok) return window.location.assign(j.next);
    setError(j?.error ?? "No pudimos guardar la contraseña.");
    setBusy(false);
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      {!resetToken && (
        <div className="space-y-1.5">
          <label htmlFor="cur" className="text-sm text-mid">Contraseña actual (o temporal)</label>
          <input id="cur" type={show ? "text" : "password"} autoComplete="current-password" required value={current} onChange={(e) => setCurrent(e.target.value)} className={input} />
        </div>
      )}
      <div className="space-y-1.5">
        <label htmlFor="new" className="text-sm text-mid">Nueva contraseña</label>
        <input id="new" type={show ? "text" : "password"} autoComplete="new-password" required minLength={12} value={next} onChange={(e) => setNext(e.target.value)} className={input} aria-describedby="pw-help" />
        <div className="flex items-center gap-3 pt-1" aria-live="polite">
          <div className="flex flex-1 gap-1" aria-hidden>
            {[0, 1, 2, 3].map((i) => (
              <span key={i} className="h-1 flex-1 rounded-full" style={{ background: i < st.score ? (st.score >= 3 ? "var(--gold)" : "var(--neon-down)") : "var(--border-soft)" }} />
            ))}
          </div>
          {next && <span className="num text-[11px] text-lo">{st.label}</span>}
        </div>
        <p id="pw-help" className="text-xs text-lo">Mínimo 12 caracteres, combinando al menos 3 de: minúsculas, mayúsculas, números y símbolos.</p>
      </div>
      <div className="space-y-1.5">
        <label htmlFor="conf" className="text-sm text-mid">Repite la nueva contraseña</label>
        <input id="conf" type={show ? "text" : "password"} autoComplete="new-password" required value={confirm} onChange={(e) => setConfirm(e.target.value)} className={input} />
      </div>
      <label className="flex items-center gap-2 text-sm text-mid">
        <input type="checkbox" checked={show} onChange={(e) => setShow(e.target.checked)} /> Mostrar contraseñas
      </label>
      {error && <p role="alert" className="text-sm" style={{ color: "var(--neon-down)" }}>{error}</p>}
      <button type="submit" disabled={busy} className="btn-gold w-full py-3 disabled:opacity-60">{busy ? "Guardando…" : "Guardar contraseña"}</button>
    </form>
  );
}
