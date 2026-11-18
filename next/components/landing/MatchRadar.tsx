"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";
import { isTodayBogota, type Fixture } from "@/components/experience/fixture";
import { useToday } from "@/components/experience/useFixtures";
import { Crest } from "./Crest";
import { prefersReduced } from "./motion";

const timeFmt = new Intl.DateTimeFormat("es-CO", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "America/Bogota" });

/**
 * Two rows of today's real fixtures with crests, drifting in opposite directions. Scroll speed pushes them
 * (skew + faster drift): the page reacts to the reader's hand.
 */
export function MatchRadar() {
  const today = useToday();
  const list = today?.fixtures ?? [];
  const rootRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const root = rootRef.current;
    if (!root || prefersReduced()) return;
    const rows = Array.from(root.querySelectorAll<HTMLElement>("[data-row]"));
    let last = window.scrollY, v = 0, raf = 0, x = 0, visible = false, t0 = 0;
    const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting; if (visible && !raf) raf = requestAnimationFrame(tick); });
    io.observe(root);
    function tick(t: number) {
      raf = 0;
      if (!visible) return;
      const dt = t0 ? Math.min(50, t - t0) : 16;
      t0 = t;
      const y = window.scrollY;
      v += ((y - last) - v) * 0.12;
      last = y;
      x += (0.035 + Math.min(1.6, Math.abs(v) * 0.02)) * dt;
      rows.forEach((r, i) => {
        const w = r.scrollWidth / 2 || 1;
        const off = ((i ? -x : x) % w + w) % w;
        r.style.transform = `translate3d(${-off}px,0,0) skewX(${Math.max(-8, Math.min(8, -v * 0.25))}deg)`;
      });
      raf = requestAnimationFrame(tick);
    }
    return () => { io.disconnect(); cancelAnimationFrame(raf); };
  }, [list.length]);

  const half = Math.ceil(list.length / 2);
  const rowA = list.slice(0, half), rowB = list.slice(half).length ? list.slice(half) : list;
  const fill = (r: Fixture[]) => (r.length ? Array.from({ length: Math.max(1, Math.ceil(10 / r.length)) }, () => r).flat() : []);

  return (
    <section ref={rootRef} id="radar" className="relative border-y border-line bg-[rgba(8,7,5,0.6)] py-14 sm:py-20">
      <div className="mx-auto flex max-w-6xl flex-wrap items-end justify-between gap-4 px-5 sm:px-6">
        <div>
          <p className="num text-[11px] uppercase tracking-[0.22em] text-gold">El radar · en vivo</p>
          <h2 className="display mt-3 text-[2.4rem] sm:text-[3.4rem]">Esto está analizando <em>ahora mismo</em>.</h2>
        </div>
        <Link href="/acceso" className="num text-xs uppercase tracking-[0.18em] text-gold hover:underline underline-offset-4">
          Abrir las probabilidades →
        </Link>
      </div>

      <div className="radar-viewport mt-10 space-y-4">
        {today === null ? (
          <div className="flex gap-4 px-5">{Array.from({ length: 5 }, (_, i) => <div key={i} className="radar-chip radar-skel" />)}</div>
        ) : !list.length ? (
          <p className="px-5 text-center text-mid">Hoy y mañana no hay partidos en las ligas que seguimos. Vuelve pronto.</p>
        ) : (
          [rowA, rowB].map((r, i) => (
            <div key={i} className="overflow-hidden">
              <div data-row className="flex w-max will-change-transform">
                {[0, 1].map((copy) => (
                  <div key={copy} className="flex gap-4 pr-4" aria-hidden={copy === 1 || undefined}>
                    {fill(r).map((f, j) => <Chip key={`${f.id}-${j}`} f={f} />)}
                  </div>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

function Chip({ f }: { f: Fixture }) {
  return (
    <Link href="/acceso" tabIndex={-1} className="radar-chip group">
      <div className="flex items-center justify-between num text-[10px] uppercase tracking-[0.14em]">
        <span className="text-lo truncate">{f.league}</span>
        <span className={f.state === "in" ? "text-up" : "text-gold"}>
          {f.state === "in" ? "● En vivo" : `${isTodayBogota(f.kickoffAt) ? "Hoy" : "Mañana"} ${timeFmt.format(f.kickoffAt)}`}
        </span>
      </div>
      <div className="mt-3 flex items-center gap-3">
        <Crest src={f.homeLogo} name={f.homeName ?? f.home} size={34} />
        <span className="min-w-0 flex-1 truncate text-[14px] text-hi">{f.homeName ?? f.home}</span>
      </div>
      <div className="mt-2 flex items-center gap-3">
        <Crest src={f.awayLogo} name={f.awayName ?? f.away} size={34} />
        <span className="min-w-0 flex-1 truncate text-[14px] text-hi">{f.awayName ?? f.away}</span>
      </div>
      <div className="mt-3 flex gap-1.5">
        {(f.outcomes === 3 ? ["1", "X", "2"] : ["1", "2"]).map((m) => (
          <span key={m} className="radar-q num"><span className="text-lo">{m}</span> <span className="banner-q">??%</span></span>
        ))}
      </div>
    </Link>
  );
}
