import { describe, expect, it } from "vitest";
import { picksFor } from "@/lib/picks";

describe("picksFor", () => {
  const p = {
    matchId: "m", modelVersion: "v", generatedAt: 1,
    outcome: { home: 0.81, draw: 0.12, away: 0.07 },
    markets: [
      { key: "over_2_5", label: "Más de 2.5 goles", p: 0.2 },
      { key: "btts_yes", label: "Ambos marcan", p: 0.6 },
      { key: "dc_1x", label: "Doble oportunidad 1X", p: 0.93 },
    ],
    features: [], players: [], edges: [], lines: [],
  } as never;
  it("keeps only ≥75%, adds the opposite side of over/under, names double chance, best first", () => {
    const k = picksFor(p, "Cali", "Tolima");
    expect(k.map((x) => x.label)).toEqual(["Cali o empate", "Gana Cali", "Menos de 2.5 goles"]);
    expect(k.every((x) => x.p >= 0.75)).toBe(true);
  });
});
