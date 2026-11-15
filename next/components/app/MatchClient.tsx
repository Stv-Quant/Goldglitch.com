"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { MatchView as MatchData } from "@/lib/data";
import type { Sport } from "@/lib/sports";
import { MatchView } from "./MatchView";

type State = { kind: "loading" } | { kind: "error" } | { kind: "missing" } | { kind: "ok"; m: MatchData | { locked: true; sport: Sport } };

export function MatchClient({ id }: { id: string }) {
  const [s, setS] = useState<State>({ kind: "loading" });
  useEffect(() => {
    let alive = true;
    fetch(`/api/app/match/${encodeURIComponent(id)}`, { cache: "no-store" })
      .then(async (r) => {
        if (r.status === 401) { location.href = "/acceso"; return; }
        if (r.status === 404) { if (alive) setS({ kind: "missing" }); return; }
        if (!r.ok) throw new Error(String(r.status));
        const m = await r.json();
        if (alive) setS({ kind: "ok", m });
      })
      .catch(() => alive && setS({ kind: "error" }));
    return () => { alive = false; };
  }, [id]);

  if (s.kind === "ok") return <MatchView m={s.m} />;
  return (
    <div className="space-y-6">
      <Link href="/app" className="text-sm text-lo hover:text-hi">← Partidos</Link>
      {s.kind === "loading" && (
        <div className="glass animate-pulse p-7" aria-hidden>
          <div className="h-3 w-1/4 rounded bg-[var(--seg-3)]" />
          <div className="mt-6 h-7 w-2/3 rounded bg-[var(--seg-3)]" />
          <div className="mt-8 h-3 w-full rounded bg-[var(--seg-3)]" />
        </div>
      )}
      {s.kind === "missing" && <div className="card p-8 text-mid">No encontramos ese partido.</div>}
      {s.kind === "error" && (
        <div className="card p-6 text-sm text-mid">
          No pudimos cargar el partido. <button type="button" className="text-gold underline" onClick={() => location.reload()}>Reintentar</button>
        </div>
      )}
    </div>
  );
}
