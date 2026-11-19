"use client";

import Link from "next/link";
import { useState } from "react";

type Mode = "signup" | "login" | "link";

const ERRORS: Record<string, string> = {
  invalid_email: "Revisa el correo, parece incompleto.",
  invalid_username: "El usuario debe tener de 3 a 20 caracteres: letras, números, punto o guion bajo.",
  invalid: "Completa usuario o correo y contraseña.",
  adult: "Debes confirmar que eres mayor de 18 años.",
  email_taken: "Ese correo ya tiene cuenta. Entra con tu contraseña o recupérala.",
  username_taken: "Ese usuario ya existe. Prueba con otro.",
  rate_limited: "Demasiados intentos. Espera 15 minutos e inténtalo de nuevo.",
  mail_failed: "No pudimos enviar el correo. Intenta de nuevo o entra con contraseña.",
  bad_credentials: "Usuario, correo o contraseña incorrectos.",
  suspended: "Esta cuenta está suspendida. Escríbenos si crees que es un error.",
};

const input =
  "w-full rounded-[10px] bg-raise border border-line px-4 py-3 text-hi placeholder:text-lo focus:border-[var(--border-glass)] outline-none";

export function LoginForm({ defaultMode = "signup", children }: { defaultMode?: Mode; children?: React.ReactNode } = {}) {
  const [mode, setMode] = useState<Mode>(defaultMode);
  const [username, setUsername] = useState("");
  const [login, setLogin] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [adult, setAdult] = useState(false);
  const [state, setState] = useState<"idle" | "sending" | "sent">("idle");
  const [error, setError] = useState<string | null>(null);

  const go = (m: Mode) => { setMode(m); setError(null); };

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setState("sending");
    setError(null);
    const [url, payload] =
      mode === "signup" ? ["/api/auth/register", { username, email, password, adult }]
      : mode === "login" ? ["/api/auth/password", { login, password }]
      : ["/api/auth/request", { email }];
    const r = await fetch(url, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload) }).catch(() => null);
    const j = await r?.json().catch(() => null);
    if (j?.ok) {
      if (mode === "link") return setState("sent");
      return window.location.assign(j.next ?? "/app");
    }
    setError(j?.message ?? ERRORS[j?.error] ?? "Algo falló. Intenta de nuevo.");
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

  const tab = mode === "link" ? "login" : mode;
  const pwField = (autoComplete: string) => (
    <>
      <label htmlFor="password" className="text-sm text-mid block pt-1">Contraseña</label>
      <div className="relative">
        <input id="password" type={show ? "text" : "password"} required autoComplete={autoComplete} value={password}
          onChange={(e) => setPassword(e.target.value)} className={`${input} pr-20`} minLength={mode === "signup" ? 8 : undefined} />
        <button type="button" onClick={() => setShow((v) => !v)} aria-pressed={show}
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md px-2.5 py-1.5 text-xs text-lo hover:text-hi">
          {show ? "Ocultar" : "Mostrar"}
        </button>
      </div>
    </>
  );

  const HEAD: Record<Mode, [string, string]> = {
    signup: ["Crea tu cuenta gratis", "Usuario, correo y contraseña. Listo en un minuto, sin tarjeta."],
    login: ["Entra a tu cuenta", "Con tu usuario o tu correo."],
    link: ["Entra con un enlace", "Te enviamos un enlace al correo para entrar sin contraseña."],
  };

  return (
    <div>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight">{HEAD[mode][0]}</h1>
      <p className="mt-2 text-mid">{HEAD[mode][1]}</p>
      {children}
      <div className="mt-8" />
      <div role="tablist" aria-label="Cuenta" className="grid grid-cols-2 rounded-xl border border-line p-1 text-sm mb-6">
        {(["signup", "login"] as const).map((m) => (
          <button key={m} role="tab" type="button" aria-selected={tab === m} onClick={() => go(m)}
            className={`px-4 py-2 rounded-lg transition-colors ${tab === m ? "bg-[var(--gold-faint)] text-hi" : "text-lo hover:text-hi"}`}>
            {m === "signup" ? "Crear cuenta" : "Entrar"}
          </button>
        ))}
      </div>

      <form onSubmit={submit} className="space-y-3">
        {mode === "signup" && (
          <>
            <label htmlFor="username" className="text-sm text-mid">Usuario</label>
            <input id="username" required autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)}
              placeholder="ej. steven_10" maxLength={20} pattern="[A-Za-z0-9_.]{3,20}" className={input} />
            <label htmlFor="email" className="text-sm text-mid block pt-1">Correo electrónico</label>
            <input id="email" type="email" required autoComplete="email" inputMode="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="tu@correo.com" className={input} />
            {pwField("new-password")}
            <p className="text-xs text-lo">Mínimo 8 caracteres, con letras y números.</p>
            <label className="flex items-start gap-2.5 pt-2 text-sm text-mid cursor-pointer">
              <input type="checkbox" required checked={adult} onChange={(e) => setAdult(e.target.checked)} className="mt-1 accent-[var(--gold)]" />
              <span>
                Soy mayor de 18 años y acepto los <Link href="/legal/terminos" className="text-gold hover:underline">términos</Link> y la{" "}
                <Link href="/legal/privacidad" className="text-gold hover:underline">política de privacidad</Link>.
              </span>
            </label>
          </>
        )}

        {mode === "login" && (
          <>
            <label htmlFor="login" className="text-sm text-mid">Usuario o correo</label>
            <input id="login" required autoComplete="username" value={login} onChange={(e) => setLogin(e.target.value)} placeholder="tu usuario o tu@correo.com" className={input} />
            {pwField("current-password")}
            <a href="/acceso/recuperar" className="inline-block pt-1 text-xs text-gold hover:underline underline-offset-4">¿Olvidaste tu contraseña?</a>
          </>
        )}

        {mode === "link" && (
          <>
            <label htmlFor="email" className="text-sm text-mid">Correo electrónico</label>
            <input id="email" type="email" required autoComplete="email" inputMode="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="tu@correo.com" className={input} />
          </>
        )}

        {error && <p role="alert" className="text-sm" style={{ color: "var(--neon-down)" }}>{error}</p>}
        <button type="submit" disabled={state === "sending"} className="btn-gold w-full py-3 disabled:opacity-60">
          {state === "sending" ? "Un momento…" : mode === "signup" ? "Crear cuenta gratis" : mode === "login" ? "Entrar" : "Enviarme el enlace"}
        </button>

        <p className="text-xs text-lo text-center pt-1">
          {mode === "signup" && <>¿Ya tienes cuenta? <button type="button" onClick={() => go("login")} className="text-gold hover:underline">Entra aquí</button></>}
          {mode === "login" && <>¿No tienes contraseña? <button type="button" onClick={() => go("link")} className="text-gold hover:underline">Entra con un enlace al correo</button></>}
          {mode === "link" && <><button type="button" onClick={() => go("login")} className="text-gold hover:underline">Volver a entrar con contraseña</button></>}
        </p>
      </form>
    </div>
  );
}
