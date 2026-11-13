/**
 * One colour scale for every probability in the app, so a glance tells how likely something is.
 * Cold (grey/copper) for unlikely, gold for likely, neon for the model's strongest calls.
 */
export const PROB_STEPS = [
  { min: 0.85, color: "var(--p6)", label: "85%+" , name: "Máxima" },
  { min: 0.75, color: "var(--p5)", label: "75–84%", name: "Muy alta" },
  { min: 0.65, color: "var(--p4)", label: "65–74%", name: "Alta" },
  { min: 0.55, color: "var(--p3)", label: "55–64%", name: "Media" },
  { min: 0.4, color: "var(--p2)", label: "40–54%", name: "Pareja" },
  { min: 0, color: "var(--p1)", label: "<40%", name: "Baja" },
] as const;

export type ProbStep = (typeof PROB_STEPS)[number];

export function probStep(p: number): ProbStep {
  return PROB_STEPS.find((s) => p >= s.min) ?? PROB_STEPS[PROB_STEPS.length - 1];
}

export const probColor = (p: number) => probStep(p).color;

/** ≥75%: the model's strong calls get a soft glow. */
export const isHot = (p: number) => p >= 0.75;
