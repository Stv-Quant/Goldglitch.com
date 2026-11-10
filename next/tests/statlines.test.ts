import { describe, expect, it } from "vitest";
import { defaultLine } from "@/components/stats/StatLines";

function poisson(mean: number, n = 15) {
  const pmf: number[] = [];
  let p = Math.exp(-mean);
  for (let k = 0; k < n; k++) { pmf.push(p); p = (p * mean) / (k + 1); }
  return { key: "g", label: "Goles", group: "Goles", mean, start: 0, pmf };
}

describe("defaultLine", () => {
  it("picks the least extreme line whose favourite side is ≥65%", () => {
    // Poisson(2.1): Menos de 3.5 = 84% is the smallest favourite ≥ 65% (Menos de 2.5 = 65.0%? no: 64.96%)
    expect(defaultLine(poisson(2.1))).toBe(3.5);
  });
  it("never offers a line outside the distribution", () => {
    const l = poisson(9, 30);
    const d = defaultLine(l);
    expect(d).toBeGreaterThanOrEqual(0.5);
    expect(d).toBeLessThan(l.pmf.length);
  });
});
