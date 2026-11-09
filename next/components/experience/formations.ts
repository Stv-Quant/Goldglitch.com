/**
 * Particle formations for the landing story. Each formation maps N particles to target
 * positions (CSS px) and a color index. The story interpolates between consecutive formations.
 *
 *   0 RUIDO        tipster noise: random scatter, red flares
 *   1 EL JUEGO     the pitch: lines + 22 player clusters
 *   2 PERCEPCIÓN   100 versions of the match: 49 / 27 / 24
 *   3 LA FORMA     score matrix as dust density (Poisson λ 1.46 / 0.95)
 *   4 LA PRUEBA    calibration: clusters on the diagonal
 *   5 SEÑAL        the Goldglitch mark
 */

export const COLOR = { dim: 0, gold: 1, flare: 2, bone: 3 } as const;
export const PALETTE = ["rgba(140,133,118,0.55)", "#d4af37", "#ff3b1f", "#ede6d6"];

/** Visual entropy per formation: drives wobble amplitude and the HUD reading. */
export const ENTROPY = [0.97, 0.62, 0.38, 0.21, 0.09, 0.03];
export const WOBBLE = [26, 2.4, 1.6, 1.3, 1.1, 0.7];

export type Formation = { x: Float32Array; y: Float32Array; c: Uint8Array };
type Box = { cx: number; cy: number; s: number; w: number; h: number };

