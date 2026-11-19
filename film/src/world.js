// Goldglitch film: one continuous forward camera flight through six night venues.
// Deterministic: renderAt(t) draws the exact frame for t ∈ [0,1], so seams and re-renders are identical.
import * as THREE from "three";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/examples/jsm/postprocessing/OutputPass.js";
import { ShaderPass } from "three/examples/jsm/postprocessing/ShaderPass.js";

const C = { void: 0x0a0907, gold: 0xd4af37, goldHi: 0xffe7a0, flare: 0xff3b1f, bone: 0xede6d6 };
const SEG = 160; // distance between venue centres along -Z

// ---------- seeded RNG ----------
let seed = 7;
const rnd = () => ((seed = (seed * 16807) % 2147483647) - 1) / 2147483646;
const rr = (a, b) => a + (b - a) * rnd();

// ---------- canvas textures ----------
function canvasTex(w, h, draw, repeat) {
  const c = document.createElement("canvas");
  c.width = w; c.height = h;
  draw(c.getContext("2d"), w, h);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  if (repeat) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...repeat); }
  return t;
}

const pitchTex = () => canvasTex(1024, 1536, (g, w, h) => {
  for (let i = 0; i < 12; i++) { g.fillStyle = i % 2 ? "#1d4a22" : "#22552a"; g.fillRect(0, (h / 12) * i, w, h / 12); }
  g.strokeStyle = "rgba(240,236,220,.9)"; g.lineWidth = 6;
  const m = 40; g.strokeRect(m, m, w - 2 * m, h - 2 * m);
  g.beginPath(); g.moveTo(m, h / 2); g.lineTo(w - m, h / 2); g.stroke();
  g.beginPath(); g.arc(w / 2, h / 2, 130, 0, Math.PI * 2); g.stroke();
  for (const y of [m, h - m]) {
    const d = y === m ? 1 : -1;
    g.strokeRect(w / 2 - 300, Math.min(y, y + d * 240), 600, 240);
    g.strokeRect(w / 2 - 130, Math.min(y, y + d * 90), 260, 90);
  }
});

const diamondTex = () => canvasTex(1536, 1536, (g, w, h) => {
  g.fillStyle = "#1c4620"; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 16; i++) { g.fillStyle = i % 2 ? "rgba(255,255,255,.025)" : "rgba(0,0,0,.05)"; g.fillRect((w / 16) * i, 0, w / 16, h); }
  const hx = w / 2, hy = h * 0.86;
  g.fillStyle = "#7a4f2c"; g.beginPath(); g.moveTo(hx, hy + 60); g.arc(hx, hy, 620, -Math.PI * 0.75, -Math.PI * 0.25); g.closePath(); g.fill();
  g.fillStyle = "#1f4d23"; g.save(); g.translate(hx, hy - 330); g.rotate(Math.PI / 4); g.fillRect(-235, -235, 470, 470); g.restore();
  g.strokeStyle = "rgba(240,236,220,.9)"; g.lineWidth = 6;
  g.beginPath(); g.moveTo(hx, hy); g.lineTo(hx - 760, hy - 760); g.moveTo(hx, hy); g.lineTo(hx + 760, hy - 760); g.stroke();
  g.fillStyle = "#ede6d6";
  for (const [x, y] of [[hx, hy], [hx + 330, hy - 330], [hx, hy - 660], [hx - 330, hy - 330]]) { g.save(); g.translate(x, y); g.rotate(Math.PI / 4); g.fillRect(-14, -14, 28, 28); g.restore(); }
  g.fillStyle = "#8a5a33"; g.beginPath(); g.arc(hx, hy - 330, 46, 0, Math.PI * 2); g.fill();
});

