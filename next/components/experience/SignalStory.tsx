"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";
import { buildFormations, CAMERAS, ENTROPY, stage, WOBBLE, type Formation } from "./formations";
import { makeSim, type LiveSim } from "./sims";

// 4 colors (dim, gold, flare, bone) × 3 depth bands (far, mid, near): fog without per-mark alpha changes.
const RGB = [[140, 133, 118, 0.6], [212, 175, 55, 1], [255, 59, 31, 1], [237, 230, 214, 1]] as const;
const PALETTE3D = RGB.flatMap(([r, g, b, a]) => [0.32, 0.72, 1].map((d) => `rgba(${r},${g},${b},${(a * d).toFixed(2)})`));

const ACTS = ["Ruido", "Fútbol", "MLB", "NBA", "Tenis", "La percepción", "La forma", "La prueba", "Señal"];
const NOISE = [
  ["FIJA 100%", 8, 18], ["CUOTA SEGURA", 62, 12], ["GRUPO VIP", 74, 70], ["NO FALLA", 14, 78],
  ["PARLEY DEL DÍA", 46, 86], ["+500% ESTE MES", 80, 38], ["CONFÍA EN MÍ", 30, 8], ["LA DE HOY ES FIJA", 56, 54],
  ["ASEGURADO", 4, 48], ["ÚLTIMOS CUPOS", 88, 88], ["MÉTODO INFALIBLE", 40, 30], ["100% VERIFICADO", 70, 24],
] as const;
const HUNDRED_ACT = 5;

const clamp01 = (x: number) => Math.min(1, Math.max(0, x));
const smooth = (a: number, b: number, x: number) => {
  const t = clamp01((x - a) / (b - a));
  return t * t * (3 - 2 * t);
};
const ease = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2);

/**
 * Noise → signal across sports. One pinned canvas; scroll drives a continuous formation index
 * f ∈ [0, 8]. Scroll velocity feeds inertia (particles lag behind the scroll) and, past a
 * threshold, vertical motion streaks. Canvas 2D, typed arrays, color-batched fillRect: <16ms at 6.5k marks.
 */
