"use client";

import { useEffect, useRef } from "react";

const STEPS = [
  {
    n: "01",
    title: "Datos",
    body: "Resultados, eventos y cuotas de fuentes públicas, todos los días. Lo que no se puede verificar, no entra al modelo.",
    stat: "Fuentes verificables",
  },
  {
    n: "02",
    title: "Variables",
    body: "Fuerza ofensiva y defensiva ajustada por rival, localía, descanso y calendario. Cada número tiene una razón.",
    stat: "Ajustado por rival",
  },
  {
    n: "03",
    title: "Modelo",
    body: "Modelos estadísticos de conteo (goles, carreras) y ratings de fuerza. Salen distribuciones completas, no un ganador.",
    stat: "Distribuciones, no picks",
  },
  {
    n: "04",
    title: "Calibración",
    body: "Comprobamos que el 60% signifique 60% con partidos que el modelo nunca vio. Si se desvía, se corrige y se publica.",
    stat: "Validación fuera de muestra",
  },
  {
    n: "05",
    title: "Sello",
    body: "Cada pronóstico queda sellado con hora antes del pitazo. Después del inicio, el servidor no permite editarlo.",
    stat: "Inmutable tras el inicio",
  },
];

/**
 * "Cómo calculamos": a CSS 3D ring of five cards. The section is pinned; scroll turns the ring
 * so each step comes to the front. 5 DOM cards → CSS transforms on the compositor, no canvas needed.
 */
export function MethodRing() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current!;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      el.dataset.static = "";
      return;
    }
    let raf = 0;
    const update = () => {
      raf = 0;
      const r = el.getBoundingClientRect();
      const total = r.height - window.innerHeight;
      const p = Math.min(1, Math.max(0, -r.top / Math.max(1, total)));
      el.style.setProperty("--mp", p.toFixed(4));
      const active = Math.min(STEPS.length - 1, Math.round(p * (STEPS.length - 1)));
      el.querySelectorAll<HTMLElement>("[data-step]").forEach((c, i) => c.toggleAttribute("data-front", i === active));
    };
    const onScroll = () => { if (!raf) raf = requestAnimationFrame(update); };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      if (raf) cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <section id="metodo" ref={ref} className="method relative" style={{ ["--mp" as string]: 0, ["--n" as string]: STEPS.length }} aria-labelledby="metodo-title">
      <div className="method-stage sticky top-0 h-dvh overflow-hidden flex flex-col">
        <div className="relative z-10 mx-auto w-full max-w-6xl px-5 sm:px-6 pt-24 sm:pt-28">
          <p className="num text-[11px] tracking-[0.22em] text-gold uppercase">Método</p>
          <h2 id="metodo-title" className="display mt-3 text-[2.6rem] sm:text-[4.2rem]">
            No especulamos. <em>Calculamos.</em>
          </h2>
          <p className="mt-3 max-w-xl text-mid">Cinco pasos, siempre los mismos, para cada partido de cada deporte.</p>
        </div>
        <div className="method-scene relative flex-1">
          <div className="method-ring">
            {STEPS.map((s, i) => (
              <article key={s.n} data-step className="method-card glass" style={{ ["--i" as string]: i }}>
                <div className="flex items-center justify-between">
                  <span className="num text-gold text-sm">{s.n}</span>
                  <span className="num text-[10px] tracking-[0.18em] uppercase text-lo">{s.stat}</span>
                </div>
                <h3 className="display mt-6 text-4xl sm:text-5xl">{s.title}</h3>
                <p className="mt-4 text-[15px] leading-relaxed text-mid">{s.body}</p>
                <div className="method-progress mt-6 h-px bg-[var(--border-soft)]" aria-hidden />
              </article>
            ))}
          </div>
          <div aria-hidden className="method-floor" />
        </div>
      </div>
    </section>
  );
}
