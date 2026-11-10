"use client";

import { useState } from "react";

const ERRORS: Record<string, string> = {
  invalid_email: "Revisa el correo, parece incompleto.",
  invalid: "Completa correo y contraseña.",
  rate_limited: "Demasiados intentos. Espera 15 minutos e inténtalo de nuevo.",
  mail_failed: "No pudimos enviar el correo. Intenta de nuevo o entra con contraseña.",
  bad_credentials: "Correo o contraseña incorrectos.",
  suspended: "Esta cuenta está suspendida. Escríbenos si crees que es un error.",
};

const input =
  "w-full rounded-[10px] bg-raise border border-line px-4 py-3 text-hi placeholder:text-lo focus:border-[var(--border-glass)] outline-none";

export function LoginForm() {
  const [mode, setMode] = useState<"password" | "link">("password");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "sent">("idle");
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setState("sending");
    setError(null);
    const url = mode === "password" ? "/api/auth/password" : "/api/auth/request";
    const payload = mode === "password" ? { email, password } : { email };
    const r = await fetch(url, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload) }).catch(() => null);
    const j = await r?.json().catch(() => null);
    if (j?.ok) {
      if (mode === "password") return window.location.assign(j.next ?? "/app");
      return setState("sent");
    }
    setError(ERRORS[j?.error] ?? "Algo falló. Intenta de nuevo.");
    setState("idle");
  }

  if (state === "sent") {
    return (
      <div className="glass p-6" role="status">
        <p className="font-medium">Revisa tu correo</p>
        <p className="mt-1 text-sm text-mid">Enviamos un enlace a <span className="text-hi">{email}</span>. Vence en 15 minutos.</p>
      </div>
    );
  }

  return (
    <div>
      <div role="tablist" aria-label="Forma de entrar" className="inline-flex rounded-xl border border-line p-1 text-sm mb-6">
        {(["password", "link"] as const).map((m) => (
          <button key={m} role="tab" type="button" aria-selected={mode === m} onClick={() => { setMode(m); setError(null); }}
            className={`px-4 py-1.5 rounded-lg transition-colors ${mode === m ? "bg-[var(--gold-faint)] text-hi" : "text-lo hover:text-hi"}`}>
            {m === "password" ? "Contraseña" : "Enlace al correo"}
          </button>
        ))}
      </div>
      <form onSubmit={submit} className="space-y-3">
        <label htmlFor="email" className="text-sm text-mid">Correo electrónico</label>
        <input id="email" type="email" required autoComplete="email" inputMode="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="tu@correo.com" className={input} />
        {mode === "password" && (
          <>
            <label htmlFor="password" className="text-sm text-mid block pt-1">Contraseña</label>
            <input id="password" type="password" required autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} className={input} />
            <a href="/acceso/recuperar" className="inline-block pt-1 text-xs text-gold hover:underline underline-offset-4">¿Olvidaste tu contraseña?</a>
          </>
        )}
        {error && <p role="alert" className="text-sm" style={{ color: "var(--neon-down)" }}>{error}</p>}
        <button type="submit" disabled={state === "sending"} className="btn-gold w-full py-3 disabled:opacity-60">
          {state === "sending" ? "Un momento…" : mode === "password" ? "Entrar" : "Enviarme el enlace"}
        </button>
        <p className="text-xs text-lo">
          {mode === "password" ? "¿Sin contraseña? Usa «Enlace al correo»: si no tienes cuenta, se crea gratis." : "Si no tienes cuenta, se crea al entrar — gratis."} Al entrar confirmas que eres mayor de 18 años.
        </p>
      </form>
    </div>
  );
}
