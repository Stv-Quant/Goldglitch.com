/**
 * Particle formations for the landing story. Each formation maps N particles to target
 * positions (CSS px) and a color index. The story interpolates between consecutive formations.
 *
 *   0 RUIDO        tipster noise: random scatter, red flares
 *   1 FÚTBOL       the pitch: lines + 22 player clusters
 *   2 MLB          the diamond: bases, foul lines, outfield arc, 9 fielders + batter
 *   3 NBA          the court: keys, arcs, 10 players
 *   4 TENIS        the court + the ball's arc over the net
 *   5 PERCEPCIÓN   100 versions of the match: 49 / 27 / 24
 *   6 LA FORMA     score matrix as dust density (Poisson λ 1.46 / 0.95)
 *   7 LA PRUEBA    calibration: clusters on the diagonal
 *   8 SEÑAL        the Goldglitch mark
 */

export const COLOR = { dim: 0, gold: 1, flare: 2, bone: 3 } as const;
export const PALETTE = ["rgba(140,133,118,0.55)", "#d4af37", "#ff3b1f", "#ede6d6"];

/** Visual entropy per formation: drives wobble amplitude and the HUD reading. */
export const ENTROPY = [0.97, 0.66, 0.6, 0.55, 0.5, 0.38, 0.21, 0.09, 0.03];
export const WOBBLE = [26, 2.4, 2.2, 2.2, 2.2, 1.6, 1.3, 1.1, 0.7];

/** World-space formation: x/y in the stage plane (px, centered on the stage), z = depth (+ away). */
export type Formation = {
  x: Float32Array; y: Float32Array; z: Float32Array; c: Uint8Array;
  /** Live-simulation group per particle (agent/column/bin index), -1 = static. */
  g: Int16Array;
  sim?: SimSpec;
};

export type Agent = { x: number; y: number; team: number }; // team 0 gold, 1 bone, 2 ball
export type SimSpec = {
  kind: "football" | "baseball" | "basketball" | "tennis" | "columns" | "towers" | "bins";
  scale: number;
  agents?: Agent[];
  pts?: Record<string, [number, number]>;
  land?: [number, number][];
  groups?: number;
};

/**
 * Camera per act. tilt: rotation about the screen X axis (ground seen from the stands);
 * yaw: in-plane orbit, swept across the act by scroll (yawSweep); spin: rotation about the
 * vertical axis after tilting (globe/coin turn), with a slow time drift (spinRate rad/s).
 */
export type Camera = { tilt: number; yaw: number; yawSweep: number; spin: number; spinRate: number; zoom: number };
export const CAMERAS: Camera[] = [
  { tilt: 0, yaw: 0, yawSweep: 0, spin: 0, spinRate: 0.07, zoom: 1.0 },         // 0 ruido: volumetric cloud turning
  { tilt: 0.98, yaw: -0.22, yawSweep: 0.44, spin: 0, spinRate: 0, zoom: 1.28 },  // 1 fútbol: stadium view, orbit
  { tilt: 0.92, yaw: 0.2, yawSweep: -0.4, spin: 0, spinRate: 0, zoom: 1.22 },    // 2 MLB
  { tilt: 1.0, yaw: -0.18, yawSweep: 0.36, spin: 0, spinRate: 0, zoom: 1.25 },   // 3 NBA
  { tilt: 1.05, yaw: 0.16, yawSweep: -0.32, spin: 0, spinRate: 0, zoom: 1.25 },  // 4 tenis
  { tilt: 0.78, yaw: -0.3, yawSweep: 0.3, spin: 0, spinRate: 0, zoom: 1.12 },    // 5 100 versiones: columns
  { tilt: 1.12, yaw: 0.5, yawSweep: -0.45, spin: 0, spinRate: 0, zoom: 1.1 },   // 6 matriz: towers, diagonal view
  { tilt: 0.28, yaw: 0, yawSweep: 0, spin: -0.25, spinRate: 0, zoom: 1.0 },     // 7 calibración: slight turn
  { tilt: 0, yaw: 0, yawSweep: 0, spin: 0, spinRate: 0.55, zoom: 1.0 },         // 8 marca: coin turning
];
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
  return { x: new Float32Array(n), y: new Float32Array(n), z: new Float32Array(n), c: new Uint8Array(n), g: new Int16Array(n).fill(-1) };
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
    f.z[i] = (r() * 1.6 - 0.55) * b.s; // volumetric: some flecks fly past the lens
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
      f.g[i] = p;
    }
  }
  // The ball: a tight red cluster that the simulation moves around the pitch.
  const ballN = Math.max(24, Math.floor(perPlayer * 0.75));
  for (let k = 0; k < ballN; k++, i++) {
    const a = r() * Math.PI * 2;
    const rad = Math.sqrt(r()) * b.s * 0.0075;
    f.x[i] = sx(52.5) + Math.cos(a) * rad;
    f.y[i] = sy(34) + Math.sin(a) * rad;
    f.c[i] = COLOR.flare;
    f.g[i] = players.length;
  }
  f.sim = {
    kind: "football",
    scale: b.s,
    agents: [
      ...players.map(([x, y], p) => ({ x: sx(x), y: sy(y), team: p < 11 ? 0 : 1 })),
      { x: sx(52.5), y: sy(34), team: 2 },
    ],
    pts: { min: [sx(1), sy(1)], max: [sx(104), sy(67)], goal0: [sx(0), sy(34)], goal1: [sx(105), sy(34)] },
  };
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
    // Each version is a column; home wins stand tallest so the 49 read as a block.
    const height = k < 49 ? 1.1 : k < 76 ? 0.55 : 0.22;
    f.z[i] = -r() * cell * height;
    f.c[i] = k < 49 ? COLOR.gold : k < 76 ? COLOR.bone : COLOR.dim;
    f.g[i] = k;
  }
  f.sim = { kind: "columns", scale: b.s, groups: 100 };
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
    f.x[i] = x0 + (a + 0.2 + r() * 0.6) * cell;
    f.y[i] = y0 + (h + 0.2 + r() * 0.6) * cell;
    const rel = p[k] / max;
    // Probability = tower height, built in discrete floors so the eye reads stacked 3D bars, not a cloud.
    const floors = Math.max(1, Math.round(rel * 14));
    f.z[i] = -Math.floor(r() * floors) * b.s * 0.02;
    f.c[i] = rel > 0.98 ? COLOR.bone : rel > 0.42 ? COLOR.gold : COLOR.dim;
    f.g[i] = k;
  }
  f.sim = { kind: "towers", scale: b.s, groups: G * G };
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
    f.g[i] = bi;
  }
  f.sim = { kind: "bins", scale: b.s, groups: 10 };
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


