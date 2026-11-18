"use client";

import { useEffect, useState } from "react";
import type { Fixture } from "./fixture";

export type Sample = {
  matchId: string; league: string; home: string; away: string; homeLogo?: string; awayLogo?: string;
  kickoffAt: number; p: { home: number; draw: number; away: number }; picks: number;
};
export type RecordSummary = { settled: number; won: number; expected: number | null; pending: number; matches: number };
export type Today = { fixtures: Fixture[]; sample: Sample | null; record: RecordSummary | null };

let inflight: Promise<Today> | null = null;

/** One request per page load, shared by every component that shows upcoming fixtures. */
function load(): Promise<Today> {
  inflight ??= fetch("/api/today")
    .then((r) => (r.ok ? r.json() : {}))
    .then((d: Partial<Today>) => ({ fixtures: d.fixtures ?? [], sample: d.sample ?? null, record: d.record ?? null }))
    .catch(() => ({ fixtures: [], sample: null, record: null }));
  return inflight;
}

/** null while loading. */
export function useToday(): Today | null {
  const [t, setT] = useState<Today | null>(null);
  useEffect(() => {
    let alive = true;
    load().then((x) => alive && setT(x));
    return () => { alive = false; };
  }, []);
  return t;
}

/** null while loading, [] when there is nothing scheduled. */
export function useFixtures(): Fixture[] | null {
  return useToday()?.fixtures ?? null;
}
