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
  /** Prices in COP cents (Wompi amount_in_cents).  */
  price: Record<BillingPeriod, number>;
  features: string[];
};

export const CURRENCY = "COP";

export const PLANS: Record<Tier, PlanDef> = {
  free: {
    name: "Free",
    tagline: "Los datos, sin humo. Solo necesitas una cuenta.",
    price: { monthly: 0, annual: 0 },
    features: [
      "Cuenta gratis, siempre",
      "Calendario y resultados de las ligas cubiertas",
      "Probabilidades 1X2 de fútbol",
      "Comparativa y forma de los equipos",
      "Historial público de aciertos",
    ],
  },
  pro: {
    name: "Pro",
    tagline: "Todas las estadísticas, partido a partido.",
    price: { monthly: 50_000_00, annual: 500_000_00 },
    features: [
      "Todo lo de Free",
      "Fútbol, béisbol, baloncesto, hockey y NFL",
      "Picks del modelo con 75% o más",
      "Todas las líneas: goles, córners, tarjetas, remates y jugadores",
      "xG, marcadores más probables y portería a cero",
      "Mercados completos con su rango de incertidumbre",
    ],
  },
  elite: {
    name: "Elite",
    tagline: "Todo Pro, más funciones exclusivas.",
    price: { monthly: 250_000_00, annual: 2_500_000_00 },
    features: [
      "Todo lo de Pro",
      "Funciones exclusivas de Elite (se anuncian pronto)",
      "Acceso anticipado a cada novedad",
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
