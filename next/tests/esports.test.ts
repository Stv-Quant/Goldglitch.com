import { describe, expect, it } from "vitest";
import { ingestBatchSchema, predictionSchema } from "@/lib/contracts";
import { redactPrediction } from "@/lib/entitlements";
import { acceptedSports, filterBySport } from "@/lib/schema";

const OLD_DDL = `CREATE TABLE matches (
  id             TEXT PRIMARY KEY,
  sport          TEXT NOT NULL CHECK (sport IN ('football','baseball','basketball','hockey')),
  competition_id TEXT NOT NULL REFERENCES competitions(id))`;
const fakeDb = (sql: string | null) =>
  ({ prepare: () => ({ first: async () => (sql === null ? null : { sql }) }) }) as never;

const batch = () =>
  ingestBatchSchema.parse({
    batchId: "b1", source: "sqpc",
    competitions: [{ id: "football-e0", sport: "football", name: "Premier League" }, { id: "esports-valorant", sport: "esports", name: "Valorant" }],
    teams: [
      { id: "football-a", sport: "football", name: "A" }, { id: "football-b", sport: "football", name: "B" },
      { id: "esports-x", sport: "esports", name: "X" }, { id: "esports-y", sport: "esports", name: "Y" },
    ],
    matches: [
      { id: "m1", sport: "football", competitionId: "football-e0", homeTeamId: "football-a", awayTeamId: "football-b", kickoffAt: 2e12, status: "scheduled" },
      { id: "es-vlr1", sport: "esports", competitionId: "esports-valorant", homeTeamId: "esports-x", awayTeamId: "esports-y", kickoffAt: 2e12, status: "scheduled" },
    ],
    predictions: [
      { matchId: "m1", modelVersion: "sqpc-football", generatedAt: 1e12, outcome: { home: 0.5, draw: 0.3, away: 0.2 } },
      { matchId: "es-vlr1", modelVersion: "sqpc-esports", generatedAt: 1e12, outcome: { home: 0.6, draw: null, away: 0.4 } },
    ],
  });

describe("sport acceptance guard", () => {
  it("reads the CHECK list from the live schema", async () => {
    expect([...(await acceptedSports(fakeDb(OLD_DDL)))!]).toEqual(["football", "baseball", "basketball", "hockey"]);
    expect((await acceptedSports(fakeDb(OLD_DDL.replace("'hockey'", "'hockey','esports'"))))!.has("esports")).toBe(true);
    expect(await acceptedSports(fakeDb(null))).toBeNull();
  });

  it("drops e-sports rows until migration 0009 runs, keeping everything else", async () => {
    const ok = await acceptedSports(fakeDb(OLD_DDL));
    const { batch: b, skipped } = filterBySport(batch(), ok);
    expect(b.matches.map((m) => m.id)).toEqual(["m1"]);
    expect(b.predictions.map((p) => p.matchId)).toEqual(["m1"]);
    expect(b.competitions.map((c) => c.id)).toEqual(["football-e0"]);
    expect(b.teams).toHaveLength(2);
    expect(skipped).toEqual({ esports: 1 });
  });

  it("passes everything through when the schema accepts e-sports (or is unknown)", async () => {
    const ok = await acceptedSports(fakeDb(OLD_DDL.replace("'hockey'", "'hockey','esports'")));
    expect(filterBySport(batch(), ok).batch.matches).toHaveLength(2);
    expect(filterBySport(batch(), null).batch.matches).toHaveLength(2);
  });
});

describe("stakes block", () => {
  const side = { team: "A", pos: 3, pts: 20, gp: 10, gd: 6, pTop: 0.2, pZone: 0.7, pReleg: 0, levTop: 0.08, levZone: 0.15, levDown: 0, dead: false, need: "Champions (70%)" };
  const pred = predictionSchema.parse({
    matchId: "m1", modelVersion: "sqpc-football", generatedAt: 1, outcome: { home: 0.5, draw: 0.3, away: 0.2 },
    stakes: {
      format: { teams: 20, games: 38, top: 1, zone: 4, releg: 3, topLabel: "Título", zoneLabel: "Champions" }, progress: 0.26,
      home: side, away: { ...side, team: "B", pos: 18, pReleg: 0.5, levDown: 0.2, need: "Evitar el descenso (50% de riesgo)" },
      mood: { home: { form: 0.4, slump: false, last: "GGEPG" } }, effect: { home: 0.98, away: 1.04, applied: true },
    },
  });

  it("is Pro content: free viewers only learn that it exists", () => {
    const free = redactPrediction(pred, "free");
    expect(free.stakes).toBeUndefined();
    expect(free.stakesLocked).toBe(true);
    const pro = redactPrediction(pred, "pro");
    expect(pro.stakes?.away?.need).toContain("descenso");
    expect(pro.stakesLocked).toBe(false);
  });

  it("rejects out-of-range values", () => {
    expect(predictionSchema.safeParse({ ...pred, stakes: { home: { ...side, pTop: 1.4 } } }).success).toBe(false);
  });
});
