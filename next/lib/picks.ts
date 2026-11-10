import type { Prediction } from "./contracts";

export type Pick = { key: string; label: string; p: number; source: "resultado" | "mercado" };

export const PICK_MIN = 0.75;     // highlighted in each match
export const PICK_FEATURED = 0.8; // featured on the app home

const DC: Record<string, (h: string, a: string) => string> = {
  dc_1x: (h) => `${h} o empate`,
  dc_x2: (_h, a) => `Empate o ${a}`,
  dc_12: () => "No hay empate",
};

/** "Más de 2.5 goles" → "Menos de 2.5 goles" (and lowercase variants inside action labels). */
const flip = (label: string) => label.replace("Más de", "Menos de").replace("más de", "menos de");

/**
 * The model's most probable selections for a match: 1X2 outcomes, the published markets and the opposite side of
 * every over/under and "ambos marcan" market. Nothing is invented: each pick is a probability SQPC already published.
 */
export function picksFor(p: Prediction, home: string, away: string, min = PICK_MIN): Pick[] {
  const out: Pick[] = [];
  const add = (key: string, label: string, prob: number | null | undefined, source: Pick["source"]) => {
    if (typeof prob === "number" && prob >= min && prob < 0.995) out.push({ key, label, p: prob, source });
  };
  add("win_home", `Gana ${home}`, p.outcome.home, "resultado");
  add("win_away", `Gana ${away}`, p.outcome.away, "resultado");
  add("draw", "Empate", p.outcome.draw, "resultado");
  for (const m of p.markets ?? []) {
    if (m.key.startsWith("pl_") || m.key.startsWith("reg_")) {
      add(m.key, m.label, m.p, "mercado");
      continue;
    }
    add(m.key, DC[m.key]?.(home, away) ?? m.label, m.p, "mercado");
    if (m.key === "btts_yes") add("btts_no", "Ambos marcan: No", 1 - m.p, "mercado");
    else if (/(^|_)over(_|$)/.test(m.key)) add(`${m.key}_under`, flip(m.label), 1 - m.p, "mercado");
  }
  const seen = new Set<string>();
  return out
    .sort((a, b) => b.p - a.p)
    .filter((x) => (seen.has(x.label) ? false : (seen.add(x.label), true)));
}
