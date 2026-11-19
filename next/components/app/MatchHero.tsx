"use client";

import { useEffect, useState } from "react";
import { ProbLegend } from "@/components/stats/Prob";
import { ProbabilityBar } from "@/components/stats/ProbabilityBar";
import { dayLabel, timeLabel } from "@/lib/format";
import type { MatchView as MatchData } from "@/lib/data";
import { Crest, useMatchBrand } from "./Crest";
import { SportBadge, SportIcon } from "./SportBadge";

const GOLD = "#d4af37";

/**
 * Broadcast-style match header: each half lit in its club's colour, big crests, score or countdown in the middle,
 * then the 1X2 strip. Colours and crests come from /api/crests; without them it falls back to gold and monograms.
 */
export function MatchHero({ m }: { m: MatchData }) {
  const brand = useMatchBrand(m.competition.id, m.home.name, m.away.name);
  const hc = brand.home.color ?? GOLD, ac = brand.away.color ?? GOLD;
  const p = m.prediction;
  const scored = m.homeScore !== null && m.awayScore !== null;
  const live = m.status === "live", finished = m.status === "finished";
  const fav = p ? (p.outcome.home > p.outcome.away ? "home" : "away") : null;

  return (
    <header className="match-hero relative isolate overflow-hidden rounded-[22px] border border-[rgba(212,175,55,0.22)]"
      style={{ ["--hc" as string]: hc, ["--ac" as string]: ac }}>
      <div aria-hidden className="match-hero-light" />
      <span aria-hidden className="pointer-events-none absolute left-1/2 top-1/2 -z-10 -translate-x-1/2 -translate-y-1/2 text-gold opacity-[0.035]">
        <SportIcon sport={m.sport} league={m.competition.name} className="h-[26rem] w-[26rem]" />
      </span>

      <div className="relative flex flex-wrap items-center justify-between gap-2 px-5 pt-5 text-xs text-lo sm:px-8 sm:pt-7">
        <span className="flex flex-wrap items-center gap-2">
          <SportBadge sport={m.sport} league={m.competition.name} />
          <span className="text-mid">{m.competition.name}</span>
          {m.venue && <span className="hidden sm:inline">· {m.venue}</span>}
        </span>
        <span className="num">{dayLabel(m.kickoffAt)} · {timeLabel(m.kickoffAt)}</span>
      </div>

      <div className="relative grid grid-cols-[1fr_auto_1fr] items-start gap-2 px-4 pb-2 pt-8 sm:gap-6 sm:px-8 sm:pt-10">
        <Side name={m.home.name} logo={brand.home.logo} ready={brand.ready} fav={fav === "home"} color={hc} />
        <div className="flex min-w-[5.5rem] flex-col items-center pt-4 text-center sm:min-w-[9rem] sm:pt-8">
          {scored ? (
            <span className="font-display text-5xl leading-none text-hi sm:text-7xl">
              {m.homeScore}<span className="mx-2 text-lo sm:mx-3">–</span>{m.awayScore}
            </span>
          ) : (
            <span className="font-display text-3xl italic leading-none text-gold sm:text-5xl">vs</span>
          )}
          <span className="mt-3 num text-[11px] uppercase tracking-[0.18em]">
            {live ? <span className="match-live">● En vivo</span> : finished ? <span className="text-lo">Final</span> : <Countdown at={m.kickoffAt} />}
          </span>
        </div>
        <Side name={m.away.name} logo={brand.away.logo} ready={brand.ready} fav={fav === "away"} color={ac} />
      </div>

      {p ? (
        <div className="relative px-5 pb-6 pt-6 sm:px-8 sm:pb-8">
          <ProbabilityBar home={p.outcome.home} draw={p.outcome.draw} away={p.outcome.away}
            labels={{ home: m.home.short, away: m.away.short }} interval={p.interval} />
          <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-[rgba(237,230,214,0.06)] pt-4">
            <p className="num text-[11px] text-lo">
              Modelo {p.modelVersion} · actualizado {timeLabel(p.generatedAt)}
              {p.locked.pro && " · el rango de incertidumbre es parte de Pro"}
            </p>
            <ProbLegend />
          </div>
        </div>
      ) : (
        <p className="relative px-5 pb-6 pt-6 text-sm text-lo sm:px-8">El modelo aún no publica este partido.</p>
      )}
    </header>
  );
}

function Side({ name, logo, ready, fav, color }: { name: string; logo?: string; ready: boolean; fav: boolean; color: string }) {
  return (
    <div className="flex min-w-0 flex-col items-center gap-3 text-center sm:gap-4">
      <div className="match-crest relative grid place-items-center" style={{ ["--c" as string]: color }}>
        <span aria-hidden className="match-crest-halo" />
        {ready ? (
          <Crest src={logo} name={name} size={112} fluid className="match-crest-img h-16 w-16 sm:h-28 sm:w-28" />
        ) : (
          <span className="h-16 w-16 animate-pulse rounded-full bg-[rgba(237,230,214,0.05)] sm:h-28 sm:w-28" />
        )}
      </div>
      <h2 className="font-display w-full break-words text-[1.35rem] leading-[1.05] text-hi sm:text-[2.6rem]">{name}</h2>
      {fav && <span className="num rounded-full border border-[rgba(212,175,55,0.35)] px-2 py-0.5 text-[9.5px] uppercase tracking-[0.18em] text-gold">Favorito</span>}
    </div>
  );
}

function Countdown({ at }: { at: number }) {
  const [now, setNow] = useState<number | null>(null);
  useEffect(() => {
    const t = () => setNow(Date.now());
    const first = setTimeout(t, 0);
    const id = setInterval(t, 30_000);
    return () => { clearTimeout(first); clearInterval(id); };
  }, []);
  if (now === null) return <span className="text-lo">&nbsp;</span>;
  const d = at - now;
  if (d <= 0) return <span className="text-lo">Por empezar</span>;
  const days = Math.floor(d / 86_400_000), h = Math.floor((d % 86_400_000) / 3_600_000), min = Math.floor((d % 3_600_000) / 60_000);
  return <span className="text-gold">Empieza en {days ? `${days} d ${h} h` : h ? `${h} h ${min} min` : `${min} min`}</span>;
}
