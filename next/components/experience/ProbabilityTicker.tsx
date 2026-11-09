"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useFixtures } from "./useFixtures";

export type Fixture = {
  id: string;
  sport: string;
  league: string;
  home: string;
  away: string;
  kickoffAt: number;
  state: "pre" | "in" | "post";
  outcomes: 2 | 3;
};

const timeFmt = new Intl.DateTimeFormat("es-CO", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "America/Bogota" });

const ymdFmt = new Intl.DateTimeFormat("en-CA", { timeZone: "America/Bogota" });
export function dayTag(ms: number) {
  return ymdFmt.format(ms) === ymdFmt.format(Date.now()) ? "" : "MAÑ ";
}

function when(f: Fixture) {
  if (f.state === "in") return <span className="text-up">EN VIVO</span>;
  return <span className="text-lo">{dayTag(f.kickoffAt)}{timeFmt.format(f.kickoffAt)}</span>;
}

/** Fill the track so a short match day still loops seamlessly. */
function pad(items: Fixture[], min = 8): Fixture[] {
  if (!items.length) return items;
  const out = [...items];
  while (out.length < min) out.push(...items);
  return out;
}

function Row({ items, reverse, dur, scramble }: { items: Fixture[]; reverse?: boolean; dur: string; scramble: string | null }) {
  const doubled = [...items, ...items];
  return (
    <div className="ticker overflow-hidden py-3">
      <ul className="ticker-track" data-reverse={reverse ? "" : undefined} style={{ ["--ticker-dur" as string]: dur }}>
        {doubled.map((m, i) => {
          const hot = scramble === m.id;
          return (
            <li key={i} className={`flex items-center gap-4 num text-sm whitespace-nowrap ${hot ? "tick-lit" : ""}`} aria-hidden={i >= items.length}>
              <span className="text-[10px] tracking-[0.2em] text-lo border border-line rounded px-1.5 py-0.5">{m.sport}</span>
              <span className="text-[11px]">{when(m)}</span>
              <span className="text-hi">{m.home}</span>
              <span className="flex gap-2" aria-label="Probabilidad oculta">
                {Array.from({ length: m.outcomes }, (_, j) => (
                  <span key={j} className="tick-q">{hot ? <Scramble seed={i * 7 + j} /> : "???"}</span>
                ))}
              </span>
              <span className="text-hi">{m.away}</span>
              <span className="text-line">/</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

/** Digits flicker for a moment, as if the model were recalculating, then fall back to "??". */
function Scramble({ seed }: { seed: number }) {
  const [v, setV] = useState("??");
  useEffect(() => {
    let n = seed;
    const id = setInterval(() => {
      n = (n * 9301 + 49297) % 233280;
      setV(String(10 + (n % 80)));
    }, 70);
    return () => clearInterval(id);
  }, [seed]);
  return <>{v}</>;
}

export function ProbabilityTicker() {
  const fixtures = useFixtures();
  const [scramble, setScramble] = useState<string | null>(null);

  useEffect(() => {
    if (!fixtures?.length || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const id = setInterval(() => {
      setScramble(fixtures[Math.floor(Math.random() * fixtures.length)].id);
      setTimeout(() => setScramble(null), 650);
    }, 1600);
    return () => clearInterval(id);
  }, [fixtures]);

  if (fixtures && !fixtures.length) return null;

  const a = pad((fixtures ?? []).filter((_, i) => i % 2 === 0));
  const b = pad((fixtures ?? []).filter((_, i) => i % 2 === 1).concat(fixtures && fixtures.length < 2 ? fixtures : []));

  return (
    <section aria-label="Próximos partidos" className="relative border-y border-line bg-[var(--bg-raise)]/60 py-2 my-10">
      <div className="px-5 sm:px-6 pt-2 flex flex-wrap items-center justify-between gap-2 num text-[10px] tracking-[0.2em] uppercase text-lo">
        <span className="flex items-center gap-2">
          <span className="live-dot" aria-hidden /> Próximos partidos
          {fixtures && <span className="text-mid">· {fixtures.length}</span>}
        </span>
        <span className="hidden sm:inline">Hora Colombia</span>
      </div>
      {fixtures ? (
        <>
          <Row items={a} dur={`${Math.max(40, a.length * 6)}s`} scramble={scramble} />
          <Row items={b} dur={`${Math.max(50, b.length * 7)}s`} reverse scramble={scramble} />
        </>
      ) : (
        <div className="px-5 sm:px-6 py-6 space-y-4" aria-hidden>
          <div className="h-4 w-3/4 rounded bg-[var(--seg-3)] animate-pulse" />
          <div className="h-4 w-2/3 rounded bg-[var(--seg-3)] animate-pulse" />
        </div>
      )}
      <p className="px-5 sm:px-6 pb-2 text-[11px] num tracking-[0.12em] uppercase text-lo">
        ??? = probabilidad del modelo.{" "}
        <Link href="/acceso" className="text-gold hover:underline underline-offset-4">Entra gratis para ver las de los partidos que cubrimos →</Link>
      </p>
    </section>
  );
}
