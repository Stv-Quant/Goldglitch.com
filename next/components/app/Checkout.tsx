"use client";

import { useState } from "react";
import { PlanCards } from "@/components/site/PlanCards";
import type { BillingPeriod, Tier } from "@/lib/plans";

export function Checkout({ currentTier }: { currentTier: Tier }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function choose(plan: "pro" | "elite", period: BillingPeriod) {
    setBusy(true);
    setError(null);
    const r = await fetch("/api/billing/checkout", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ plan, period }),
    }).catch(() => null);
    const j = await r?.json().catch(() => null);
    if (j?.ok && typeof j.url === "string") {
      window.location.assign(j.url);
      return;
    }
    setError(j?.error === "billing_not_configured" ? "Los pagos aún no están habilitados." : "No pudimos abrir el pago. Intenta de nuevo.");
    setBusy(false);
  }

  return (
    <>
      <PlanCards currentTier={currentTier} onChoose={choose} busy={busy} />
      {error && <p role="alert" className="mt-4 text-sm" style={{ color: "var(--neon-down)" }}>{error}</p>}
    </>
  );
}