const courtTex = () => canvasTex(1536, 820, (g, w, h) => {
  for (let i = 0; i < 48; i++) { g.fillStyle = `hsl(${30 + rr(-3, 3)}, ${45 + rr(-6, 6)}%, ${30 + rr(-4, 4)}%)`; g.fillRect(0, (h / 48) * i, w, h / 48 + 1); }
  for (let i = 0; i < 600; i++) { g.fillStyle = "rgba(0,0,0,.08)"; g.fillRect(rr(0, w), rr(0, h), rr(30, 160), 1); }
  g.strokeStyle = "rgba(245,240,225,.92)"; g.lineWidth = 5;
  const m = 30; g.strokeRect(m, m, w - 2 * m, h - 2 * m);
  g.beginPath(); g.moveTo(w / 2, m); g.lineTo(w / 2, h - m); g.stroke();
  g.beginPath(); g.arc(w / 2, h / 2, 90, 0, Math.PI * 2); g.stroke();
  for (const s of [1, -1]) {
    const x = s > 0 ? m : w - m;
    g.fillStyle = "rgba(212,175,55,.35)"; g.fillRect(s > 0 ? x : x - 280, h / 2 - 120, 280, 240);
    g.strokeRect(s > 0 ? x : x - 280, h / 2 - 120, 280, 240);
    g.beginPath(); g.arc(x, h / 2, 360, -Math.PI / 2, Math.PI / 2, s < 0); g.stroke();
  }
});

const iceTex = () => canvasTex(1536, 680, (g, w, h) => {
  const gr = g.createLinearGradient(0, 0, w, h); gr.addColorStop(0, "#dfe8ee"); gr.addColorStop(1, "#c9d6df"); g.fillStyle = gr; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 900; i++) { g.strokeStyle = "rgba(255,255,255,.35)"; g.lineWidth = 1; g.beginPath(); const x = rr(0, w), y = rr(0, h); g.moveTo(x, y); g.lineTo(x + rr(-60, 60), y + rr(-10, 10)); g.stroke(); }
  g.fillStyle = "#b8352a"; g.fillRect(w / 2 - 6, 0, 12, h);
  g.fillStyle = "#2e4d8a"; g.fillRect(w * 0.33 - 8, 0, 16, h); g.fillRect(w * 0.67 - 8, 0, 16, h);
  g.strokeStyle = "#2e4d8a"; g.lineWidth = 5; g.beginPath(); g.arc(w / 2, h / 2, 90, 0, Math.PI * 2); g.stroke();
  g.strokeStyle = "#b8352a"; for (const x of [w * 0.1, w * 0.9]) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, h); g.stroke(); }
  for (const [x, y] of [[w * 0.2, h * 0.28], [w * 0.2, h * 0.72], [w * 0.8, h * 0.28], [w * 0.8, h * 0.72]]) { g.beginPath(); g.arc(x, y, 70, 0, Math.PI * 2); g.stroke(); }
});

// Glitch screen: noisy red bars, no text.
function screenTex(i) {
  return canvasTex(256, 160, (g, w, h) => {
    seed = 1000 + i * 97;
    g.fillStyle = "#1a0703"; g.fillRect(0, 0, w, h);
    for (let k = 0; k < 26; k++) {
      g.fillStyle = rnd() > 0.35 ? `rgba(255,${40 + rr(0, 40)},20,${rr(0.4, 1)})` : `rgba(255,230,200,${rr(0.3, 0.9)})`;
      g.fillRect(rr(0, w), rr(0, h), rr(10, 140), rr(3, 18));
    }
    g.fillStyle = "rgba(0,255,230,.15)"; g.fillRect(0, rr(0, h), w, 4);
    for (let y = 0; y < h; y += 3) { g.fillStyle = "rgba(0,0,0,.25)"; g.fillRect(0, y, w, 1); }
  });
}

// ---------- builders ----------
const glow = (color, opacity = 1) => new THREE.MeshBasicMaterial({ color, transparent: opacity < 1, opacity, toneMapped: false });

