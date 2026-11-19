"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { isTodayBogota, type Fixture } from "@/components/experience/fixture";
import { useToday } from "@/components/experience/useFixtures";
import { Crest } from "./Crest";

/**
 * "El recorrido": a pre-rendered camera flight (one continuous take, rendered in-house with Three.js) scrubbed by scroll.
 * One file per format (16:9 desktop, 9:16 phone), fetched as a Blob so every frame is seekable on any host.
 * Seeks are coalesced (never queued while the decoder is busy) and eased with rAF; reduced motion gets chapter stills.
 */
const CHAPTERS: { at: number; tag?: string; eyebrow: string; title: React.ReactNode; body: string }[] = [
  { at: 0, eyebrow: "00 · Afuera", title: <>Afuera, todo <em>grita</em>.</>, body: "Fijas, grupos VIP, ganancias seguras. Pantallas que nadie audita." },
  { at: 0.16, tag: "FÚT", eyebrow: "01 · Fútbol", title: <>Entramos al <em>estadio</em>.</>, body: "Tiros, xG, córners y tarjetas de cada equipo y cada jugador, convertidos en probabilidades." },
  { at: 0.35, tag: "MLB", eyebrow: "02 · MLB", title: <>Cada lanzamiento, <em>un dato</em>.</>, body: "Abridores, bullpen, parque y clima: carreras esperadas, no corazonadas." },
  { at: 0.54, tag: "NBA", eyebrow: "03 · NBA", title: <>La ventaja vive en <em>el ritmo</em>.</>, body: "Eficiencia por posesión, rotaciones y descanso." },
  { at: 0.72, tag: "NHL", eyebrow: "04 · NHL", title: <>Sobre el hielo, <em>también</em>.</>, body: "Remates, porteros y superioridades numéricas, partido a partido." },
  { at: 0.9, eyebrow: "05 · La señal", title: <>Al final, <em>un porcentaje</em> honesto.</>, body: "Publicado antes del pitazo. Auditado después, en público." },
];

const HOLD = 0.88;
const SRC = { desktop: "/film/recorrido.mp4", mobile: "/film/recorrido-m.mp4" };
const POSTER = { desktop: "/film/recorrido.jpg", mobile: "/film/recorrido-m.jpg" };

