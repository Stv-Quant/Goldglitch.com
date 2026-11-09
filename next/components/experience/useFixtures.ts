"use client";

import { useEffect, useState } from "react";
import type { Fixture } from "./fixture";

let inflight: Promise<Fixture[]> | null = null;

/** One request per page load, shared by every component that shows upcoming fixtures. */
function load(): Promise<Fixture[]> {
  inflight ??= fetch("/api/today")
    .then((r) => (r.ok ? r.json() : { fixtures: [] }))
    .then((d: { fixtures?: Fixture[] }) => d.fixtures ?? [])
    .catch(() => []);
  return inflight;
}

/** null while loading, [] when there is nothing scheduled. */
export function useFixtures(): Fixture[] | null {
  const [f, setF] = useState<Fixture[] | null>(null);
  useEffect(() => {
    let alive = true;
    load().then((x) => alive && setF(x));
    return () => { alive = false; };
  }, []);
  return f;
}
