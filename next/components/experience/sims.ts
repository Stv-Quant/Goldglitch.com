import type { Formation, SimSpec } from "./formations";

/**
 * Live simulations that animate formation groups. Each sim writes per-group offsets
 * (ox, oy, oz in world px; oz < 0 lifts toward the camera) and a z-scale (sz) that the
 * render loop applies to every particle of that group. Cheap: O(agents) per frame.
 */
export type LiveSim = {
  ox: Float32Array;
  oy: Float32Array;
  oz: Float32Array;
  sz: Float32Array;
  step(t: number, dt: number): void;
};

type V = [number, number];
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));
const easeIO = (t: number) => (t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2);

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

function buffers(n: number) {
  return { ox: new Float32Array(n), oy: new Float32Array(n), oz: new Float32Array(n), sz: new Float32Array(n).fill(1) };
}

/** Shared agent machinery: homes, smoothed current positions, a ball in flight. */
function agentsBase(spec: SimSpec) {
  const A = spec.agents!;
  const n = A.length;
  const ball = A.findIndex((a) => a.team === 2);
  const hx = Float32Array.from(A, (a) => a.x);
  const hy = Float32Array.from(A, (a) => a.y);
  const cx = Float32Array.from(hx);
  const cy = Float32Array.from(hy);
  const dx = Float32Array.from(hx);
  const dy = Float32Array.from(hy);
  const buf = buffers(n);
  const flight = { on: false, t0: 0, dur: 1, from: [0, 0] as V, to: [0, 0] as V, lift: 0 };
  const ballPos = { x: hx[ball], y: hy[ball], z: 0 };

  function launch(t: number, to: V, speed: number, liftK: number, minDur = 0.3, maxDur = 1.6) {
    const from: V = [ballPos.x, ballPos.y];
    const d = Math.hypot(to[0] - from[0], to[1] - from[1]);
    flight.on = true;
    flight.t0 = t;
    flight.from = from;
    flight.to = to;
    flight.dur = clamp(d / speed, minDur, maxDur);
    flight.lift = d * liftK;
  }

  /** Advances the ball; returns true on the frame it lands. */
  function flyBall(t: number): boolean {
    if (!flight.on) return false;
    const u = clamp((t - flight.t0) / flight.dur, 0, 1);
    const e = easeIO(u);
    ballPos.x = lerp(flight.from[0], flight.to[0], e);
    ballPos.y = lerp(flight.from[1], flight.to[1], e);
    ballPos.z = -Math.sin(Math.PI * u) * flight.lift;
    if (u >= 1) {
      flight.on = false;
      ballPos.z = 0;
      return true;
    }
    return false;
  }

  function settle(dt: number, rate: number, fast: Set<number>) {
    for (let i = 0; i < n; i++) {
      if (i === ball) continue;
      const k = Math.min(1, dt * (fast.has(i) ? rate * 2.8 : rate));
      cx[i] += (dx[i] - cx[i]) * k;
      cy[i] += (dy[i] - cy[i]) * k;
    }
  }

  function write() {
    for (let i = 0; i < n; i++) {
      if (i === ball) continue;
      buf.ox[i] = cx[i] - hx[i];
      buf.oy[i] = cy[i] - hy[i];
    }
    buf.ox[ball] = ballPos.x - hx[ball];
    buf.oy[ball] = ballPos.y - hy[ball];
    buf.oz[ball] = ballPos.z;
  }

  return { A, n, ball, hx, hy, cx, cy, dx, dy, buf, flight, ballPos, launch, flyBall, settle, write };
}

