"""La oficina de EGG en 3D isométrico (estilo Habbo), con datos reales del PC.

Zonas de trabajo por departamento (Dirección, Estrategia Económica, Datos y Tendencias, Mercados Internacionales,
Creativo, Sala de juntas, Biblioteca, Estudio de Lives) y zonas de esparcimiento mental: jardín, zona zen con estanque
koi y lounge. Quien está trabajando (habló en los últimos 40 min) aparece en su escritorio con "TRABAJANDO"; el resto
descansa en el jardín, la zona zen o el lounge. Pasa el mouse o toca a alguien para ver qué dijo.

    python goldglitch_oficina.py          # genera oficina.html
    python goldglitch_oficina.py --abrir  # y la abre en el navegador
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys
import time
import webbrowser
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "oficina.html")
TZ = timezone(timedelta(hours=-5))
ACTIVE_MIN = 40


def load(name: str, default):
    try:
        return json.load(open(os.path.join(HERE, name), encoding="utf-8"))
    except (OSError, ValueError):
        return default


LOOKS = {  # hair, skin, top, pants
    "director": ("#2b1a12", "#e9b48f", "#d4af37", "#1c1c24"), "sofia": ("#c99a5b", "#f1c9a5", "#f3ecdc", "#2a2a33"),
    "diseno": ("#14100c", "#d9a17d", "#111111", "#3a2f25"), "analista": ("#5a3420", "#eebd99", "#3b82f6", "#1e293b"),
    "viral": ("#e8c07a", "#f3cfb0", "#ff4d8d", "#1f2937"), "copy": ("#3a2416", "#d79f78", "#a78bfa", "#111827"),
    "video": ("#0d0d0d", "#c98c63", "#ef4444", "#0f172a"), "comunidad": ("#7a4a2a", "#efc3a0", "#22c55e", "#334155"),
    "marca": ("#1a1a1a", "#e6b896", "#0f766e", "#111827"), "viralidad": ("#b8325a", "#f0c4a2", "#f59e0b", "#1f2937"),
    "seo": ("#2e1b10", "#d29a74", "#6366f1", "#18181b"), "audiencia": ("#4b2e1c", "#c98e66", "#16a34a", "#1c1917"),
    "tiburon": ("#151515", "#c98a62", "#1e3a8a", "#0a0a0a"), "parche": ("#3b2416", "#b97a52", "#16a34a", "#1e293b"),
    "unit_econ": ("#1f1f1f", "#d6a07a", "#334155", "#0f172a"), "econometria": ("#2a1a10", "#f0c6a4", "#7c3aed", "#18181b"),
    "pricing": ("#3d2817", "#c88f68", "#0ea5e9", "#1e293b"), "internacional": ("#5b3a1e", "#e9b892", "#dc2626", "#111827"),
    "mx_us": ("#0f0f0f", "#b8774f", "#15803d", "#1c1917"), "conosur_es": ("#d8b26e", "#f2cdb0", "#2563eb", "#1f2937"),
    "segmentos": ("#2b2b2b", "#d19a72", "#f97316", "#111827"), "neuro": ("#101010", "#e2ad88", "#06b6d4", "#0b1220"),
    "disrupcion": ("#7c3aed", "#e8b691", "#facc15", "#111111"), "narrativa": ("#8a5a33", "#f2cfb3", "#be185d", "#27272a"),
}
ROOM_OF = {  # department → room in the floor plan (10-agent company)
    "direccion": ["econ_crecimiento", "econ_consumidor"],
    "economia": [],
    "datos": ["ig_contenido", "ig_crecimiento"],
    "mercados": ["yt_contenido", "yt_busqueda"],
    "creativo": ["tt_contenido", "tt_crecimiento"],
    "juntas": ["fb_contenido", "fb_comunidad"],
}


def statuses(names: dict[str, str]) -> dict[str, tuple[str, str]]:
    try:
        lines = open(os.path.join(HERE, "redes.log"), encoding="utf-8").read().splitlines()[-4000:]
    except OSError:
        return {}
    inv = {n: k for k, n in names.items()}
    out = {}
    for ln in lines:
        m = re.match(r"\[(\d{4}-\d\d-\d\d \d\d:\d\d)\]\s+\[([^\]]+)\]\s*(.*)", ln)
        if m and m.group(2).strip() in inv:
            out[inv[m.group(2).strip()]] = (m.group(1), re.sub(r"^\([^)]*\)\s*", "", m.group(3)))
    return out


def roster() -> dict:
    try:
        import goldglitch_growth as G
        return G.roster()["miembros"]
    except Exception:
        return load("redes_comite.json", {}).get("miembros") or {}


def data() -> dict:
    now = datetime.now(TZ)
    today = now.strftime("%Y-%m-%d")
    members = roster()
    names = {k: v.get("nombre", "") for k, v in members.items() if v.get("nombre")}
    st = statuses(names)
    people = []
    for k, m in members.items():
        t, said = st.get(k, ("", ""))
        active = False
        if t:
            try:
                active = now - datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=TZ) < timedelta(minutes=ACTIVE_MIN)
            except ValueError:
                pass
        room = next((r for r, ks in ROOM_OF.items() if k in ks), "juntas")
        people.append({"k": k, "n": m.get("nombre") or k, "r": m.get("rol", ""), "room": room, "male": m.get("genero") == "h",
                       "look": LOOKS.get(k) or ("#3b2a1f", "#e0aa84", f"hsl({sum(map(ord, k)) * 37 % 360},70%,55%)", "#1f2937"),
                       "t": t[11:] if t else "", "day": t[:10], "said": said[:400], "active": active})
    state = load("redes_estado.json", {})
    posts = state.get("plan") if state.get("day") == today else []
    try:
        lines = open(os.path.join(HERE, "redes.log"), encoding="utf-8").read().splitlines()
    except OSError:
        lines = []
    last = lines[-1][1:17] if lines else ""
    try:
        live = bool(last) and now - datetime.strptime(last, "%Y-%m-%d %H:%M").replace(tzinfo=TZ) < timedelta(minutes=25)
    except ValueError:
        live = False
    trends = load("redes_tendencias.json", {})
    actas = sorted(glob.glob(os.path.join(HERE, "redes_comite_actas", "*.md")), key=os.path.getmtime)
    acta = open(actas[-1], encoding="utf-8").read() if actas else ""
    plan = load("redes_plan_comite.json", {})
    return {
        "now": now.strftime("%d/%m %H:%M"), "people": people, "live": live,
        "plan": [{"time": p.get("time"), "type": p.get("type"), "status": p.get("status"), "angle": (p.get("angle") or "")[:80],
                  "mercado": p.get("mercado"), "done": list(p.get("done") or {})} for p in posts or []],
        "done": sum(1 for p in posts or [] if p.get("status") == "done"), "total": len(posts or []),
        "trends": {"age": int((time.time() - float(trends["ts"])) / 60) if trends.get("ts") else None,
                   "google": [t["busqueda"] for t in ((trends.get("google") or {}).get("Colombia") or [])[:6]],
                   "futbol": [f"{a['liga']}: {a['titular']}" for a in (trends.get("futbol") or [])[:4]],
                   "songs": ((trends.get("canciones_tiktok") or []) + (trends.get("canciones") or []))[:5],
                   "tags": (trends.get("tiktok") or [])[:8]},
        "seo": (plan.get("seo") or {}).get("hashtags", [])[:10] if plan.get("day") == today else [],
        "econ": load("redes_plan_economico.json", {}),
        "decisions": (load("redes_decisiones.json", []) or [])[-4:][::-1],
        "acta": {"title": os.path.basename(actas[-1])[:-3] if actas else "", "body": re.split(r"\n## ", acta)[0].split("\n", 1)[-1].strip()[:900]},
        "log": [l[:170] for l in lines[-7:]],
        "books": sorted(((v[-1].get("dia", ""), names.get(k, k), v[-1].get("texto", "")[:160])
                         for k, v in (load("redes_cuadernos.json", {}) or {}).items() if v), reverse=True)[:4],
    }


PAGE = r"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta http-equiv="refresh" content="60">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Oficina EGG</title>
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&display=swap" rel="stylesheet">
<style>
:root{--gold:#d4af37;--ink:#f3ecdc;--panel:#0f1b26;--edge:#6ec6ff}
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0a1118;color:var(--ink);font-family:VT323,monospace;font-size:19px}
.top{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;padding:12px 16px}
h1{font-family:'Press Start 2P',monospace;font-size:15px;color:var(--gold);letter-spacing:2px}
.chips{display:flex;gap:8px;flex-wrap:wrap}.chip{border:2px solid #24425a;background:#0f1b26;padding:4px 10px}.chip b{color:var(--gold)}
.stage{position:relative;max-width:1720px;margin:0 auto}
canvas{display:block;width:100%;height:auto;image-rendering:pixelated;cursor:default}
.win{position:absolute;background:#0d1a24ee;border:3px solid var(--edge);box-shadow:0 0 0 3px #000,0 10px 30px #0008;font-size:17px}
.win h3{font-family:'Press Start 2P';font-size:9px;background:#163246;color:#bfe6ff;padding:6px 8px;display:flex;justify-content:space-between}
.chat{left:1.2%;top:2%;width:min(420px,40%)}.chat div.l{padding:2px 8px;line-height:1.1}.chat b{color:#7cffb0}
.board{right:1.2%;bottom:3%;width:min(340px,36%)}#board>div{display:flex;justify-content:space-between;gap:10px;padding:2px 12px;font-size:21px;line-height:1.1}
.board .ok{color:#7cff9b}.board .warn{color:#ffb86b}
.tip{position:absolute;pointer-events:none;display:none;width:300px;z-index:5}.tip p{padding:6px 9px;line-height:1.1}.tip small{color:#9fc3d9}
.cards{max-width:1720px;margin:14px auto;padding:0 16px 30px;display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px}
.card{background:var(--panel);border:3px solid #24425a;padding:10px 12px;line-height:1.15}
.card h4{font-family:'Press Start 2P';font-size:9px;color:var(--gold);margin-bottom:8px}
.card li{list-style:none;padding:3px 0;border-bottom:1px dashed #ffffff14}.card span{color:var(--gold)}
.bar{display:flex;align-items:center;gap:6px;font-size:16px}.bar i{display:block;height:9px;background:var(--gold);border:2px solid #000}
@media(max-width:800px){.chat,.board{position:static;width:auto;margin:8px 16px}}
</style></head><body>
<div class="top"><h1>EGG · FIRMA DE MARKETING</h1><div class="chips" id="chips"></div></div>
<div class="stage"><canvas id="c"></canvas>
 <div class="win chat"><h3><span>CANAL DE LA FIRMA</span><span>▢ ✕</span></h3><div id="chat"></div></div>
 <div class="win board"><h3><span>TABLERO DE CONTROL</span><span>▢</span></h3><div id="board"></div></div>
 <div class="win tip" id="tip"></div></div>
<div class="cards" id="cards"></div>
<script>
const D = __DATA__;
const cv = document.getElementById('c'), cx = cv.getContext('2d');
const TW = 64, TH = 32, GW = 30, GH = 24, W = (GW + GH) * TW / 2 + 40, H = (GW + GH) * TH / 2 + 190;
const OX = GH * TW / 2 + 20, OY = 150;
cv.width = W; cv.height = H;
const iso = (x, y, z = 0) => [OX + (x - y) * TW / 2, OY + (x + y) * TH / 2 - z];
const up = s => String(s).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase();   // pixel font has no accents
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function shade(hex, f) { const n = parseInt(hex.slice(1), 16); let r = n >> 16, g = n >> 8 & 255, b = n & 255;
  r = Math.min(255, r * f | 0); g = Math.min(255, g * f | 0); b = Math.min(255, b * f | 0); return `rgb(${r},${g},${b})`; }
function poly(pts, fill, stroke) { cx.beginPath(); pts.forEach(([a, b], i) => i ? cx.lineTo(a, b) : cx.moveTo(a, b)); cx.closePath();
  cx.fillStyle = fill; cx.fill(); if (stroke) { cx.strokeStyle = stroke; cx.lineWidth = 1; cx.stroke(); } }
function tile(x, y, c, w = 1, d = 1) { poly([iso(x, y), iso(x + w, y), iso(x + w, y + d), iso(x, y + d)], c, 'rgba(0,0,0,.18)'); }
function box(x, y, w, d, h, c, z = 0, faceDeco) {
  const t = [iso(x, y, z + h), iso(x + w, y, z + h), iso(x + w, y + d, z + h), iso(x, y + d, z + h)];
  poly([iso(x, y + d, z), iso(x + w, y + d, z), t[2], t[3]], shade(c, .72), '#0006');      // left face
  poly([iso(x + w, y, z), iso(x + w, y + d, z), t[2], t[1]], shade(c, .55), '#0006');      // right face
  poly(t, shade(c, 1.08), '#0006');                                                         // top
  if (faceDeco) faceDeco(x, y, w, d, h, z);
}
function ell(x, y, rx, ry, c, z = 0) { const [a, b] = iso(x, y, z); cx.beginPath(); cx.ellipse(a, b, rx, ry, 0, 0, 7); cx.fillStyle = c; cx.fill(); }
// -------------------------------------------------- floor plan
const ROOMS = {
  direccion: {x: 0, y: 0, w: 8, d: 7, floor: ['#6b4423', '#764b27'], name: 'DIRECCIÓN · ECONOMISTAS'},
  economia: {x: 8, y: 0, w: 10, d: 7, floor: ['#8e9aa6', '#97a3ae'], name: 'SALA DE ESTRATEGIA'},
  datos: {x: 18, y: 0, w: 12, d: 7, floor: ['#7c8a99', '#8593a1'], name: 'INSTAGRAM'},
  mercados: {x: 0, y: 7, w: 8, d: 8, floor: ['#3b4f7a', '#425883'], name: 'YOUTUBE'},
  pasillo: {x: 8, y: 7, w: 14, d: 3, floor: ['#3a3f47', '#41464f']},
  juntas: {x: 8, y: 10, w: 8, d: 6, floor: ['#7a4e2a', '#83552e'], name: 'FACEBOOK'},
  biblio: {x: 16, y: 10, w: 6, d: 6, floor: ['#5c3b22', '#654126'], name: 'BIBLIOTECA'},
  creativo: {x: 22, y: 7, w: 8, d: 9, floor: ['#2e3a66', '#34416f'], name: 'TIKTOK'},
  jardin: {x: 0, y: 15, w: 11, d: 9, floor: ['#3f8f3a', '#46993f'], name: 'JARDÍN'},
  zen: {x: 11, y: 16, w: 9, d: 8, floor: ['#d9c9a0', '#e1d2ab'], name: 'ZONA ZEN'},
  lounge: {x: 20, y: 16, w: 10, d: 8, floor: ['#5a2f4a', '#633452'], name: 'LOUNGE Y LIVES'},
  hall2: {x: 8, y: 16, w: 3, d: 8, floor: ['#3f8f3a', '#46993f']},
};
const drawables = [];   // [depth, fn]
const put = (depth, fn) => drawables.push([depth, fn]);
function floors() {
  for (const r of Object.values(ROOMS)) for (let i = 0; i < r.w; i++) for (let j = 0; j < r.d; j++)
    tile(r.x + i, r.y + j, r.floor[(i + j) % 2]);
  // zen sand rake lines
  cx.strokeStyle = 'rgba(120,100,60,.35)'; cx.lineWidth = 1;
  for (let j = 0; j < 8 * 3; j++) { const y = 16 + j / 3; cx.beginPath(); let p = iso(11, y); cx.moveTo(...p); p = iso(20, y); cx.lineTo(...p); cx.stroke(); }
  // rugs
  tile(1.5, 2.5, '#2b3a6b', 5, 3); tile(23, 9, '#1d2550', 6, 5); tile(21, 18, '#3b1e33', 8, 5);
}
function walls() {
  // back walls (Habbo style) along y=0 and x=0
  for (let i = 0; i < GW; i++) { const c = i % 2 ? '#c9d4dd' : '#c2ced8';
    poly([iso(i, 0, 0), iso(i + 1, 0, 0), iso(i + 1, 0, 110), iso(i, 0, 110)], c, '#0003'); }
  for (let j = 0; j < GH; j++) { const c = j % 2 ? '#aebbc6' : '#a7b5c1';
    poly([iso(0, j, 0), iso(0, j + 1, 0), iso(0, j + 1, 110), iso(0, j, 110)], c, '#0003'); }
  // windows on the back wall
  for (const i of [3, 11, 15, 21, 26]) { poly([iso(i, 0, 40), iso(i + 2, 0, 40), iso(i + 2, 0, 95), iso(i, 0, 95)], '#7ec8f0', '#2a5574');
    poly([iso(i + 1, 0, 40), iso(i + 1.05, 0, 40), iso(i + 1.05, 0, 95), iso(i + 1, 0, 95)], '#2a5574'); }
  for (const j of [17, 20]) poly([iso(0, j, 40), iso(0, j + 2, 40), iso(0, j + 2, 95), iso(0, j, 95)], '#9be7a8', '#2f6b3a');
  // department sign plates on the back wall
  const sign = (x, y, txt, onX) => { const [a, b] = onX ? iso(x, 0, 104) : iso(0, y, 104);
    cx.font = "9px 'Press Start 2P'"; const w = cx.measureText(txt).width + 14;
    cx.fillStyle = '#0d1a24'; cx.fillRect(a - w / 2, b - 6, w, 18); cx.strokeStyle = '#d4af37'; cx.strokeRect(a - w / 2, b - 6, w, 18);
    cx.fillStyle = '#d4af37'; cx.textAlign = 'center'; cx.fillText(up(txt), a, b + 7); };
  sign(4, 0, 'DIRECCIÓN', true); sign(13, 0, 'ECONOMÍA', true); sign(24, 0, 'DATOS Y TENDENCIAS', true);
  sign(0, 11, 'MERCADOS', false); sign(0, 19.5, 'JARDÍN', false);
}
function partitions() {   // low glass partitions with doorways
  const glass = (x, y, w, d) => put(x + w + y + d - .5, () => box(x, y, w, d, 34, '#9fd3ef'));
  glass(8, 0.0, .12, 2.5); glass(8, 4.5, .12, 2.5); glass(18, 0, .12, 2.5); glass(18, 4.5, .12, 2.5);
  glass(0, 7, 3, .12); glass(5, 7, 3, .12); glass(8, 7, .12, 3);
  glass(22, 7, .12, 3); glass(22, 12.5, .12, 3.5); glass(16, 10, .12, 2); glass(16, 13.5, .12, 2.5);
  glass(8, 10, 3, .12); glass(13, 10, 3, .12); glass(23, 7, 2, .12); glass(27, 7, 3, .12);
}
// -------------------------------------------------- furniture
const T = 0;  // shorthand
function desk(x, y, screen, dir = 0) {
  put(x + y + 1.4, () => {
    box(x, y, 1.6, .8, 18, '#a8743f');
    box(x + .25, y + .1, .45, .12, 16, '#1b1b1b', 18); box(x + .85, y + .1, .45, .12, 16, '#1b1b1b', 18);
    poly([iso(x + .27, y + .22, 21), iso(x + .68, y + .22, 21), iso(x + .68, y + .22, 33), iso(x + .27, y + .22, 33)], screen);
    poly([iso(x + .87, y + .22, 21), iso(x + 1.28, y + .22, 21), iso(x + 1.28, y + .22, 33), iso(x + .87, y + .22, 33)], screen);
    box(x + .55, y + .45, .5, .25, 2, '#333', 18);
  });
  put(x + y + 2.3, () => { box(x + .55, y + 1.05, .5, .5, 10, '#1f3b73'); box(x + .55, y + 1.45, .5, .1, 22, '#1f3b73', 10); });
  return [x + .8, y + 1.3];
}
function plant(x, y, big) { put(x + y + .8, () => { box(x, y, .5, .5, 12, '#a0522d');
  const [a, b] = iso(x + .25, y + .25, big ? 40 : 26); cx.fillStyle = '#2f9e44';
  for (const [dx, dy, r] of [[0, 0, big ? 14 : 10], [-8, 6, 8], [8, 6, 8], [0, -10, 8]]) { cx.beginPath(); cx.arc(a + dx, b + dy, r, 0, 7); cx.fill(); }
  cx.fillStyle = '#3fbf55'; cx.beginPath(); cx.arc(a - 3, b - 4, 5, 0, 7); cx.fill(); }); }
function tree(x, y) { put(x + y + 1, () => { box(x + .35, y + .35, .3, .3, 30, '#6b4226');
  const [a, b] = iso(x + .5, y + .5, 58); const g = ['#1f7a34', '#279444', '#33ad52'];
  [[0, 8, 26], [-14, -4, 20], [14, -4, 20], [0, -18, 18]].forEach(([dx, dy, r], i) => { cx.fillStyle = g[i % 3]; cx.beginPath(); cx.arc(a + dx, b + dy, r, 0, 7); cx.fill(); });
  cx.fillStyle = '#ffffff22'; cx.beginPath(); cx.arc(a - 8, b - 14, 7, 0, 7); cx.fill(); }); }
function bush(x, y, c = '#2e9440', flowers) { put(x + y + .5, () => { const [a, b] = iso(x + .5, y + .5, 10);
  cx.fillStyle = c; cx.beginPath(); cx.ellipse(a, b, 22, 13, 0, 0, 7); cx.fill();
  if (flowers) for (let i = 0; i < 7; i++) { cx.fillStyle = flowers[i % flowers.length]; cx.fillRect(a - 16 + i * 5, b - 6 + (i % 3) * 4, 4, 4); } }); }
function bench(x, y) { put(x + y + 1.2, () => { box(x, y, 1.6, .5, 10, '#8a5a2b'); box(x, y, 1.6, .12, 22, '#8a5a2b', 10); }); return [x + .8, y + .55]; }
function sofa(x, y, c) { put(x + y + 1.5, () => { box(x, y, 2, .9, 12, c); box(x, y, 2, .25, 26, c, 0); box(x, y, .25, .9, 18, c); box(x + 1.75, y, .25, .9, 18, c); }); return [x + 1, y + .6]; }
function cushion(x, y, c) { put(x + y + .4, () => box(x, y, .6, .6, 5, c)); return [x + .3, y + .3]; }
function shelf(x, y, w = 2) { put(x + y + w, () => box(x, y, w, .5, 80, '#5b3a1e', 0, () => {
  for (let r = 0; r < 4; r++) for (let i = 0; i < w * 6; i++) { const cols = ['#c0392b', '#2e86c1', '#d4ac0d', '#27ae60', '#8e44ad'];
    const xx = x + .08 + i * (w - .16) / (w * 6); poly([iso(xx, y + .5, 8 + r * 18), iso(xx + .12, y + .5, 8 + r * 18), iso(xx + .12, y + .5, 20 + r * 18), iso(xx, y + .5, 20 + r * 18)], cols[(i + r) % 5]); } })); }
function screenWall(x, y, w, lines) { put(x + y + w, () => { box(x, y, w, .2, 70, '#111', 12);
  poly([iso(x + .1, y + .2, 18), iso(x + w - .1, y + .2, 18), iso(x + w - .1, y + .2, 78), iso(x + .1, y + .2, 78)], '#06222e');
  cx.save(); const [a, b] = iso(x + .25, y + .2, 70); cx.font = "13px VT323"; cx.fillStyle = '#7ff3ff';
  cx.setTransform(1, 0.5, 0, 1, a, b); lines.slice(0, 4).forEach((l, i) => cx.fillText(String(l).slice(0, 38), 0, i * 13)); cx.restore(); }); }
function whiteboard(x, y, w) { put(x + y + w, () => { box(x, y, w, .1, 60, '#f4f4f4', 14);
  cx.strokeStyle = '#d4402a'; cx.lineWidth = 2; cx.beginPath(); const p = [[.2, 30], [.5, 42], [.8, 38], [1.1, 55], [1.4, 50], [1.7, 66]];
  p.forEach(([dx, z], i) => { const [a, b] = iso(x + dx * w / 2, y + .1, z); i ? cx.lineTo(a, b) : cx.moveTo(a, b); }); cx.stroke();
  [[.3, 1], [.7, 1.6], [1.1, 1.2], [1.5, 2]].forEach(([dx, hh]) => { const [a, b] = iso(x + dx * w / 2, y + .1, 22); cx.fillStyle = '#2e86c1'; cx.fillRect(a, b - hh * 9, 6, hh * 9); }); }); }
function roundTable(x, y) { put(x + y + 1, () => { box(x + .85, y + .85, .3, .3, 16, '#222'); ell(x + 1, y + 1, 54, 27, '#1e2a4a', 18); ell(x + 1, y + 1, 50, 24, '#26365e', 19);
  const [a, b] = iso(x + 1, y + 1, 19); cx.font = "8px 'Press Start 2P'"; cx.fillStyle = '#d4af37'; cx.textAlign = 'center'; cx.fillText('EGG', a, b + 3); });
  return [[x - .2, y + 1], [x + 1, y - .2], [x + 2.2, y + 1], [x + 1, y + 2.2], [x + .1, y + .1], [x + 1.9, y + 1.9]]; }
function globe(x, y) { put(x + y + 1, () => { box(x + .3, y + .3, .4, .4, 14, '#5b3a1e'); const [a, b] = iso(x + .5, y + .5, 34);
  cx.fillStyle = '#2e86c1'; cx.beginPath(); cx.arc(a, b, 15, 0, 7); cx.fill(); cx.fillStyle = '#27ae60';
  cx.fillRect(a - 8, b - 6, 7, 5); cx.fillRect(a + 2, b + 1, 6, 6); cx.fillRect(a - 3, b + 6, 4, 3); }); }
function pond(x, y, w, d, t) { put(x + y - 1, () => {
  const [a, b] = iso(x + w / 2, y + d / 2); cx.fillStyle = '#6d6d6d'; cx.beginPath(); cx.ellipse(a, b, w * 22 + 8, d * 11 + 5, 0, 0, 7); cx.fill();
  const g = cx.createRadialGradient(a, b, 4, a, b, w * 22); g.addColorStop(0, '#5fd3e6'); g.addColorStop(1, '#1f7ea8');
  cx.fillStyle = g; cx.beginPath(); cx.ellipse(a, b, w * 22, d * 11, 0, 0, 7); cx.fill();
  cx.strokeStyle = 'rgba(255,255,255,.35)'; for (let i = 0; i < 3; i++) { const r = ((t / 40 + i * 12) % 36); cx.beginPath(); cx.ellipse(a + 10, b - 2, r, r / 2, 0, 0, 7); cx.stroke(); }
  for (let i = 0; i < 3; i++) { const ang = t / (900 + i * 250) + i * 2; cx.fillStyle = i ? '#ff7a1a' : '#fff1e0';
    cx.beginPath(); cx.ellipse(a + Math.cos(ang) * w * 13, b + Math.sin(ang) * d * 6, 6, 3, ang, 0, 7); cx.fill(); }
  cx.fillStyle = '#3aa655'; [[-.3, .1], [.25, -.25]].forEach(([dx, dy]) => { cx.beginPath(); cx.ellipse(a + dx * w * 22, b + dy * d * 11, 7, 4, 0, 0, 7); cx.fill(); }); }); }
function stone(x, y, s = 1) { put(x + y + .3, () => { const [a, b] = iso(x, y, 4); cx.fillStyle = '#7d7d7d'; cx.beginPath(); cx.ellipse(a, b, 12 * s, 7 * s, 0, 0, 7); cx.fill(); cx.fillStyle = '#9a9a9a'; cx.beginPath(); cx.ellipse(a - 2, b - 2, 7 * s, 4 * s, 0, 0, 7); cx.fill(); }); }
function bamboo(x, y) { put(x + y + .5, () => { for (let i = 0; i < 4; i++) box(x + i * .14, y + (i % 2) * .12, .08, .08, 70 + i * 9, '#5fa83a'); }); }
function bonsai(x, y) { put(x + y + .6, () => { box(x, y, .5, .5, 8, '#2b2b2b'); const [a, b] = iso(x + .25, y + .25, 22);
  cx.fillStyle = '#5b3a1e'; cx.fillRect(a - 1, b, 3, 8); cx.fillStyle = '#2f7d32'; cx.beginPath(); cx.ellipse(a - 6, b - 2, 9, 5, 0, 0, 7); cx.ellipse(a + 7, b - 6, 8, 4, 0, 0, 7); cx.fill(); }); }
function fountain(x, y, t) { put(x + y + 1, () => { box(x, y, 1.2, 1.2, 10, '#bfc6cc'); ell(x + .6, y + .6, 30, 15, '#5fd3e6', 10);
  box(x + .5, y + .5, .2, .2, 26, '#bfc6cc', 10); const [a, b] = iso(x + .6, y + .6, 40); cx.fillStyle = '#bff3ff';
  for (let i = 0; i < 6; i++) { const k = ((t / 300 + i / 6) % 1); cx.fillRect(a + Math.sin(i) * k * 16, b + k * k * 22, 2, 2); } }); }
function bar(x, y) { put(x + y + 2, () => { box(x, y, 2.4, .8, 26, '#3a2a1e'); box(x + .2, y + .1, .4, .3, 14, '#c0c0c0', 26); box(x + 1.4, y + .1, .3, .3, 8, '#fff', 26); }); }
function futbolin(x, y) { put(x + y + 1.5, () => { box(x, y, 1.6, .8, 18, '#1d6b2a'); poly([iso(x + .1, y + .1, 18.5), iso(x + 1.5, y + .1, 18.5), iso(x + 1.5, y + .7, 18.5), iso(x + .1, y + .7, 18.5)], '#2fa84a');
  for (let i = 1; i < 5; i++) { const [a1, b1] = iso(x + i * .32, y - .1, 22), [a2, b2] = iso(x + i * .32, y + .9, 22); cx.strokeStyle = '#ccc'; cx.beginPath(); cx.moveTo(a1, b1); cx.lineTo(a2, b2); cx.stroke(); } }); return [x + .8, y + 1.2]; }
function liveStudio(x, y) { put(x + y + 1, () => { box(x + .45, y + .45, .1, .1, 46, '#222'); const [a, b] = iso(x + .5, y + .5, 60);
  cx.strokeStyle = '#fff7d6'; cx.lineWidth = 6; cx.beginPath(); cx.arc(a, b, 14, 0, 7); cx.stroke(); cx.lineWidth = 1;
  cx.fillStyle = '#ff2d55'; cx.fillRect(a + 22, b - 26, 46, 12); cx.fillStyle = '#fff'; cx.font = "7px 'Press Start 2P'"; cx.fillText('● LIVE', a + 26, b - 17); }); }
// -------------------------------------------------- people
const SPR_F = ["....HHHH....", "...HHHHHH...", "..HHSSSSHH..", "..HSESSESH..", "..HSSSSSSH..", "..HHSMMSHH..", "..HH.SS.HH..",
  "..HTTTTTTH..", "..TTTTTTTT..", ".STTTTTTTTS.", ".S.TTTTTT.S.", "...PPPPPP...", "...PP..PP...", "...PP..PP...", "...KK..KK..."];
const SPR_M = ["....HHHH....", "...HHHHHH...", "...HSSSSH...", "...SESSES...", "...SSSSSS...", "...SSMMSS...", ".....SS.....",
  "..TTTTTTTT..", ".TTTTTTTTTT.", ".STTTTTTTTS.", ".S.TTTTTT.S.", "...PPPPPP...", "...PP..PP...", "...PP..PP...", "...KK..KK..."];
const SEATS = { leisure: [] };
function layout() {
  // Dirección
  SEATS.direccion = [desk(2, 3, '#d4af37'), desk(5, 1.2, '#38e1ff'), desk(1, 1.2, '#7cff9b')];
  shelf(0.3, 0.2, 2); plant(7.2, 0.4, true); plant(0.3, 6, false); sofa(4.5, 5, '#26365e');
  // Economía
  SEATS.economia = [desk(9, 1.3, '#7cff9b'), desk(11.5, 1.3, '#7cff9b'), desk(14, 1.3, '#38e1ff'), desk(9.5, 4, '#ffd36b'), desk(12.5, 4, '#7cff9b')];
  whiteboard(15.5, 0.2, 2.2); plant(17.3, 6.2);
  // Datos y tendencias
  screenWall(19, 0.2, 5, ['EN TENDENCIA:', ...(D.trends.google || []).slice(0, 3)]);
  SEATS.datos = [desk(19, 1.6, '#38e1ff'), desk(21.5, 1.6, '#ff4d8d'), desk(24, 1.6, '#7cff9b'), desk(20, 4.3, '#a78bfa'), desk(23, 4.3, '#38e1ff')];
  screenWall(25.5, 0.2, 4, ['HASHTAGS:', ...(D.trends.tags || []).slice(0, 3).map(t => '#' + t)]); plant(29.2, 6.2, true);
  // Mercados
  globe(1, 8.5); SEATS.mercados = [desk(3, 8.5, '#38e1ff'), desk(1.5, 11.5, '#ffd36b'), desk(4.5, 11.5, '#ff4d8d')]; plant(7.2, 14.2);
  // Creativo
  SEATS.creativo = [desk(23, 8.4, '#ff4d8d'), desk(26, 8.4, '#a78bfa'), desk(23.5, 11.5, '#ffd36b'), desk(26.5, 11.5, '#38e1ff'), desk(24.5, 14, '#ff4d8d')];
  whiteboard(28, 7.3, 1.8); plant(29.2, 15.2, true);
  // Juntas
  SEATS.juntas = roundTable(11, 12); plant(8.3, 15.2); whiteboard(9, 10.2, 2);
  // Biblioteca
  shelf(16.4, 10.2, 2.5); shelf(19.2, 10.2, 2.5); SEATS.leisure.push(sofa(17.5, 13.5, '#7a2d2d'));
  // Jardín
  [[1, 16], [3.5, 22], [8.5, 17], [0.6, 20.3], [9.5, 22.3], [5.5, 16.2]].forEach(([x, y]) => tree(x, y));
  bush(2.5, 18, '#2e9440', ['#ff6b9d', '#ffd36b', '#fff']); bush(6.5, 21, '#2e9440', ['#c084fc', '#fff']); bush(9, 19.5); bush(4.2, 19.8, '#2e9440', ['#ff9f43']);
  fountain(5.2, 18.3, 0); SEATS.leisure.push(bench(2, 21.4), bench(7, 19.8), bench(6.7, 22.6));
  // Zen
  pond(14, 18.6, 3, 2.6, 0); stone(12.2, 17.2, 1.2); stone(12.8, 22.6); stone(18.8, 17.4, .8); stone(17.6, 22.7, 1.3);
  bamboo(19.2, 16.3); bamboo(11.3, 23.2); bonsai(18.6, 20.4); bonsai(12, 19.6);
  SEATS.leisure.push(cushion(12.4, 21.2, '#c0392b'), cushion(13.6, 22.4, '#8e44ad'), cushion(18.4, 22, '#2e86c1'), cushion(17.2, 17.2, '#d4ac0d'));
  // Lounge + Lives
  SEATS.leisure.push(sofa(21.5, 19, '#2b4c7e'), sofa(24.5, 21.6, '#2b4c7e'), futbolin(26.5, 17.5));
  bar(21, 16.4); liveStudio(28.3, 21.3); plant(29.2, 23.2, true); plant(20.3, 23.2);
  SEATS.leisure.push([22.2, 17.6], [27, 19.5], [3, 18.6], [8.2, 21], [1.6, 23.2], [10.2, 16.6], [13.2, 17.6], [16.6, 21.6],
    [19.4, 18.8], [15.4, 23.2], [23.2, 23], [28.2, 18.6], [25.4, 17.2], [21, 22.9], [18.6, 15.2], [20.8, 12.6], [12, 8.6],
    [18, 8.6], [27, 23.2], [9.6, 23.4], [4.4, 23.4], [6, 17.4]);
}
const people = D.people.map((p, i) => ({...p, i}));
function placePeople() {
  const used = {};
  let li = 0;
  for (const p of people) {
    const seats = SEATS[p.room] || SEATS.juntas;
    used[p.room] = (used[p.room] || 0);
    const desk = seats[used[p.room]++ % seats.length];
    if (p.active) { p.home = desk; p.mode = 'work'; }
    else { p.home = SEATS.leisure[li++ % SEATS.leisure.length]; p.mode = 'rest'; }
  }
}
const hits = [];
function drawPerson(p, t) {
  const wob = p.mode === 'rest' ? [Math.sin(t / 2600 + p.i) * .2, Math.cos(t / 3100 + p.i * 2) * .15] : [0, 0];
  const x = p.home[0] + wob[0], y = p.home[1] + wob[1];
  put(x + y + .2, () => {
    const [a, b0] = iso(x, y); const bob = p.mode === 'work' ? (Math.floor(t / 300 + p.i) % 2) : (Math.floor(t / 520 + p.i) % 2);
    const s = 3, b = b0 - bob;
    cx.fillStyle = 'rgba(0,0,0,.28)'; cx.beginPath(); cx.ellipse(a, b0, 14, 6, 0, 0, 7); cx.fill();
    const [hair, skin, top, pants] = p.look, col = {H: hair, S: skin, E: '#1b1b1b', M: '#c2566b', T: top, P: pants, K: '#0b0b0b'};
    (p.male ? SPR_M : SPR_F).forEach((row, yy) => [...row].forEach((c, xx) => { if (col[c]) { cx.fillStyle = col[c]; cx.fillRect(a - 18 + xx * s, b - 46 + yy * s, s, s); } }));
    // labels
    cx.font = "8px 'Press Start 2P'"; cx.textAlign = 'center';
    const name = up(p.n.replace(/'.*'/, '').trim()), w = cx.measureText(name).width + 10;
    cx.fillStyle = '#0d1a24e6'; cx.fillRect(a - w / 2, b - 64, w, 14); cx.fillStyle = '#ffffff'; cx.fillText(name, a, b - 54);
    const st = p.mode === 'work' ? ['TRABAJANDO', '#2ecc71'] : ['EN PAUSA', '#5dade2'];
    const w2 = cx.measureText(st[0]).width + 10; cx.fillStyle = st[1]; cx.fillRect(a - w2 / 2, b - 80, w2, 14);
    cx.fillStyle = '#04110a'; cx.fillText(st[0], a, b - 70);
    hits.push({p, x0: a - 22, x1: a + 22, y0: b - 82, y1: b0 + 4});
  });
}
// -------------------------------------------------- frame
function frame(t) {
  drawables.length = 0; hits.length = 0;
  cx.fillStyle = '#0a1118'; cx.fillRect(0, 0, W, H);
  floors(); walls(); partitions(); layoutDynamic(t); people.forEach(p => drawPerson(p, t));
  drawables.sort((a, b) => a[0] - b[0]).forEach(([, f]) => f());
  // zone labels on the floor
  cx.font = "9px 'Press Start 2P'"; cx.textAlign = 'center';
  for (const r of Object.values(ROOMS)) if (r.name) { const [a, b] = iso(r.x + r.w / 2, r.y + r.d - .4);
    const w = cx.measureText(up(r.name)).width + 12; cx.fillStyle = '#000a'; cx.fillRect(a - w / 2, b - 10, w, 15); cx.fillStyle = '#ffe9a8'; cx.fillText(up(r.name), a, b + 1); }
  requestAnimationFrame(frame);
}
let staticDone = false; const dyn = [];
function layoutDynamic(t) { if (!staticDone) { const keep = drawables.length; layout(); dyn.push(...drawables.splice(keep)); staticDone = true; placePeople(); }
  for (const d of dyn) drawables.push(d); pond(14, 18.6, 3, 2.6, t); fountain(5.2, 18.3, t); }
// -------------------------------------------------- overlays
const tip = document.getElementById('tip');
cv.addEventListener('mousemove', e => {
  const r = cv.getBoundingClientRect(), sx = (e.clientX - r.left) * W / r.width, sy = (e.clientY - r.top) * H / r.height;
  const h = hits.slice().reverse().find(h => sx > h.x0 && sx < h.x1 && sy > h.y0 && sy < h.y1);
  if (!h) { tip.style.display = 'none'; cv.style.cursor = 'default'; return; }
  cv.style.cursor = 'pointer'; const p = h.p;
  tip.innerHTML = `<h3><span>${esc(p.n)}</span><span>${p.mode === 'work' ? 'TRABAJANDO' : 'EN PAUSA'}</span></h3><p><small>${esc(p.r)}</small><br>` +
    (p.said ? `<b style="color:#ffd36b">${esc(p.t)}</b> ${esc(p.said)}` : 'Todavía no ha hablado hoy.') + '</p>';
  tip.style.display = 'block'; tip.style.left = Math.min(e.clientX - r.left + 14, r.width - 310) + 'px'; tip.style.top = (e.clientY - r.top + 14) + 'px';
});
cv.addEventListener('mouseleave', () => tip.style.display = 'none');
const active = people.filter(p => p.active).length;
document.getElementById('chips').innerHTML = `<div class="chip">🗓️ ${esc(D.now)}</div><div class="chip">👥 Equipo <b>${people.length}</b></div>` +
  `<div class="chip">📤 Hoy <b>${D.done}/${D.total}</b></div><div class="chip">🔥 Tendencias ${D.trends.age == null ? 'sin datos' : 'hace ' + D.trends.age + ' min'}</div>`;
const said = people.filter(p => p.said && p.day).sort((a, b) => (a.day + a.t < b.day + b.t ? 1 : -1)).slice(0, 4).reverse();
document.getElementById('chat').innerHTML = said.map(p => `<div class="l"><b>${esc(p.n.replace(/'.*'/, '').trim())}:</b> ${esc(p.said.slice(0, 110))}</div>`).join('') || '<div class="l">Sin mensajes todavía.</div>';
document.getElementById('board').innerHTML = `<div><span>AGENTES ACTIVOS:</span><span class="ok">${active}</span></div>` +
  `<div><span>EN PAUSA:</span><span>${people.length - active}</span></div><div><span>PUBLICADAS HOY:</span><span>${D.done}/${D.total}</span></div>` +
  `<div><span>ESTADO:</span><span class="${D.live ? 'ok' : 'warn'}">${D.live ? 'OPERATIVO' : 'EN ESPERA'}</span></div>`;
const icon = {done: '✅', skipped: '⏭️'};
const card = (h, body) => `<div class="card"><h4>${h}</h4>${body}</div>`;
const al = (D.econ && D.econ.asignacion) || {};
const bars = ['formatos', 'mercados', 'segmentos'].filter(g => al[g]).map(g => `<div style="margin-top:6px"><span>${g}</span>` +
  Object.entries(al[g]).slice(0, 6).map(([k, v]) => `<div class="bar"><span style="width:110px;color:#ddd">${esc(k)}</span><i style="width:${Math.max(2, v * 2)}px"></i>${esc(v)}%</div>`).join('') + '</div>').join('');
document.getElementById('cards').innerHTML =
  card('📋 PLAN DE HOY', '<ul>' + (D.plan.map(p => `<li><span>${esc(p.time)}</span> ${icon[p.status] || '🕒'} <b>${esc(p.type)}</b>${p.mercado ? ' · ' + esc(p.mercado) : ''} — ${esc(p.angle)}</li>`).join('') || '<li>La reunión de la mañana define el plan.</li>') + '</ul>') +
  card('📈 PLAN ECONÓMICO ' + esc((D.econ && D.econ.semana) || ''), `<div style="color:#ffd36b">${esc((D.econ && D.econ.objetivo) || 'La Junta Económica se reúne los lunes.')}</div>${bars}`) +
  card('🧾 DECISIONES', '<ul>' + (D.decisions.map(d => `<li><span>${esc((d.dia || '').slice(5))}</span> ${esc(d.decision)} → <i>${esc(d.metrica)}</i></li>`).join('') || '<li>Aparecen después de cada reunión.</li>') + '</ul>') +
  card('🔥 TENDENCIAS', '<ul>' + [...D.trends.google.map(x => '🔎 ' + x), ...D.trends.futbol.map(x => '⚽ ' + x), ...D.trends.songs.map(x => '🎵 ' + x)].map(x => `<li>${esc(x)}</li>`).join('') + '</ul>' +
       (D.seo.length ? `<div style="color:#c9b6ff;margin-top:6px">SEO: ${D.seo.map(h => '#' + esc(h)).join(' ')}</div>` : '')) +
  card('🤝 ÚLTIMA ACTA · ' + esc(D.acta.title), `<div style="white-space:pre-wrap">${esc(D.acta.body || 'Todavía no hay actas.')}</div>`) +
  card('📚 BIBLIOTECA', '<ul>' + (D.books.map(([d, n, t]) => `<li><span>${esc(n)}</span> ${esc(t)}</li>`).join('') || '<li>Los cuadernos se llenan en cada reunión.</li>') + '</ul>') +
  card('🖥️ EN VIVO (PC)', '<div style="color:#9effa0;font-size:16px">' + D.log.map(esc).join('<br>') + '</div>');
(document.fonts ? document.fonts.ready : Promise.resolve()).then(() => requestAnimationFrame(frame));
</script></body></html>"""


def build() -> str:
    page = PAGE.replace("__DATA__", json.dumps(data(), ensure_ascii=False).replace("</", "<\\/"))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    return OUT


if __name__ == "__main__":
    path = build()
    print(path)
    if "--abrir" in sys.argv:
        webbrowser.open("file:///" + path.replace("\\", "/"))
