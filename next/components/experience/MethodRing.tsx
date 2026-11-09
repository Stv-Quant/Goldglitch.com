"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";
import { isTodayBogota, type Fixture } from "./fixture";
import { useFixtures } from "./useFixtures";

const MAX = 10;
const STEP_DEG = 42; // tight enough that the neighbours stay visible around the cylinder
// Funnel of spinning rings: narrow at the bottom, wide at the top (a whirlwind), alternating directions.
const RINGS = [0.66, 0.86, 1.08, 1.34];
const RIBS = 10;

const timeFmt = new Intl.DateTimeFormat("es-CO", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "America/Bogota" });

function when(f: Fixture) {
  if (f.state === "in") return <span className="text-up">● EN VIVO</span>;
  return <>{isTodayBogota(f.kickoffAt) ? "HOY" : "MAÑANA"} · {timeFmt.format(f.kickoffAt)}</>;
}

function MatchCard({ f }: { f: Fixture }) {
  const labels = f.outcomes === 3 ? ["Local", "Empate", "Visitante"] : ["Local", "Visitante"];
  return (
    <>
      <div className="flex items-center justify-between gap-3 num text-[10px] tracking-[0.18em] uppercase">
        <span className="text-gold truncate">{f.league === f.sport ? f.sport : `${f.sport} · ${f.league}`}</span>
        <span className="text-lo whitespace-nowrap">{when(f)}</span>
      </div>
      <div className="mt-5 grid grid-cols-[1fr_auto_1fr] items-baseline gap-3">
        <h3 className="display text-4xl sm:text-5xl truncate">{f.home}</h3>
        <span className="num text-xs text-lo">vs</span>
        <p className="display text-4xl sm:text-5xl truncate text-right">{f.away}</p>
      </div>
      <ul className="mt-5 space-y-2.5" aria-label="Probabilidades ocultas">
        {labels.map((l, j) => (
          <li key={l} className="grid grid-cols-[5rem_1fr_2.5rem] items-center gap-3 text-[13px]">
            <span className="text-mid">{l}</span>
            <span className="match-bar" style={{ ["--j" as string]: j }} aria-hidden />
            <span className="num text-right text-gold match-q">???</span>
          </li>
        ))}
      </ul>
      <Link href="/acceso" className="mt-5 inline-flex text-sm text-gold hover:underline underline-offset-4">Ver probabilidades →</Link>
    </>
  );
}

/**
 * Upcoming matches as a vortex: the fixtures sit on a helix wrapped around a cylinder of light.
 * Scrolling screws the helix so the next match turns to the front; the funnel rings spin on their own.
 * No probability ever reaches this page: every value is "???".
 */
