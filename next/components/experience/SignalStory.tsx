"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";
import { buildFormations, ENTROPY, PALETTE, WOBBLE, type Formation } from "./formations";

const ACTS = ["Ruido", "El juego", "La percepción", "La forma", "La prueba", "Señal"];
const NOISE = [
  ["FIJA 100%", 8, 18], ["CUOTA SEGURA", 62, 12], ["GRUPO VIP", 74, 70], ["NO FALLA", 14, 78],
  ["PARLEY DEL DÍA", 46, 86], ["+500% ESTE MES", 80, 38], ["CONFÍA EN MÍ", 30, 8], ["LA DE HOY ES FIJA", 56, 54],
  ["ASEGURADO", 4, 48], ["ÚLTIMOS CUPOS", 88, 88],
] as const;

const smooth = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};
const ease = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2);

/**
 * Noise → signal. One pinned canvas; scroll position drives a continuous formation index f ∈ [0,5].
 * Canvas 2D: ≤6.5k square marks, typed arrays, color-batched draws; well under the 16ms budget.
 */
export function SignalStory() {
  const rootRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const actRef = useRef<HTMLSpanElement>(null);
  const entRef = useRef<HTMLSpanElement>(null);
  const barRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const root = rootRef.current!;
    const canvas = canvasRef.current!;
    const ctx = canvas.getContext("2d", { alpha: false })!;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const sections = Array.from(root.querySelectorAll<HTMLElement>("[data-act]"));

    let W = 0, H = 0, dpr = 1, N = 0;
    let F: Formation[] = [];
    let px = new Float32Array(0), py = new Float32Array(0), delay = new Float32Array(0), phase = new Float32Array(0);
    let buckets: Uint32Array[] = [];
    const counts = new Uint32Array(4);
    let tops: number[] = [], heights: number[] = [];
    let f = 0, raf = 0, running = false, lastAct = -1;
    const pointer = { x: -9999, y: -9999, t: 0 };

    function measure() {
      const y = window.scrollY;
      tops = sections.map((s) => s.getBoundingClientRect().top + y);
      heights = sections.map((s) => s.offsetHeight);
    }

    function resize() {
      W = window.innerWidth;
      H = window.innerHeight;
      dpr = Math.min(window.devicePixelRatio || 1, 1.75);
      canvas.width = Math.round(W * dpr);
      canvas.height = Math.round(H * dpr);
      canvas.style.width = `${W}px`;
      canvas.style.height = `${H}px`;
      const cores = navigator.hardwareConcurrency || 4;
      const nextN = W < 700 || cores <= 4 ? 3200 : 6500;
      const first = N === 0;
      F = buildFormations(nextN, W, H);
      if (nextN !== N) {
        N = nextN;
        px = new Float32Array(N); py = new Float32Array(N);
        delay = new Float32Array(N); phase = new Float32Array(N);
        for (let i = 0; i < N; i++) { delay[i] = Math.random() * 0.35; phase[i] = Math.random() * Math.PI * 2; }
        buckets = [0, 1, 2, 3].map(() => new Uint32Array(N));
      }
      if (first || reduce) { px.set(F[0].x); py.set(F[0].y); }
      measure();
    }

    function progress() {
      const c = window.scrollY + H * 0.5;
      let idx = 0;
      for (let i = 0; i < sections.length; i++) if (c >= tops[i]) idx = i;
      const p = (c - tops[idx]) / Math.max(1, heights[idx]);
      return Math.min(F.length - 1, idx + (idx < F.length - 1 ? smooth(0.52, 0.98, p) : 0));
    }

    function frame(time: number) {
      raf = 0;
      const target = progress();
      f = reduce ? Math.round(target) : target;
      const a = Math.floor(f);
      const b = Math.min(F.length - 1, a + 1);
      const t = f - a;
      const A = F[a], B = F[b];
      const wob = WOBBLE[a] + (WOBBLE[b] - WOBBLE[a]) * t;
      const k = reduce ? 1 : 0.12;
      const sec = time * 0.001;
      const pointerLive = !reduce && time - pointer.t < 1800;

      // Long-exposure trails: the field never fully clears, so motion leaves a wake.
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.fillStyle = reduce ? "#0a0907" : "rgba(10,9,7,0.34)";
      ctx.fillRect(0, 0, W, H);

      counts.fill(0);
      for (let i = 0; i < N; i++) {
        const ti = reduce ? t : ease(Math.min(1, Math.max(0, (t - delay[i]) / 0.65)));
        let tx = A.x[i] + (B.x[i] - A.x[i]) * ti;
        let ty = A.y[i] + (B.y[i] - A.y[i]) * ti;
        if (wob > 0 && !reduce) {
          const ph = phase[i];
          tx += Math.sin(sec * 0.9 + ph) * wob + (a === 0 ? Math.sin(sec * 0.3 + ty * 0.004) * wob * 1.4 : 0);
          ty += Math.cos(sec * 1.1 + ph * 1.3) * wob;
        }
        if (pointerLive) {
          const dx = px[i] - pointer.x, dy = py[i] - pointer.y;
          const d2 = dx * dx + dy * dy;
          if (d2 < 9000) {
            const push = (1 - d2 / 9000) * 38;
            const d = Math.sqrt(d2) + 0.001;
            tx += (dx / d) * push;
            ty += (dy / d) * push;
          }
        }
        px[i] += (tx - px[i]) * k;
        py[i] += (ty - py[i]) * k;
        const g = ti < 0.5 ? A.c[i] : B.c[i];
        buckets[g][counts[g]++] = i;
      }
      const sz = W < 700 ? 1.5 : 1.7;
      for (let g = 0; g < 4; g++) {
        ctx.fillStyle = PALETTE[g];
        const list = buckets[g];
        for (let j = 0, c = counts[g]; j < c; j++) ctx.fillRect(px[list[j]], py[list[j]], sz, sz);
      }

      // HUD + CSS hooks
      root.style.setProperty("--f", f.toFixed(3));
      const ent = ENTROPY[a] + (ENTROPY[b] - ENTROPY[a]) * t;
      if (entRef.current) entRef.current.textContent = ent.toFixed(2);
      if (barRef.current) barRef.current.style.transform = `scaleY(${(f / (F.length - 1)).toFixed(3)})`;
      const act = Math.round(f);
      if (act !== lastAct && actRef.current) {
        actRef.current.textContent = `${String(act).padStart(2, "0")} · ${ACTS[act]}`;
        lastAct = act;
      }

      if (running && (!reduce || Math.abs(target - f) > 0.001)) raf = requestAnimationFrame(frame);
    }

    const start = () => { if (!running) { running = true; raf = requestAnimationFrame(frame); } };
    const stop = () => { running = false; if (raf) cancelAnimationFrame(raf); raf = 0; };
    const onScroll = () => { if (running && !raf) raf = requestAnimationFrame(frame); };
    const onPointer = (e: PointerEvent) => { pointer.x = e.clientX; pointer.y = e.clientY; pointer.t = performance.now(); };
    const onResize = () => { resize(); onScroll(); };

    resize();
    const io = new IntersectionObserver(([e]) => (e.isIntersecting ? start() : stop()), { threshold: 0 });
    io.observe(root);
    const onVis = () => (document.hidden ? stop() : start());
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onResize);
    window.addEventListener("pointermove", onPointer, { passive: true });
    document.addEventListener("visibilitychange", onVis);
    const ro = new ResizeObserver(measure);
    ro.observe(root);

    return () => {
      stop();
      io.disconnect();
      ro.disconnect();
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onResize);
      window.removeEventListener("pointermove", onPointer);
      document.removeEventListener("visibilitychange", onVis);
    };
  }, []);

  return (
    <div ref={rootRef} className="relative" style={{ ["--f" as string]: 0 }}>
      {/* Pinned stage */}
      <div className="sticky top-0 h-dvh -mb-[100dvh] overflow-hidden" aria-hidden>
        <canvas ref={canvasRef} className="absolute inset-0 block" />
        <div className="absolute inset-0 pointer-events-none" style={{ opacity: "calc(1 - var(--f) * 1.6)" }}>
          {NOISE.map(([w, x, y], i) => (
            <span key={w} className={`noise-word absolute text-[11px] sm:text-xs tracking-widest ${y > 24 && y < 92 ? "hidden sm:inline" : ""}`}
              style={{ left: `${x}%`, top: `${y}%`, animationDelay: `${i * 0.37}s` }}>{w}</span>
          ))}
        </div>
        {/* Instrument readout */}
        <div className="absolute right-8 bottom-8 hidden sm:flex items-end gap-3 text-right num text-[10px] sm:text-[11px] tracking-[0.18em] uppercase text-lo">
          <div className="h-16 w-px bg-[var(--border-soft)] relative overflow-hidden">
            <div ref={barRef} className="absolute inset-0 origin-top bg-[var(--gold)]" style={{ transform: "scaleY(0)" }} />
          </div>
          <div className="space-y-1">
            <div><span ref={actRef}>00 · Ruido</span></div>
            <div>Entropía <span ref={entRef} className="text-hi">0.97</span></div>
          </div>
        </div>
      </div>

      {/* Narrative */}
      <section data-act="0" className="relative min-h-[150dvh] flex items-start pt-[30dvh] sm:items-center sm:pt-0">
        <div className="px-5 sm:px-10 lg:px-16 max-w-[44rem]">
          <p className="num text-[11px] tracking-[0.22em] text-flare uppercase">00 — Ruido</p>
          <h1 className="display mt-5 text-[3.1rem] sm:text-[5.6rem] lg:text-[7rem]">
            Te venden <span className="line-through decoration-[var(--flare)] decoration-2">certezas</span>.
            <br />
            Nosotros <em>medimos</em> dudas.
          </h1>
          <p className="mt-7 text-lg text-mid max-w-md leading-relaxed">
            Esto es lo que ves todos los días: fijas, cuotas seguras, grupos VIP. Ruido. Baja y mira qué queda cuando
            lo quitas.
          </p>
          <div className="mt-10 num text-[11px] tracking-[0.2em] uppercase text-lo flex items-center gap-3">
            <span className="inline-block h-8 w-px bg-[var(--text-lo)] scroll-cue" /> Desliza
          </div>
        </div>
      </section>

      <Act n="01" title="El juego" lines={["22 jugadores.", "90 minutos.", <>Ninguna corazonada sobrevive a <em>la muestra</em>.</>]}>
        Miles de eventos por partido: tiros, posesiones, presiones, errores. El modelo los cuenta todos, no solo los
        que salen en el resumen.
      </Act>

      <Act n="02" title="La percepción" lines={[<>49% no significa <em>«gana»</em>.</>]}>
        Significa que si este partido se jugara 100 veces, el local ganaría unas 49. Las otras 51 también existen, y
        cualquiera puede ser la de esta noche.
        <Legend />
      </Act>

      <Act n="03" title="La forma" lines={[<>El marcador más probable <em>casi nunca</em> pasa.</>]}>
        Cada resultado tiene su peso. Aquí, 1–0 es el más probable y aun así ocurre solo 13 de cada 100 veces. La
        densidad del polvo es la probabilidad.
      </Act>

      <Act n="04" title="La prueba" lines={[<>Decimos 60. <em>Pasa 60.</em></>]}>
        Medimos cada pronóstico contra lo que ocurrió y lo publicamos. Si el modelo se desvía de la diagonal, lo vas a
        ver antes que nadie.
        <Link href="/historial" className="mt-6 inline-flex items-center gap-2 num text-xs tracking-[0.18em] uppercase text-gold hover:underline underline-offset-4">
          Auditar el modelo →
        </Link>
      </Act>

      <section data-act="5" className="relative min-h-[130dvh] flex items-end sm:items-center pb-[16dvh] sm:pb-0">
        <div className="px-5 sm:px-10 lg:px-16 max-w-[46rem]">
          <p className="num text-[11px] tracking-[0.22em] text-gold uppercase">05 — Señal</p>
          <h2 className="display mt-5 text-[3rem] sm:text-[5rem] lg:text-[6.2rem]">
            No somos tipsters.
            <br />
            Somos la <em>objetividad</em> de los datos.
          </h2>
          <div className="mt-10 flex flex-wrap gap-3">
            <Link href="/acceso" className="btn-gold px-6 py-3.5 text-[15px]">Entrar gratis</Link>
            <Link href="/planes" className="btn-ghost px-6 py-3.5 text-[15px] bg-[rgba(10,9,7,0.5)]">Ver planes</Link>
          </div>
        </div>
      </section>
    </div>
  );
}

