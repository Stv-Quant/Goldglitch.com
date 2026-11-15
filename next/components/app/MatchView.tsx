"use client";

import { SportBadge, SportIcon } from "./SportBadge";

import Link from "next/link";
import { Tabs, type Tab } from "@/components/app/Tabs";
import { FeatureCompare } from "@/components/stats/FeatureCompare";
import { GoalsPanel } from "@/components/stats/GoalsPanel";
import { LockedPanel } from "@/components/stats/LockedPanel";
import { MarketsPanel, PicksList } from "@/components/stats/MatchPanels";
import { PlayersExplorer } from "@/components/stats/PlayersExplorer";
import { StakesPanel } from "@/components/stats/StakesPanel";
import { ProbLegend } from "@/components/stats/Prob";
import { ProbabilityBar } from "@/components/stats/ProbabilityBar";
import { StatLines } from "@/components/stats/StatLines";
import { dayLabel, timeLabel } from "@/lib/format";
import { PICK_MIN } from "@/lib/picks";
import { SPORT_LABEL } from "@/lib/sports";

import type { MatchView as MatchData } from "@/lib/data";
import type { Sport } from "@/lib/sports";

/** Full match sheet, drawn in the browser from /api/app/match/[id] (server rendering it exceeded the CPU limit). */
export function MatchView({ m }: { m: MatchData | { locked: true; sport: Sport } }) {
  if ("locked" in m) {
    return (
      <div className="max-w-xl space-y-4">
        <Link href="/app" className="text-sm text-lo hover:text-hi">← Partidos</Link>
        <LockedPanel tier="Pro" title={`${SPORT_LABEL[m.sport]} es parte de Pro`}>
          {`El modelo completo de ${SPORT_LABEL[m.sport].toLowerCase()} (probabilidades, picks y líneas) está disponible desde el plan Pro.`}
        </LockedPanel>
      </div>
    );
  }

  const p = m.prediction;
  const pro = p ? !p.locked.pro : false;
  const upcoming = m.status !== "finished";
  const tabs: Tab[] = [];

  if (p) {
    if (p.lines.length > 0 || p.linesLocked > 0) {
      tabs.push({
        id: "lineas",
        label: "Estadísticas",
        content: (
          <div className="space-y-4">
            <p className="text-[11px] text-lo">Mueve la línea con − y +. Arranca en la línea cuyo lado favorito tiene 65% o más.</p>
            {p.lines.length > 0 && <StatLines lines={p.lines} />}
            {p.linesLocked > 0 && (
              <LockedPanel tier="Pro" title={`${p.linesLocked} estadísticas más con Pro`}>
                {"Goles por equipo, córners, remates, remates al arco, faltas, tarjetas, fueras de juego y jugadores, cada una con su línea ajustable."}
              </LockedPanel>
            )}
          </div>
        ),
      });
    }

    if (m.sport === "football" || p.xg || p.scoreMatrix) {
      tabs.push({
        id: "marcador",
        label: "Marcador",
        badge: pro ? undefined : "PRO",
        content: pro ? (
          p.xg || p.scoreMatrix
            ? <GoalsPanel xg={p.xg} matrix={p.scoreMatrix} home={m.home.short} away={m.away.short} />
            : <p className="text-sm text-lo">El modelo no publicó goles esperados para este partido.</p>
        ) : (
          <LockedPanel tier="Pro" title="Goles esperados y marcadores">
            {"xG de cada equipo, los marcadores más probables, la distribución del total de goles y la probabilidad de que cada equipo no reciba gol."}
          </LockedPanel>
        ),
      });
    }

    tabs.push({
      id: "mercados",
      label: "Mercados",
      badge: pro ? undefined : "PRO",
      content: pro ? (
        (p.markets?.length ?? 0) > 0 ? <MarketsPanel markets={p.markets!} /> : <p className="text-sm text-lo">Sin mercados para este partido.</p>
      ) : (
        <LockedPanel tier="Pro" title="Todos los mercados">
          {"Resultado, hándicap, totales, ambos marcan, córners, tarjetas y combinadas, cada uno con su rango de incertidumbre."}
        </LockedPanel>
      ),
    });

    if (!pro || (p.players?.length ?? 0) > 0) {
      tabs.push({
        id: "jugadores",
        label: "Jugadores",
        badge: pro ? (p.players?.length ? String(p.players.length) : undefined) : "PRO",
        content: pro ? (
          <PlayersExplorer players={p.players!} home={{ name: m.home.name, short: m.home.short }} away={{ name: m.away.name, short: m.away.short }} />
        ) : (
          <LockedPanel tier="Pro" title="Desglose por jugador">
            {"Ficha completa de cada jugador: probabilidad de ser titular, minutos, gol, asistencia, remates y remates al arco, faltas, tarjetas, atajadas, su temporada por 90 minutos y su historial contra el rival."}
          </LockedPanel>
        ),
      });
    }

    if (p.stakes || p.stakesLocked) {
      tabs.push({
        id: "en-juego",
        label: "En juego",
        badge: pro ? undefined : "PRO",
        content: pro ? (
          <StakesPanel s={p.stakes!} home={m.home.name} away={m.away.name} />
        ) : (
          <LockedPanel tier="Pro" title="Lo que se juega cada equipo">
            {"Posición, probabilidad de título, plazas europeas o de ascenso y descenso al final de la temporada, cuánto mueve este partido cada una y el estado anímico (racha frente a lo esperado). Ya está incluido en las probabilidades."}
          </LockedPanel>
        ),
      });
    }

    tabs.push({
      id: "equipos",
      label: "Equipos",
      content: (
        <div className="card p-4 sm:p-6">
          {p.features.length
            ? <FeatureCompare rows={p.features} homeShort={m.home.short} awayShort={m.away.short} />
            : <p className="text-sm text-lo">Sin estadísticas descriptivas para este partido.</p>}
        </div>
      ),
    });

  }

  return (
    <article className="space-y-6">
      <Link href="/app" className="text-sm text-lo hover:text-hi">← Partidos</Link>

      <header className="glass relative overflow-hidden p-5 sm:p-7">
        <span aria-hidden className="pointer-events-none absolute -right-8 -top-8 text-gold opacity-[0.06]"><SportIcon sport={m.sport} league={m.competition.name} className="h-56 w-56" /></span>
        <div className="relative flex flex-wrap items-center justify-between gap-2 text-xs text-lo">
          <span className="flex flex-wrap items-center gap-2"><SportBadge sport={m.sport} league={m.competition.name} /><span>{m.competition.name}{m.venue ? ` · ${m.venue}` : ""}</span></span>
          <span className="num">
            {m.status === "live" ? <span style={{ color: "var(--neon-up)" }}>● EN VIVO</span> : `${dayLabel(m.kickoffAt)} · ${timeLabel(m.kickoffAt)}`}
          </span>
        </div>
        <div className="relative mt-6 grid grid-cols-[1fr_auto_1fr] items-center gap-4">
          <h1 className="font-display text-2xl leading-tight break-words text-hi sm:text-5xl">{m.home.name}</h1>
          <span className="num text-lg text-lo">
            {m.homeScore !== null && m.awayScore !== null ? `${m.homeScore} – ${m.awayScore}` : "vs"}
          </span>
          <p className="font-display text-right text-2xl leading-tight break-words text-hi sm:text-5xl">{m.away.name}</p>
        </div>
        {p ? (
          <div className="mt-6">
            <ProbabilityBar home={p.outcome.home} draw={p.outcome.draw} away={p.outcome.away}
              labels={{ home: m.home.short, away: m.away.short }} interval={p.interval} />
            <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
              <p className="num text-[11px] text-lo">
                Modelo {p.modelVersion} · actualizado {timeLabel(p.generatedAt)}
                {p.locked.pro && " · el rango de incertidumbre es parte de Pro"}
              </p>
              <ProbLegend />
            </div>
          </div>
        ) : (
          <p className="mt-6 text-sm text-lo">El modelo aún no publica este partido.</p>
        )}
      </header>

      {p && upcoming && (m.picks.length > 0 || m.picksLocked > 0) && (
        <section aria-labelledby="h-picks">
          <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
            <h2 id="h-picks" className="font-display text-3xl">
              Lo más probable <span className="num text-sm font-normal text-lo">· {Math.round(PICK_MIN * 100)}% o más</span>
            </h2>
            <p className="text-[11px] text-lo">Probabilidad, no certeza: un 80% falla 1 de cada 5 veces.</p>
          </div>
          {m.picks.length > 0 ? (
            <PicksList picks={m.picks} match={m.picks.some((k) => k.key.startsWith("sqpc_")) && m.status === "scheduled"
              ? { matchId: m.id, sport: m.sport, competition: m.competition.name, home: m.home.name, away: m.away.name, kickoffAt: m.kickoffAt }
              : undefined} />
          ) : (
            <LockedPanel tier="Pro" title={`${m.picksLocked} pick${m.picksLocked === 1 ? "" : "s"} del modelo en este partido`}>
              {"Las selecciones con 75% o más de probabilidad según el modelo, con su nivel de confianza."}
            </LockedPanel>
          )}
        </section>
      )}

      {tabs.length > 0 && <Tabs tabs={tabs} label="Secciones del partido" />}
    </article>
  );
}