type Seg = [number, number, number, number];
type Arc = { cx: number; cy: number; r: number; a0: number; a1: number };
type Blob = { x: number; y: number; c: number; r?: number; team?: number };

/**
 * Generic "field drawing": distributes particles along line segments and arcs (in field units),
 * plus clusters (players/ball). `toPx` maps field units into the stage box.
 */
function drawField(
  n: number, seed: number, toPx: (x: number, y: number) => [number, number],
  segs: Seg[], arcs: Arc[], blobs: Blob[], blobShare: number, blobR: number, extra?: (f: Formation, i: number, r: () => number) => boolean,
): Formation {
  const f = alloc(n);
  const r = rng(seed);
  const segLen = segs.map(([a, b, c, d]) => Math.hypot(c - a, d - b));
  const arcLen = arcs.map((a) => Math.abs(a.a1 - a.a0) * a.r);
  const total = segLen.reduce((s, v) => s + v, 0) + arcLen.reduce((s, v) => s + v, 0);
  const nBlobs = Math.floor(n * blobShare);
  const per = Math.max(1, Math.floor(nBlobs / Math.max(1, blobs.length)));
  let i = 0;
  const agents: Agent[] = [];
  for (let b = 0; b < blobs.length; b++) {
    const [bx, by] = toPx(blobs[b].x, blobs[b].y);
    const rad = blobs[b].r ?? blobR;
    const team = blobs[b].team;
    const gi = team === undefined ? -1 : agents.push({ x: bx, y: by, team }) - 1;
    const count = team === 2 ? Math.max(24, Math.floor(per * 0.7)) : per;
    for (let k = 0; k < count && i < n; k++, i++) {
      const a = r() * Math.PI * 2;
      const d = Math.sqrt(r()) * rad;
      f.x[i] = bx + Math.cos(a) * d;
      f.y[i] = by + Math.sin(a) * d;
      f.c[i] = blobs[b].c;
      f.g[i] = gi;
    }
  }
  if (agents.length) f.sim = { kind: "football", scale: 0, agents }; // kind/scale/pts set by the caller
  for (; i < n; i++) {
    if (extra && extra(f, i, r)) continue;
    let d = r() * total;
    let done = false;
    for (let s = 0; s < segs.length && !done; s++) {
      if (d <= segLen[s]) {
        const t = d / segLen[s];
        const [a, b, c, e] = segs[s];
        const [x, y] = toPx(a + (c - a) * t, b + (e - b) * t);
        f.x[i] = x + gauss(r) * 0.7;
        f.y[i] = y + gauss(r) * 0.7;
        done = true;
      } else d -= segLen[s];
    }
    for (let s = 0; s < arcs.length && !done; s++) {
      if (d <= arcLen[s] || s === arcs.length - 1) {
        const A = arcs[s];
        const t = Math.min(1, d / arcLen[s]);
        const ang = A.a0 + (A.a1 - A.a0) * t;
        const [x, y] = toPx(A.cx + Math.cos(ang) * A.r, A.cy + Math.sin(ang) * A.r);
        f.x[i] = x + gauss(r) * 0.7;
        f.y[i] = y + gauss(r) * 0.7;
        done = true;
      } else d -= arcLen[s];
    }
    f.c[i] = COLOR.dim;
  }
  return f;
}

