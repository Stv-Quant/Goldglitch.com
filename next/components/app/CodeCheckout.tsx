"use client";

import { useState } from "react";

const ERRORS: Record<string, string> = {
  billing_not_configured: "Los pagos aún no están habilitados.",
  code_used: "Este código ya fue usado.",
  invalid_code: "Código no válido.",
};

export function CodeCheckout({ code }: { code: string }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function pay() {
    setBusy(true);
    setError(null);
    const r = await fetch("/api/billing/code", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ code }),
    }).catch(() => null);
    const j = await r?.json().catch(() => null);
    if (j?.ok && typeof j.url === "string") {
      window.location.assign(j.url);
      return;
    }
    setError(ERRORS[j?.error] ?? "No pudimos abrir el pago. Intenta de nuevo.");
    setBusy(false);
  }

  return (
    <>
      <button onClick={pay} disabled={busy}
        className="btn-gold mt-6 w-full px-4 py-3 text-sm">
        {busy ? "Abriendo Wompi…" : "Pagar con Wompi"}
      </button>
      {error && <p role="alert" className="mt-4 text-sm" style={{ color: "var(--neon-down)" }}>{error}</p>}
    </>
  );
}