function rng(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function gauss(r: () => number) {
  return Math.sqrt(-2 * Math.log(r() + 1e-9)) * Math.cos(2 * Math.PI * r());
}

function alloc(n: number): Formation {
  return { x: new Float32Array(n), y: new Float32Array(n), c: new Uint8Array(n) };
}

/** Where formations live: right half on desktop (text on the left), upper area on mobile. */
export function stage(w: number, h: number): Box {
  if (w >= 900) return { cx: w * 0.66, cy: h * 0.52, s: Math.min(w * 0.5, h * 0.74), w, h };
  return { cx: w * 0.5, cy: h * 0.33, s: Math.min(w * 0.88, h * 0.46), w, h };
}

function noise(n: number, b: Box): Formation {
  const f = alloc(n);
  const r = rng(11);
  for (let i = 0; i < n; i++) {
    f.x[i] = -0.1 * b.w + r() * b.w * 1.2;
    f.y[i] = -0.1 * b.h + r() * b.h * 1.2;
    const k = r();
    f.c[i] = k < 0.18 ? COLOR.flare : k < 0.24 ? COLOR.bone : COLOR.dim;
  }
  return f;
}

function pitch(n: number, b: Box): Formation {
  const f = alloc(n);
  const r = rng(23);
  const W = b.s * 1.05;
  const H = W * (68 / 105);
  const x0 = b.cx - W / 2;
  const y0 = b.cy - H / 2;
  const sx = (m: number) => x0 + (m / 105) * W;
  const sy = (m: number) => y0 + (m / 68) * H;
  type Seg = [number, number, number, number];
  const segs: Seg[] = [
    [0, 0, 105, 0], [105, 0, 105, 68], [105, 68, 0, 68], [0, 68, 0, 0], [52.5, 0, 52.5, 68],
    [0, 13.85, 16.5, 13.85], [16.5, 13.85, 16.5, 54.15], [16.5, 54.15, 0, 54.15],
    [105, 13.85, 88.5, 13.85], [88.5, 13.85, 88.5, 54.15], [88.5, 54.15, 105, 54.15],
    [0, 24.85, 5.5, 24.85], [5.5, 24.85, 5.5, 43.15], [5.5, 43.15, 0, 43.15],
    [105, 24.85, 99.5, 24.85], [99.5, 24.85, 99.5, 43.15], [99.5, 43.15, 105, 43.15],
  ];
  const segLen = segs.map(([a, c, d, e]) => Math.hypot(d - a, e - c));
  const circleLen = 2 * Math.PI * 9.15;
  const total = segLen.reduce((s, v) => s + v, 0) + circleLen;

  const players = [
    // home 4-3-3 (gold), away 4-4-2 (bone)
    [5, 34], [18, 10], [16, 26], [16, 42], [18, 58], [32, 18], [30, 34], [32, 50], [44, 12], [46, 34], [44, 56],
    [100, 34], [86, 12], [88, 28], [88, 40], [86, 56], [72, 10], [70, 27], [70, 41], [72, 58], [60, 26], [60, 42],
  ];
  const nPlayers = Math.floor(n * 0.24);
  const perPlayer = Math.floor(nPlayers / players.length);
  let i = 0;
  for (let p = 0; p < players.length; p++) {
    for (let k = 0; k < perPlayer; k++, i++) {
      const a = r() * Math.PI * 2;
      const rad = Math.sqrt(r()) * b.s * 0.018;
      f.x[i] = sx(players[p][0]) + Math.cos(a) * rad;
      f.y[i] = sy(players[p][1]) + Math.sin(a) * rad;
      f.c[i] = p < 11 ? COLOR.gold : COLOR.bone;
    }
  }
  for (; i < n; i++) {
    let d = r() * total;
    let placed = false;
    for (let s = 0; s < segs.length; s++) {
      if (d <= segLen[s]) {
        const t = d / segLen[s];
        const [a, c, e, g] = segs[s];
        f.x[i] = sx(a + (e - a) * t) + gauss(r) * 0.8;
        f.y[i] = sy(c + (g - c) * t) + gauss(r) * 0.8;
        placed = true;
        break;
      }
      d -= segLen[s];
    }
    if (!placed) {
      const a = (d / circleLen) * Math.PI * 2;
      f.x[i] = sx(52.5 + Math.cos(a) * 9.15);
      f.y[i] = sy(34 + Math.sin(a) * 9.15);
    }
    f.c[i] = COLOR.dim;
  }
  return f;
}

function hundred(n: number, b: Box): Formation {
  const f = alloc(n);
  const r = rng(37);
  const size = b.s * 0.86;
  const cell = size / 10;
  const x0 = b.cx - size / 2;
  const y0 = b.cy - size / 2;
  for (let i = 0; i < n; i++) {
    const k = i % 100; // cell index; reading order = left→right, top→bottom
    const col = k % 10;
    const row = Math.floor(k / 10);
    const a = r() * Math.PI * 2;
    const rad = Math.sqrt(r()) * cell * 0.3;
    f.x[i] = x0 + (col + 0.5) * cell + Math.cos(a) * rad;
    f.y[i] = y0 + (row + 0.5) * cell + Math.sin(a) * rad;
    f.c[i] = k < 49 ? COLOR.gold : k < 76 ? COLOR.bone : COLOR.dim;
  }
  return f;
}

function poisson(k: number, l: number) {
  let f = 1;
  for (let i = 2; i <= k; i++) f *= i;
  return (Math.exp(-l) * l ** k) / f;
}

function matrix(n: number, b: Box): Formation {
  const f = alloc(n);
  const r = rng(53);
  const G = 6;
  const size = b.s * 0.82;
  const cell = size / G;
  const x0 = b.cx - size / 2;
  const y0 = b.cy - size / 2;
  const p: number[] = [];
  let sum = 0;
  for (let h = 0; h < G; h++) for (let a = 0; a < G; a++) { const v = poisson(h, 1.46) * poisson(a, 0.95); p.push(v); sum += v; }
  const max = Math.max(...p);
  // Cumulative distribution for particle allocation; a floor keeps empty cells faintly visible.
  const w = p.map((v) => v / sum + 0.004);
  const ws = w.reduce((s, v) => s + v, 0);
  const cdf: number[] = [];
  w.reduce((acc, v) => (cdf.push((acc + v) / ws), acc + v), 0);
  for (let i = 0; i < n; i++) {
    const u = r();
    let k = 0;
    while (k < cdf.length - 1 && u > cdf[k]) k++;
    const h = Math.floor(k / G);
    const a = k % G;
    f.x[i] = x0 + (a + 0.07 + r() * 0.86) * cell;
    f.y[i] = y0 + (h + 0.07 + r() * 0.86) * cell;
    const rel = p[k] / max;
    f.c[i] = rel > 0.98 ? COLOR.bone : rel > 0.42 ? COLOR.gold : COLOR.dim;
  }
  return f;
}

function calibration(n: number, b: Box): Formation {
  const f = alloc(n);
  const r = rng(71);
  const size = b.s * 0.8;
  const x0 = b.cx - size / 2;
  const y0 = b.cy + size / 2;
  const bins = Array.from({ length: 10 }, (_, k) => {
    const pred = (k + 0.5) / 10;
    const obs = pred + (((k * 37) % 7) - 3) * 0.008;
    return { pred, obs, n: 40 + ((k * 53) % 90) };
  });
  const totalN = bins.reduce((s, v) => s + v.n, 0);
  const nAxes = Math.floor(n * 0.12);
  const nDiag = Math.floor(n * 0.16);
  let i = 0;
  for (; i < nAxes; i++) {
    const t = r();
    if (i % 2) { f.x[i] = x0 + t * size; f.y[i] = y0; } else { f.x[i] = x0; f.y[i] = y0 - t * size; }
    f.c[i] = COLOR.dim;
  }
  for (let k = 0; k < nDiag; k++, i++) {
    const t = Math.floor(r() * 40) / 40 + r() * 0.008; // dashed diagonal
    f.x[i] = x0 + t * size;
    f.y[i] = y0 - t * size;
    f.c[i] = COLOR.bone;
  }
  const rest = n - i;
  for (let k = 0; k < rest; k++, i++) {
    let u = r() * totalN;
    let bi = 0;
    while (bi < 9 && u > bins[bi].n) { u -= bins[bi].n; bi++; }
    const bin = bins[bi];
    const spread = size * 0.012 * Math.sqrt(bin.n / 60);
    f.x[i] = x0 + bin.pred * size + gauss(r) * spread;
    f.y[i] = y0 - bin.obs * size + gauss(r) * spread;
    f.c[i] = COLOR.gold;
  }
  return f;
}

function mark(n: number, b: Box): Formation {
  const f = alloc(n);
  const r = rng(97);
  const R = b.s * 0.36;
  const bars = [
    { x: -0.26, top: 0.1, h: 0.34, c: COLOR.dim },
    { x: -0.04, top: -0.14, h: 0.58, c: COLOR.gold },
    { x: 0.18, top: -0.38, h: 0.82, c: COLOR.gold },
  ];
  const bw = 0.15;
  for (let i = 0; i < n; i++) {
    const k = r();
    if (k < 0.42) {
      const a = r() * Math.PI * 2;
      const rr = R + gauss(r) * 1.2;
      f.x[i] = b.cx + Math.cos(a) * rr;
      f.y[i] = b.cy + Math.sin(a) * rr;
      f.c[i] = COLOR.gold;
    } else if (k < 0.55) {
      const a = r() * Math.PI * 2;
      f.x[i] = b.cx + Math.cos(a) * R * 0.76;
      f.y[i] = b.cy + Math.sin(a) * R * 0.76;
      f.c[i] = COLOR.dim;
    } else {
      const bar = bars[Math.floor(r() * 3)];
      f.x[i] = b.cx + (bar.x + r() * bw) * R;
      f.y[i] = b.cy + (bar.top + r() * bar.h) * R;
      f.c[i] = bar.c;
    }
  }
  return f;
}

export function buildFormations(n: number, w: number, h: number): Formation[] {
  const b = stage(w, h);
  return [noise(n, b), pitch(n, b), hundred(n, b), matrix(n, b), calibration(n, b), mark(n, b)];
}
