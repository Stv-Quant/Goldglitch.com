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
    title: "Historial",
    body: "Publicamos cómo le fue a cada pronóstico, acierte o falle, en un historial abierto. Sin borrar los malos días.",
    stat: "Aciertos y fallos",
  },
];

const TURNS = 3; // the helix repeats the 5 steps three times; the middle turn is the one you read
const STEP_DEG = 42; // tighter than 360/5 so neighbours stay visible around the cylinder
const CARDS = Array.from({ length: STEPS.length * TURNS }, (_, k) => ({ k, s: STEPS[k % STEPS.length] }));
// Funnel of spinning rings: narrow at the bottom, wide at the top (a whirlwind), alternating directions.
const RINGS = [0.62, 0.72, 0.82, 0.93, 1.05, 1.18, 1.32, 1.48];
const RIBS = 18;

/**
 * "Cómo calculamos" as a vortex: the steps sit on a helix wrapped around a cylinder of light.
 * Scrolling screws the helix (rotate + rise) so the next step turns to the front, while the
 * funnel rings and ribs spin on their own. 15 cards + a few dozen lines, all CSS transforms on
 * the compositor; JS only writes one transform/opacity per card per frame while on screen.
 */
export function MethodRing() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current!;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      el.dataset.static = "";
      return;
    }
    const cards = Array.from(el.querySelectorAll<HTMLElement>("[data-card]"));
    const dots = Array.from(el.querySelectorAll<HTMLElement>("[data-dot]"));
    let target = STEPS.length;
    let cur = target;
    let raf = 0;
    let visible = false;
    let lastActive = -1;

    const readScroll = () => {
      const r = el.getBoundingClientRect();
      const total = r.height - window.innerHeight;
      const p = Math.min(1, Math.max(0, -r.top / Math.max(1, total)));
      target = STEPS.length + p * (STEPS.length - 1);
    };

    const frame = () => {
      raf = 0;
      cur += (target - cur) * 0.11;
      if (Math.abs(target - cur) < 0.0005) cur = target;
      const mobile = window.innerWidth < 640;
      const R = mobile ? 190 : 300;
      const pitch = mobile ? 112 : 128;
      for (const c of cards) {
        const rel = Number(c.dataset.k) - cur;
        const a = rel * STEP_DEG;
        const facing = Math.cos((a * Math.PI) / 180); // 1 = front, -1 = back
        const near = Math.exp(-(rel * rel) / 9);
        const focus = 0.4 + 0.6 * Math.exp(-(rel * rel) / 0.12); // the card being read is fully lit
        const o = focus * Math.max(0, facing) ** 0.8 * near;
        c.style.transform = `translate(-50%, -50%) translateY(${(rel * pitch).toFixed(1)}px) rotateY(${a.toFixed(2)}deg) translateZ(${R}px)`;
        c.style.opacity = o < 0.02 ? "0" : o.toFixed(3);
        c.style.visibility = o < 0.02 ? "hidden" : "visible";
      }
      const active = Math.round(cur) % STEPS.length;
      if (active !== lastActive) {
        lastActive = active;
        cards.forEach((c) => c.toggleAttribute("data-front", Number(c.dataset.k) === Math.round(cur)));
        dots.forEach((d, i) => d.toggleAttribute("data-on", i === active));
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
  }, []);

  return (
    <section id="metodo" ref={ref} className="method relative" aria-labelledby="metodo-title">
      <div className="method-stage sticky top-0 h-dvh overflow-hidden flex flex-col">
        <div className="relative z-10 mx-auto w-full max-w-6xl px-5 sm:px-6 pt-24 sm:pt-28">
          <p className="num text-[11px] tracking-[0.22em] text-gold uppercase">Método</p>
          <h2 id="metodo-title" className="display mt-3 text-[2.6rem] sm:text-[4.2rem]">
            No especulamos. <em>Calculamos.</em>
          </h2>
          <p className="mt-3 max-w-xl text-mid">Cinco pasos, siempre los mismos, para cada partido de cada deporte.</p>
        </div>

        <div className="method-scene relative flex-1">
          {/* The whirlwind: a funnel of spinning rings, ribs of light and a glowing axis */}
          <div aria-hidden className="vortex">
            <div className="vortex-axis" />
            <div className="vortex-spin">
              {Array.from({ length: RIBS }, (_, j) => (
                <span key={j} className="vortex-rib" style={{ ["--j" as string]: j, ["--ribs" as string]: RIBS }} />
              ))}
            </div>
            {RINGS.map((s, j) => (
              <span key={j} className="vortex-ring"
                style={{ ["--s" as string]: s, ["--y" as string]: (RINGS.length - 1) / 2 - j, ["--d" as string]: `${14 + j * 3}s`, ["--dir" as string]: j % 2 ? "reverse" : "normal" }} />
            ))}
          </div>

          <div className="method-helix">
            {CARDS.map(({ k, s }) => {
              const dup = k < STEPS.length || k >= STEPS.length * 2;
              return (
                <article key={k} data-card data-k={k} data-dup={dup ? "" : undefined} aria-hidden={dup || undefined}
                  className="method-card glass">
                  <div className="flex items-center justify-between gap-3">
                    <span className="num text-gold text-sm">{s.n}</span>
                    <span className="num text-[10px] tracking-[0.18em] uppercase text-lo text-right">{s.stat}</span>
                  </div>
                  <h3 className="display mt-5 text-4xl sm:text-5xl">{s.title}</h3>
                  <p className="mt-4 text-[15px] leading-relaxed text-mid">{s.body}</p>
                  <div className="method-progress mt-6 h-px" aria-hidden />
                </article>
              );
            })}
          </div>

          <ol aria-hidden className="method-dots">
            {STEPS.map((s) => (
              <li key={s.n} data-dot className="num">{s.n}</li>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
}
