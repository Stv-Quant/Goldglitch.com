import { describe, expect, it } from "vitest";
import { ingestBatchSchema } from "@/lib/contracts";
import { bandOf, summarize, type TrackedRow } from "@/lib/tracked";

const row = (over: Partial<TrackedRow>): TrackedRow => ({
  id: Math.random().toString(36), kind: "featured", sport: "football", competition: "LaLiga", home: "A", away: "B",
  kickoffAt: 1_800_000_000_000, group: "Goles", label: "Más de 1.5", p: 0.85, price: null, ev: null,
  status: "won", result: "2-1", profit: null, ...over,
});

describe("tracked picks summary", () => {
  it("counts only won/lost toward the hit rate and compares it with the promised probability", () => {
    const rows = [
      row({ p: 0.9 }), row({ p: 0.8, status: "lost" }), row({ p: 0.95 }), row({ status: "void" }), row({ status: "pending" }),
      row({ kind: "value", p: 0.45, price: 2.4, profit: 1.4 }), row({ kind: "value", p: 0.4, price: 2.6, status: "lost", profit: -1 }),
    ];
    const f = summarize(rows, "featured");
    expect(f.settled).toBe(3);
    expect(f.won).toBe(2);
    expect(f.void).toBe(1);
    expect(f.pending).toBe(1);
    expect(f.hitRate).toBeCloseTo(2 / 3);
    expect(f.expected).toBeCloseTo((0.9 + 0.8 + 0.95) / 3);
    expect(f.curve.at(-1)!.diff).toBeCloseTo(2 - (0.9 + 0.8 + 0.95));
    const v = summarize(rows, "value");
    expect(v.profit).toBeCloseTo(0.4);
    expect(v.roi).toBeCloseTo(0.2);
  });
  it("bands", () => {
    expect([0.76, 0.8, 0.86, 0.91, 0.97].map(bandOf)).toEqual(["75–80%", "80–85%", "85–90%", "90–95%", "95%+"]);
  });
  it("batch accepts tracked picks and rejects bad status", () => {
    const base = { batchId: "b1", source: "sqpc" };
    const pick = { id: "tp-1", kind: "featured", sport: "football", competitionId: "football-sp1", matchId: "espn-1", home: "A", away: "B",
      kickoffAt: 1_800_000_000_000, group: "Goles", label: "Más de 1.5", p: 0.85, status: "pending", pickedAt: 1_799_000_000_000 };
    expect(ingestBatchSchema.parse({ ...base, trackedPicks: [pick] }).trackedPicks).toHaveLength(1);
    expect(ingestBatchSchema.safeParse({ ...base, trackedPicks: [{ ...pick, status: "maybe" }] }).success).toBe(false);
    expect(ingestBatchSchema.parse(base).trackedPicks).toEqual([]);
  });
});
