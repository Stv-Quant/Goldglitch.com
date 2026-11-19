"""Piezas v2 de Goldglitch para redes: carrusel premium (ligas top) y reels verticales de ritmo rápido.

- Solo ligas profesionales de primera división de LATAM y Europa (y sus copas continentales), ordenadas por relevancia.
- Escudos y logos de clubes NO se usan (son marcas de terceros): cada equipo lleva un monograma propio de color.
- Los reels llevan cortes rápidos, zoom de golpe, destellos y un ritmo de percusión ORIGINAL generado aquí (sin música
  de terceros).
Todos los números vienen de los datos de la web; aquí solo se maquetan.
"""
from __future__ import annotations

import colorsys
import hashlib
import html
import math
import os
import struct
import subprocess
import unicodedata
import wave
from pathlib import Path

from goldglitch_social_render import MARK, OUT, render

# ------------------------------------------------------------------ top leagues
# (name variants, display name, hashtag, relevance: lower = more important)
TOP_LEAGUES = [
    (("champions league", "ucl", "uefa champions"), "Champions League", "ChampionsLeague", 0),
    (("copa libertadores", "libertadores", "lib"), "Copa Libertadores", "CopaLibertadores", 0),
    (("premier league", "e0"), "Premier League", "PremierLeague", 1),
    (("laliga", "la liga", "sp1"), "LaLiga", "LaLiga", 1),
    (("liga betplay", "betplay", "col"), "Liga BetPlay", "LigaBetPlay", 1),
    (("serie a", "i1"), "Serie A", "SerieA", 2),
    (("bundesliga", "d1"), "Bundesliga", "Bundesliga", 2),
    (("brasileirão", "brasileirao", "bra"), "Brasileirão", "Brasileirao", 2),
    (("liga argentina", "liga profesional", "arg"), "Liga Profesional Argentina", "LigaProfesional", 2),
    (("liga mx", "mex"), "Liga MX", "LigaMX", 2),
    (("europa league", "uel"), "Europa League", "EuropaLeague", 3),
    (("copa sudamericana", "sudamericana", "sud"), "Copa Sudamericana", "CopaSudamericana", 3),
    (("ligue 1", "f1"), "Ligue 1", "Ligue1", 3),
    (("primeira liga", "liga portugal", "p1"), "Primeira Liga", "LigaPortugal", 4),
    (("eredivisie", "n1"), "Eredivisie", "Eredivisie", 4),
]
EXCLUDE = ("2.", " 2", "segunda", "serie b", "championship", "ligue 2", "laliga 2", "austria", "premiership")

ACCENT = {"Champions League": "#4f8cff", "Europa League": "#ff8a1f", "Premier League": "#a25cff", "LaLiga": "#ff4d6d",
          "Serie A": "#2fb6ff", "Bundesliga": "#ff3b3b", "Ligue 1": "#d8ff3c", "Liga BetPlay": "#ffd23f",
          "Copa Libertadores": "#ffcc33", "Copa Sudamericana": "#3ad1a7", "Brasileirão": "#2ee66b",
          "Liga Profesional Argentina": "#7cc7ff", "Liga MX": "#21d4a0", "Primeira Liga": "#ff5a36", "Eredivisie": "#ff7a00"}


def top_league(name: str | None) -> tuple[str, str, int] | None:
    n = (name or "").strip().lower()
    if not n or any(x in n for x in EXCLUDE):
        return None
    for variants, display, tag, rank in TOP_LEAGUES:
        if any(n == v or n.startswith(v) or v in n for v in variants if len(v) > 3) or n in variants:
            return display, tag, rank
    return None