export function MethodRing() {
  const ref = useRef<HTMLDivElement>(null);
  const fixtures = useFixtures();
  const list = (fixtures ?? []).slice(0, MAX);
  const n = list.length;

  useEffect(() => {
    const el = ref.current;
    if (!el || !n) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      el.dataset.static = "";
      return;
    }
    const cards = Array.from(el.querySelectorAll<HTMLElement>("[data-card]"));
    let target = 0;
    let cur = 0;
    let raf = 0;
    let visible = false;
    let lastActive = -1;

    const readScroll = () => {
      const r = el.getBoundingClientRect();
      const total = r.height - window.innerHeight;
      const p = Math.min(1, Math.max(0, -r.top / Math.max(1, total)));
      // Dwell on each match: the middle half of every segment turns the helix, the rest holds still.
      const x = p * (n - 1);
      const i = Math.min(n - 2, Math.floor(x));
      const t = Math.min(1, Math.max(0, (x - i - 0.25) / 0.5));
      target = n > 1 ? i + t * t * (3 - 2 * t) : 0;
    };

    const frame = () => {
      raf = 0;
      cur += (target - cur) * 0.22;
      if (Math.abs(target - cur) < 0.0005) cur = target;
      const mobile = window.innerWidth < 640;
      const R = mobile ? 190 : 300;
      const pitch = mobile ? 112 : 128;
      for (const c of cards) {
        const rel = Number(c.dataset.k) - cur;
        const a = rel * STEP_DEG;
        const facing = Math.cos((a * Math.PI) / 180);
        const near = Math.exp(-(rel * rel) / 9);
        const focus = 0.4 + 0.6 * Math.exp(-(rel * rel) / 0.12);
        const o = focus * Math.max(0, facing) ** 0.8 * near;
        // Neighbours sit on a smaller radius so their near edge never pokes through the card being read.
        const r = R * (0.72 + 0.28 * Math.exp(-(rel * rel) / 0.12));
        c.style.transform = `translate(-50%, -50%) translateY(${(rel * pitch).toFixed(1)}px) rotateY(${a.toFixed(2)}deg) translateZ(${r.toFixed(1)}px)`;
        c.style.opacity = o < 0.02 ? "0" : o.toFixed(3);
        c.style.visibility = o < 0.02 ? "hidden" : "visible";
      }
      const active = Math.round(cur);
      if (active !== lastActive) {
        lastActive = active;
        cards.forEach((c) => {
          const on = Number(c.dataset.k) === active;
          c.toggleAttribute("data-front", on);
          c.inert = !on; // only the card being read is clickable / focusable
        });
      }
      el.style.setProperty("--twist", `${(cur * STEP_DEG * -0.35).toFixed(2)}deg`);
      if (visible && cur !== target) raf = requestAnimationFrame(frame);
    };

    const kick = () => {
      readScroll();
      if (!raf) raf = requestAnimationFrame(frame);
    };
    const io = new IntersectionObserver(([e]) => {
      visible = e.isIntersecting;
      el.toggleAttribute("data-live", visible); // pauses the CSS spin when off screen
      if (visible) kick();
    });
    io.observe(el);
    readScroll();
    cur = target;
    frame();
    window.addEventListener("scroll", kick, { passive: true });
    window.addEventListener("resize", kick);
    return () => {
      io.disconnect();
      window.removeEventListener("scroll", kick);
      window.removeEventListener("resize", kick);
      if (raf) cancelAnimationFrame(raf);
    };
  }, [n]);

  const header = (
    <div className="relative z-10 mx-auto w-full max-w-6xl px-5 sm:px-6 pt-24 sm:pt-28">
      <p className="num text-[11px] tracking-[0.22em] text-gold uppercase">Próximos partidos</p>
      <h2 id="metodo-title" className="display mt-3 text-[2.6rem] sm:text-[4.2rem]">
        No especulamos. <em>Calculamos.</em>
      </h2>
      <p className="mt-3 max-w-xl text-mid">Los partidos de hoy y mañana. Los números se ven al entrar.</p>
    </div>
  );

  if (fixtures && !n) {
    return (
      <section id="metodo" className="relative pb-16" aria-labelledby="metodo-title">
        {header}
        <p className="mx-auto max-w-6xl px-5 sm:px-6 mt-8 text-sm text-lo">Hoy y mañana no hay partidos en las ligas que seguimos.</p>
      </section>
    );
  }

  return (
    <section id="metodo" ref={ref} className="method relative" aria-labelledby="metodo-title"
      style={{ height: `${100 + Math.max(n || 6, 2) * 26}dvh` }}>
      <div className="method-stage sticky top-0 h-dvh overflow-hidden flex flex-col">
        {header}
        <div className="method-scene relative flex-1">
          <div aria-hidden className="vortex">
            <div className="vortex-axis" />
            <div className="vortex-spin">
              {Array.from({ length: RIBS }, (_, j) => (
                <span key={j} className="vortex-rib" style={{ ["--j" as string]: j, ["--ribs" as string]: RIBS }} />
              ))}
            </div>
            {RINGS.map((s, j) => (
              <span key={j} className="vortex-ring"
                style={{ ["--s" as string]: s, ["--y" as string]: (RINGS.length - 1) / 2 - j, ["--d" as string]: `${16 + j * 5}s`, ["--dir" as string]: j % 2 ? "reverse" : "normal" }} />
            ))}
          </div>

          <div className="method-helix">
            {fixtures === null ? (
              <div className="method-card glass" data-front style={{ transform: "translate(-50%, -50%) translateZ(var(--R))" }}>
                <div className="h-3 w-1/2 rounded bg-[var(--seg-3)] animate-pulse" />
                <div className="mt-6 h-10 w-3/4 rounded bg-[var(--seg-3)] animate-pulse" />
                <div className="mt-6 space-y-3">{[0, 1, 2].map((i) => <div key={i} className="h-2 rounded bg-[var(--seg-3)] animate-pulse" />)}</div>
              </div>
            ) : (
              list.map((f, k) => (
                <article key={f.id} data-card data-k={k} className="method-card glass">
                  <MatchCard f={f} />
                </article>
              ))
            )}
          </div>

          {n > 1 && <p aria-hidden className="method-count num">{n} partidos</p>}
        </div>
      </div>
    </section>
  );
}
