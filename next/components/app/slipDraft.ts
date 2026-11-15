"use client";

import { useSyncExternalStore } from "react";
import { MAX_LEGS, type Leg } from "@/lib/slip";

/**
 * The combinada being built, kept in this browser until it is saved (per-viewer convenience; saved slips live in D1).
 * All components using the hook stay in sync through a window event.
 */
const KEY = "gg_slip_draft";
const EVT = "gg-slip-draft";

function read(): Leg[] {
  try {
    const v = JSON.parse(localStorage.getItem(KEY) ?? "[]");
    return Array.isArray(v) ? (v as Leg[]).filter((l) => l.kickoffAt > Date.now()) : [];
  } catch {
    return [];
  }
}

function write(legs: Leg[]) {
  try { localStorage.setItem(KEY, JSON.stringify(legs)); } catch { /* storage unavailable: keep it in memory only */ }
  window.dispatchEvent(new CustomEvent(EVT, { detail: legs }));
}

export const legKey = (l: Pick<Leg, "matchId" | "label">) => `${l.matchId}\u0000${l.label}`;

let cache: { raw: string | null; legs: Leg[] } = { raw: null, legs: [] };
const EMPTY: Leg[] = [];
function snapshot(): Leg[] {
  let raw: string | null = null;
  try { raw = localStorage.getItem(KEY); } catch { /* unavailable */ }
  if (raw !== cache.raw) cache = { raw, legs: read() };
  return cache.legs;
}
function subscribe(cb: () => void) {
  window.addEventListener(EVT, cb);
  window.addEventListener("storage", cb);
  return () => { window.removeEventListener(EVT, cb); window.removeEventListener("storage", cb); };
}

export function useSlipDraft() {
  const legs = useSyncExternalStore(subscribe, snapshot, () => EMPTY);
  const set = (next: Leg[]) => write(next);
  return {
    legs,
    has: (l: Pick<Leg, "matchId" | "label">) => legs.some((x) => legKey(x) === legKey(l)),
    toggle: (l: Leg) => {
      const cur = read();
      set(cur.some((x) => legKey(x) === legKey(l)) ? cur.filter((x) => legKey(x) !== legKey(l)) : cur.length >= MAX_LEGS ? cur : [...cur, l]);
    },
    remove: (l: Leg) => set(read().filter((x) => legKey(x) !== legKey(l))),
    clear: () => set([]),
    full: legs.length >= MAX_LEGS,
  };
}