function football(spec: SimSpec, seed: number): LiveSim {
  const s = agentsBase(spec);
  const { A, n, ball, hx, hy, cx, cy, dx, dy, ballPos } = s;
  const r = rng(seed);
  const S = spec.scale;
  const [minX, minY] = spec.pts!.min;
  const [maxX, maxY] = spec.pts!.max;
  const goal = [spec.pts!.goal1, spec.pts!.goal0]; // team 0 attacks goal1 (right), team 1 attacks goal0 (left)
  const gk = [0, 11];
  const team = (i: number) => A[i].team;
  let holder = 9;
  let receiver = -1;
  let nextAction = 0.6;
  let shot = false;
  let restartAt = -1;
  ballPos.x = hx[holder];
  ballPos.y = hy[holder];
  const fast = new Set<number>();

  function nearest(teamId: number, x: number, y: number, skipGk = true) {
    let best = -1;
    let bd = Infinity;
    for (let i = 0; i < n; i++) {
      if (i === ball || team(i) !== teamId || (skipGk && gk.includes(i))) continue;
      const d = Math.hypot(cx[i] - x, cy[i] - y);
      if (d < bd) { bd = d; best = i; }
    }
    return best;
  }

  function choosePass(t: number) {
    const tm = team(holder);
    const dir = tm === 0 ? 1 : -1;
    const g = goal[tm];
    // Close to the opponent goal → shoot.
    if (Math.abs(g[0] - cx[holder]) < S * 0.3 && r() < 0.6) {
      shot = true;
      receiver = -1;
      s.launch(t, [g[0], g[1] + (r() - 0.5) * S * 0.08], S * 1.7, 0.12, 0.35, 0.8);
      return;
    }
    let best = -1;
    let bestScore = -Infinity;
    for (let i = 0; i < n; i++) {
      if (i === ball || i === holder || team(i) !== tm || gk.includes(i)) continue;
      const fwd = (cx[i] - cx[holder]) * dir;
      const d = Math.hypot(cx[i] - cx[holder], cy[i] - cy[holder]);
      const score = fwd / S + r() * 0.55 - Math.abs(d / S - 0.22) * 1.4;
      if (score > bestScore) { bestScore = score; best = i; }
    }
    // 16%: the pass is read and intercepted.
    if (r() < 0.16) {
      const mx = (cx[holder] + cx[best]) / 2;
      const my = (cy[holder] + cy[best]) / 2;
      best = nearest(1 - tm, mx, my);
    }
    receiver = best;
    const lead = S * 0.03 * (team(best) === 0 ? 1 : -1);
    s.launch(t, [clamp(cx[best] + lead, minX, maxX), cy[best]], S * 1.15, 0.18);
  }

  return {
    ...s.buf,
    step(t, dt) {
      if (restartAt > 0 && t >= restartAt) {
        restartAt = -1;
        nextAction = t + 0.5;
      }
      if (s.flight.on) {
        if (s.flyBall(t)) {
          if (shot) {
            // Goal or save: restart from the defending keeper after a beat.
            shot = false;
            const tm = team(holder);
            holder = gk[1 - tm];
            restartAt = t + 0.9;
            ballPos.x = cx[holder];
            ballPos.y = cy[holder];
          } else {
            holder = receiver;
            nextAction = t + 0.35 + r() * 0.65;
          }
          receiver = -1;
        }
      } else if (restartAt < 0) {
        // Dribble: the holder carries the ball forward a little.
        const dir = team(holder) === 0 ? 1 : -1;
        if (!gk.includes(holder)) dx[holder] = clamp(cx[holder] + dir * S * 0.05, minX, maxX);
        ballPos.x = cx[holder] + dir * S * 0.008;
        ballPos.y = cy[holder];
        if (t >= nextAction) choosePass(t);
      }

      // Formation shift: both teams slide with the ball; one presser per team closes in.
      const bx = ballPos.x;
      const by = ballPos.y;
      const press0 = nearest(0, bx, by);
      const press1 = nearest(1, bx, by);
      fast.clear();
      for (let i = 0; i < n; i++) {
        if (i === ball) continue;
        if (gk.includes(i)) {
          dx[i] = hx[i];
          dy[i] = hy[i] + by * 0.18;
          continue;
        }
        dx[i] = hx[i] + bx * 0.42 + Math.sin(t * 0.7 + i * 1.9) * S * 0.012;
        dy[i] = hy[i] + by * 0.3 + Math.cos(t * 0.6 + i * 1.3) * S * 0.01;
        const pressing = (i === press0 || i === press1) && i !== holder;
        if (pressing) {
          dx[i] = lerp(dx[i], bx, 0.78);
          dy[i] = lerp(dy[i], by, 0.78);
          fast.add(i);
        }
        dx[i] = clamp(dx[i], minX, maxX);
        dy[i] = clamp(dy[i], minY, maxY);
      }
      if (receiver >= 0) { dx[receiver] = s.flight.to[0]; dy[receiver] = s.flight.to[1]; fast.add(receiver); }
      if (!s.flight.on && restartAt < 0) fast.add(holder);
      s.settle(dt, 1.8, fast);
      s.write();
    },
  };
}