function lightCone(scene, pos, target, color = C.goldHi, len = 70, rad = 14, op = 0.06) {
  const geo = new THREE.ConeGeometry(rad, len, 24, 1, true);
  geo.translate(0, -len / 2, 0);
  const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color, transparent: true, opacity: op, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide, toneMapped: false }));
  m.position.copy(pos);
  const dir = new THREE.Vector3().subVectors(target, pos).normalize();
  m.quaternion.setFromUnitVectors(new THREE.Vector3(0, -1, 0), dir);
  scene.add(m);
}

function floodTower(scene, x, z, h, target) {
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.6, h, 8), new THREE.MeshStandardMaterial({ color: 0x1a1712, roughness: 0.8 }));
  pole.position.set(x, h / 2, z); scene.add(pole);
  const head = new THREE.Mesh(new THREE.BoxGeometry(7, 3.4, 1), glow(0xfff3d0));
  head.position.set(x, h + 1.5, z); head.lookAt(target.x, h, target.z); scene.add(head);
  const pl = new THREE.PointLight(0xffe2a0, 1300, 160, 1.6);
  pl.position.set(x, h, z); scene.add(pl);
  lightCone(scene, new THREE.Vector3(x, h, z), target, 0xffe7b0, Math.hypot(x - target.x, h, z - target.z), 12, 0.016);
}

/** Bowl of seat tiers: instanced boxes on an ellipse, rising and receding. */
function bowl(scene, cz, rx, rz, rows, color = 0x1d1a15, gap = 0) {
  const per = 140;
  const geo = new THREE.BoxGeometry(1.4, 0.55, 1.2);
  const mat = new THREE.MeshStandardMaterial({ color, roughness: 0.9 });
  const inst = new THREE.InstancedMesh(geo, mat, per * rows);
  const m4 = new THREE.Matrix4(); let n = 0;
  const col = new THREE.Color();
  for (let r = 0; r < rows; r++) {
    const k = 1 + r * 0.06;
    for (let i = 0; i < per; i++) {
      const a = (i / per) * Math.PI * 2;
      if (gap && Math.abs(Math.sin(a)) < gap) continue; // tunnels at both ends: the camera flies through
      m4.makeRotationY(-a);
      m4.setPosition(Math.sin(a) * rx * k, 1 + r * 1.3, cz + Math.cos(a) * rz * k);
      inst.setMatrixAt(n, m4);
      const lit = rnd() < 0.05;
      inst.setColorAt(n, lit ? col.set(C.gold) : col.set(color).offsetHSL(0, 0, rr(-0.03, 0.04)));
      n++;
    }
  }
  inst.count = n;
  scene.add(inst);
  // glowing rim
  const rim = new THREE.Mesh(new THREE.TorusGeometry(1, 0.012, 6, 160), glow(C.gold, 0.9));
  rim.scale.set(rx * (1 + rows * 0.06), rz * (1 + rows * 0.06), 1);
  rim.rotation.x = Math.PI / 2; rim.position.set(0, 1 + rows * 1.3, cz); scene.add(rim);
}

function ground(scene) {
  const g = new THREE.Mesh(new THREE.PlaneGeometry(800, 1400), new THREE.MeshStandardMaterial({ color: 0x0c0b09, roughness: 0.95, metalness: 0.05 }));
  g.rotation.x = -Math.PI / 2; g.position.set(0, -0.05, -SEG * 2.6); scene.add(g);
}

