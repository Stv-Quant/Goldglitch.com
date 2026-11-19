"use client";

import { useEffect, useState } from "react";
import { findCrest, teamKey } from "@/lib/crests";

/** Team crest; monogram when there is no crest or the image fails. */
export function Crest({ src, name, size = 24, className = "", fluid = false, sport }: {
  src?: string | null; name: string; size?: number; className?: string; fluid?: boolean;
  /** When set and `src` is null (looked up, not found), ask the fallback source. */
  sport?: string;
}) {
  const [broken, setBroken] = useState(false);
  const [alt, setAlt] = useState<string | undefined>();
  useEffect(() => {
    if (src !== null || !sport) return;
    let alive = true;
    fallback(name, sport).then((f) => alive && f.logo && setAlt(f.logo));
    return () => { alive = false; };
  }, [src, sport, name]);
  src = src ?? alt;
  const initials = name.replace(/[^\p{L}\p{N} ]/gu, "").split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase() || "?";
  return (
    <span className={`inline-grid shrink-0 place-items-center overflow-hidden rounded-full ${src && !broken ? "" : "border border-line bg-[rgba(237,230,214,0.04)]"} ${className}`}
      style={fluid ? undefined : { width: size, height: size }} aria-hidden>
      {src && !broken ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={src} alt="" width={size} height={size} loading="lazy" decoding="async" referrerPolicy="no-referrer"
          onError={() => setBroken(true)} className="h-full w-full object-contain" />
      ) : (
        <span className="num font-semibold text-gold-dim" style={{ fontSize: Math.max(8, size * 0.36) }}>{initials}</span>
      )}
    </span>
  );
}

const fb = new Map<string, Promise<{ logo?: string; color?: string }>>();
const TSDB_SPORT: Record<string, string[]> = {
  football: ["Soccer"], baseball: ["Baseball"], basketball: ["Basketball"], hockey: ["Ice Hockey"], esports: ["ESports"],
};

/** TheSportsDB straight from the browser (CORS open; its free key limits per IP, so it cannot run on shared Workers IPs). */
async function tsdb(name: string, sport: string): Promise<{ logo?: string; color?: string }> {
  const lsKey = `gg:crest:${sport}:${teamKey(name)}`;
  try {
    const c = localStorage.getItem(lsKey);
    if (c) { const v = JSON.parse(c); if (v.t > Date.now() - (v.logo ? 30 : 1) * 86_400_000) return v; }
  } catch { /* storage unavailable */ }
  const r = await fetch(`https://www.thesportsdb.com/api/v1/json/123/searchteams.php?t=${encodeURIComponent(name)}`);
  if (!r.ok) return {};
  const d = (await r.json()) as { teams?: { strTeam?: string; strTeamAlternate?: string; strSport?: string; strBadge?: string }[] | null };
  const want = teamKey(name), sports = TSDB_SPORT[sport] ?? [];
  const ok = (d.teams ?? []).filter((t) => t.strBadge && sports.includes(t.strSport ?? ""));
  const hit = ok.find((t) => [t.strTeam, ...(t.strTeamAlternate ?? "").split(",")].some((n) => n && teamKey(n) === want))
    ?? ok.find((t) => { const k = teamKey(t.strTeam ?? ""); return k.length >= 4 && (k.includes(want) || want.includes(k)); });
  const v = { logo: hit?.strBadge ? `${hit.strBadge}/small` : undefined, t: Date.now() };
  try { localStorage.setItem(lsKey, JSON.stringify(v)); } catch { /* ignore */ }
  return v;
}

/** Server fallback (ESPN team search), then TheSportsDB from the browser. */
export function fallback(name: string, sport: string) {
  const k = `${sport}:${name}`;
  let p = fb.get(k);
  if (!p) {
    p = fetch(`/api/crest?n=${encodeURIComponent(name)}&s=${sport}`).then((r) => (r.ok ? r.json() : {})).catch(() => ({}))
      .then((v: { logo?: string }) => (v.logo ? v : tsdb(name, sport).catch(() => ({}))));
    fb.set(k, p);
  }
  return p;
}

type Maps = { teams: Record<string, string>; colors: Record<string, string> };
const memo = new Map<string, Promise<Maps>>();
function loadAll(comp: string) {
  let p = memo.get(comp);
  if (!p) {
    p = fetch(`/api/crests?c=${encodeURIComponent(comp)}`).then((r) => (r.ok ? r.json() : {}))
      .then((d: Partial<Maps>) => ({ teams: d.teams ?? {}, colors: d.colors ?? {} })).catch(() => ({ teams: {}, colors: {} }));
    memo.set(comp, p);
  }
  return p;
}
const load = (comp: string) => loadAll(comp).then((m) => m.teams);

/** Crest and brand colour of both teams of one match (colour only when it reads on a dark page). */
export function useMatchBrand(comp: string, home: string, away: string, sport?: string) {
  const [maps, setMaps] = useState<Maps | null>(null);
  useEffect(() => {
    let alive = true;
    loadAll(comp).then((m) => alive && setMaps(m));
    return () => { alive = false; };
  }, [comp]);
  const [extra, setExtra] = useState<Record<string, { logo?: string; color?: string }>>({});
  const side = (name: string) => {
    if (!maps) return { logo: undefined, color: undefined };
    const logo = findCrest(maps.teams, name);
    if (!logo) return extra[name] ?? { logo: undefined, color: undefined };
    const color = Object.entries(maps.teams).find(([k, u]) => u === logo && maps.colors[k])?.[0];
    return { logo, color: color ? maps.colors[color] : undefined };
  };
  useEffect(() => {
    if (!maps || !sport) return;
    let alive = true;
    for (const n of [home, away]) if (!findCrest(maps.teams, n)) fallback(n, sport).then((f) => alive && setExtra((e) => ({ ...e, [n]: f })));
    return () => { alive = false; };
  }, [maps, home, away, sport]);
  return { ready: !!maps, home: side(home), away: side(away) };
}

/** Crest maps for the competitions on screen; returns a lookup (competition, team name) → url. */
export function useCrests(comps: string[]) {
  const [maps, setMaps] = useState<Record<string, Record<string, string>>>({});
  const key = [...new Set(comps)].sort().join(",");
  useEffect(() => {
    let alive = true;
    for (const c of key ? key.split(",") : []) load(c).then((m) => alive && setMaps((s) => (s[c] ? s : { ...s, [c]: m })));
    return () => { alive = false; };
  }, [key]);
  return (comp: string, team: string): string | null | undefined => (maps[comp] ? findCrest(maps[comp], team) ?? null : undefined);
}