def top_picks(rows: list[dict], n: int = 5, focus: str = "") -> list[dict]:
    """Football picks from top leagues only: most relevant league first, then probability; one per match."""
    out = []
    for r in rows:
        if r.get("sport") not in (None, "football"):
            continue
        lg = top_league(r.get("league"))
        if not lg:
            continue
        if focus and focus.lower() not in (lg[0].lower() + " " + str(r.get("league", "")).lower()):
            continue
        out.append({**r, "league": lg[0], "_tag": lg[1], "_rank": lg[2]})
    out.sort(key=lambda r: (r["_rank"], -float(r["p"])))
    seen, best = set(), []
    for r in out:
        if r.get("matchId") in seen:
            continue
        seen.add(r.get("matchId"))
        best.append(r)
    best = best[: max(n * 3, n)]
    best.sort(key=lambda r: -float(r["p"]))          # strongest of the most relevant
    return best[:n]


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return "".join(w.capitalize() for w in "".join(c if c.isalnum() else " " for c in s).split())[:30]


def hashtags_for(rows: list[dict]) -> list[str]:
    """League and team hashtags taken from the real picks."""
    tags = []
    for r in rows:
        for t in (r.get("_tag"), slug(r.get("home", "")), slug(r.get("away", ""))):
            if t and t not in tags:
                tags.append(t)
    return tags


# ------------------------------------------------------------------ shared look
FONTS = ("@import url('https://fonts.googleapis.com/css2?family=Anton&family=Inter:wght@400;600;800"
         "&family=JetBrains+Mono:wght@500;700&display=swap');")
STEPS = [(0.85, "#00f0a0"), (0.75, "#a6ff3c"), (0.65, "#ffe14d"), (0.55, "#ffb020"), (0.40, "#ff7a2f"), (0.0, "#ff4d6d")]


def pcolor(p: float) -> str:
    return next(c for t, c in STEPS if p >= t)


def esc(s) -> str:
    return html.escape(str(s or ""))


def team_color(name: str) -> str:
    h = int(hashlib.md5(name.encode()).hexdigest()[:6], 16) / 0xFFFFFF
    r, g, b = colorsys.hls_to_rgb(h, 0.42, 0.62)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def initials(name: str) -> str:
    words = [w for w in "".join(c if c.isalnum() else " " for c in name).split() if w.lower() not in ("fc", "cf", "de", "club", "the", "ac", "cd", "sc")]
    return ("".join(w[0] for w in words[:3]) or name[:2]).upper()


def badge(name: str, size: int) -> str:
    c = team_color(name)
    return (f"<div style='width:{size}px;height:{size}px;border-radius:50%;flex:none;display:grid;place-items:center;"
            f"background:radial-gradient(circle at 35% 30%,{c},#0b0a08 78%);border:3px solid {c};box-shadow:0 0 40px {c}55;"
            f"font-family:Anton;font-size:{int(size * .36)}px;color:#fff;letter-spacing:.02em'>{esc(initials(name))}</div>")