export function FilmScrub() {
  const rootRef = useRef<HTMLElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [chapter, setChapter] = useState(0);
  const [mobile, setMobile] = useState<boolean | null>(null);
  const [reduce, setReduce] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const mq = () => setMobile(window.matchMedia("(max-width: 860px), (pointer: coarse)").matches && window.innerHeight > window.innerWidth);
    const t = setTimeout(() => { mq(); setReduce(window.matchMedia("(prefers-reduced-motion: reduce)").matches); }, 0);
    return () => clearTimeout(t);
  }, []);

  // Load the right file as a Blob once the section is near.
  useEffect(() => {
    if (mobile === null || reduce) return;
    const root = rootRef.current!, video = videoRef.current!;
    let url = "", cancelled = false;
    const io = new IntersectionObserver(async ([e]) => {
      if (!e.isIntersecting) return;
      io.disconnect();
      try {
        const res = await fetch(mobile ? SRC.mobile : SRC.desktop);
        const blob = await res.blob();
        if (cancelled) return;
        url = URL.createObjectURL(blob);
        video.src = url;
        video.addEventListener("loadeddata", () => setReady(true), { once: true });
      } catch { /* the poster stays: nothing breaks */ }
    }, { rootMargin: "150% 0px" });
    io.observe(root);
    // iOS paints seeked frames only after a play(): prime on first touch.
    const prime = () => { video.play().then(() => video.pause()).catch(() => {}); };
    window.addEventListener("touchstart", prime, { once: true, passive: true });
    return () => { cancelled = true; io.disconnect(); window.removeEventListener("touchstart", prime); if (url) URL.revokeObjectURL(url); };
  }, [mobile, reduce]);

  // Scroll → time, eased; seeks coalesced.
  useEffect(() => {
    const root = rootRef.current!, video = videoRef.current!;
    let raf = 0, cur = 0, target = 0, lastCh = -1, visible = false;
    const progress = () => {
      const r = root.getBoundingClientRect();
      return Math.min(1, Math.max(0, -r.top / Math.max(1, r.height - window.innerHeight)));
    };
    const tick = () => {
      raf = 0;
      target = progress();
      cur += (target - cur) * 0.14;
      if (Math.abs(target - cur) < 0.0004) cur = target;
      root.style.setProperty("--fp", cur.toFixed(4));
      const ft = Math.min(1, cur / HOLD); // the last stretch of scroll holds the final frame for the CTA
      let ch = 0;
      for (let i = 0; i < CHAPTERS.length; i++) if (ft >= CHAPTERS[i].at) ch = i;
      if (ch !== lastCh) { lastCh = ch; setChapter(ch); }
      if (video.duration && !video.seeking) {
        const t = ft * (video.duration - 0.05);
        if (Math.abs(video.currentTime - t) > 1 / 48) video.currentTime = t;
      }
      if (visible && (cur !== target || video.seeking)) raf = requestAnimationFrame(tick);
    };
    const kick = () => { if (visible && !raf) raf = requestAnimationFrame(tick); };
    const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting; kick(); });
    io.observe(root);
    window.addEventListener("scroll", kick, { passive: true });
    video.addEventListener("seeked", kick);
    return () => { io.disconnect(); window.removeEventListener("scroll", kick); video.removeEventListener("seeked", kick); cancelAnimationFrame(raf); };
  }, []);

  const c = CHAPTERS[chapter];
  const poster = mobile ? POSTER.mobile : POSTER.desktop;

  return (
    <section ref={rootRef} id="recorrido" aria-label="El recorrido" className="relative" style={{ height: "640dvh", ["--fp" as string]: 0 }}>
      <div className="sticky top-0 h-dvh overflow-hidden bg-void">
        {reduce ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={`/film/ch${chapter}${mobile ? "-m" : ""}.jpg`} alt="" className="absolute inset-0 h-full w-full object-cover" />
        ) : (
          <>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            {mobile !== null && <img src={poster} alt="" aria-hidden className={`absolute inset-0 h-full w-full object-cover transition-opacity duration-500 ${ready ? "opacity-0" : "opacity-100"}`} />}
            <video ref={videoRef} muted playsInline preload="none" aria-hidden className="absolute inset-0 h-full w-full object-cover" />
          </>
        )}
        <div aria-hidden className="film-scrim" />

        <div className="absolute inset-x-0 bottom-0 px-5 pb-[calc(6dvh+env(safe-area-inset-bottom))] sm:px-10 lg:px-16">
          <div key={chapter} className="film-copy max-w-[38rem]">
            <p className={`num text-[11px] uppercase tracking-[0.22em] ${chapter === 0 ? "text-flare" : "text-gold"}`}>{c.eyebrow}</p>
            <h2 className="display mt-3 text-[2.6rem] sm:text-[4.2rem] lg:text-[5rem]">{c.title}</h2>
            <p className="mt-4 max-w-md text-base leading-relaxed text-mid sm:text-lg">{c.body}</p>
            {c.tag && <VenueFixtures tag={c.tag} />}
            {chapter === CHAPTERS.length - 1 && (
              <div className="mt-7 flex flex-wrap gap-3">
                <Link href="/acceso" className="btn-gold cta-shine px-6 py-3.5 text-[15px]">Ver los partidos de hoy gratis →</Link>
                <Link href="/historial" className="btn-ghost px-5 py-3.5 text-[15px] bg-[rgba(10,9,7,0.5)]">Auditar el modelo</Link>
              </div>
            )}
          </div>
        </div>

        <ol aria-hidden className="absolute right-5 top-1/2 hidden -translate-y-1/2 flex-col gap-2 md:flex">
          {CHAPTERS.map((ch, i) => (
            <li key={i} className={`h-8 w-[3px] rounded-full transition-colors duration-300 ${i === chapter ? "bg-[var(--gold)]" : i < chapter ? "bg-[rgba(212,175,55,.35)]" : "bg-[rgba(237,230,214,.12)]"}`} />
          ))}
        </ol>
        <div aria-hidden className="absolute inset-x-0 top-0 h-[2px] origin-left bg-[var(--gold)] opacity-60" style={{ transform: "scaleX(var(--fp))" }} />
      </div>
    </section>
  );
}

const timeFmt = new Intl.DateTimeFormat("es-CO", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "America/Bogota" });

function VenueFixtures({ tag }: { tag: string }) {
  const list = (useToday()?.fixtures ?? []).filter((f: Fixture) => f.sport === tag).slice(0, 3);
  if (!list.length) return null;
  return (
    <ul className="mt-5 flex flex-wrap gap-2">
      {list.map((f) => (
        <li key={f.id}>
          <Link href="/acceso" className="act-fixture">
            <span className="flex -space-x-2">
              <Crest src={f.homeLogo} name={f.homeName ?? f.home} size={26} />
              <Crest src={f.awayLogo} name={f.awayName ?? f.away} size={26} />
            </span>
            <span className="text-[13px] text-hi">{f.homeName ?? f.home} <span className="text-lo">vs</span> {f.awayName ?? f.away}</span>
            <span className="num text-[10.5px] text-lo">{f.state === "in" ? "En vivo" : `${isTodayBogota(f.kickoffAt) ? "Hoy" : "Mañ"} ${timeFmt.format(f.kickoffAt)}`}</span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