function Act({ n, title, lines, children }: { n: string; title: string; lines: React.ReactNode[]; children: React.ReactNode }) {
  return (
    <section data-act={Number(n)} className="relative min-h-[150dvh] flex items-end sm:items-center pb-[14dvh] sm:pb-0">
      <div className="px-5 sm:px-10 lg:px-16 max-w-[40rem]">
        <div className="rounded-2xl p-5 -m-5 sm:p-0 sm:m-0 bg-[rgba(10,9,7,0.72)] sm:bg-transparent backdrop-blur-sm sm:backdrop-blur-none">
          <p className="num text-[11px] tracking-[0.22em] text-gold uppercase">{n} — {title}</p>
          <h2 className="display mt-4 text-[2.6rem] sm:text-[4rem] lg:text-[4.6rem]">
            {lines.map((l, i) => (<span key={i} className="block">{l}</span>))}
          </h2>
          <div className="mt-6 text-base sm:text-lg text-mid leading-relaxed max-w-md">{children}</div>
        </div>
      </div>
    </section>
  );
}

function Legend() {
  const items = [
    ["var(--gold)", "49 local"],
    ["var(--text-hi)", "27 empate"],
    ["rgba(140,133,118,0.8)", "24 visita"],
  ];
  return (
    <span className="mt-5 flex flex-wrap gap-4 num text-xs">
      {items.map(([c, l]) => (
        <span key={l} className="inline-flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full" style={{ background: c }} />
          {l}
        </span>
      ))}
    </span>
  );
}