function noiseCity(scene, cz) {
  const towerMat = new THREE.MeshStandardMaterial({ color: 0x14110d, roughness: 0.7 });
  const screens = [];
  for (let i = 0; i < 70; i++) {
    const side = i % 2 ? 1 : -1;
    const x = side * rr(9, 55), z = cz + rr(-80, 60);
    const h = rr(12, 58), w = rr(6, 14);
    const t = new THREE.Mesh(new THREE.BoxGeometry(w, h, w), towerMat);
    t.position.set(x, h / 2, z); scene.add(t);
    const nScreens = 1 + Math.floor(rnd() * 3);
    for (let k = 0; k < nScreens; k++) {
      const s = new THREE.Mesh(new THREE.PlaneGeometry(w * 0.85, w * 0.5), new THREE.MeshBasicMaterial({ map: screenTex(i * 3 + k), toneMapped: false, color: 0xffffff }));
      s.position.set(x - side * (w / 2 + 0.05), rr(4, h - 3), z + rr(-w / 3, w / 3));
      s.rotation.y = side > 0 ? -Math.PI / 2 : Math.PI / 2;
      scene.add(s); screens.push(s);
    }
  }
  return screens;
}

function stadium(scene, cz) {
  const pitch = new THREE.Mesh(new THREE.PlaneGeometry(48, 72), new THREE.MeshStandardMaterial({ map: pitchTex(), roughness: 0.85 }));
  pitch.rotation.x = -Math.PI / 2; pitch.position.set(0, 0.02, cz); scene.add(pitch);
  for (const zz of [cz - 36, cz + 36]) {
    const goal = new THREE.Mesh(new THREE.BoxGeometry(7.3, 2.4, 0.2), new THREE.MeshBasicMaterial({ color: 0xf2eee2, wireframe: true }));
    goal.position.set(0, 1.2, zz); scene.add(goal);
  }
  bowl(scene, cz, 34, 48, 16, 0x1d1a15, 0.18);
  const tgt = new THREE.Vector3(0, 0, cz);
  for (const [x, z] of [[-44, cz - 52], [44, cz - 52], [-44, cz + 52], [44, cz + 52]]) floodTower(scene, x, z, 40, tgt);
}

function ballpark(scene, cz) {
  const field = new THREE.Mesh(new THREE.CircleGeometry(46, 64, Math.PI * 0.25, Math.PI * 1.5), new THREE.MeshStandardMaterial({ map: diamondTex(), roughness: 0.85 }));
  field.rotation.x = -Math.PI / 2; field.rotation.z = Math.PI; field.position.set(0, 0.02, cz); scene.add(field);
  // outfield wall arc
  const wall = new THREE.Mesh(new THREE.CylinderGeometry(47, 47, 4, 64, 1, true, Math.PI * 0.75, Math.PI * 0.5 + Math.PI), new THREE.MeshStandardMaterial({ color: 0x15301a, side: THREE.DoubleSide, roughness: 0.9 }));
  wall.position.set(0, 2, cz); scene.add(wall);
  const wallRim = new THREE.Mesh(new THREE.TorusGeometry(47, 0.08, 6, 120, Math.PI * 1.5), glow(C.gold));
  wallRim.rotation.x = Math.PI / 2; wallRim.rotation.z = Math.PI * 0.75; wallRim.position.set(0, 4, cz); scene.add(wallRim);
  bowl(scene, cz, 54, 54, 10, 0x1b1813, 0.25);
  const tgt = new THREE.Vector3(0, 0, cz);
  for (const [x, z] of [[-58, cz - 20], [58, cz - 20], [-40, cz + 46], [40, cz + 46]]) floodTower(scene, x, z, 42, tgt);
}