function diamond(n: number, b: Box): Formation {
  // Field units: home plate at (0,0), y grows toward center field. Fair territory = 90° wedge.
  const S = b.s * 0.92;
  const R = 1; // outfield fence radius (normalized)
  const toPx = (x: number, y: number): [number, number] => [b.cx + x * S * 0.5, b.cy + S * 0.42 - y * S * 0.78];
  const q = Math.SQRT1_2;
  const base = 0.24; // 90 ft relative to ~400 ft fence
  const first: [number, number] = [base * q, base * q];
  const second: [number, number] = [0, base * 2 * q];
  const third: [number, number] = [-base * q, base * q];
  const segs: Seg[] = [
    [0, 0, R * q, R * q], [0, 0, -R * q, R * q], // foul lines
    [0, 0, ...first], [...first, ...second], [...second, ...third], [...third, 0, 0],
  ];
  const arcs: Arc[] = [
    { cx: 0, cy: 0, r: R, a0: Math.PI / 4, a1: (3 * Math.PI) / 4 },
    { cx: 0, cy: 0, r: 0.5, a0: Math.PI / 4, a1: (3 * Math.PI) / 4 }, // infield grass edge
  ];
  const G = COLOR.gold;
  const blobs: Blob[] = [
    { x: 0, y: base * q, c: G, team: 0 }, { x: 0, y: -0.04, c: G, team: 0 }, // 0 pitcher, 1 catcher
    { x: first[0] + 0.03, y: first[1] + 0.04, c: G, team: 0 }, { x: 0.1, y: 0.42, c: G, team: 0 }, { x: -0.1, y: 0.42, c: G, team: 0 },
    { x: third[0] - 0.03, y: third[1] + 0.04, c: G, team: 0 },
    { x: -0.55, y: 0.62, c: G, team: 0 }, { x: 0, y: 0.82, c: G, team: 0 }, { x: 0.55, y: 0.62, c: G, team: 0 },
    { x: 0.035, y: 0.0, c: COLOR.bone, team: 1 }, // 9 batter
    { x: 0, y: base * q, c: COLOR.flare, r: b.s * 0.007, team: 2 }, // 10 ball (starts with the pitcher)
    { x: 0, y: 0, c: COLOR.bone, r: b.s * 0.008 }, ...[first, second, third].map(([x, y]) => ({ x, y, c: COLOR.bone, r: b.s * 0.008 })),
  ];
  const f = drawField(n, 131, toPx, segs, arcs, blobs, 0.26, b.s * 0.016);
  const land: [number, number][] = [];
  for (let k = 0; k < 9; k++) {
    const ang = Math.PI / 4 + (Math.PI / 2) * ((k + 0.5) / 9);
    const rr = 0.55 + ((k * 37) % 5) * 0.08;
    land.push(toPx(Math.cos(ang) * rr, Math.sin(ang) * rr));
  }
  f.sim = { ...f.sim!, kind: "baseball", scale: b.s, pts: { home: toPx(0, 0), first: toPx(...first), pitcher: toPx(0, base * q) }, land };
  return f;
}

