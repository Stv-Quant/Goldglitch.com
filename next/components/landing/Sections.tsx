"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useToday } from "@/components/experience/useFixtures";
import { CountUp, useInView, useTilt } from "./motion";

/* ---------------- Proof: the public record in four numbers ---------------- */

export function ProofNumbers() {
  const today = useToday();
  const r = today?.record;
  const [ref, inView] = useInView<HTMLDivElement>();
  const hit = r && r.settled ? (r.won / r.settled) * 100 : null;
  const exp = r?.expected != null ? r.expected * 100 : null;
  const items: { v: number | null; d?: number; suf?: string; label: string; hint: string }[] = [
    { v: r?.matches ?? null, label: "partidos analizados", hint: "Cada uno con su pronóstico guardado" },
    { v: r?.settled ?? null, label: "picks auditados", hint: "Acertados y fallados, sin borrar ninguno" },
    { v: hit, d: 1, suf: "%", label: "acierto real", hint: exp != null ? `El modelo esperaba ${exp.toFixed(1)}%` : "En selecciones de 75% o más" },
    { v: 15, suf: "+", label: "ligas y competiciones", hint: "Fútbol, MLB, NBA, NHL y NFL" },
  ];
  return (
    <section className="relative mx-auto max-w-6xl px-5 py-20 sm:px-6 sm:py-28">
      <p className="num text-[11px] uppercase tracking-[0.22em] text-gold">La prueba</p>
      <h2 className="display mt-3 max-w-3xl text-[2.4rem] sm:text-[3.6rem]">
        Un tipster te muestra sus aciertos. <em>Nosotros, todo.</em>
      </h2>
      <div ref={ref} className="mt-12 grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-line bg-[var(--border-soft)] lg:grid-flow-col lg:auto-cols-fr lg:grid-cols-none">
        {items.filter((it) => today === null || it.v != null).map((it, i) => (
          <div key={it.label} className="proof-cell bg-void p-6 sm:p-8" style={{ transitionDelay: `${i * 90}ms` }} data-in={inView || undefined}>
            <div className="num gold-leaf text-[2.6rem] leading-none sm:text-[3.4rem]">
              {it.v == null ? "—" : <CountUp to={it.v} run={inView} decimals={it.d ?? 0} suffix={it.suf} />}
            </div>
            <div className="mt-3 text-[15px] text-hi">{it.label}</div>
            <div className="mt-1 text-[13px] text-lo">{it.hint}</div>
          </div>
        ))}
      </div>
      <Link href="/historial" className="mt-6 inline-flex num text-xs uppercase tracking-[0.18em] text-gold hover:underline underline-offset-4">
        Ver cada pick, uno por uno →
      </Link>
    </section>
  );
}

/* ---------------- How it works: pinned, scroll-driven 4 steps ---------------- */

const STEPS = [
  { k: "Datos", t: "Descarga todo lo que pasó", d: "Resultados, tiros, xG, córners, tarjetas, alineaciones y forma de cada equipo y jugador. Miles de partidos, todos los días, sin que tengas que buscar nada.", icon: "M4 6h16M4 12h16M4 18h10" },
  { k: "Modelo", t: "Simula el partido miles de veces", d: "Modelos estadísticos (Poisson, Dixon-Coles, Monte Carlo) juegan el partido una y otra vez. Sin corazonadas, sin camisetas.", icon: "M4 18l5-6 4 3 7-9" },
  { k: "Probabilidad", t: "Te dice qué tan probable es cada cosa", d: "Ganador, goles, córners, tarjetas y jugadores en porcentaje, con su rango de incertidumbre. Tú decides con los números delante.", icon: "M12 3a9 9 0 1 0 9 9h-9V3Z" },
  { k: "Auditoría", t: "Y se juzga en público", d: "Cada pronóstico se guarda antes del pitazo y se liquida con el resultado real. Si el modelo falla, lo ves en el historial.", icon: "M5 12l4 4 10-10" },
];