function baseball(spec: SimSpec, seed: number): LiveSim {
  const s = agentsBase(spec);
  const { n, ball, hx, hy, cx, cy, dx, dy, ballPos } = s;
  const r = rng(seed);
  const S = spec.scale;
  const P = spec.pts!;
  const land = spec.land!;
  const pitcher = 0, catcher = 1, batter = 9;
  type Phase = "windup" | "pitch" | "return" | "hit" | "throw" | "reset";
  let phase: Phase = "windup";
  let until = 0.8;
  let fielder = -1;
  let hitTarget: [number, number] = [0, 0];
  const fast = new Set<number>();

  function nearestFielder(x: number, y: number) {
    let best = 2, bd = Infinity;
    for (let i = 2; i <= 8; i++) {
      const d = Math.hypot(hx[i] - x, hy[i] - y);
      if (d < bd) { bd = d; best = i; }
    }
    return best;
  }

  return {
    ...s.buf,
    step(t, dt) {
      for (let i = 0; i < n; i++) { if (i !== ball) { dx[i] = hx[i]; dy[i] = hy[i]; } }
      fast.clear();
      const landed = s.flyBall(t);
      switch (phase) {
        case "windup":
          ballPos.x = cx[pitcher]; ballPos.y = cy[pitcher];
          if (t >= until) { phase = "pitch"; s.launch(t, [cx[catcher], cy[catcher]], S * 2.4, 0.04, 0.32, 0.5); }
          break;
        case "pitch":
          if (landed || (!s.flight.on && t > until + 0.1)) {
            if (r() < 0.38) {
              phase = "hit";
              hitTarget = land[Math.floor(r() * land.length)];
              fielder = nearestFielder(hitTarget[0], hitTarget[1]);
              s.launch(t, hitTarget, S * 0.7, 0.55, 1.2, 1.9);
            } else {
              phase = "return";
              until = t + 0.35;
            }
          }
          break;
        case "return":
          if (t >= until && !s.flight.on) { s.launch(t, [cx[pitcher], cy[pitcher]], S * 1.2, 0.12, 0.45, 0.8); until = Infinity; }
          if (landed) { phase = "windup"; until = t + 0.6 + r() * 0.5; }
          break;
        case "hit":
          dx[fielder] = hitTarget[0]; dy[fielder] = hitTarget[1]; fast.add(fielder);
          dx[batter] = P.first[0]; dy[batter] = P.first[1]; fast.add(batter);
          if (landed) { phase = "throw"; s.launch(t, [P.first[0], P.first[1]], S * 1.6, 0.14, 0.5, 1.0); }
          break;
        case "throw":
          dx[fielder] = hitTarget[0]; dy[fielder] = hitTarget[1];
          dx[batter] = P.first[0]; dy[batter] = P.first[1]; fast.add(batter);
          if (landed) { phase = "reset"; until = t + 1.4; }
          break;
        case "reset":
          ballPos.x = lerp(ballPos.x, cx[pitcher], Math.min(1, dt * 3));
          ballPos.y = lerp(ballPos.y, cy[pitcher], Math.min(1, dt * 3));
          if (t >= until) { phase = "windup"; until = t + 0.6; }
          break;
      }
      s.settle(dt, 1.6, fast);
      s.write();
    },
  };
}

