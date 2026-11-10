"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function MailActions({ email }: { email: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  async function run(kind: "test" | "reminders") {
    setBusy(kind); setMsg(null);
    const r = await fetch(kind === "test" ? "/api/admin/mail-test" : "/api/cron/reminders", { method: "POST" }).catch(() => null);
    const j = await r?.json().catch(() => null);
    setBusy(null);
    if (!j?.ok) setMsg(kind === "test" ? "No se pudo enviar. Revisa el registro abajo." : "No se pudo ejecutar.");
    else if (kind === "test") setMsg(`Enviado a ${email}. Revisa tu bandeja (y spam).`);
    else setMsg(`Listo: ${j.renewal_7d} aviso(s) de 7 días, ${j.renewal_1d} de 1 día y ${j.expired} de vencimiento, de ${j.checked} membresía(s) revisadas.`);
    router.refresh();
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <button onClick={() => run("test")} disabled={!!busy} className="btn-gold px-4 py-2 text-sm disabled:opacity-60">
        {busy === "test" ? "Enviando…" : "Enviarme un correo de prueba"}
      </button>
      <button onClick={() => run("reminders")} disabled={!!busy} className="rounded-lg border border-line px-4 py-2 text-sm text-mid hover:text-hi disabled:opacity-60">
        {busy === "reminders" ? "Ejecutando…" : "Ejecutar recordatorios ahora"}
      </button>
      {msg && <p className="w-full text-sm text-mid" role="status">{msg}</p>}
    </div>
  );
}