function arena(scene, cz, tex, w, d, kind) {
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(w, d), new THREE.MeshStandardMaterial({ map: tex, roughness: kind === "ice" ? 0.35 : 0.5, metalness: 0.05, color: kind === "ice" ? 0xc4ced4 : 0xd0d0d0 }));
  floor.rotation.x = -Math.PI / 2; floor.rotation.z = Math.PI / 2; floor.position.set(0, 0.03, cz); scene.add(floor);
  bowl(scene, cz, w * 0.75, d * 0.68, 12, 0x17140f, 0.2);
  // roof ring of lights
  const ringR = Math.max(w, d) * 0.62;
  const ring = new THREE.Mesh(new THREE.TorusGeometry(ringR, 0.25, 8, 120), glow(0xfff0c8));
  ring.rotation.x = Math.PI / 2; ring.scale.set(w / Math.max(w, d), d / Math.max(w, d), 1); ring.position.set(0, 26, cz); scene.add(ring);
  const pl = new THREE.PointLight(0xffe6b0, 1100, 120, 1.6); pl.position.set(0, 24, cz); scene.add(pl);
  lightCone(scene, new THREE.Vector3(0, 30, cz), new THREE.Vector3(0, 0, cz), 0xfff0d0, 30, Math.max(w, d) * 0.5, 0.012);
  // centre-hung scoreboard: glowing gold bars, no text
  const cube = new THREE.Mesh(new THREE.BoxGeometry(8, 5, 8), new THREE.MeshStandardMaterial({ color: 0x0d0b08, roughness: 0.4 }));
  cube.position.set(0, 18, cz); scene.add(cube);
  for (let f = 0; f < 4; f++) {
    for (let b = 0; b < 5; b++) {
      const bar = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 1 + b * 0.55), glow(b === 4 ? C.goldHi : C.gold, 0.9));
      const a = (f * Math.PI) / 2;
      bar.position.set(Math.sin(a) * 4.02 + Math.cos(a) * (-2.4 + b * 1.2), 16.4 + (1 + b * 0.55) / 2, cz + Math.cos(a) * 4.02 - Math.sin(a) * (-2.4 + b * 1.2));
      bar.rotation.y = a; scene.add(bar);
    }
  }
  if (kind === "court") {
    for (const s of [1, -1]) {
      const pole = new THREE.Mesh(new THREE.BoxGeometry(0.3, 4, 0.3), new THREE.MeshStandardMaterial({ color: 0x222 }));
      pole.position.set(0, 2, cz + s * (d / 2 + 1)); scene.add(pole);
      const board = new THREE.Mesh(new THREE.PlaneGeometry(2.2, 1.4), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.35 }));
      board.position.set(0, 4.4, cz + s * (d / 2 + 0.6)); scene.add(board);
      const hoop = new THREE.Mesh(new THREE.TorusGeometry(0.35, 0.04, 6, 24), glow(0xff7a2f));
      hoop.rotation.x = Math.PI / 2; hoop.position.set(0, 3.9, cz + s * (d / 2 - 0.1)); scene.add(hoop);
    }
  } else {
    const glass = new THREE.Mesh(new THREE.BoxGeometry(w + 1, 2.2, d + 1), new THREE.MeshBasicMaterial({ color: 0xbfe0ff, transparent: true, opacity: 0.07, side: THREE.BackSide, depthWrite: false }));
    glass.position.set(0, 1.1, cz); scene.add(glass);
    const boards = new THREE.Mesh(new THREE.BoxGeometry(w + 0.6, 1, d + 0.6), new THREE.MeshStandardMaterial({ color: 0xe8e8e8, side: THREE.BackSide }));
    boards.position.set(0, 0.5, cz); scene.add(boards);
  }
}

