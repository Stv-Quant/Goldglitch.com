"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useToday } from "@/components/experience/useFixtures";
import { CountUp, useInView } from "./motion";

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