export function SignalStory() {
  const rootRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const entRef = useRef<HTMLSpanElement>(null);
  const railRef = useRef<HTMLOListElement>(null);
  const countRef = useRef<HTMLSpanElement>(null);
  const navRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const root = rootRef.current!;
    const canvas = canvasRef.current!;
    const ctx = canvas.getContext("2d", { alpha: false })!;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const sections = Array.from(root.querySelectorAll<HTMLElement>("[data-act]"));

    let W = 0, H = 0, dpr = 1, N = 0, CX = 0, CY = 0, FOV = 900, ZK = 1;
    let F: Formation[] = [];
    let SIM: (LiveSim | null)[] = [];
    let lastT = 0;
    // World state (smoothed toward targets) + last projected screen positions.
    let wx = new Float32Array(0), wy = new Float32Array(0), wz = new Float32Array(0);
    let sx = new Float32Array(0), sy = new Float32Array(0), ss = new Float32Array(0), psy = new Float32Array(0);
    let ux = new Float32Array(0), uy = new Float32Array(0);
    let delay = new Float32Array(0), phase = new Float32Array(0);
    let buckets: Uint32Array[] = [];
    const counts = new Uint32Array(12);
    let tops: number[] = [], heights: number[] = [];
    let f = 0, raf = 0, running = false, lastAct = -1;
    let lastY = window.scrollY, vel = 0;
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
      const st = stage(W, H);
      CX = st.cx; CY = st.cy; FOV = Math.max(W, H) * 1.05;
      ZK = W < 700 ? 0.8 : 1; // phones: pull the camera back so tilted fields stay on screen
      const cores = navigator.hardwareConcurrency || 4;
      const nextN = W < 700 || cores <= 4 ? 3400 : 6500;
      const first = N === 0;
      F = buildFormations(nextN, W, H);
      SIM = F.map((fm, i) => makeSim(fm, 11 + i));
      if (nextN !== N) {
        N = nextN;
        wx = new Float32Array(N); wy = new Float32Array(N); wz = new Float32Array(N);
        sx = new Float32Array(N); sy = new Float32Array(N); ss = new Float32Array(N); psy = new Float32Array(N);
        ux = new Float32Array(N); uy = new Float32Array(N);
        delay = new Float32Array(N); phase = new Float32Array(N);
        for (let i = 0; i < N; i++) { delay[i] = Math.random() * 0.35; phase[i] = Math.random() * Math.PI * 2; }
        buckets = Array.from({ length: 12 }, () => new Uint32Array(N));
      }
      if (first || reduce) { wx.set(F[0].x); wy.set(F[0].y); wz.set(F[0].z); }
      measure();
    }

    function progress() {
      const c = window.scrollY + H * 0.5;
      let idx = 0;
      for (let i = 0; i < sections.length; i++) if (c >= tops[i]) idx = i;
      const p = (c - tops[idx]) / Math.max(1, heights[idx]);
      return {
        f: Math.min(F.length - 1, idx + (idx < F.length - 1 ? smooth(0.52, 0.98, p) : 0)),
        idx,
        p,
      };
    }

    /** Camera for formation `i` at act-local phase `ph` (0..1), time `sec`. */
    function cam(i: number, ph: number, sec: number) {
      const c = CAMERAS[i];
      const drift = reduce || !c.spinRate ? 0 : i === 0 ? sec * c.spinRate : Math.sin(sec * c.spinRate) * 0.6;
      return { tilt: c.tilt, yaw: c.yaw + c.yawSweep * ((reduce ? 0.5 : ph) - 0.5), spin: c.spin + drift, zoom: c.zoom };
    }

    function frame(time: number) {
      raf = 0;
      const pr = progress();
      f = reduce ? Math.round(pr.f) : pr.f;
      const a = Math.floor(f);
      const b = Math.min(F.length - 1, a + 1);
      const t = f - a;
      const A = F[a], B = F[b];
      const wob = reduce ? 0 : WOBBLE[a] + (WOBBLE[b] - WOBBLE[a]) * t;
      const k = reduce ? 1 : 0.11;
      const sec = time * 0.001;
      const dt = lastT ? Math.min(0.05, Math.max(0, sec - lastT)) : 0.016;
      lastT = sec;
      // Live simulations: only the two formations currently on screen are stepped.
      const SA = reduce ? null : SIM[a];
      const SB = reduce || b === a ? null : SIM[b];
      SA?.step(sec, dt);
      SB?.step(sec, dt);
      const pointerLive = !reduce && time - pointer.t < 1800;

      // Camera: interpolate the act's camera (swept by scroll) toward the next act's opening pose.
      const phA = pr.idx === a ? clamp01(pr.p) : pr.idx > a ? 1 : 0;
      const ca = cam(a, phA, sec), cb = cam(b, 0, sec);
      const ct = ease(t);
      const tilt = ca.tilt + (cb.tilt - ca.tilt) * ct;
      const yaw = ca.yaw + (cb.yaw - ca.yaw) * ct;
      const spin = ca.spin + (cb.spin - ca.spin) * ct;
      const zoom = (ca.zoom + (cb.zoom - ca.zoom) * ct) * ZK;
      const cY = Math.cos(yaw), sY = Math.sin(yaw);
      const cT = Math.cos(tilt), sT = Math.sin(tilt);
      const cS = Math.cos(spin), sS = Math.sin(spin);

      // Scroll velocity (px/frame, smoothed) → inertia + streaks.
      const y = window.scrollY;
      vel += ((y - lastY) - vel) * 0.25;
      lastY = y;
      const streak = reduce ? 0 : Math.min(1, Math.abs(vel) / 38);

      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.fillStyle = reduce ? "#0a0907" : `rgba(10,9,7,${0.36 - streak * 0.16})`;
      ctx.fillRect(0, 0, W, H);

      counts.fill(0);
      for (let i = 0; i < N; i++) {
        const ti = reduce ? t : ease(clamp01((t - delay[i]) / 0.65));
        let axp = A.x[i], ayp = A.y[i], azp = A.z[i];
        let bxp = B.x[i], byp = B.y[i], bzp = B.z[i];
        const ga = A.g[i], gb = B.g[i];
        if (SA && ga >= 0) { axp += SA.ox[ga]; ayp += SA.oy[ga]; azp = azp * SA.sz[ga] + SA.oz[ga]; }
        if (SB && gb >= 0) { bxp += SB.ox[gb]; byp += SB.oy[gb]; bzp = bzp * SB.sz[gb] + SB.oz[gb]; }
        let tx = axp + (bxp - axp) * ti;
        let ty = ayp + (byp - ayp) * ti;
        const tz = azp + (bzp - azp) * ti;
        // Agents (players, ball) track their target tightly so passes read crisp; scenery eases.
        const kk = (SA && ga >= 0 && ti < 0.5) || (SB && gb >= 0 && ti >= 0.5) ? Math.max(k, 0.32) : k;
        if (wob) {
          const ph = phase[i];
          tx += Math.sin(sec * 0.9 + ph) * wob + (a === 0 ? Math.sin(sec * 0.3 + ty * 0.004) * wob * 1.4 : 0);
          ty += Math.cos(sec * 1.1 + ph * 1.3) * wob;
        }
        wx[i] += (tx - wx[i]) * kk;
        wy[i] += (ty - wy[i]) * kk;
        wz[i] += (tz - wz[i]) * kk;

        // Project: in-plane yaw → tilt about X → spin about Y → perspective.
        const x1 = wx[i] * cY - wy[i] * sY;
        const y1 = wx[i] * sY + wy[i] * cY;
        const y2 = y1 * cT + wz[i] * sT;
        const z2 = -y1 * sT + wz[i] * cT;
        const x3 = x1 * cS + z2 * sS;
        const z3 = -x1 * sS + z2 * cS;
        const d = FOV + z3;
        if (d < FOV * 0.15) { ss[i] = 0; continue; } // behind the lens
        const sc = (FOV / d) * zoom;
        psy[i] = sy[i];
        let px = CX + x3 * sc;
        let py = CY + y2 * sc - vel * (0.6 + delay[i] * 2.2); // particles trail the scroll like a fluid

        if (pointerLive) {
          const dx = px - pointer.x, dy = py - pointer.y;
          const d2 = dx * dx + dy * dy;
          let fx = 0, fy = 0;
          if (d2 < 9000) {
            const push = (1 - d2 / 9000) * 38;
            const dd = Math.sqrt(d2) + 0.001;
            fx = (dx / dd) * push;
            fy = (dy / dd) * push;
          }
          ux[i] += (fx - ux[i]) * 0.15;
          uy[i] += (fy - uy[i]) * 0.15;
        } else if (ux[i] || uy[i]) {
          ux[i] *= 0.9;
          uy[i] *= 0.9;
        }
        px += ux[i];
        py += uy[i];
        sx[i] = px;
        sy[i] = py;
        ss[i] = sc;

        // Depth band: near / mid / far → brightness (fog). 4 colors × 3 bands = 12 batches.
        const depth = sc / zoom; // fog follows true depth, not zoom (ZK included)
        const band = depth > 1.12 ? 2 : depth > 0.9 ? 1 : 0;
        const g = (ti < 0.5 ? A.c[i] : B.c[i]) * 3 + band;
        buckets[g][counts[g]++] = i;
      }

      // Streaks: inertia is vertical, so a y-stretched rect reads as a motion trail on the fast fillRect path.
      const base = W < 700 ? 1.4 : 1.6;
      const stretch = streak > 0.08 ? 1 + streak * 7 : 0;
      for (let g = 0; g < 12; g++) {
        const c = counts[g];
        if (!c) continue;
        const isBall = g >= 6 && g <= 8; // flare color = ball / noise flecks: drawn larger, with a halo
        if (isBall && !stretch) {
          ctx.fillStyle = "rgba(255,59,31,0.12)";
          const list = buckets[g];
          for (let j = 0; j < c; j += 3) {
            const i = list[j];
            const hs = base * 4.5 * Math.min(ss[i], 2);
            ctx.fillRect(sx[i] - hs / 2, sy[i] - hs / 2, hs, hs);
          }
        }
        ctx.fillStyle = PALETTE3D[g];
        const list = buckets[g];
        const mul = isBall ? 1.7 : 1;
        for (let j = 0; j < c; j++) {
          const i = list[j];
          const sz = Math.min(5, base * mul * Math.min(ss[i], 2.2));
          if (stretch) {
            const dy = Math.max(-70, Math.min(70, (sy[i] - psy[i]) * stretch));
            ctx.fillRect(sx[i], dy > 0 ? sy[i] - dy : sy[i], sz, Math.max(sz, Math.abs(dy)));
          } else ctx.fillRect(sx[i], sy[i], sz, sz);
        }
      }

      // DOM hooks (no React re-render on scroll).
      root.style.setProperty("--f", f.toFixed(3));
      const ent = ENTROPY[a] + (ENTROPY[b] - ENTROPY[a]) * t;
      if (entRef.current) entRef.current.textContent = ent.toFixed(2);
      if (countRef.current) {
        const local = pr.idx === HUNDRED_ACT ? smooth(0.05, 0.45, pr.p) : pr.idx > HUNDRED_ACT ? 1 : 0;
        countRef.current.textContent = String(Math.round(local * 49)).padStart(2, "0");
      }
      if (navRef.current) {
        const out = pr.idx === F.length - 1 ? smooth(0.45, 0.8, pr.p) : 0;
        navRef.current.style.opacity = String(1 - out);
        navRef.current.style.visibility = out > 0.99 ? "hidden" : "visible";
      }
      const act = Math.round(f);
      if (act !== lastAct && railRef.current) {
        railRef.current.querySelectorAll("li").forEach((li, i) => li.toggleAttribute("data-active", i === act));
        lastAct = act;
      }

      const settling = Math.abs(vel) > 0.05;
      if (running && (!reduce || settling)) raf = requestAnimationFrame(frame);
    }

    const start = () => { if (!running) { running = true; lastY = window.scrollY; raf = requestAnimationFrame(frame); } };
    const stop = () => {
      running = false;
      if (raf) cancelAnimationFrame(raf);
      raf = 0;
      if (navRef.current) navRef.current.style.visibility = "hidden"; // story off-screen → no rail
    };
    const onScroll = () => { if (running && !raf) raf = requestAnimationFrame(frame); };
    const onPointer = (e: PointerEvent) => { pointer.x = e.clientX; pointer.y = e.clientY; pointer.t = performance.now(); };
    const onResize = () => { resize(); onScroll(); };

    resize();
    const io = new IntersectionObserver(([e]) => (e.isIntersecting ? start() : stop()), { threshold: 0 });
    io.observe(root);

    // Mask-reveal headings as each act enters.
    const reveal = new IntersectionObserver(
      (entries) => entries.forEach((e) => e.isIntersecting && e.target.classList.add("is-in")),
      { rootMargin: "0px 0px -25% 0px" },
    );
    sections.forEach((s) => reveal.observe(s));

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
      reveal.disconnect();
      ro.disconnect();
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onResize);
      window.removeEventListener("pointermove", onPointer);
      document.removeEventListener("visibilitychange", onVis);
    };
  }, []);

  function jump(i: number) {
    const s = rootRef.current?.querySelectorAll<HTMLElement>("[data-act]")[i];
    if (!s) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const top = s.getBoundingClientRect().top + window.scrollY;
    window.scrollTo({ top: top + s.offsetHeight * 0.3 - window.innerHeight * 0.5, behavior: reduce ? "auto" : "smooth" });
  }

  return (
    <div ref={rootRef} className="relative" style={{ ["--f" as string]: 0 }}>
      {/* Pinned stage */}
      <div className="sticky top-0 h-dvh overflow-hidden" aria-hidden>
        <canvas ref={canvasRef} className="absolute inset-0 block" />
        <div className="absolute inset-0 pointer-events-none" style={{ opacity: "calc(1 - var(--f) * 1.6)" }}>
          {NOISE.map(([w, x, y], i) => (
            <span key={w} className={`noise-word absolute text-[11px] sm:text-xs tracking-widest ${y > 24 && y < 92 ? "hidden sm:inline" : ""}`}
              style={{ left: `${x}%`, top: `${y}%`, animationDelay: `${i * 0.37}s` }}>{w}</span>
          ))}
        </div>
      </div>

      {/* Act rail: where you are in the story, and a way to jump */}
      <nav ref={navRef} aria-label="Actos" className="hidden md:block fixed right-6 top-1/2 -translate-y-1/2 z-30 transition-opacity">
        <ol ref={railRef} className="act-rail flex flex-col items-end gap-2.5">
          {ACTS.map((a, i) => (
            <li key={a} data-active={i === 0 ? "" : undefined}>
              <button type="button" onClick={() => jump(i)} className="group flex items-center gap-3 py-0.5" aria-label={`Ir a ${a}`}>
                <span className="act-label num text-[10px] tracking-[0.18em] uppercase">{String(i).padStart(2, "0")} {a}</span>
                <span className="act-tick block h-px" />
              </button>
            </li>
          ))}
        </ol>
        <p className="mt-6 text-right num text-[10px] tracking-[0.18em] uppercase text-lo">
          Entropía <span ref={entRef} className="text-hi">0.97</span>
        </p>
      </nav>

      {/* Narrative: pulled up over the stage so the sticky box never overflows the story */}
      <div className="-mt-[100dvh]">
        <section data-act="0" className="relative min-h-[150dvh] flex items-start pt-[30dvh] sm:items-center sm:pt-0">
          <div className="px-5 sm:px-10 lg:px-16 max-w-[46rem]">
            <p className="num text-[11px] tracking-[0.22em] text-flare uppercase">00 — Ruido</p>
            <h1 className="display mt-5 text-[3.1rem] sm:text-[5.6rem] lg:text-[7rem]">
              <Line>Te venden <span className="line-through decoration-[var(--flare)] decoration-2">certezas</span>.</Line>
              <Line>Nosotros <em>medimos</em> dudas.</Line>
            </h1>
            <p className="mt-7 text-lg text-mid max-w-md leading-relaxed">
              Fútbol, béisbol y lo que venga: siempre las mismas fijas, cuotas seguras y grupos VIP. Ruido. Baja y mira
              qué queda cuando lo quitas.
            </p>
            <SportChips />
            <div className="mt-10 num text-[11px] tracking-[0.2em] uppercase text-lo flex items-center gap-3">
              <span className="inline-block h-8 w-px bg-[var(--text-lo)] scroll-cue" /> Desliza
            </div>
          </div>
        </section>

        <Act n="01" title="Fútbol" word="FÚTBOL" status="Activo" lines={["22 jugadores.", "90 minutos.", <>Ninguna corazonada sobrevive a <em>la muestra</em>.</>]}>
          Tiros, posesiones, presiones y errores: el modelo cuenta todos los eventos, no solo los del resumen.
        </Act>

        <Act n="02" title="MLB" word="BÉISBOL" status="Activo" short lines={["162 juegos.", <>Cada lanzamiento, <em>un dato</em>.</>]}>
          Abridores, bullpen, parque y clima convertidos en carreras esperadas. Mismo método, otro deporte.
        </Act>

        <Act n="03" title="NBA" word="BASKET" status="Pronto" short lines={["100 posesiones.", <>La ventaja vive en <em>el ritmo</em>.</>]}>
          Eficiencia por posesión, rotaciones y descanso. El modelo de baloncesto está en entrenamiento.
        </Act>

        <Act n="04" title="Tenis" word="TENIS" status="Pronto" short lines={["Punto a punto,", <>el saque <em>se mide</em>.</>]}>
          Probabilidad de quiebre en cada juego, superficie y fatiga acumulada. Llega después del baloncesto.
        </Act>

        <Act n="05" title="La percepción" lines={[<>49% no significa <em>«gana»</em>.</>]}
          aside={<p className="num text-gold leading-none text-[5.5rem] sm:text-[8rem] tracking-tight" aria-hidden><span ref={countRef}>00</span><span className="text-lo text-[0.35em] align-top ml-2">/100</span></p>}>
          Si este partido se jugara 100 veces, el local ganaría unas 49. Las otras 51 también existen, y cualquiera puede
          ser la de esta noche.
          <Legend />
        </Act>

        <Act n="06" title="La forma" lines={[<>El marcador más probable <em>casi nunca</em> pasa.</>]}>
          Aquí 1–0 es el más probable y aun así ocurre solo 13 de cada 100 veces. La densidad del polvo es la probabilidad.
        </Act>

        <Act n="07" title="La prueba" lines={[<>Decimos 60. <em>Pasa 60.</em></>]}>
          Medimos cada pronóstico contra lo que ocurrió y lo publicamos. Si el modelo se desvía de la diagonal, lo vas a
          ver antes que nadie.
          <Link href="/historial" className="mt-6 inline-flex items-center gap-2 num text-xs tracking-[0.18em] uppercase text-gold hover:underline underline-offset-4">
            Auditar el modelo →
          </Link>
        </Act>

        <section data-act="8" className="relative min-h-[130dvh] flex items-end sm:items-center pb-[16dvh] sm:pb-0">
          <div className="px-5 sm:px-10 lg:px-16 max-w-[46rem]">
            <p className="num text-[11px] tracking-[0.22em] text-gold uppercase">08 — Señal</p>
            <h2 className="display mt-5 text-[3rem] sm:text-[5rem] lg:text-[6.2rem]">
              <Line>No somos tipsters.</Line>
              <Line>Somos la <em>objetividad</em></Line>
              <Line>de los datos.</Line>
            </h2>
            <div className="mt-10 flex flex-wrap gap-3">
              <Link href="/acceso" className="btn-gold px-6 py-3.5 text-[15px]">Entrar gratis</Link>
              <Link href="/planes" className="btn-ghost px-6 py-3.5 text-[15px] bg-[rgba(10,9,7,0.5)]">Ver planes</Link>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

/** Masked line: slides up from behind its own baseline when the section enters. */
function Line({ children }: { children: React.ReactNode }) {
  return (
    <span className="reveal-line block">
      <span className="block">{children}</span>
    </span>
  );
}

function Act({
  n, title, lines, children, word, status, short, aside,
}: {
  n: string; title: string; lines: React.ReactNode[]; children: React.ReactNode;
  word?: string; status?: "Activo" | "Pronto"; short?: boolean; aside?: React.ReactNode;
}) {
  return (
    <section data-act={Number(n)}
      className={`relative ${short ? "min-h-[120dvh]" : "min-h-[150dvh]"} flex items-end sm:items-center pb-[14dvh] sm:pb-0 overflow-hidden`}>
      {word && (
        <span aria-hidden className="sport-word display pointer-events-none select-none absolute left-[-0.04em] top-[12%] sm:top-1/2 sm:-translate-y-1/2 text-[24vw] sm:text-[19vw] leading-none whitespace-nowrap">
          {word}
        </span>
      )}
      <div className="relative px-5 sm:px-10 lg:px-16 max-w-[40rem]">
        <div className="rounded-2xl p-5 -m-5 sm:p-0 sm:m-0 bg-[rgba(10,9,7,0.72)] sm:bg-transparent backdrop-blur-sm sm:backdrop-blur-none">
          {aside}
          <p className="num text-[11px] tracking-[0.22em] text-gold uppercase flex items-center gap-3">
            {n} — {title}
            {status && (
              <span className={`rounded-full border px-2 py-0.5 text-[9px] tracking-[0.2em] ${status === "Activo" ? "border-[var(--border-glass)] text-gold" : "border-line text-lo"}`}>
                {status === "Activo" ? "● Activo" : "Pronto"}
              </span>
            )}
          </p>
          <h2 className="display mt-4 text-[2.6rem] sm:text-[4rem] lg:text-[4.6rem]">
            {lines.map((l, i) => (<Line key={i}>{l}</Line>))}
          </h2>
          <div className="mt-6 text-base sm:text-lg text-mid leading-relaxed max-w-md">{children}</div>
        </div>
      </div>
    </section>
  );
}

function SportChips() {
  const sports: [string, boolean][] = [["Fútbol", true], ["MLB", true], ["NBA", false], ["Tenis", false]];
  return (
    <ul className="mt-6 flex flex-wrap gap-2 num text-[11px] tracking-[0.14em] uppercase" aria-label="Deportes">
      {sports.map(([s, live]) => (
        <li key={s} className={`rounded-full border px-3 py-1 ${live ? "border-[var(--border-glass)] text-hi" : "border-line text-lo"}`}>
          {live && <span className="text-gold mr-1.5" aria-hidden>●</span>}
          {s}
          {!live && <span className="sr-only"> (próximamente)</span>}
        </li>
      ))}
    </ul>
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
