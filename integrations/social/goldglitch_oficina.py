"""La oficina de EGG: un espacio pixel art donde se ve a cada agente trabajando, con datos reales del PC.

Salas: Dirección · Centro de datos y tendencias · Biblioteca (cuadernos de aprendizaje) · Estudio creativo ·
Sala de juntas (plan y acta) · Estudio de redes y Lives. Se actualiza sola en cada vuelta de redes y al abrirla con
oficina.bat; la página se recarga cada minuto.

    python goldglitch_oficina.py          # genera oficina.html
    python goldglitch_oficina.py --abrir  # y la abre en el navegador
"""
from __future__ import annotations

import glob
import html
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


def load(name: str, default):
    try:
        return json.load(open(os.path.join(HERE, name), encoding="utf-8"))
    except (OSError, ValueError):
        return default


def esc(s) -> str:
    return html.escape(str(s or ""))


# ------------------------------------------------------------------ pixel sprites
SPRITE_M = ["....HHHH....", "...HHHHHH...", "...HSSSSH...", "...SESSES...", "...SSSSSS...", "...SSMMSS...",
            ".....SS.....", "..TTTTTTTT..", ".TTTTTTTTTT.", ".STTTTTTTTS.", ".S.TTTTTT.S.", "...PPPPPP...",
            "...PP..PP...", "...PP..PP...", "...KK..KK..."]
SPRITE = ["....HHHH....", "...HHHHHH...", "..HHSSSSHH..", "..HSESSESH..", "..HSSSSSSH..", "..HHSMMSHH..",
          "..HH.SS.HH..", "..HTTTTTTH..", "..TTTTTTTT..", ".STTTTTTTTS.", ".S.TTTTTT.S.", "...PPPPPP...",
          "...PP..PP...", "...PP..PP...", "...KK..KK..."]
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
    "segmentos": ("#2b2b2b", "#d19a72", "#f97316", "#111827"),
    "neuro": ("#101010", "#e2ad88", "#06b6d4", "#0b1220"), "disrupcion": ("#7c3aed", "#e8b691", "#facc15", "#111111"), "narrativa": ("#8a5a33", "#f2cfb3", "#be185d", "#27272a"),
}


def sprite(key: str, scale: int = 4, male: bool = False) -> str:
    hair, skin, top, pants = LOOKS.get(key) or ("#3b2a1f", "#e0aa84", f"hsl({sum(map(ord, key)) * 37 % 360},70%,55%)", "#1f2937")
    col = {"H": hair, "S": skin, "E": "#1b1b1b", "M": "#c2566b", "T": top, "P": pants, "K": "#0b0b0b"}
    rects = "".join(f"<rect x='{x}' y='{y}' width='1' height='1' fill='{col[c]}'/>"
                    for y, row in enumerate(SPRITE_M if male else SPRITE) for x, c in enumerate(row) if c in col)
    return (f"<svg class='spr' width='{12 * scale}' height='{15 * scale}' viewBox='0 0 12 15' shape-rendering='crispEdges'>"
            f"{rects}</svg>")


def plant() -> str:
    return "<div class='plant'><i></i><i></i><i></i><b></b></div>"


def desk(screen: str = "#38e1ff", n: int = 1) -> str:
    return "<div class='desk'>" + "".join(f"<div class='mon'><div style='background:{screen}'></div></div>" for _ in range(n)) + "</div>"


# ------------------------------------------------------------------ data
def statuses(names: dict[str, str]) -> dict[str, tuple[str, str]]:
    """Last thing each member said in redes.log → {key: (time, text)}."""
    try:
        lines = open(os.path.join(HERE, "redes.log"), encoding="utf-8").read().splitlines()[-3000:]
    except OSError:
        return {}
    out = {}
    for ln in lines:
        m = re.match(r"\[(\d{4}-\d\d-\d\d \d\d:\d\d)\]\s+\[([^\]]+)\]\s*(.*)", ln)
        if m:
            for k, n in names.items():
                if m.group(2).strip() == n:
                    out[k] = (m.group(1), m.group(3))
    return out


def log_tail(n: int = 9) -> list[str]:
    try:
        return open(os.path.join(HERE, "redes.log"), encoding="utf-8").read().splitlines()[-n:]
    except OSError:
        return []


def roster() -> dict:
    try:
        import goldglitch_growth as G
        return G.roster()["miembros"]
    except Exception:
        return load("redes_comite.json", {}).get("miembros") or {}


