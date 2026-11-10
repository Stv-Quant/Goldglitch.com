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

describe("picksFor with SQPC picks", () => {
  it("uses SQPC's own selections when the batch carries them", () => {
    const p = {
      matchId: "m", modelVersion: "v", generatedAt: 1, outcome: { home: 0.5, draw: 0.3, away: 0.2 },
      markets: [], features: [], players: [], edges: [], lines: [],
      picks: [
        { group: "Goles", market: "Total de goles", selection: "Menos de 3.5", p: 0.88 },
        { group: "Jugadores", market: "Remates de X", selection: "Más de 0.5", p: 0.7 },
      ],
    } as never;
    const k = picksFor(p, "A", "B");
    expect(k).toHaveLength(1);
    expect(k[0]).toMatchObject({ label: "Total de goles: Menos de 3.5", source: "Goles" });
  });
});