def base(body: str, w: int, h: int, accent: str = "#d4af37", watermark: str = "") -> str:
    wm = (f"<div style='position:absolute;right:-40px;top:38%;font-family:Anton;font-size:{int(w * .26)}px;line-height:.85;"
          f"color:rgba(255,255,255,.035);text-transform:uppercase;transform:rotate(-8deg);white-space:nowrap'>{esc(watermark)}</div>") if watermark else ""
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>{FONTS}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:{w}px;height:{h}px;overflow:hidden;position:relative;color:#f3ecdc;font-family:Inter,sans-serif;
 background:radial-gradient(900px 700px at 100% 0%,{accent}33,transparent 60%),radial-gradient(800px 700px at 0% 100%,#d4af3726,transparent 60%),#050403}}
.grain{{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.028) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.028) 1px,transparent 1px);background-size:60px 60px}}
.streak{{position:absolute;left:-20%;top:12%;width:140%;height:180px;transform:rotate(-14deg);background:linear-gradient(90deg,transparent,{accent}22,#d4af3722,transparent);filter:blur(30px)}}
.wrap{{position:relative;height:100%;display:flex;flex-direction:column;padding:70px 72px}}
.top{{display:flex;justify-content:space-between;align-items:center}}
.brand{{display:flex;align-items:center;gap:14px;font-weight:800;letter-spacing:.14em;font-size:24px;text-transform:uppercase}}
.chip{{display:inline-flex;align-items:center;gap:10px;border-radius:99px;padding:10px 22px;font-family:'JetBrains Mono',monospace;font-size:24px;letter-spacing:.12em;text-transform:uppercase}}
.anton{{font-family:Anton,Impact,sans-serif;text-transform:uppercase;letter-spacing:.01em}}
.gold{{background:linear-gradient(180deg,#fff2c0,#e7c25a 45%,#a77c18);-webkit-background-clip:text;color:transparent}}
.foot{{margin-top:auto;display:flex;justify-content:space-between;align-items:center;font-size:22px;color:#8e877a}}
</style></head><body><div class='grain'></div><div class='streak'></div>{wm}<div class='wrap'>{body}</div></body></html>"""


def top_bar(right: str, accent: str = "#d4af37") -> str:
    return (f"<div class='top'><div class='brand'>{MARK.format(s=46)}<span>Goldglitch <span style='color:#d4af37'>Stats</span></span></div>"
            f"<div class='chip' style='border:2px solid {accent};color:{accent}'>{esc(right)}</div></div>")


FOOT = "<div class='foot'><span>easygoldglitch.com</span><span>Probabilidad, no certeza · +18</span></div>"


# ------------------------------------------------------------------ carousel
def cover(hook: str, sub: str, leagues: list[str], w: int, h: int) -> str:
    chips = "".join(f"<div class='chip' style='border:2px solid {ACCENT.get(l, '#d4af37')};color:{ACCENT.get(l, '#d4af37')};font-size:22px'>{esc(l)}</div>"
                    for l in leagues[:5])
    words = esc(hook).split()
    head = " ".join(words[:-2]) + (f" <span class='gold'>{' '.join(words[-2:])}</span>" if len(words) > 2 else " ".join(words))
    return base(f"""{top_bar("Ligas top")}
      <div style='margin:auto 0'>
        <div class='anton' style='font-size:{int(w * .118)}px;line-height:.98'>{head}</div>
        <div style='font-size:{int(w * .034)}px;color:#cfc6b2;margin-top:34px;line-height:1.35;max-width:92%'>{esc(sub)}</div>
        <div style='display:flex;flex-wrap:wrap;gap:14px;margin-top:44px'>{chips}</div>
      </div>
      <div class='foot'><span class='anton' style='font-size:34px;color:#d4af37;letter-spacing:.04em'>DESLIZA →</span><span>Probabilidad, no certeza · +18</span></div>""",
                w, h, watermark="picks")


def pick(pk: dict, idx: int, total: int, when: str, w: int, h: int) -> str:
    p = float(pk["p"])
    c, acc = pcolor(p), ACCENT.get(pk["league"], "#d4af37")
    deg = int(p * 360)
    hot = "<div class='chip' style='background:#00f0a01f;border:2px solid #00f0a0;color:#00f0a0;font-size:20px'>Probabilidad alta</div>" if p >= 0.85 else ""
    teams = "".join(f"<div style='display:flex;align-items:center;gap:26px'>{badge(t, 118)}<div class='anton' style='font-size:{int(w * .07)}px;line-height:1'>{esc(t)}</div></div>"
                    for t in (pk["home"], pk["away"]))
    return base(f"""{top_bar(f"Pick {idx}/{total}", acc)}
      <div style='display:flex;gap:16px;align-items:center;margin-top:46px;flex-wrap:wrap'>
        <div class='chip' style='background:{acc}22;border:2px solid {acc};color:{acc}'>{esc(pk['league'])}</div>
        <div class='chip' style='border:2px solid #3a352b;color:#cfc6b2'>{esc(when)}</div>{hot}
      </div>
      <div style='display:flex;flex-direction:column;gap:22px;margin-top:44px'>{teams}</div>
      <div style='margin-top:auto;display:flex;align-items:center;gap:40px;background:rgba(14,12,9,.82);border:2px solid {c}55;border-radius:36px;padding:34px 38px'>
        <div style='width:{int(w * .3)}px;height:{int(w * .3)}px;border-radius:50%;flex:none;display:grid;place-items:center;
             background:conic-gradient({c} {deg}deg,#24211b {deg}deg);box-shadow:0 0 60px {c}44'>
          <div style='width:84%;height:84%;border-radius:50%;background:#0b0a08;display:grid;place-items:center'>
            <div class='anton' style='font-size:{int(w * .1)}px;color:{c};line-height:1'>{round(p * 100)}%</div></div></div>
        <div><div style='font-family:JetBrains Mono,monospace;letter-spacing:.2em;text-transform:uppercase;color:#9a9384;font-size:22px'>{esc(pk.get('group') or 'Mercado')}</div>
          <div style='font-size:{int(w * .046)}px;font-weight:800;line-height:1.12;margin-top:10px'>{esc(pk['label'])}</div>
          <div style='font-size:21px;color:#8e877a;margin-top:14px'>Si se repitiera 100 veces, el modelo espera que ocurra ~{round(p * 100)}.</div></div>
      </div>
      <div style='height:34px'></div>{FOOT}""", w, h, acc, watermark=pk["league"])


def results(rows: list[dict], won: int, n: int, w: int, h: int) -> str:
    items = "".join(
        f"<div style='display:flex;gap:20px;align-items:center;padding:16px 0;border-top:1px solid rgba(255,255,255,.07)'>"
        f"<div class='anton' style='font-size:40px;width:52px;color:{'#00f0a0' if r['status'] == 'won' else '#ff4d6d'}'>{'✓' if r['status'] == 'won' else '✗'}</div>"
        f"<div style='flex:1'><div style='font-size:28px;font-weight:600;line-height:1.2'>{esc(r['label'])}</div>"
        f"<div style='font-size:21px;color:#9a9384;margin-top:4px'>{esc(r['home'])} vs {esc(r['away'])}</div></div>"
        f"<div class='anton' style='font-size:34px;color:#9a9384'>{round(float(r['p']) * 100)}%</div></div>" for r in rows)
    rate = round(won / n * 100) if n else 0
    return base(f"""{top_bar("Resultados")}
      <div style='margin-top:50px;display:flex;align-items:baseline;gap:26px'>
        <div class='anton gold' style='font-size:{int(w * .17)}px;line-height:1'>{won}/{n}</div>
        <div style='font-size:34px;color:#cfc6b2'>acertados · {rate}%<br><span style='font-size:22px;color:#8e877a'>aciertos y fallos, sin esconder nada</span></div>
      </div><div style='margin-top:26px'>{items}</div>{FOOT}""", w, h, watermark="resultados")


def text_card(title: str, body: str, eyebrow: str, w: int, h: int) -> str:
    lines = "".join(f"<div style='display:flex;gap:18px;margin-top:26px'><div style='width:10px;border-radius:9px;background:#d4af37;flex:none'></div>"
                    f"<div style='font-size:{int(w * .036)}px;line-height:1.35;color:#e9e1cf'>{esc(x)}</div></div>"
                    for x in body.split("\n") if x.strip())
    return base(f"""{top_bar(eyebrow)}
      <div style='margin:auto 0'><div class='anton' style='font-size:{int(w * .092)}px;line-height:1'>{esc(title)}</div>{lines}</div>{FOOT}""",
                w, h, watermark="datos")


def cta(w: int, h: int) -> str:
    return base(f"""{top_bar("Gratis")}
      <div style='margin:auto 0'>
        <div class='anton' style='font-size:{int(w * .11)}px;line-height:1'>Todas las<br><span class='gold'>probabilidades</span><br>de cada partido</div>
        <div style='font-size:{int(w * .034)}px;color:#cfc6b2;margin-top:34px;line-height:1.4'>Goles, córners, tarjetas y jugadores, más el historial público de aciertos y fallos.</div>
        <div class='chip anton' style='margin-top:50px;background:#d4af37;color:#050403;font-size:{int(w * .045)}px;padding:22px 40px;letter-spacing:.04em'>Link en la bio →</div>
      </div>{FOOT}""", w, h, watermark="gratis")


# ------------------------------------------------------------------ reel frames (1080×1920)
def reel_frame(big: str, small: str = "", color: str = "#f3ecdc", accent: str = "#d4af37", glitch: bool = True,
               badge_names: tuple[str, str] | None = None, top: str = "") -> str:
    w, h = 1080, 1920
    shadow = "text-shadow:6px 0 0 #ff2d55,-6px 0 0 #00e5ff,0 0 60px rgba(0,0,0,.6);" if glitch else "text-shadow:0 0 60px rgba(0,0,0,.6);"
    badges = ""
    if badge_names:
        badges = (f"<div style='display:flex;justify-content:center;align-items:center;gap:40px;margin-bottom:60px'>{badge(badge_names[0], 230)}"
                  f"<div class='anton' style='font-size:90px;color:#d4af37'>VS</div>{badge(badge_names[1], 230)}</div>")
    size = 240 if len(big) <= 8 else 172 if len(big) <= 18 else 130 if len(big) <= 34 else 98
    return base(f"""{top_bar(top or "Goldglitch", accent)}
      <div style='margin:auto 0;text-align:center'>{badges}
        <div class='anton' style='font-size:{size}px;line-height:.98;color:{color};{shadow}'>{esc(big)}</div>
        <div style='font-size:58px;font-weight:800;margin-top:44px;color:#e9e1cf;line-height:1.2'>{esc(small)}</div>
      </div>
      <div class='foot' style='font-size:30px;margin-top:0'><span>easygoldglitch.com</span><span>+18 · probabilidad ≠ certeza</span></div>""", w, h, accent)


def reel_script(kind: str, rows: list[dict], tx: dict, when_fn) -> list[tuple[str, float, str]]:
    """[(html, seconds, effect)] — effect: punch | flash | shake | none."""
    f: list[tuple[str, float, str]] = []
    if kind in ("picks_dia", "reel") and rows:
        f.append((reel_frame(tx.get("reel_hook") or "EL MODELO VIO ALGO 👀", tx.get("reel_sub") or f"top {len(rows)} de las ligas grandes"), 1.3, "punch"))
        for i, r in enumerate(rows):
            acc = ACCENT.get(r["league"], "#d4af37")
            n = len(rows) - i
            f.append((reel_frame(f"#{n}", f"{r['league']} · {when_fn(r)}", accent=acc, top=r["league"]), 0.55, "flash"))
            f.append((reel_frame(f"{r['home']} vs {r['away']}", r["label"], accent=acc, glitch=False,
                                 badge_names=(r["home"], r["away"]), top=r["league"]), 1.25, "punch"))
            f.append((reel_frame(f"{round(float(r['p']) * 100)}%", r["label"], color=pcolor(float(r["p"])), accent=acc,
                                 top=r["league"]), 1.05, "shake"))
        f.append((reel_frame("¿ENTRA O NO ENTRA?", "comenta tu pick 👇", color="#d4af37"), 1.4, "punch"))
    elif kind == "resultados" and rows:
        won = sum(r["status"] == "won" for r in rows)
        f.append((reel_frame("¿CÓMO LE FUE AL MODELO?", "aciertos y fallos, sin filtro"), 1.3, "punch"))
        for r in rows[:5]:
            ok = r["status"] == "won"
            f.append((reel_frame("✓ ACERTÓ" if ok else "✗ FALLÓ", f"{r['label']} · {r['home']} vs {r['away']}",
                                 color="#00f0a0" if ok else "#ff4d6d"), 0.95, "shake" if ok else "flash"))
        f.append((reel_frame(f"{won}/{len(rows)}", "picks de 75%+ ya jugados", color="#d4af37"), 1.4, "punch"))
    else:
        f.append((reel_frame(tx.get("edu_title") or tx.get("cover_title") or "DATO", "espera al final 👀"), 1.5, "punch"))
        for line in [x for x in (tx.get("edu_body") or tx.get("cover_subtitle") or "").split("\n") if x.strip()][:5]:
            f.append((reel_frame(line, "", glitch=False), 1.6, "punch"))
    f.append((reel_frame("LINK EN LA BIO", "todas las probabilidades, gratis", color="#d4af37"), 1.8, "punch"))
    return f


def beat(path: str, seconds: float, bpm: int = 148) -> str:
    """Original percussion loop (kick, clap, hats) synthesized here — no third-party audio."""
    import random
    sr, n = 44100, int(seconds * 44100)
    buf = [0.0] * n
    step = 60 / bpm / 4                                      # 16th notes
    rnd = random.Random(7)

    def add(t0: float, gen, dur: float):
        i0 = int(t0 * sr)
        for k in range(int(dur * sr)):
            if i0 + k < n:
                buf[i0 + k] += gen(k / sr)
    kick = lambda t: math.sin(2 * math.pi * (55 + 140 * math.exp(-t * 28)) * t) * math.exp(-t * 9) * 0.9
    clap = lambda t: (rnd.random() * 2 - 1) * math.exp(-t * 22) * 0.45
    hat = lambda t: (rnd.random() * 2 - 1) * math.exp(-t * 90) * 0.18
    sub = lambda t: math.sin(2 * math.pi * 41.2 * t) * math.exp(-t * 3) * 0.35
    i = 0
    while i * step < seconds:
        t = i * step
        s = i % 16
        if s in (0, 6, 8, 11):
            add(t, kick, 0.35)
        if s in (4, 12):
            add(t, clap, 0.2)
        if s % 2 == 0 or s in (13, 15):
            add(t, hat, 0.05)
        if s == 0 and (i // 16) % 2 == 0:
            add(t, sub, 0.9)
        i += 1
    peak = max(1e-6, max(abs(x) for x in buf))
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, x / peak * 0.85)) * 32000)) for x in buf))
    return path


def reel_video(frames: list[tuple[str, float, str]], name: str) -> str:
    """Hard cuts, punch-in zooms, white flashes and shakes over an original beat. 1080×1920, 30 fps, H.264 + AAC."""
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    imgs = render([f[0] for f in frames], 1080, 1920, f"{name}_frames")
    inputs, parts, labels = [], [], []
    for i, (img, (_, secs, fx)) in enumerate(zip(imgs, frames)):
        nfr = max(8, int(secs * 30))
        inputs += ["-i", img]
        if fx == "punch":
            z = f"zoompan=z='max(1.18-0.012*on,1)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={nfr}:s=1080x1920:fps=30"
        elif fx == "shake":
            z = (f"zoompan=z='1.08':x='iw/2-(iw/zoom/2)+if(lt(on,10),18*sin(on*2.7),0)':"
                 f"y='ih/2-(ih/zoom/2)+if(lt(on,10),14*cos(on*3.1),0)':d={nfr}:s=1080x1920:fps=30")
        else:
            z = f"zoompan=z='1.0':d={nfr}:s=1080x1920:fps=30"
        flash = ",fade=t=in:st=0:d=0.12:color=white" if fx in ("flash", "shake") else ""
        parts.append(f"[{i}:v]scale=1080:1920,{z},format=yuv420p,setsar=1{flash}[v{i}]")
        labels.append(f"[v{i}]")
    total = sum(max(8, int(f[1] * 30)) for f in frames) / 30
    Path(OUT).mkdir(exist_ok=True)
    audio = beat(os.path.join(OUT, f"{name}_beat.wav"), total + 0.5)
    graph = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(labels)}:v=1:a=0[v]"
    out = os.path.join(OUT, f"{name}.mp4")
    cmd = [ff, "-y", *inputs, "-i", audio, "-filter_complex", graph, "-map", "[v]", "-map", f"{len(imgs)}:a",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-maxrate", "8M", "-bufsize", "16M", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-r", "30", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True, capture_output=True)
    return out