ROOMS = {  # where each member sits (by department)
    "direccion": ["tiburon", "marca"], "datos": ["viralidad", "viral", "comunidad", "neuro", "seo"],
    "estudio": ["disrupcion", "diseno", "video", "copy", "narrativa"], "juntas": ["audiencia", "segmentos", "parche"],
    "economia": ["sofia", "unit_econ", "econometria", "pricing", "analista"], "mercados": ["internacional", "mx_us", "conosur_es"],
}


def person(key: str, m: dict, st: dict, now: datetime) -> str:
    t, said = st.get(key, ("", ""))
    fresh = False
    if t:
        try:
            fresh = now - datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=TZ) < timedelta(minutes=40)
        except ValueError:
            pass
    bubble = (f"<div class='bubble{' live' if fresh else ''}'><b>{esc(t[11:])}</b> {esc(said[:110])}…</div>" if said
              else "<div class='bubble'>en su escritorio ✨</div>")
    return (f"<div class='person{' talking' if fresh else ''}' title='{esc(m.get('rol'))}'>{bubble}{sprite(key, male=m.get('genero') == 'h')}"
            f"<div class='tag'>{esc(m.get('nombre') or key)}<small>{esc((m.get('rol') or '')[:38])}</small></div></div>")


def build() -> str:
    now = datetime.now(TZ)
    today = now.strftime("%Y-%m-%d")
    members = roster()
    names = {k: v.get("nombre", "") for k, v in members.items() if v.get("nombre")}
    names["director"] = "Valentina"
    st_by = statuses(names)
    state = load("redes_estado.json", {})
    plan = load("redes_plan_comite.json", {})
    trends = load("redes_tendencias.json", {})
    books = load("redes_cuadernos.json", {})
    seo = plan.get("seo") if plan.get("day") == today else {}
    arte = plan.get("arte") if plan.get("day") == today else {}
    actas = sorted(glob.glob(os.path.join(HERE, "redes_comite_actas", "*.md")))
    acta = open(actas[-1], encoding="utf-8").read() if actas else "Todavía no hay actas."
    acta_title = os.path.basename(actas[-1])[:-3] if actas else ""
    acta_body = re.split(r"\n## Plan", acta)[0].split("\n", 1)[-1].strip()[:700]

    placed = {k for v in ROOMS.values() for k in v}
    extra = [k for k in members if k not in placed]
    people = lambda keys: "".join(person(k, members[k], st_by, now) for k in keys if k in members)
    director = person("director", {"nombre": "Valentina", "rol": "Directora de Crecimiento"}, st_by, now)

    posts = state.get("plan") if state.get("day") == today else []
    icon = {"done": "✅", "skipped": "⏭️"}
    plan_rows = "".join(f"<li><span>{esc(p.get('time'))}</span> {icon.get(p.get('status'), '🕒')} <b>{esc(p.get('type'))}</b>"
                        f"{' · ' + esc(p.get('meme_formato')) if p.get('meme_formato') else ''} — {esc((p.get('angle') or '')[:60])}"
                        f"{' · ' + ', '.join(p.get('done') or {}) if p.get('done') else ''}</li>" for p in posts or []) \
        or "<li>La reunión de la mañana define el plan (07:00).</li>"
    hist = (state.get("history") or [])[-6:][::-1]
    hist_rows = "".join(f"<li><span>{esc(h.get('day', '')[5:])} {esc(h.get('time'))}</span> {esc(h.get('type'))} → "
                        f"{esc(', '.join(h.get('done') or []) or 'sin publicar')}{' ⚠️' if h.get('errors') else ''}</li>" for h in hist) \
        or "<li>Sin publicaciones todavía.</li>"
    g = trends.get("google") or {}
    tr_rows = "".join(f"<li>🔎 {esc(t['busqueda'])} <i>{esc(t.get('trafico'))}</i></li>" for t in (g.get("Colombia") or [])[:6])
    tr_rows += "".join(f"<li>⚽ {esc(a['liga'])}: {esc(a['titular'][:70])}</li>" for a in (trends.get("futbol") or [])[:5])
    tt = " ".join(f"#{esc(h)}" for h in (trends.get("tiktok") or [])[:10])
    tr_age = f"hace {int((time.time() - float(trends['ts'])) / 60)} min" if trends.get("ts") else "sin datos aún"
    seo_tags = " ".join(f"#{esc(h)}" for h in (seo or {}).get("hashtags", [])[:12]) or "Daniela lo arma en la reunión"
    notes = []
    for k, items in books.items():
        if items:
            notes.append((items[-1].get("dia", ""), names.get(k, k), items[-1].get("texto", "")))
    notes.sort(reverse=True)
    lib_rows = "".join(f"<li><b>{esc(n)}</b> <span>{esc(d[5:])}</span><br>{esc(t[:150])}</li>" for d, n, t in notes[:5]) \
        or "<li>Los cuadernos se llenan en cada reunión y en la sesión de estudio del domingo.</li>"
    ticker = "".join(f"<div>{esc(l[:150])}</div>" for l in log_tail())
    art = (f"Acento <b>{esc(arte.get('acento'))}</b> · portada <b>{esc(arte.get('portada'))}</b> · ritmo <b>{esc(arte.get('ritmo'))}</b>"
           if arte else "Martina la define en la reunión")
    done_today = sum(1 for p in posts or [] if p.get("status") == "done")

    page = f"""<!doctype html><html lang='es'><head><meta charset='utf-8'><meta http-equiv='refresh' content='60'>
<meta name='viewport' content='width=device-width,initial-scale=1'><title>Oficina EGG</title>
<link href='https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&display=swap' rel='stylesheet'>
<style>
:root{{--wall:#16141c;--ink:#f3ecdc;--gold:#d4af37}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0b0a0f;color:var(--ink);font-family:VT323,monospace;font-size:20px;padding:18px}}
h1{{font-family:'Press Start 2P',monospace;font-size:18px;color:var(--gold);letter-spacing:2px}}
.head{{display:flex;justify-content:space-between;align-items:end;max-width:1500px;margin:0 auto 14px;gap:12px;flex-wrap:wrap}}
.kpis{{display:flex;gap:10px;flex-wrap:wrap}} .kpi{{border:3px solid #2c2838;background:#15131c;padding:6px 12px}} .kpi b{{color:var(--gold)}}
.office{{max-width:1500px;margin:0 auto;display:grid;gap:10px;grid-template-columns:1.15fr .9fr 1.2fr;grid-template-rows:auto auto auto;
 border:10px solid #2a2433;background:#2a2433;box-shadow:0 0 0 4px #000,0 30px 80px #000}}
.room{{position:relative;padding:14px 14px 16px;min-height:300px;border:4px solid #000;image-rendering:pixelated;overflow:hidden}}
.room h2{{font-family:'Press Start 2P',monospace;font-size:11px;background:#000a;display:inline-block;padding:6px 8px;color:var(--gold);margin-bottom:10px}}
.wood{{background:repeating-linear-gradient(0deg,#7a4b26 0 18px,#6b4020 18px 20px),#7a4b26}}
.oak{{background:repeating-linear-gradient(90deg,#9a6534 0 36px,#8a5a2e 36px 38px)}}
.tile{{background:linear-gradient(#5d6470 2px,transparent 2px) 0 0/34px 34px,linear-gradient(90deg,#5d6470 2px,transparent 2px) 0 0/34px 34px,#7d8592}}
.hall{{background:linear-gradient(45deg,#2b2b33 25%,#33333d 25% 50%,#2b2b33 50% 75%,#33333d 75%) 0 0/48px 48px}}
.carpet{{background:radial-gradient(circle at 50% 50%,#33406b,#232c4d)}}
.rug{{position:absolute;inset:auto 18% 8% 18%;height:38%;background:#2e3a63;border:6px double #c9a24a;opacity:.55}}
.people{{display:flex;flex-wrap:wrap;gap:18px 14px;align-items:end;position:relative;z-index:2;margin-top:8px}}
.person{{position:relative;width:132px;display:flex;flex-direction:column;align-items:center}}
.spr{{filter:drop-shadow(3px 4px 0 #0008)}} .person.talking .spr{{animation:bob 1s steps(2) infinite}}
@keyframes bob{{50%{{transform:translateY(-4px)}}}}
.tag{{background:#000c;border:2px solid #000;padding:2px 6px;text-align:center;font-size:18px;line-height:1;margin-top:3px;width:100%}}
.tag small{{display:block;font-size:14px;color:#bdb4a2;margin-top:2px}}
.bubble{{background:#f3ecdc;color:#16141c;border:3px solid #000;padding:4px 6px;font-size:15px;line-height:1;margin-bottom:6px;width:132px;
 max-height:64px;overflow:hidden;position:relative}}
.bubble:after{{content:'';position:absolute;bottom:-9px;left:56px;border:6px solid transparent;border-top-color:#000}}
.bubble.live{{background:#fff4c2;box-shadow:0 0 0 2px var(--gold)}} .bubble b{{color:#9a6c00}}
.desk{{display:inline-flex;gap:4px;background:#5a3a1e;border:3px solid #000;padding:6px 8px 10px;box-shadow:0 6px 0 #3a2412}}
.mon{{width:44px;height:30px;background:#111;border:3px solid #000;padding:3px}} .mon div{{height:100%;opacity:.85;animation:flick 3s infinite}}
@keyframes flick{{50%{{opacity:.6}}}}
.plant{{position:absolute;width:34px;height:46px}} .plant i{{position:absolute;width:18px;height:18px;background:#2f9e44;border:2px solid #0b3d17;border-radius:50%}}
.plant i:nth-child(1){{left:0;top:6px}} .plant i:nth-child(2){{left:14px;top:0}} .plant i:nth-child(3){{left:8px;top:14px}}
.plant b{{position:absolute;left:7px;bottom:0;width:20px;height:16px;background:#a0522d;border:2px solid #000}}
.panel{{background:#0d0c12e6;border:3px solid #000;padding:8px 10px;font-size:17px;line-height:1.15;position:relative;z-index:2}}
.panel ul{{list-style:none}} .panel li{{padding:3px 0;border-bottom:1px dashed #ffffff1a}} .panel li span{{color:var(--gold)}}
.panel i{{color:#8ef;font-style:normal}}
.screen{{background:#06131a;border:4px solid #000;box-shadow:inset 0 0 0 3px #1a3946;color:#8ef;padding:8px 10px;font-size:17px;line-height:1.15}}
.shelf{{height:16px;background:#4a2e17;border:3px solid #000;margin:4px 0;display:flex;gap:2px;padding:0 4px;align-items:end}}
.shelf i{{width:8px;background:#c0392b;border:1px solid #000}} .shelf i:nth-child(3n){{background:#2e86c1;height:12px}} .shelf i:nth-child(4n){{background:#d4ac0d;height:9px}}
.table{{width:150px;height:84px;border-radius:50%;background:#1e2a4a;border:5px solid #000;margin:6px auto;box-shadow:0 8px 0 #0008;display:grid;place-items:center;color:var(--gold);font-family:'Press Start 2P';font-size:9px}}
.ring{{width:70px;height:70px;border-radius:50%;border:10px solid #fff7d6;box-shadow:0 0 30px #fff7d6aa;margin:6px auto}}
.onair{{display:inline-block;background:#3a0b14;color:#ff4d6d;border:3px solid #000;padding:4px 8px;font-family:'Press Start 2P';font-size:9px}}
.ticker{{max-width:1500px;margin:12px auto 0;background:#000;border:3px solid #2c2838;padding:8px 12px;color:#9effa0;font-size:16px;line-height:1.15}}
.span2{{grid-column:span 2}}
@media(max-width:1000px){{.office{{grid-template-columns:1fr}}.span2{{grid-column:auto}}}}
</style></head><body>
<div class='head'><h1>EGG · OFICINA DE MARKETING</h1>
<div class='kpis'><div class='kpi'>🗓️ {now:%d/%m %H:%M}</div><div class='kpi'>👩‍💼 Equipo <b>{len(members) + 1}</b></div>
<div class='kpi'>📤 Hoy <b>{done_today}/{len(posts or [])}</b> publicadas</div><div class='kpi'>🔥 Tendencias {esc(tr_age)}</div></div></div>
<div class='office'>
 <section class='room wood'><h2>🏛️ DIRECCIÓN</h2>{plant()}<div class='rug'></div>
  <div class='people'>{director}{people(ROOMS['direccion'])}</div>
  <div style='margin-top:10px'>{desk('#d4af37')}</div>
  <div class='panel' style='margin-top:10px'><b style='color:var(--gold)'>Plan de hoy</b><ul>{plan_rows}</ul></div></section>
 <section class='room hall'><h2>📱 ESTUDIO DE REDES Y LIVES</h2>
  <div style='display:flex;gap:10px;align-items:center'><div class='ring'></div><div><span class='onair'>● LIVE: EN PREPARACIÓN</span>
  <div style='font-size:16px;margin-top:6px;color:#cfc6b2'>Instagram y TikTok solo dejan hacer lives desde su app, y TikTok además pide un
  mínimo de seguidores. El guion lo prepara el equipo; el live lo hacés vos.</div></div></div>
  <div class='panel' style='margin-top:10px'><b style='color:var(--gold)'>Últimas publicaciones</b><ul>{hist_rows}</ul></div></section>
 <section class='room tile'><h2>📊 DATOS Y TENDENCIAS</h2>
  <div style='display:flex;gap:6px'>{desk('#38e1ff', 2)}{desk('#7cff9b', 2)}</div>
  <div class='people'>{people(ROOMS['datos'])}</div>
  <div class='screen' style='margin-top:10px'><b>EN TENDENCIA AHORA</b><ul style='list-style:none'>{tr_rows or '<li>Esperando la primera lectura…</li>'}</ul>
  <div style='margin-top:4px;color:#ffd36b'>{tt}</div><div style='margin-top:6px;color:#c9b6ff'>SEO de hoy: {seo_tags}</div></div></section>
 <section class='room oak'><h2>📚 BIBLIOTECA · ACADEMIA</h2>
  <div class='shelf'>{'<i style="height:12px"></i>' * 26}</div><div class='shelf'>{'<i style="height:10px"></i>' * 26}</div>
  <div class='panel' style='margin-top:10px'><b style='color:var(--gold)'>Cuadernos de aprendizaje</b><ul>{lib_rows}</ul>
  <div style='font-size:15px;color:#9a9384;margin-top:6px'>Cada domingo: sesión de estudio. Cada reunión: aprendizajes por persona.</div></div></section>
 <section class='room carpet span2'><h2>🎨 ESTUDIO CREATIVO</h2>{plant()}
  <div style='display:flex;gap:6px'>{desk('#ff4d8d')}{desk('#a78bfa')}{desk('#ffd36b')}</div>
  <div class='people'>{people(ROOMS['estudio'])}</div>
  <div class='panel' style='margin-top:10px'>🎬 Dirección de arte de hoy: {art}</div></section>
 <section class='room wood span2'><h2>🤝 SALA DE JUNTAS</h2>
  <div style='display:grid;grid-template-columns:auto 1fr;gap:14px;align-items:start'>
   <div><div class='table'>EGG</div><div class='people'>{people(ROOMS['juntas'] + extra)}</div></div>
   <div class='panel'><b style='color:var(--gold)'>Última acta · {esc(acta_title)}</b><div style='white-space:pre-wrap;margin-top:6px'>{esc(acta_body)}</div></div></div></section>
 <section class='room hall'><h2>☕ LOUNGE</h2>{plant()}
  <div class='panel' style='margin-top:40px'>Aquí se ve lo que pasa en vivo en el PC (redes.log):</div>
  <div class='ticker' style='margin-top:8px'>{ticker or 'Sin actividad todavía.'}</div></section>
</div></body></html>"""
    econ = load("redes_plan_economico.json", {})
    alloc = econ.get("asignacion") or {}
    bars = "".join(
        f"<div style='margin-top:6px'><b style='color:var(--gold)'>{esc(g.capitalize())}</b>" + "".join(
            f"<div style='display:flex;align-items:center;gap:8px;font-size:16px'><span style='width:110px'>{esc(k)}</span>"
            f"<div style='height:10px;width:{max(2, int(float(v or 0) * 2.2))}px;background:#d4af37;border:2px solid #000'></div>{esc(v)}%</div>"
            for k, v in list((alloc.get(g) or {}).items())[:7]) + "</div>" for g in ("formatos", "mercados", "segmentos") if alloc.get(g))
    decs = (load("redes_decisiones.json", []) or [])[-4:][::-1]
    dec_rows = "".join(f"<li><span>{esc(d.get('dia', '')[5:])}</span> {esc(d.get('decision', '')[:90])} → <i>{esc(d.get('metrica', '')[:40])}</i></li>" for d in decs) \
        or "<li>Las decisiones con su razón económica aparecen aquí después de cada reunión.</li>"
    extra_rooms = f"""
 <section class='room tile span2'><h2>📈 ESTRATEGIA ECONÓMICA</h2>
  <div style='display:flex;gap:6px'>{desk('#7cff9b', 3)}{desk('#38e1ff', 2)}</div>
  <div class='people'>{people(ROOMS['economia'])}</div>
  <div style='display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px'>
   <div class='screen'><b>PLAN ECONÓMICO {esc(econ.get('semana', ''))}</b><div style='color:#ffd36b;margin-top:4px'>{esc(str(econ.get('objetivo') or 'La Junta Económica se reúne los lunes.'))[:160]}</div>{bars}</div>
   <div class='panel'><b style='color:var(--gold)'>Registro de decisiones</b><ul>{dec_rows}</ul></div></div></section>
 <section class='room carpet'><h2>🌎 MERCADOS INTERNACIONALES</h2>
  <div style='font-size:34px;letter-spacing:6px'>🇨🇴🇲🇽🇺🇸🇦🇷🇪🇸🇨🇱🇵🇪</div>
  <div class='people'>{people(ROOMS['mercados'])}</div></section>"""
    page = page.replace("</div></body></html>", extra_rooms + "\n</div></body></html>")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    return OUT


if __name__ == "__main__":
    path = build()
    print(path)
    if "--abrir" in sys.argv:
        webbrowser.open("file:///" + path.replace("\\", "/"))