export function Pipeline() {
  const ref = useRef<HTMLElement>(null);
  const [step, setStep] = useState(0);
  useEffect(() => {
    const el = ref.current!;
    let raf = 0;
    const on = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const r = el.getBoundingClientRect();
        const p = Math.min(1, Math.max(0, -r.top / Math.max(1, r.height - window.innerHeight)));
        el.style.setProperty("--pp", p.toFixed(3));
        setStep(Math.min(STEPS.length - 1, Math.floor(p * STEPS.length * 0.999)));
      });
    };
    on();
    window.addEventListener("scroll", on, { passive: true });
    window.addEventListener("resize", on);
    return () => { window.removeEventListener("scroll", on); window.removeEventListener("resize", on); cancelAnimationFrame(raf); };
  }, []);

  return (
    <section ref={ref} className="relative" style={{ height: `${STEPS.length * 70 + 40}dvh`, ["--pp" as string]: 0 }} aria-labelledby="como-title">
      <div className="sticky top-0 flex h-dvh items-center overflow-hidden">
        <div className="mx-auto grid w-full max-w-6xl gap-10 px-5 sm:px-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
          <div>
            <p className="num text-[11px] uppercase tracking-[0.22em] text-gold">Cómo funciona</p>
            <h2 id="como-title" className="display mt-3 text-[2.4rem] sm:text-[3.6rem]">De miles de datos a <em>un porcentaje</em> honesto.</h2>
            <ol className="mt-8 space-y-1">
              {STEPS.map((s, i) => (
                <li key={s.k} data-on={i === step || undefined} data-done={i < step || undefined} className="pipe-step">
                  <span className="num pipe-n">{String(i + 1).padStart(2, "0")}</span>
                  <span>{s.k}</span>
                </li>
              ))}
            </ol>
            <div className="mt-6 h-px w-full max-w-xs bg-[var(--border-soft)]">
              <div className="h-full origin-left bg-[var(--gold)]" style={{ transform: "scaleX(var(--pp))" }} />
            </div>
          </div>

          <div className="relative min-h-[340px]">
            {STEPS.map((s, i) => (
              <article key={s.k} className="pipe-card" data-on={i === step || undefined} data-past={i < step || undefined} aria-hidden={i !== step}>
                <div className="pipe-icon">
                  <svg viewBox="0 0 24 24" className="h-7 w-7" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d={s.icon} /></svg>
                </div>
                <p className="mt-6 num text-[11px] uppercase tracking-[0.2em] text-lo">Paso {i + 1} de {STEPS.length}</p>
                <h3 className="display mt-2 text-[2rem] sm:text-[2.8rem]">{s.t}</h3>
                <p className="mt-4 max-w-md text-[16px] leading-relaxed text-mid sm:text-[17px]">{s.d}</p>
                <StepVisual i={i} on={i === step} />
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function StepVisual({ i, on }: { i: number; on: boolean }) {
  if (i === 0) {
    return (
      <div className="mt-6 flex h-16 items-end gap-1" aria-hidden>
        {Array.from({ length: 36 }, (_, k) => (
          <span key={k} className="viz-bar" style={{ height: `${18 + ((k * 37) % 82)}%`, transitionDelay: `${k * 18}ms`, transform: on ? "scaleY(1)" : "scaleY(0.1)" }} />
        ))}
      </div>
    );
  }
  if (i === 1) {
    return (
      <svg viewBox="0 0 300 70" className="mt-6 h-16 w-full max-w-md" aria-hidden>
        {Array.from({ length: 14 }, (_, k) => (
          <path key={k} d={`M0 ${50 - k} C 60 ${20 + k * 3}, 120 ${60 - k * 2}, 180 ${30 + k}, S 260 ${15 + k * 2}, 300 ${35 - k}`}
            fill="none" stroke="var(--gold)" strokeOpacity={0.08 + (k % 4) * 0.06} strokeWidth="1" className="viz-path" data-on={on || undefined} style={{ transitionDelay: `${k * 40}ms` }} />
        ))}
      </svg>
    );
  }
  if (i === 2) {
    return (
      <div className="mt-6 flex max-w-md gap-1" aria-hidden>
        {[["49%", 49, "var(--p3)"], ["27%", 27, "var(--seg-2)"], ["24%", 24, "var(--seg-3)"]].map(([l, w, c], k) => (
          <div key={k} className="viz-seg num" style={{ flexBasis: on ? `${w}%` : "33%", background: String(c), color: k ? "var(--text-hi)" : "#0a0907" }}>{l}</div>
        ))}
      </div>
    );
  }
  return (
    <div className="mt-6 flex flex-wrap gap-1.5" aria-hidden>
      {Array.from({ length: 24 }, (_, k) => {
        const won = (k * 7) % 10 < 8;
        return <span key={k} className={`viz-tick ${won ? "is-won" : "is-lost"}`} style={{ transitionDelay: `${k * 35}ms`, opacity: on ? 1 : 0 }}>{won ? "✓" : "✕"}</span>;
      })}
    </div>
  );
}

/* ---------------- Versus: the contrast ---------------- */

const VS: [string, string][] = [
  ["«Fija 100%, no falla»", "Probabilidades: 62% significa que 38 de cada 100 veces pasa lo otro"],
  ["Capturas solo de lo que acertó", "Historial público de cada pick, acertado o fallado"],
  ["Grupo VIP por WhatsApp", "Una app con todos los partidos y todas las estadísticas"],
  ["Corazonadas y «fuentes internas»", "Modelos estadísticos con miles de partidos de datos"],
  ["Te empuja a apostar", "No somos casa de apuestas ni vendemos apuestas"],
];

export function Versus() {
  const [ref, inView] = useInView<HTMLDivElement>();
  return (
    <section id="versus" className="mx-auto max-w-6xl px-5 py-20 sm:px-6 sm:py-28">
      <p className="num text-[11px] uppercase tracking-[0.22em] text-flare">Lo que no somos</p>
      <h2 className="display mt-3 max-w-3xl text-[2.4rem] sm:text-[3.6rem]">
        No somos tipsters. Somos <em>lo opuesto</em>.
      </h2>
      <div ref={ref} className="mt-12 overflow-hidden rounded-2xl border border-line">
        <div className="grid grid-cols-2 border-b border-line num text-[11px] uppercase tracking-[0.18em]">
          <div className="p-4 text-flare sm:p-5">El tipster</div>
          <div className="border-l border-line bg-[rgba(212,175,55,0.05)] p-4 text-gold sm:p-5">Goldglitch</div>
        </div>
        {VS.map(([bad, good], i) => (
          <div key={bad} className="vs-row grid grid-cols-2 border-b border-line last:border-0" data-in={inView || undefined} style={{ ["--i" as string]: i }}>
            <div className="p-4 text-[14px] text-lo sm:p-5 sm:text-[16px]"><span className="vs-strike">{bad}</span></div>
            <div className="border-l border-line bg-[rgba(212,175,55,0.035)] p-4 text-[14px] text-hi sm:p-5 sm:text-[16px]">
              <span className="vs-check" aria-hidden>✓</span> {good}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ---------------- What's inside: bento of real UI ---------------- */

export function Bento() {
  return (
    <section id="bento" className="mx-auto max-w-6xl px-5 py-20 sm:px-6 sm:py-28">
      <p className="num text-[11px] uppercase tracking-[0.22em] text-gold">Qué recibes</p>
      <h2 className="display mt-3 max-w-3xl text-[2.4rem] sm:text-[3.6rem]">Todo el partido, <em>en números</em>.</h2>
      <div className="mt-12 grid gap-4 md:grid-cols-6">
        <Tile className="md:col-span-3" plan="Free" title="Ganador del partido" text="Local, empate o visitante en porcentaje, para cada partido de fútbol.">
          <div className="mt-5 space-y-2">
            {[["Local", 52, "var(--p3)"], ["Empate", 26, "var(--seg-2)"], ["Visita", 22, "var(--seg-2)"]].map(([l, v, c]) => (
              <div key={String(l)} className="flex items-center gap-3 text-[13px]">
                <span className="w-14 text-mid">{l}</span>
                <span className="h-2 flex-1 overflow-hidden rounded-full bg-[rgba(237,230,214,0.06)]"><span className="tile-bar block h-full rounded-full" style={{ ["--w" as string]: `${v}%`, background: String(c) }} /></span>
                <span className="num w-10 text-right text-hi">{v}%</span>
              </div>
            ))}
          </div>
        </Tile>
        <Tile className="md:col-span-3" plan="Pro" title="Marcador exacto" text="La matriz completa de marcadores. La densidad es la probabilidad.">
          <div className="mt-5 grid w-fit grid-cols-5 gap-1" aria-hidden>
            {Array.from({ length: 25 }, (_, k) => {
              const h = Math.floor(k / 5), a = k % 5;
              const p = Math.exp(-((h - 1) ** 2 + (a - 0.8) ** 2) / 2.2);
              return <span key={k} className="num grid h-7 w-9 place-items-center rounded text-[10px]" style={{ background: `rgba(212,175,55,${(p * 0.75).toFixed(2)})`, color: p > 0.5 ? "#0a0907" : "var(--text-lo)" }}>{h}-{a}</span>;
            })}
          </div>
        </Tile>
        <Tile className="md:col-span-2" plan="Pro" title="Goles, córners y tarjetas" text="Cada línea con su probabilidad de más o menos.">
          <ul className="mt-5 space-y-2 text-[13px]">
            {[["+2.5 goles", 58], ["+9.5 córners", 47], ["+4.5 tarjetas", 64]].map(([l, v]) => (
              <li key={String(l)} className="flex justify-between border-b border-line pb-2 last:border-0"><span className="text-mid">{l}</span><span className="num text-gold">{v}%</span></li>
            ))}
          </ul>
        </Tile>
        <Tile className="md:col-span-2" plan="Pro" title="Jugadores" text="Remates, goles, faltas y tarjetas por jugador, con su historial contra el rival.">
          <ul className="mt-5 space-y-2 text-[13px]">
            {[["Delantero · remate a puerta", 71], ["Extremo · 1+ remates", 83], ["Medio · tarjeta", 22]].map(([l, v]) => (
              <li key={String(l)} className="flex justify-between gap-2"><span className="truncate text-mid">{l}</span><span className="num text-gold">{v}%</span></li>
            ))}
          </ul>
        </Tile>
        <Tile className="md:col-span-2" plan="Free" title="Historial auditable" text="Cada pick queda guardado antes del partido.">
          <svg viewBox="0 0 200 60" className="mt-5 h-14 w-full" aria-hidden>
            <line x1="0" y1="30" x2="200" y2="30" stroke="var(--border-soft)" strokeDasharray="3 4" />
            <path className="tile-line" d="M0 30 L20 27 L40 33 L60 29 L80 31 L100 26 L120 30 L140 28 L160 32 L180 29 L200 30" fill="none" stroke="var(--gold)" strokeWidth="1.6" />
          </svg>
          <p className="text-[12px] text-lo">Cerca de 0 = el modelo acierta lo que dice.</p>
        </Tile>
      </div>
      <p className="mt-4 text-[12px] text-lo">Las cifras de esta sección son ilustrativas: los números reales están dentro de la app.</p>
    </section>
  );
}

function Tile({ className = "", plan, title, text, children }: { className?: string; plan: "Free" | "Pro"; title: string; text: string; children: React.ReactNode }) {
  const ref = useTilt<HTMLElement>(3);
  return (
    <article ref={ref} className={`bento-tile ${className}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-[17px] font-medium text-hi">{title}</h3>
        <span className={`num rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-[0.16em] ${plan === "Pro" ? "border-[var(--border-glass)] text-gold" : "border-line text-mid"}`}>{plan}</span>
      </div>
      <p className="mt-2 text-[14px] leading-relaxed text-mid">{text}</p>
      {children}
    </article>
  );
}

/* ---------------- Closing CTA, progress bar, mobile sticky CTA ---------------- */

export function FinalCta() {
  return (
    <section className="final-cta relative isolate overflow-hidden py-28 sm:py-36">
      <div aria-hidden className="hero-aurora" />
      <div className="mx-auto max-w-4xl px-5 text-center sm:px-6">
        <h2 className="display text-[3rem] sm:text-[5.2rem]">Deja de adivinar. <em>Mide.</em></h2>
        <p className="mx-auto mt-6 max-w-xl text-lg text-mid">
          Los partidos de hoy ya están calculados. Crea tu cuenta gratis y mira las probabilidades en menos de un minuto.
        </p>
        <div className="mt-10 flex flex-wrap justify-center gap-3">
          <Link href="/acceso" className="btn-gold cta-shine px-7 py-4 text-[16px]">Entrar gratis →</Link>
          <Link href="/planes" className="btn-ghost px-6 py-4 text-[16px]">Comparar planes</Link>
        </div>
        <p className="mt-5 text-[12px] text-lo">Estadística informativa. No garantizamos resultados ni recibimos apuestas. +18.</p>
      </div>
    </section>
  );
}

export function ScrollProgress() {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    let raf = 0;
    const on = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const d = document.documentElement;
        const p = d.scrollTop / Math.max(1, d.scrollHeight - d.clientHeight);
        if (ref.current) ref.current.style.transform = `scaleX(${p})`;
      });
    };
    on();
    window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, []);
  return <div aria-hidden className="fixed inset-x-0 top-0 z-[70] h-[2px]"><div ref={ref} className="h-full origin-left bg-gradient-to-r from-[var(--gold-dim)] via-[var(--gold)] to-[#fff3c4]" style={{ transform: "scaleX(0)" }} /></div>;
}

export function MobileCta() {
  const [show, setShow] = useState(false);
  useEffect(() => {
    const on = () => setShow(window.scrollY > window.innerHeight * 0.9 && window.innerHeight + window.scrollY < document.documentElement.scrollHeight - 500);
    on();
    window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, []);
  return (
    <div className={`mobile-cta md:hidden ${show ? "is-on" : ""}`} aria-hidden={!show}>
      <Link href="/acceso" tabIndex={show ? 0 : -1} className="btn-gold block w-full py-3.5 text-center text-[15px]">Ver probabilidades de hoy · gratis</Link>
    </div>
  );
}