function basketball(spec: SimSpec, seed: number): LiveSim {
  const s = agentsBase(spec);
  const { n, ball, hx, hy, cx, cy, dx, dy, ballPos } = s;
  const r = rng(seed);
  const S = spec.scale;
  const hoop = spec.pts!.hoop;
  const [minX, minY] = spec.pts!.min;
  const [maxX, maxY] = spec.pts!.max;
  const offense = [0, 2, 4, 6, 8];
  let holder = 2;
  let receiver = -1;
  let passes = 0;
  let shooting = false;
  let nextAction = 0.6;
  let rebound = -1;
  const fast = new Set<number>();

  return {
    ...s.buf,
    step(t, dt) {
      fast.clear();
      if (s.flight.on) {
        if (s.flyBall(t)) {
          if (shooting) {
            shooting = false;
            rebound = t + 0.35;
          } else {
            holder = receiver;
            nextAction = t + 0.45 + r() * 0.5;
          }
          receiver = -1;
        }
      } else if (rebound > 0) {
        ballPos.x = hoop[0]; ballPos.y = hoop[1]; ballPos.z = -S * 0.01;
        if (t >= rebound) {
          rebound = -1;
          receiver = offense[Math.floor(r() * offense.length)];
          s.launch(t, [cx[receiver], cy[receiver]], S * 1.3, 0.1, 0.35, 0.7);
          passes = 0;
        }
      } else {
        // Dribble: bounce in z while held.
        ballPos.x = cx[holder] + S * 0.01;
        ballPos.y = cy[holder];
        ballPos.z = -Math.abs(Math.sin(t * 9)) * S * 0.018;
        if (t >= nextAction) {
          if (passes >= 3 + Math.floor(r() * 3)) {
            shooting = true;
            s.launch(t, hoop, S * 0.75, 0.55, 0.8, 1.15);
          } else {
            let next = holder;
            while (next === holder) next = offense[Math.floor(r() * offense.length)];
            receiver = next;
            passes++;
            s.launch(t, [cx[next], cy[next]], S * 1.5, 0.08, 0.3, 0.6);
          }
        }
      }

      const by = ballPos.y;
      for (const i of offense) {
        dx[i] = clamp(hx[i] + Math.sin(t * 0.9 + i * 1.7) * S * 0.05, minX, maxX);
        dy[i] = clamp(hy[i] + Math.cos(t * 1.1 + i) * S * 0.045 + (by - hy[i]) * 0.12, minY, maxY);
      }
      // Man-to-man: each defender stays between his man and the hoop.
      for (const i of offense) {
        const d = i + 1;
        dx[d] = cx[i] + (hoop[0] - cx[i]) * 0.24;
        dy[d] = cy[i] + (hoop[1] - cy[i]) * 0.24;
        if (i === holder) fast.add(d);
      }
      if (receiver >= 0) fast.add(receiver);
      void n; void ball;
      s.settle(dt, 2.2, fast);
      s.write();
    },
  };
}

