"use client";

import { useEffect, useState } from "react";
import { findCrest } from "@/lib/crests";

/** Team crest; monogram when there is no crest or the image fails. */
export function Crest({ src, name, size = 24, className = "" }: { src?: string; name: string; size?: number; className?: string }) {
  const [broken, setBroken] = useState(false);
  const initials = name.replace(/[^\p{L}\p{N} ]/gu, "").split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase() || "?";
  return (
    <span className={`inline-grid shrink-0 place-items-center overflow-hidden rounded-full ${src && !broken ? "" : "border border-line bg-[rgba(237,230,214,0.04)]"} ${className}`}
      style={{ width: size, height: size }} aria-hidden>
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

const memo = new Map<string, Promise<Record<string, string>>>();
function load(comp: string) {
  let p = memo.get(comp);
  if (!p) {
    p = fetch(`/api/crests?c=${encodeURIComponent(comp)}`).then((r) => (r.ok ? r.json() : { teams: {} })).then((d) => d.teams ?? {}).catch(() => ({}));
    memo.set(comp, p);
  }
  return p;
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
  return (comp: string, team: string) => (maps[comp] ? findCrest(maps[comp], team) : undefined);
}
