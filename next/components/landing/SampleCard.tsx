"use client";

import { useEffect, useState } from "react";
import type { Sample } from "@/components/experience/useFixtures";
import { Crest } from "./Crest";
import { CountUp, useTilt } from "./motion";

const timeFmt = new Intl.DateTimeFormat("es-CO", { weekday: "short", hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "America/Bogota" });

const EXAMPLE: Sample = {
  matchId: "ejemplo", league: "Ejemplo ilustrativo", home: "Local", away: "Visitante",
  kickoffAt: 0, p: { home: 0.49, draw: 0.27, away: 0.24 }, picks: 3,
};

export function SampleStack({ sample, loading }: { sample: Sample | null; loading: boolean }) {
  const tilt = useTilt<HTMLDivElement>(7);
  const s = sample ?? EXAMPLE;
  const real = !!sample;
  const [run, setRun] = useState(false);
  useEffect(() => { if (!loading) { const t = setTimeout(() => setRun(true), 250); return () => clearTimeout(t); } }, [loading]);

  const rows: [string, string, number][] = [
    [s.home, "home", s.p.home], ["Empate", "draw", s.p.draw], [s.away, "away", s.p.away],
  ];
  const top = Math.max(s.p.home, s.p.draw, s.p.away);

  return (
    <div className="hero-in relative mx-auto w-full max-w-[460px] [perspective:1400px]" style={{ animationDelay: "200ms" }}>
      {/* Depth: two ghost cards behind the real one */}
      <div aria-hidden className="sample-ghost" style={{ ["--d" as string]: 2 }} />
      <div aria-hidden className="sample-ghost" style={{ ["--d" as string]: 1 }} />

      <div ref={tilt} className="sample-card relative">
        <div aria-hidden className="sample-light" />
        <div className="flex items-center justify-between gap-3 num text-[10.5px] uppercase tracking-[0.16em]">
          <span className={real ? "text-gold" : "text-lo"}>{real ? "● Muestra gratis · datos reales" : "Ejemplo ilustrativo"}</span>
          <span className="truncate text-lo">{real ? s.league : ""}</span>
        </div>

        <div className="mt-6 grid grid-cols-[1fr_auto_1fr] items-center gap-3 text-center">
          <Team name={s.home} logo={s.homeLogo} />
          <div className="num text-[11px] uppercase tracking-[0.14em] text-lo">
            {real ? <><div className="text-hi text-sm normal-case tracking-normal">{timeFmt.format(s.kickoffAt)}</div><Countdown at={s.kickoffAt} /></> : "vs"}
          </div>
          <Team name={s.away} logo={s.awayLogo} />
        </div>

        <div className="mt-7 space-y-3">
          {rows.map(([label, k, p], i) => (
            <div key={k}>
              <div className="flex items-baseline justify-between text-sm">
                <span className={p === top ? "text-hi" : "text-mid"}>{label}</span>
                <span className={`num text-lg ${p === top ? "text-gold p-glow" : "text-mid"}`}>
                  <CountUp to={p * 100} run={run} ms={1300 + i * 200} />%
                </span>
              </div>
              <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-[rgba(237,230,214,0.06)]">
                <div className="sample-bar h-full rounded-full" data-top={p === top || undefined}
                  style={{ width: run ? `${p * 100}%` : "0%", transitionDelay: `${i * 120}ms` }} />
              </div>
            </div>
          ))}
        </div>

        <div className="mt-7 border-t border-line pt-5">
          <p className="num text-[10.5px] uppercase tracking-[0.16em] text-lo">Dentro del partido</p>
          <ul className="mt-3 grid grid-cols-2 gap-2 text-[13px]">
            {["Goles +2.5", "Córners", "Tarjetas", "Remates por jugador"].map((m) => (
              <li key={m} className="locked-row">
                <span className="text-mid">{m}</span>
                <span className="num blur-[5px] select-none text-gold" aria-hidden>{(37 + m.length * 3) % 100}%</span>
                <span className="sr-only">Disponible en Pro</span>
              </li>
            ))}
          </ul>
          {s.picks > 0 && (
            <p className="mt-4 flex items-center gap-2 text-[13px] text-hi">
              <span className="pick-pulse num">{s.picks}</span>
              {s.picks === 1 ? "selección" : "selecciones"} con 75% o más según el modelo
            </p>
          )}
        </div>
      </div>
      <p className="mt-4 text-center text-[12px] text-lo">
        Esto es lo que ves: probabilidades, no promesas. {real ? "Actualizado cada 10 minutos." : ""}
      </p>
    </div>
  );
}

function Team({ name, logo }: { name: string; logo?: string }) {
  return (
    <div className="flex min-w-0 flex-col items-center gap-2.5">
      <Crest src={logo} name={name} size={64} className="crest-lg" />
      <span className="line-clamp-2 text-[15px] font-medium leading-tight text-hi">{name}</span>
    </div>
  );
}

function Countdown({ at }: { at: number }) {
  const [now, setNow] = useState<number | null>(null);
  useEffect(() => {
    const t = () => setNow(Date.now());
    const first = setTimeout(t, 0);
    const id = setInterval(t, 1000);
    return () => { clearTimeout(first); clearInterval(id); };
  }, []);
  if (now === null) return <div className="mt-1">&nbsp;</div>;
  const d = Math.max(0, at - now);
  const h = Math.floor(d / 3_600_000), m = Math.floor((d % 3_600_000) / 60_000), s = Math.floor((d % 60_000) / 1000);
  return <div className="mt-1 text-gold">{d ? `${h}h ${String(m).padStart(2, "0")}m ${String(s).padStart(2, "0")}s` : "En juego"}</div>;
}
