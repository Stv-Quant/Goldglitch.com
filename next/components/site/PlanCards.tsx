"use client";

import { useState } from "react";
import { PLANS, formatCOP, type BillingPeriod, type Tier } from "@/lib/plans";

const ORDER: Tier[] = ["free", "pro", "elite"];

/**
 * Plan grid. With `onChoose`, paid cards become checkout buttons (account page);
 * otherwise they link to sign-in (marketing pages).
 */
export function PlanCards({
  currentTier,
  onChoose,
  busy,
}: {
  currentTier?: Tier;
  onChoose?: (plan: "pro" | "elite", period: BillingPeriod) => void;
  busy?: boolean;
}) {
  const [period, setPeriod] = useState<BillingPeriod>("monthly");

  return (
    <div>
      <div role="radiogroup" aria-label="Periodo de facturación" className="inline-flex rounded-xl border border-line p-1 text-sm">
        {(["monthly", "annual"] as const).map((p) => (
          <button
            key={p}
            role="radio"
            aria-checked={period === p}
            onClick={() => setPeriod(p)}
            className={`px-4 py-1.5 rounded-lg transition-colors ${period === p ? "bg-[var(--gold-faint)] text-hi" : "text-lo hover:text-hi"}`}
          >
            {p === "monthly" ? "Mensual" : "Anual · 2 meses gratis"}
          </button>
        ))}
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-3">
        {ORDER.map((t) => {
          const plan = PLANS[t];
          const featured = t === "pro";
          const isCurrent = currentTier === t;
          const price = plan.price[period];
          return (
            <article
              key={t}
              className={`relative p-6 flex flex-col ${featured ? "glass" : "card"}`}
              style={featured ? { borderColor: "var(--border-glass)" } : undefined}
            >
              {featured && <span className="absolute -top-2.5 left-6 eyebrow bg-void px-2" style={{ color: "var(--gold)" }}>Recomendado</span>}
              <h3 className="text-lg font-semibold">{plan.name}</h3>
              <p className="text-sm text-lo mt-1">{plan.tagline}</p>
              <p className="mt-5">
                <span className="num text-3xl font-semibold">{price === 0 ? "$0" : formatCOP(price)}</span>
                {price > 0 && <span className="text-sm text-lo"> / {period === "monthly" ? "mes" : "año"}</span>}
              </p>
              <ul className="mt-5 space-y-2 text-sm text-mid flex-1">
                {plan.features.map((f) => (
                  <li key={f} className="flex gap-2">
                    <span aria-hidden className="text-gold">·</span>
                    {f}
                  </li>
                ))}
              </ul>
              <div className="mt-6">
                {isCurrent ? (
                  <span className="block text-center text-sm text-lo py-2.5 border border-line rounded-[10px]">Tu plan actual</span>
                ) : t === "free" ? (
                  onChoose ? null : (
                    <a href="/acceso" className="btn-ghost block text-center py-2.5 text-sm">Crear cuenta gratis</a>
                  )
                ) : onChoose ? (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => onChoose(t as "pro" | "elite", period)}
                    className={`${featured ? "btn-gold" : "btn-ghost"} w-full py-2.5 text-sm disabled:opacity-50`}
                  >
                    {busy ? "Abriendo pago…" : `Activar ${plan.name}`}
                  </button>
                ) : (
                  <a href="/acceso?next=planes" className={`${featured ? "btn-gold" : "btn-ghost"} block text-center py-2.5 text-sm`}>
                    Empezar con {plan.name}
                  </a>
                )}
              </div>
            </article>
          );
        })}
      </div>
      <p className="mt-4 text-xs text-lo">
        Pagos en COP con Wompi (tarjeta, PSE, Nequi). Cada pago activa el periodo elegido; no hay cobros automáticos.
      </p>
    </div>
  );
}