/** The model: probability bars rising out of the dark and a calibration ring (the Goldglitch mark). */
function observatory(scene, cz) {
  const bars = [];
  for (let i = 0; i < 160; i++) {
    const a = rr(0, Math.PI * 2), r = rr(14, 60);
    const h = rr(1, 22) * Math.exp(-r / 60);
    const b = new THREE.Mesh(new THREE.BoxGeometry(0.8, 1, 0.8), glow(rnd() < 0.2 ? C.goldHi : C.gold, rr(0.35, 0.9)));
    b.position.set(Math.sin(a) * r, 0, cz + Math.cos(a) * r); b.userData.h = h; b.userData.p = rr(0, 6);
    scene.add(b); bars.push(b);
  }
  const ring = new THREE.Group();
  const outer = new THREE.Mesh(new THREE.TorusGeometry(12, 0.35, 12, 160), glow(C.gold));
  const inner = new THREE.Mesh(new THREE.TorusGeometry(9, 0.12, 8, 160), glow(C.gold, 0.35));
  ring.add(outer, inner);
  [[-4.2, 0.45, 5], [0, 0.7, 8.5], [4.2, 1, 12]].forEach(([x, o, h]) => {
    const bar = new THREE.Mesh(new THREE.BoxGeometry(2.6, h, 0.6), glow(C.gold, o));
    bar.position.set(x, -7 + h / 2, 0); ring.add(bar);
  });
  ring.position.set(0, 16, cz - 30); scene.add(ring);
  // calibration diagonal: dots on y = x, glowing
  for (let i = 0; i <= 20; i++) {
    const d = new THREE.Mesh(new THREE.SphereGeometry(0.35, 10, 8), glow(C.goldHi));
    d.position.set(-20 + i * 2, 1 + i * 1.1, cz + 10 - i * 2); scene.add(d);
  }
  return { bars, ring };
}

/** Data stream: particles that ride the camera path ahead, red at the start, gold after the noise. */
function dataStream(scene, curve) {
  const N = 2600;
  const pos = new Float32Array(N * 3), col = new Float32Array(N * 3);
  const base = [];
  for (let i = 0; i < N; i++) base.push({ u: rnd(), ox: (rnd() < 0.5 ? -1 : 1) * rr(3, 16), oy: rr(-5, 9), sp: rr(0.004, 0.012) });
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
  const pts = new THREE.Points(geo, new THREE.PointsMaterial({ size: 0.13, vertexColors: true, transparent: true, opacity: 0.9, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false }));
  scene.add(pts);
  const red = new THREE.Color(C.flare), gold = new THREE.Color(C.gold), tmp = new THREE.Color(), p = new THREE.Vector3();
  return (t) => {
    for (let i = 0; i < N; i++) {
      const b = base[i];
      const u = (b.u + t * b.sp * 40) % 1;
      curve.getPointAt(u, p);
      pos[i * 3] = p.x + b.ox; pos[i * 3 + 1] = Math.max(0.3, p.y * 0.35 + b.oy); pos[i * 3 + 2] = p.z;
      const k = Math.min(1, Math.max(0, (u - 0.1) / 0.08));
      tmp.copy(red).lerp(gold, k);
      col[i * 3] = tmp.r; col[i * 3 + 1] = tmp.g; col[i * 3 + 2] = tmp.b;
    }
    geo.attributes.position.needsUpdate = true;
    geo.attributes.color.needsUpdate = true;
  };
}

