"use client";

import Link from "next/link";
import { useState } from "react";

const input =
  "w-full rounded-[10px] bg-raise border border-line px-4 py-3 text-hi placeholder:text-lo focus:border-[var(--border-glass)] outline-none";

export function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "sent">("idle");
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setState("sending");
    const r = await fetch("/api/auth/forgot", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ email }) }).catch(() => null);
    const j = await r?.json().catch(() => null);
    if (j?.ok) return setState("sent");
    setError(j?.error ?? "No pudimos enviar el correo. Intenta de nuevo.");
    setState("idle");
  }

  if (state === "sent") {
    return (
      <div className="card p-5 text-sm text-mid" role="status">
        Si <span className="text-hi">{email}</span> tiene una cuenta, en un minuto te llega el enlace. Revisa también la carpeta de spam.
        <div className="mt-4"><Link href="/acceso" className="text-gold hover:underline underline-offset-4">← Volver a entrar</Link></div>
      </div>
    );
  }
  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="space-y-1.5">
        <label htmlFor="email" className="text-sm text-mid">Correo</label>
        <input id="email" type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} className={input} />
      </div>
      {error && <p role="alert" className="text-sm" style={{ color: "var(--neon-down)" }}>{error}</p>}
      <button type="submit" disabled={state === "sending"} className="btn-gold w-full py-3 disabled:opacity-60">
        {state === "sending" ? "Enviando…" : "Enviarme el enlace"}
      </button>
      <p className="text-center text-sm"><Link href="/acceso" className="text-lo hover:text-hi">Volver a entrar</Link></p>
    </form>
  );
}