function basketball(n: number, b: Box): Formation {
  // FIBA court 28 × 15 m, centered.
  const W = b.s * 1.08;
  const H = (W * 15) / 28;
  const toPx = (x: number, y: number): [number, number] => [b.cx + ((x - 14) / 28) * W, b.cy + ((y - 7.5) / 15) * H];
  const segs: Seg[] = [
    [0, 0, 28, 0], [28, 0, 28, 15], [28, 15, 0, 15], [0, 15, 0, 0], [14, 0, 14, 15],
    [0, 5.05, 5.8, 5.05], [5.8, 5.05, 5.8, 9.95], [5.8, 9.95, 0, 9.95],
    [28, 5.05, 22.2, 5.05], [22.2, 5.05, 22.2, 9.95], [22.2, 9.95, 28, 9.95],
    [0, 0.9, 2.99, 0.9], [0, 14.1, 2.99, 14.1], [28, 0.9, 25.01, 0.9], [28, 14.1, 25.01, 14.1],
  ];
  const a3 = Math.asin(6.6 / 6.75);
  const arcs: Arc[] = [
    { cx: 14, cy: 7.5, r: 1.8, a0: 0, a1: Math.PI * 2 },
    { cx: 1.575, cy: 7.5, r: 6.75, a0: -a3, a1: a3 },
    { cx: 26.425, cy: 7.5, r: 6.75, a0: Math.PI - a3, a1: Math.PI + a3 },
    { cx: 5.8, cy: 7.5, r: 1.8, a0: -Math.PI / 2, a1: Math.PI / 2 },
    { cx: 22.2, cy: 7.5, r: 1.8, a0: Math.PI / 2, a1: (3 * Math.PI) / 2 },
  ];
  const blobs: Blob[] = [
    [4, 7.5], [7.5, 3.2], [7.5, 11.8], [10.5, 5.5], [11, 9.5],
  ].flatMap(([x, y]): Blob[] => [
    { x, y, c: COLOR.gold, team: 0 },
    { x: x + 1.1, y: y + 0.6, c: COLOR.bone, team: 1 },
  ]).concat([
    { x: 7.5, y: 3.2, c: COLOR.flare, r: b.s * 0.0075, team: 2 }, // ball, starts with a guard
    { x: 1.575, y: 7.5, c: COLOR.bone, r: b.s * 0.011 }, { x: 26.425, y: 7.5, c: COLOR.bone, r: b.s * 0.011 },
  ]);
  const f = drawField(n, 151, toPx, segs, arcs, blobs, 0.22, b.s * 0.017);
  f.sim = { ...f.sim!, kind: "basketball", scale: b.s, pts: { hoop: toPx(1.575, 7.5), min: toPx(0.5, 0.5), max: toPx(13.5, 14.5) } };
  return f;
}

function tennis(n: number, b: Box): Formation {
  // Doubles court 23.77 × 10.97 m, drawn lengthwise (horizontal), net at x = 11.885.
  const W = b.s * 1.1;
  const H = (W * 10.97) / 23.77;
  const toPx = (x: number, y: number): [number, number] => [b.cx + ((x - 11.885) / 23.77) * W, b.cy + ((y - 5.485) / 10.97) * H];
  const segs: Seg[] = [
    [0, 0, 23.77, 0], [23.77, 0, 23.77, 10.97], [23.77, 10.97, 0, 10.97], [0, 10.97, 0, 0],
    [0, 1.37, 23.77, 1.37], [0, 9.6, 23.77, 9.6],
    [5.485, 1.37, 5.485, 9.6], [18.285, 1.37, 18.285, 9.6], [5.485, 5.485, 18.285, 5.485],
    [11.885, -0.9, 11.885, 11.87], [11.885, -0.9, 11.885, 11.87], // net, weighted double
  ];
  const blobs: Blob[] = [
    { x: -0.4, y: 5.485, c: COLOR.gold, team: 0 },
    { x: 24.17, y: 5.485, c: COLOR.bone, team: 1 },
    { x: -0.1, y: 5.485, c: COLOR.flare, r: b.s * 0.007, team: 2 },
  ];
  const f = drawField(n, 171, toPx, segs, [], blobs, 0.1, b.s * 0.02);
  void H;
  f.sim = {
    ...f.sim!, kind: "tennis", scale: b.s,
    pts: { min: toPx(-1.2, 0.6), max: toPx(24.97, 10.37), net: toPx(11.885, 5.485), base0: toPx(-0.4, 5.485), base1: toPx(24.17, 5.485) },
  };
  return f;
}

export function buildFormations(n: number, w: number, h: number): Formation[] {
  const b = stage(w, h);
  const list = [noise(n, b), pitch(n, b), diamond(n, b), basketball(n, b), tennis(n, b), hundred(n, b), matrix(n, b), calibration(n, b), mark(n, b)];
  // Center every formation on the stage origin; the camera projects back onto the stage.
  for (const f of list) {
    for (let i = 0; i < n; i++) { f.x[i] -= b.cx; f.y[i] -= b.cy; }
    const sp = f.sim;
    if (!sp) continue;
    sp.agents?.forEach((a) => { a.x -= b.cx; a.y -= b.cy; });
    if (sp.pts) for (const k in sp.pts) sp.pts[k] = [sp.pts[k][0] - b.cx, sp.pts[k][1] - b.cy];
    sp.land = sp.land?.map(([x, y]) => [x - b.cx, y - b.cy]);
  }
  return list;
}
