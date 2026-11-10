export type Tier = "free" | "pro" | "elite";
export type PaidPlan = Exclude<Tier, "free">;
export type BillingPeriod = "monthly" | "annual";

export const TIER_RANK: Record<Tier, number> = { free: 0, pro: 1, elite: 2 };

export function hasTier(current: Tier, required: Tier): boolean {
  return TIER_RANK[current] >= TIER_RANK[required];
}

type PlanDef = {
  name: string;
  tagline: string;
  /** Prices in COP cents (Wompi amount_in_cents). Placeholders — adjust before launch. */
  price: Record<BillingPeriod, number>;
  features: string[];
};

export const CURRENCY = "COP";

export const PLANS: Record<Tier, PlanDef> = {
  free: {
    name: "Free",
    tagline: "Los datos, sin humo.",
    price: { monthly: 0, annual: 0 },
    features: [
      "Calendario y resultados de las ligas cubiertas",
      "Probabilidades 1X2 del modelo",
      "Forma reciente y estadísticas descriptivas",
      "Historial público de aciertos y calibración",
    ],
  },
  pro: {
    name: "Pro",
    tagline: "El modelo completo, partido a partido.",
    price: { monthly: 39_900_00, annual: 399_000_00 },
    features: [
      "Todo lo de Free",
      "Rango de incertidumbre de cada probabilidad",
      "Goles esperados (xG) y matriz de marcadores",
      "Mercados: más/menos de 2.5, ambos marcan",
      "Desglose por jugador",
    ],
  },
  elite: {
    name: "Elite",
    tagline: "Modelo contra mercado.",
    price: { monthly: 89_900_00, annual: 899_000_00 },
    features: [
      "Todo lo de Pro",
      "Valor esperado (EV) frente a cuotas de casas",
      "Béisbol, baloncesto y hockey: modelo completo",
      "Alertas cuando el modelo y el mercado divergen",
    ],
  },
};

export const PERIOD_DAYS: Record<BillingPeriod, number> = { monthly: 30, annual: 365 };

export function formatCOP(cents: number): string {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(cents / 100);
}