function tennis(spec: SimSpec, seed: number): LiveSim {
  const s = agentsBase(spec);
  const { hx, hy, cx, cy, dx, dy, ballPos } = s;
  const r = rng(seed);
  const S = spec.scale;
  const P = spec.pts!;
  const [minX, minY] = P.min;
  const [maxX, maxY] = P.max;
  const net = P.net[0];
  let hitter = 0;
  let shots = 0;
  let pauseUntil = 0.8;
  let target: V = [0, 0];
  const fast = new Set<number>();

  function hit(t: number) {
    const other = 1 - hitter;
    const depth = 0.55 + r() * 0.35;
    const tx = other === 1 ? lerp(net, maxX, depth) : lerp(net, minX, depth);
    const ty = lerp(minY, maxY, 0.12 + r() * 0.76);
    target = [tx, ty];
    s.launch(t, target, S * 1.25, 0.16, 0.65, 1.0);
  }

  return {
    ...s.buf,
    step(t, dt) {
      fast.clear();
      if (s.flight.on) {
        if (s.flyBall(t)) {
          hitter = 1 - hitter;
          shots++;
          if (shots >= 6 + Math.floor(r() * 4)) {
            shots = 0;
            pauseUntil = t + 1.1; // point over
          } else hit(t);
        }
      } else if (t >= pauseUntil) {
        hit(t);
      } else {
        ballPos.x = cx[hitter] + (hitter === 0 ? 1 : -1) * S * 0.012;
        ballPos.y = cy[hitter];
        ballPos.z = -Math.abs(Math.sin(t * 5)) * S * 0.02;
      }
      // Receiver runs to the landing spot; the hitter recovers to the center of the baseline.
      const recv = 1 - hitter;
      for (const p of [0, 1]) {
        if (p === recv && s.flight.on) {
          dx[p] = clamp(target[0] + (p === 1 ? 1 : -1) * S * 0.02, minX, maxX);
          dy[p] = clamp(target[1], minY, maxY);
          fast.add(p);
        } else {
          dx[p] = hx[p];
          dy[p] = hy[p] + (ballPos.y - hy[p]) * 0.25;
        }
      }
      s.settle(dt, 1.7, fast);
      s.write();
    },
  };
}

/** 100 columns: an equalizer wave, as if the 100 versions were being re-simulated live. */
function columns(spec: SimSpec): LiveSim {
  const b = buffers(spec.groups!);
  return {
    ...b,
    step(t) {
      for (let k = 0; k < 100; k++) {
        const col = k % 10, row = (k / 10) | 0;
        const w = 0.5 + 0.5 * Math.sin(t * 2.1 - col * 0.55 - row * 0.42);
        b.sz[k] = 0.3 + 0.95 * w * w;
      }
    },
  };
}

/** Score-matrix towers: heights breathe and a model-update pulse sweeps diagonally. */
function towers(spec: SimSpec): LiveSim {
  const b = buffers(spec.groups!);
  const G = Math.round(Math.sqrt(spec.groups!));
  return {
    ...b,
    step(t) {
      const cycle = 3.2;
      const front = ((t % cycle) / cycle) * (2 * G + 2) - 1; // diagonal position of the update pulse
      for (let k = 0; k < spec.groups!; k++) {
        const h = (k / G) | 0, a = k % G;
        const d = h + a - front;
        const pulse = Math.exp(-d * d * 0.9) * 0.45;
        b.sz[k] = 0.82 + 0.18 * Math.sin(t * 1.5 + k * 0.7) + pulse;
      }
    },
  };
}

/** Calibration bins: each cluster takes its turn to light up and settle on the diagonal. */
function bins(spec: SimSpec): LiveSim {
  const b = buffers(spec.groups!);
  const S = spec.scale;
  return {
    ...b,
    step(t) {
      for (let k = 0; k < spec.groups!; k++) {
        const ph = t * 2.2 - k * 0.65;
        b.oy[k] = Math.sin(ph) * S * 0.012;
        b.oz[k] = -Math.max(0, Math.sin(ph)) * S * 0.03;
      }
    },
  };
}

export function makeSim(f: Formation, seed = 7): LiveSim | null {
  const sp = f.sim;
  if (!sp) return null;
  switch (sp.kind) {
    case "football": return football(sp, seed);
    case "baseball": return baseball(sp, seed + 1);
    case "basketball": return basketball(sp, seed + 2);
    case "tennis": return tennis(sp, seed + 3);
    case "columns": return columns(sp);
    case "towers": return towers(sp);
    case "bins": return bins(sp);
  }
}
