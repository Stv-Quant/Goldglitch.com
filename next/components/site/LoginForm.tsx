"use client";

import { useState } from "react";

const ERRORS: Record<string, string> = {
  invalid_email: "Revisa el correo, parece incompleto.",
  rate_limited: "Ya enviamos varios enlaces. Espera unos minutos y revisa spam.",
  mail_failed: "No pudimos enviar el correo. Intenta de nuevo.",
};

export function LoginForm() {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "sent">("idle");
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setState("sending");
    setError(null);
    const r = await fetch("/api/auth/request", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email }),
    }).catch(() => null);
    const j = await r?.json().catch(() => null);
    if (j?.ok) return setState("sent");
    setError(ERRORS[j?.error] ?? "Algo falló. Intenta de nuevo.");
    setState("idle");
  }

  if (state === "sent") {
    return (
      <div className="glass p-6" role="status">
        <p className="font-medium">Revisa tu correo</p>
        <p className="mt-1 text-sm text-mid">
          Enviamos un enlace a <span className="text-hi">{email}</span>. Vence en 15 minutos.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={submit} className="space-y-3">
      <label htmlFor="email" className="text-sm text-mid">Correo electrónico</label>
      <input
        id="email"
        type="email"
        required
        autoComplete="email"
        inputMode="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="tu@correo.com"
        className="w-full rounded-[10px] bg-raise border border-line px-4 py-3 text-hi placeholder:text-lo focus:border-[var(--border-glass)] outline-none"
      />
      {error && <p role="alert" className="text-sm" style={{ color: "var(--neon-down)" }}>{error}</p>}
      <button type="submit" disabled={state === "sending"} className="btn-gold w-full py-3 disabled:opacity-60">
        {state === "sending" ? "Enviando…" : "Enviarme el enlace"}
      </button>
      <p className="text-xs text-lo">Al entrar confirmas que eres mayor de 18 años.</p>
    </form>
  );
}