// ---------- film ----------
export function createFilm(canvas, W, H) {
  seed = 7;
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(1);
  renderer.setSize(W, H, false);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(C.void);
  scene.fog = new THREE.FogExp2(C.void, 0.0105);
  scene.add(new THREE.HemisphereLight(0x3a3024, 0x050403, 0.6));

  ground(scene);
  const screens = noiseCity(scene, 0);
  stadium(scene, -SEG);
  ballpark(scene, -SEG * 2);
  arena(scene, -SEG * 3, courtTex(), 28, 15, "court");
  arena(scene, -SEG * 4, iceTex(), 30, 13, "ice");
  const obs = observatory(scene, -SEG * 5);

  // distant warm lights scattered over the ground: the world feels inhabited between venues
  {
    const n = 1800, a = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) { const x = (rnd() < 0.5 ? -1 : 1) * rr(26, 260); a[i * 3] = x; a[i * 3 + 1] = rr(0.3, 2.5); a[i * 3 + 2] = rr(-SEG * 5.6, 80); }
    const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.BufferAttribute(a, 3));
    scene.add(new THREE.Points(g, new THREE.PointsMaterial({ color: 0xd4af37, size: 0.5, transparent: true, opacity: 0.8, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false })));
  }
  // stars / haze specks high up
  {
    const n = 1500, a = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) { a[i * 3] = rr(-300, 300); a[i * 3 + 1] = rr(60, 180); a[i * 3 + 2] = rr(-SEG * 6, 120); }
    const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.BufferAttribute(a, 3));
    scene.add(new THREE.Points(g, new THREE.PointsMaterial({ color: 0x8c8576, size: 0.6, transparent: true, opacity: 0.5, fog: false })));
  }

  // Camera path: forward only (z decreases monotonically). Swoop over each venue, low pass across the field.
  const K = [
    [0, 9, 70], [-3, 7, 25], [2, 10, -30], [0, 30, -SEG + 62], [0, 9, -SEG + 22], [3, 4.5, -SEG - 10], [-2, 14, -SEG - 52],
    [0, 26, -SEG * 2 + 66], [-8, 8, -SEG * 2 + 20], [6, 5, -SEG * 2 - 14], [0, 16, -SEG * 2 - 56],
    [0, 20, -SEG * 3 + 40], [0, 9, -SEG * 3 + 12], [2, 5, -SEG * 3 - 6], [0, 12, -SEG * 3 - 36],
    [0, 18, -SEG * 4 + 40], [-3, 7, -SEG * 4 + 12], [3, 3.5, -SEG * 4 - 8], [0, 12, -SEG * 4 - 38],
    [0, 22, -SEG * 5 + 70], [0, 14, -SEG * 5 + 30], [0, 15, -SEG * 5 - 2],
  ].map(([x, y, z]) => new THREE.Vector3(x, y, z));
  const curve = new THREE.CatmullRomCurve3(K, false, "centripetal", 0.5);
  const stream = dataStream(scene, curve);

  const camera = new THREE.PerspectiveCamera(W > H ? 50 : 68, W / H, 0.1, 900);
  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));
  composer.addPass(new UnrealBloomPass(new THREE.Vector2(W, H), 0.7, 0.5, 0.86));
  composer.addPass(new ShaderPass({
    uniforms: { tDiffuse: { value: null }, uT: { value: 0 } },
    vertexShader: "varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }",
    fragmentShader: `uniform sampler2D tDiffuse; uniform float uT; varying vec2 vUv;
      float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233)) + uT*7.) * 43758.5453); }
      void main(){ vec4 c = texture2D(tDiffuse, vUv);
        float v = smoothstep(1.15, .35, length(vUv-.5)*1.25); c.rgb *= mix(.55, 1., v);
        c.rgb += (h(vUv*vec2(1920.,1080.))-.5)*.035; gl_FragColor = c; }`,
  }));
  composer.addPass(new OutputPass());

  const look = new THREE.Vector3(), here = new THREE.Vector3();
  function renderAt(t) {
    const u = 0.0005 + t * 0.999;
    curve.getPointAt(u, here);
    curve.getPointAt(Math.min(1, u + 0.018), look);
    look.y -= 2.2;
    if (t > 0.9) look.lerp(obs.ring.position, Math.min(1, (t - 0.9) / 0.08)); // land on the mark
    camera.position.copy(here);
    camera.lookAt(look);
    // flicker the noise screens; fade them as the camera leaves the city
    screens.forEach((s, i) => { s.material.color.setScalar(0.55 + 0.45 * Math.abs(Math.sin(t * 90 + i * 1.7))); });
    obs.bars.forEach((b) => { const k = Math.min(1, Math.max(0, (t - 0.8) / 0.12)); const hh = Math.max(0.05, b.userData.h * k * (0.85 + 0.15 * Math.sin(t * 40 + b.userData.p))); b.scale.y = hh; b.position.y = hh / 2; });
    obs.ring.rotation.y = Math.sin(t * 6) * 0.25;
    stream(t);
    composer.passes[2].uniforms.uT.value = t;
    composer.render();
  }
  return { renderAt };
}
