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
  it("keeps only ≥80%, adds the opposite side of over/under, names double chance, best first", () => {
    const k = picksFor(p, "Cali", "Tolima");
    expect(k.map((x) => x.label)).toEqual(["Cali o empate", "Gana Cali", "Menos de 2.5 goles"]);
    expect(k.every((x) => x.p >= 0.8)).toBe(true);
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

import { scoreSlip, slipStatus } from "@/lib/slip";
import { pickLabel } from "@/lib/picks";

describe("Combinadas", () => {
  const leg = (matchId: string, p: number) => ({ matchId, sport: "football", competition: "X", home: "A", away: "B", kickoffAt: 1, label: `l${p}`, group: "Goles", p });
  it("joint probability, hits distribution and grade", () => {
    const s = scoreSlip([leg("m1", 0.9), leg("m2", 0.8)]);
    expect(s.p).toBeCloseTo(0.72);
    expect(s.hits.reduce((a, b) => a + b, 0)).toBeCloseTo(1);
    expect(s.hits[2]).toBeCloseTo(0.72);
    expect(s.weakest).toBe(1);
    expect(s.sameMatch).toBe(false);
    expect(scoreSlip([leg("m1", 0.9), leg("m1", 0.8)]).sameMatch).toBe(true);
  });
  it("slip result from legs", () => {
    expect(slipStatus(["won", "lost", "pending"])).toBe("lost");
    expect(slipStatus(["won", "pending"])).toBe("pending");
    expect(slipStatus(["won", "void"])).toBe("won");
    expect(slipStatus(["void", "void"])).toBe("void");
  });
  it("labels match SQPC's tracker", () => {
    expect(pickLabel("Total de goles", "Más de 0.5")).toBe("Total de goles: Más de 0.5");
    expect(pickLabel("Ambos marcan (60')", "Ambos marcan")).toBe("Ambos marcan (60')");
    expect(pickLabel("", "Gana A")).toBe("Gana A");
  });
});
