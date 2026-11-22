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
ESPN_SLUG = {"Champions League": "uefa.champions", "Europa League": "uefa.europa", "Premier League": "eng.1", "LaLiga": "esp.1",
             "Serie A": "ita.1", "Bundesliga": "ger.1", "Ligue 1": "fra.1", "Primeira Liga": "por.1", "Eredivisie": "ned.1",
             "Liga BetPlay": "col.1", "Brasileirão": "bra.1", "Liga Profesional Argentina": "arg.1", "Liga MX": "mex.1",
             "Copa Libertadores": "conmebol.libertadores", "Copa Sudamericana": "conmebol.sudamericana"}
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
    load_colors([r["league"] for r in best[:n]])
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
FONTS = ("@import url('https://fonts.googleapis.com/css2?family=Anton&family=Instrument+Serif&family=Inter:wght@400;600;800"
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


COLORS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "redes_colores.json")
_COLORS: dict | None = None


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return " ".join(w for w in "".join(c if c.isalnum() else " " for c in s).split()
                    if w not in ("fc", "cf", "cd", "sc", "ac", "club", "de", "the", "afc", "ca", "se", "cr"))


def load_colors(leagues: list[str]) -> dict:
    """Club colours (primary, alternate) from ESPN's public team list, cached for 7 days. Only colours: no logos."""
    global _COLORS
    import json
    import time
    if _COLORS is None:
        try:
            with open(COLORS_FILE, encoding="utf-8") as f:
                _COLORS = json.load(f)
        except (OSError, ValueError):
            _COLORS = {}
    changed = False
    for lg in set(leagues):
        slug_ = ESPN_SLUG.get(lg)
        meta = _COLORS.get("_leagues", {}).get(slug_ or "")
        if not slug_ or (meta and time.time() - meta < 7 * 86400):
            continue
        try:
            import requests
            j = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug_}/teams", timeout=15).json()
            for t in ((j.get("sports") or [{}])[0].get("leagues") or [{}])[0].get("teams") or []:
                tm = t.get("team") or {}
                col, alt = tm.get("color"), tm.get("alternateColor")
                if not col:
                    continue
                for nm in {tm.get("displayName"), tm.get("shortDisplayName"), tm.get("name"), tm.get("location")}:
                    if nm:
                        _COLORS[_norm(nm)] = [f"#{col}", f"#{alt or col}"]
            _COLORS.setdefault("_leagues", {})[slug_] = time.time()
            changed = True
        except Exception:
            continue
    if changed:
        try:
            with open(COLORS_FILE, "w", encoding="utf-8") as f:
                json.dump(_COLORS, f)
        except OSError:
            pass
    return _COLORS


def club_colors(name: str) -> tuple[str, str]:
    c = (_COLORS or {}).get(_norm(name))
    if not c:
        n = _norm(name)
        c = next((v for k, v in (_COLORS or {}).items() if k != "_leagues" and isinstance(v, list) and k and (k in n or n in k)), None)
    if c:
        return c[0], c[1]
    h = team_color(name)
    return h, "#d4af37"


def _lum(hexc: str) -> float:
    try:
        r, g, b = (int(hexc.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    except ValueError:
        return 0.3


def initials(name: str) -> str:
    words = [w for w in "".join(c if c.isalnum() else " " for c in name).split() if w.lower() not in ("fc", "cf", "de", "club", "the", "ac", "cd", "sc")]
    return ("".join(w[0] for w in words[:3]) or name[:2]).upper()


def badge(name: str, size: int) -> str:
    """Original monogram in the club's real colours (solid primary, thick ring in the alternate colour). Not a crest."""
    c1, c2 = club_colors(name)
    ink = "#0b0a08" if _lum(c1) > 0.62 else "#ffffff"
    ring = c2 if c2.lower() != c1.lower() else "#d4af37"
    rw = max(5, size // 14)
    return (f"<div style='width:{size}px;height:{size}px;border-radius:50%;flex:none;display:grid;place-items:center;"
            f"background:radial-gradient(circle at 34% 28%,rgba(255,255,255,.28),transparent 46%),{c1};"
            f"border:{rw}px solid {ring};box-shadow:0 0 0 {max(2, size // 45)}px #0b0a08,0 0 {size // 2}px {c1}77,"
            f"inset 0 -{size // 9}px {size // 5}px rgba(0,0,0,.30);"
            f"font-family:Anton;font-size:{int(size * .36)}px;color:{ink};letter-spacing:.02em'>{esc(initials(name))}</div>")


ACCENTS = {"oro": "#d4af37", "esmeralda": "#19e0a0", "rubi": "#ff3b5c", "zafiro": "#3d8bff", "violeta": "#a25cff", "champana": "#f1d9a7"}
STYLE = {"acento": "oro", "portada": "impacto", "ritmo": "rapido"}     # set each day from Martina's art direction


def set_style(art: dict | None) -> None:
    for k in STYLE:
        if art and art.get(k):
            STYLE[k] = art[k]


BG: dict = {"feed": None, "reel": None, "_cache": {}}   # AI illustrations behind the current piece (goldglitch_ilustrador)


def set_bg(feed: str | None = None, reel: str | None = None) -> None:
    BG["feed"], BG["reel"] = feed, reel


def _data_uri(path: str, max_w: int = 2160) -> str:
    if path in BG["_cache"]:
        return BG["_cache"][path]
    import base64
    import io
    from PIL import Image
    im = Image.open(path).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, int(im.height * max_w / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=90)
    uri = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    BG["_cache"] = {path: uri}
    return uri


def house() -> str:
    return ACCENTS.get(STYLE["acento"], "#d4af37")


def base(body: str, w: int, h: int, accent: str | None = None, watermark: str = "") -> str:
    accent = accent or house()
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
</style></head><body>{_art_layer(h)}<div class='grain'></div><div class='streak'></div>{wm}<div class='wrap'>{body}</div></body></html>"""


def _art_layer(h: int) -> str:
    """Full-bleed illustration with a dark gradient so the text always reads."""
    path = BG["reel"] if h >= 1600 else BG["feed"]
    if not path or not os.path.exists(path):
        return ""
    return (f"<div style='position:absolute;inset:0;background:url({_data_uri(path)}) center/cover no-repeat'></div>"
            "<div style='position:absolute;inset:0;background:linear-gradient(180deg,rgba(5,4,3,.38) 0%,rgba(5,4,3,.42) 40%,"
            "rgba(5,4,3,.70) 75%,rgba(5,4,3,.9) 100%)'></div><style>.wrap{text-shadow:0 4px 26px rgba(0,0,0,.9)}</style>")


def top_bar(right: str, accent: str | None = None) -> str:
    accent = accent or house()
    return (f"<div class='top'><div class='brand'>{MARK.format(s=46)}<span>Goldglitch <span style='color:#d4af37'>Stats</span></span></div>"
            f"<div class='chip' style='border:2px solid {accent};color:{accent}'>{esc(right)}</div></div>")


FOOT = "<div class='foot'><span>easygoldglitch.com</span><span>Probabilidad, no certeza · +18</span></div>"


# ------------------------------------------------------------------ carousel
def cover(hook: str, sub: str, leagues: list[str], w: int, h: int) -> str:
    chips = "".join(f"<div class='chip' style='border:2px solid {ACCENT.get(l, '#d4af37')};color:{ACCENT.get(l, '#d4af37')};font-size:22px'>{esc(l)}</div>"
                    for l in leagues[:5])
    words = esc(hook).split()
    head = " ".join(words[:-2]) + (f" <span class='gold'>{' '.join(words[-2:])}</span>" if len(words) > 2 else " ".join(words))
    editorial = STYLE["portada"] == "editorial"
    title = (f"<div style=\"font-family:'Instrument Serif',serif;font-size:{int(w * .13)}px;line-height:.95;letter-spacing:-.01em\">{head}</div>"
             if editorial else f"<div class='anton' style='font-size:{int(w * .118)}px;line-height:.98'>{head}</div>")
    return base(f"""{top_bar("Ligas top", house())}
      <div style='margin:auto 0'>
        {title}
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



# ------------------------------------------------------------------ avatars (vector portraits, goldglitch_art.py)
def avatar(who: str = "egg", size: int = 120, mood: str = "smug") -> str:
    """Portrait of a character of the EGG universe: the AI-painted gallery when it exists (instalar_ilustrador.bat),
    else the vector version. mood: smug | wink | shock | laugh | neutral."""
    from goldglitch_art import ALIASES, portrait
    try:
        import goldglitch_ilustrador as IL
        key = ALIASES.get(str(who or "").strip().lower().replace("'", ""), "")
        painted = IL.character_path(key, mood) if key in IL.CHARACTER_DESC else None
    except Exception:
        painted = None
    if painted:
        return (f"<img src='{_data_uri(painted, 1024)}' style='flex:none;width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;"
                f"box-shadow:0 0 0 {max(3, size // 34)}px #d4af37,0 {size // 12}px {size // 5}px #000b'>")
    return portrait(who, size, mood)


def meme(fmt: str, m: dict, w: int, h: int) -> str:
    """Original meme layouts (no third-party images or characters): EGG's tweet, Nadie/Literalmente nadie,
    expectativa vs realidad, POV, starter pack and no/sí."""
    m = m if isinstance(m, dict) else {}
    big = int(w * .062)
    if fmt == "tweet":
        body = (f"<div style='margin:auto 0;background:#0e0c09;border:2px solid #2a261f;border-radius:44px;padding:56px 54px'>"
                f"<div style='display:flex;align-items:center;gap:22px'>{avatar('egg', 104, 'smug')}<div><div style='font-size:38px;font-weight:800'>"
                f"EGG <span style='color:#d4af37'>✦</span></div><div style='font-size:28px;color:#8e877a'>@easygoldglitch</div></div></div>"
                f"<div style='font-size:{big}px;line-height:1.3;margin-top:40px;font-weight:600'>{esc(m.get('texto') or '')}</div></div>")
    elif fmt == "nadie":
        body = (f"<div style='margin:auto 0'><div style='font-size:{big}px;line-height:1.5;color:#cfc6b2'>Nadie:<br>Literalmente nadie:</div>"
                f"<div class='anton' style='font-size:{int(w * .085)}px;line-height:1.05;margin-top:46px'>{esc(m.get('remate') or '')}</div></div>")
    elif fmt == "expectativa":
        panel = lambda lbl, txt, c: (f"<div style='flex:1;border:2px solid {c}66;background:{c}14;border-radius:36px;padding:40px 44px'>"
                                     f"<div class='chip' style='border:2px solid {c};color:{c}'>{lbl}</div>"
                                     f"<div style='font-size:{int(w * .055)}px;font-weight:800;line-height:1.2;margin-top:26px'>{esc(txt)}</div></div>")
        body = (f"<div style='margin:auto 0;display:flex;flex-direction:column;gap:30px'>{panel('Expectativa', m.get('expectativa') or '', '#00e5ff')}"
                f"{panel('Realidad', m.get('realidad') or '', '#ff4d6d')}</div>")
    elif fmt == "pov":
        body = (f"<div style='margin:auto 0;text-align:center'><div style='display:flex;justify-content:center;align-items:center;gap:20px'>"
                f"{avatar('egg', int(w * .26), 'shock')}<div style='font-size:{int(w * .14)}px'>{esc(m.get('emoji') or '👀')}</div></div>"
                f"<div class='anton gold' style='font-size:{int(w * .12)}px;line-height:1'>POV:</div>"
                f"<div style='font-size:{int(w * .066)}px;font-weight:800;line-height:1.2;margin-top:30px'>{esc(m.get('texto') or '')}</div></div>")
    elif fmt == "starter":
        items = [str(x) for x in (m.get("items") or [])][:6]
        tiles = "".join(f"<div style='background:#0e0c09;border:2px solid #2a261f;border-radius:30px;padding:30px 26px;"
                        f"font-size:{int(w * .04)}px;font-weight:700;line-height:1.25'>{esc(x)}</div>" for x in items)
        body = (f"<div style='margin:auto 0'><div class='anton' style='font-size:{int(w * .085)}px;line-height:1'>{esc(m.get('titulo') or 'Starter pack')}</div>"
                f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:40px'>{tiles}</div></div>")
    elif fmt == "noticia":
        body = (f"<div style='margin:auto 0'><div class='anton' style='display:inline-block;background:#ff2d55;color:#fff;font-size:40px;"
                f"padding:12px 26px;border-radius:12px;letter-spacing:.06em'>● ÚLTIMO MOMENTO</div>"
                f"<div style='font-size:{int(w * .062)}px;font-weight:800;line-height:1.2;margin-top:34px'>{esc(m.get('titular') or '')}</div>"
                f"<div style='margin-top:46px;background:#0e0c09;border:2px solid #2a261f;border-radius:36px;padding:38px 40px;display:flex;gap:22px'>"
                f"{avatar('egg', 96, 'smug')}<div style='font-size:{int(w * .05)}px;line-height:1.3;font-weight:600'>{esc(m.get('reaccion') or '')}</div></div></div>")
    elif fmt == "cuando":
        body = (f"<div style='margin:auto 0'><div style='font-size:{int(w * .066)}px;font-weight:800;line-height:1.25'>{esc(m.get('cuando') or '')}</div>"
                f"<div style='display:flex;align-items:center;gap:28px;margin-top:56px'>{avatar('egg', int(w * .2), 'wink')}"
                f"<div class='anton gold' style='font-size:{int(w * .08)}px;line-height:1.05'>{esc(m.get('reaccion') or '')}</div></div></div>")
    elif fmt == "tier":
        colors = {"S": "#ff4d6d", "A": "#d4af37", "B": "#00e5ff"}
        rows = "".join(f"<div style='display:flex;gap:20px;align-items:stretch;margin-top:20px'><div class='anton' style='width:120px;"
                       f"flex:none;display:grid;place-items:center;font-size:76px;background:{c};color:#050403;border-radius:22px'>{k}</div>"
                       f"<div style='flex:1;display:flex;flex-wrap:wrap;gap:14px;align-items:center;background:#0e0c09;border:2px solid #2a261f;"
                       f"border-radius:22px;padding:20px'>" + "".join(
                           f"<div style='font-size:{int(w * .036)}px;font-weight:700;background:#1b1813;border-radius:14px;padding:10px 18px'>{esc(x)}</div>"
                           for x in (m.get(k) or [])[:3]) + "</div></div>" for k, c in colors.items())
        body = f"<div style='margin:auto 0'><div class='anton' style='font-size:{int(w * .08)}px;line-height:1'>{esc(m.get('titulo') or 'Tier list')}</div>{rows}</div>"
    elif fmt == "chat":
        msgs = [x for x in (m.get("mensajes") or []) if isinstance(x, dict)][:5]
        bubbles = "".join(
            (f"<div style='align-self:flex-end;display:flex;gap:16px;align-items:flex-end;max-width:88%'>"
             f"<div style='background:#d4af37;color:#050403;border-radius:30px 30px 6px 30px;padding:22px 30px'>"
             f"<div style='font-size:24px;font-weight:800;opacity:.7'>EGG 💅</div><div style='font-size:{int(w * .042)}px;font-weight:700;line-height:1.25'>{esc(x.get('texto') or '')}</div></div>"
             f"{avatar('egg', 84, 'smug')}</div>")
            if i == len(msgs) - 1 else
            (f"<div style='align-self:flex-start;display:flex;gap:16px;align-items:flex-end;max-width:88%'>{avatar(x.get('de') or 'Parce', 76, ('shock', 'laugh', 'neutral', 'wink')[i % 4])}"
             f"<div style='background:#1b1813;border:2px solid #2a261f;border-radius:30px 30px 30px 6px;padding:22px 30px'>"
             f"<div style='font-size:24px;font-weight:800;color:{('#00e5ff', '#ff8a3d', '#a78bfa', '#00f0a0')[i % 4]}'>{esc(x.get('de') or 'Parce')}</div>"
             f"<div style='font-size:{int(w * .04)}px;line-height:1.25'>{esc(x.get('texto') or '')}</div></div></div>")
            for i, x in enumerate(msgs))
        body = (f"<div style='margin:auto 0;display:flex;flex-direction:column;gap:18px'>"
                f"<div style='text-align:center;font-size:30px;font-weight:800;color:#cfc6b2;margin-bottom:10px'>👥 {esc(m.get('grupo') or 'El parche ⚽')}</div>{bubbles}</div>")
    elif fmt == "duelo":
        side = lambda who, txt, c, e: (f"<div style='flex:1;border:2px solid {c}66;background:{c}12;border-radius:34px;padding:34px 30px;text-align:center'>"
                                       f"<div style='display:flex;justify-content:center'>{e}</div><div class='anton' style='font-size:{int(w * .05)}px;color:{c};margin-top:18px'>{esc(who)}</div>"
                                       f"<div style='font-size:{int(w * .038)}px;font-weight:700;line-height:1.25;margin-top:18px'>{esc(txt)}</div></div>")
        body = (f"<div style='margin:auto 0;display:flex;gap:22px;align-items:stretch'>{side(m.get('izquierda') or 'Tu amigo', m.get('izq_texto') or '', '#9a9384', avatar(m.get('izquierda') or 'Tu amigo', int(w * .2), 'shock'))}"
                f"<div class='anton' style='align-self:center;font-size:70px;color:#d4af37'>VS</div>"
                f"{side(m.get('derecha') or 'Vos con datos', m.get('der_texto') or '', '#d4af37', avatar('egg', int(w * .2), 'smug'))}</div>")
    elif fmt == "impopular":
        body = (f"<div style='margin:auto 0'><div class='chip' style='border:2px solid #ff4d6d;color:#ff4d6d'>🌶️ Opinión impopular</div>"
                f"<div class='anton' style='font-size:{int(w * .08)}px;line-height:1.05;margin-top:34px'>{esc(m.get('opinion') or '')}</div>"
                f"<div style='margin-top:40px;display:flex;gap:16px;align-items:center;font-size:{int(w * .042)}px;color:#cfc6b2'>"
                f"<span style='font-size:{int(w * .08)}px'>📊</span>{esc(m.get('dato') or '')}</div>"
                f"<div style='margin-top:34px;font-size:30px;color:#d4af37;font-weight:800'>¿De acuerdo o te dolió? 👇</div></div>")
    elif fmt == "reto":
        qs = "".join(f"<div style='background:#0e0c09;border:2px solid #2a261f;border-radius:26px;padding:22px 28px;margin-top:18px;"
                     f"font-size:{int(w * .04)}px;font-weight:700'><span style='color:#d4af37'>{i + 1}.</span> {esc(q)}</div>"
                     for i, q in enumerate((m.get("opciones") or [])[:3]))
        body = (f"<div style='margin:auto 0'><div class='chip' style='border:2px solid #00f0a0;color:#00f0a0'>🏆 Reto</div>"
                f"<div class='anton gold' style='font-size:{int(w * .085)}px;line-height:1;margin-top:26px'>{esc(m.get('titulo') or '')}</div>{qs}"
                f"<div style='margin-top:26px;font-size:28px;color:#cfc6b2'>Respuestas en comentarios · etiquetá al que se cree DT</div></div>")
    elif fmt == "giro":
        body = (f"<div style='margin:auto 0'><div style='font-size:{int(w * .062)}px;font-weight:800;line-height:1.25'>{esc(m.get('setup') or '')}</div>"
                f"<div style='margin:46px 0 20px;height:6px;background:repeating-linear-gradient(90deg,#ff2d55 0 30px,#00e5ff 30px 60px)'></div>"
                f"<div class='chip' style='border:2px solid #00e5ff;color:#00e5ff'>Plot twist</div>"
                f"<div class='anton gold' style='font-size:{int(w * .08)}px;line-height:1.05;margin-top:24px'>{esc(m.get('giro') or '')}</div></div>")
    else:  # no_si
        row = lambda e, txt, c: (f"<div style='display:flex;align-items:center;gap:34px;padding:40px 0;border-top:2px solid #2a261f'>"
                                 f"<div style='font-size:{int(w * .13)}px'>{e}</div><div style='font-size:{int(w * .058)}px;font-weight:800;"
                                 f"line-height:1.2;color:{c}'>{esc(txt)}</div></div>")
        body = f"<div style='margin:auto 0'>{row('🙅‍♀️', m.get('no') or '', '#9a9384')}{row('💅', m.get('si') or '', '#f3ecdc')}</div>"
    return base(f"{top_bar('Meme EGG')}{body}{FOOT}", w, h, watermark="meme")


def meme_lines(fmt: str, m: dict) -> list[tuple[str, str]]:
    """The same meme as reel beats: [(big, small)]."""
    m = m if isinstance(m, dict) else {}
    if fmt == "nadie":
        return [("NADIE:", ""), ("LITERALMENTE NADIE:", ""), (m.get("remate") or "", "")]
    if fmt == "expectativa":
        return [("EXPECTATIVA", m.get("expectativa") or ""), ("REALIDAD", m.get("realidad") or "")]
    if fmt == "pov":
        return [("POV:", ""), (m.get("texto") or "", m.get("emoji") or "")]
    if fmt == "starter":
        return [(m.get("titulo") or "STARTER PACK", "")] + [(str(x), "") for x in (m.get("items") or [])[:5]]
    if fmt == "no_si":
        return [("🙅‍♀️", m.get("no") or ""), ("💅", m.get("si") or "")]
    if fmt == "impopular":
        return [("🌶️ OPINIÓN IMPOPULAR", ""), (m.get("opinion") or "", ""), ("📊", m.get("dato") or ""), ("¿TE DOLIÓ?", "comentá 👇")]
    if fmt == "reto":
        return [(m.get("titulo") or "RETO", "")] + [(str(q), f"{i + 1}/3") for i, q in enumerate((m.get("opciones") or [])[:3])]
    if fmt == "giro":
        return [(m.get("setup") or "", ""), ("PLOT TWIST", ""), (m.get("giro") or "", "")]
    if fmt == "chat":
        return [(m.get("grupo") or "EL PARCHE ⚽", "")] + [(str(x.get("texto") or ""), str(x.get("de") or ""))
                                                         for x in (m.get("mensajes") or []) if isinstance(x, dict)][:5]
    if fmt == "duelo":
        return [(m.get("izquierda") or "TU AMIGO", m.get("izq_texto") or ""), ("VS", ""), (m.get("derecha") or "VOS CON DATOS", m.get("der_texto") or "")]
    if fmt == "noticia":
        return [("ÚLTIMO MOMENTO 🚨", m.get("titular") or ""), (m.get("reaccion") or "", "— EGG")]
    if fmt == "cuando":
        return [(m.get("cuando") or "", ""), (m.get("reaccion") or "", "")]
    if fmt == "tier":
        return [(m.get("titulo") or "TIER LIST", "")] + [(f"{k}: " + ", ".join(m.get(k) or []), "") for k in ("B", "A", "S") if m.get(k)]
    return [(m.get("texto") or "", "— EGG")]


def meme_faces(fmt: str, m: dict) -> list[tuple[str, str] | None]:
    """Who appears (character, mood) in each reel beat of a meme, aligned with meme_lines."""
    m = m if isinstance(m, dict) else {}
    if fmt == "duelo":
        return [(m.get("izquierda") or "Tu amigo", "shock"), None, ("egg", "smug")]
    if fmt == "chat":
        msgs = [x for x in (m.get("mensajes") or []) if isinstance(x, dict)][:5]
        return [None] + [(("egg", "smug") if i == len(msgs) - 1 else (x.get("de") or "Parce", ("shock", "laugh", "neutral", "wink")[i % 4]))
                         for i, x in enumerate(msgs)]
    if fmt in ("cuando", "noticia", "giro"):
        return [None, ("egg", "wink")] + ([("egg", "smug")] if fmt == "giro" else [])
    if fmt in ("pov", "expectativa", "nadie"):
        return [None] * (2 if fmt != "nadie" else 2) + [("egg", "shock" if fmt != "nadie" else "smug")]
    if fmt == "tweet":
        return [("egg", "smug")]
    return []


def cta(w: int, h: int) -> str:
    return base(f"""{top_bar("Gratis")}
      <div style='margin:auto 0'>
        <div class='anton' style='font-size:{int(w * .11)}px;line-height:1'>Todas las<br><span class='gold'>probabilidades</span><br>de cada partido</div>
        <div style='font-size:{int(w * .034)}px;color:#cfc6b2;margin-top:34px;line-height:1.4'>Goles, córners, tarjetas y jugadores, más el historial público de aciertos y fallos.</div>
        <div style='display:flex;align-items:center;gap:26px;margin-top:50px'>{avatar('egg', int(w * .16), 'wink')}
          <div class='chip anton' style='background:#d4af37;color:#050403;font-size:{int(w * .045)}px;padding:22px 40px;letter-spacing:.04em'>Link en la bio →</div></div>
      </div>{FOOT}""", w, h, watermark="gratis")


# ------------------------------------------------------------------ reel frames (1080×1920)
def reel_frame(big: str, small: str = "", color: str = "#f3ecdc", accent: str | None = None, glitch: bool = True,
               badge_names: tuple[str, str] | None = None, top: str = "", kicker: str = "", tilt: int = 8,
               bars: list[tuple[str, float, str]] | None = None, host: str | None = None,
               face: tuple[str, str] | None = None) -> str:
    """One scene. Depth: blurred giant echo of the text behind, 3D tilt, glow and floating light.
    host: mood of EGG's avatar presenting the scene (bottom-left), e.g. shock | smug | wink | laugh."""
    accent = accent or house()
    w, h = 1080, 1920
    shadow = "text-shadow:7px 0 0 #ff2d55cc,-7px 0 0 #00e5ffcc,0 18px 60px rgba(0,0,0,.75);" if glitch else "text-shadow:0 18px 60px rgba(0,0,0,.75);"
    badges = ""
    if badge_names:
        badges = (f"<div style='display:flex;justify-content:center;align-items:center;gap:46px;margin-bottom:70px;"
                  f"transform:perspective(1200px) rotateX({tilt}deg)'>{badge(badge_names[0], 250)}"
                  f"<div class='anton' style='font-size:96px;color:#d4af37;text-shadow:0 0 40px #d4af3799'>VS</div>{badge(badge_names[1], 250)}</div>")
    chart = ""
    if bars:
        chart = "<div style='margin:56px auto 0;width:86%;text-align:left'>" + "".join(
            f"<div style='margin-top:26px'><div style='display:flex;justify-content:space-between;font-size:40px;font-weight:800'>"
            f"<span>{esc(lbl)}</span><span style='color:{c}'>{round(v * 100)}%</span></div>"
            f"<div style='height:26px;border-radius:99px;background:#24211b;margin-top:12px;overflow:hidden'>"
            f"<div style='width:{v * 100:.1f}%;height:100%;border-radius:99px;background:linear-gradient(90deg,{c}aa,{c});box-shadow:0 0 30px {c}'></div></div></div>"
            for lbl, v, c in bars) + "</div>"
    size = 250 if len(big) <= 8 else 176 if len(big) <= 18 else 132 if len(big) <= 34 else 100
    echo = (f"<div class='anton' style='position:absolute;left:50%;top:50%;transform:translate(-50%,-50%) scale(1.9);white-space:nowrap;"
            f"font-size:{size}px;color:{color};opacity:.10;filter:blur(14px)'>{esc(big)}</div>")
    kick = (f"<div class='chip' style='margin:0 auto 40px;border:2px solid {accent};color:{accent};font-size:30px'>{esc(kicker)}</div>"
            if kicker else "")
    if face:      # the character who speaks in this beat, big and centered
        kick += f"<div style='display:flex;justify-content:center;margin-bottom:46px'>{avatar(face[0], 420, face[1])}</div>"
    if host:
        kick = (f"<div style='position:absolute;left:-10px;bottom:-470px;display:flex;align-items:center;gap:18px;z-index:3'>"
                f"{avatar('egg', 190, host)}<div class='chip anton' style='background:#d4af37;color:#050403;font-size:34px'>EGG</div></div>") + kick
    return base(f"""{top_bar(top or "Goldglitch", accent)}
      <div style='margin:auto 0;text-align:center;position:relative'>{echo}{kick}{badges}
        <div style='transform:perspective(1400px) rotateX({tilt // 2}deg)'>
          <div class='anton' style='font-size:{size}px;line-height:.98;color:{color};{shadow}'>{esc(big)}</div>
          <div style='font-size:58px;font-weight:800;margin-top:44px;color:#e9e1cf;line-height:1.2;text-shadow:0 8px 30px rgba(0,0,0,.7)'>{esc(small)}</div>
        </div>{chart}
      </div>
      <div class='foot' style='font-size:30px;margin-top:0'><span>easygoldglitch.com</span><span>+18 · probabilidad ≠ certeza</span></div>""",
                w, h, accent, watermark=top if top and top != "Goldglitch" else "")


def _rate(rec: dict | None) -> tuple[int, int, int] | None:
    for k in ("all", "d30", "d7"):
        r = (rec or {}).get(k) or {}
        if r.get("n"):
            return int(r["won"]), int(r["n"]), round(r["won"] / r["n"] * 100)
    return None


def reel_script(kind: str, rows: list[dict], tx: dict, when_fn, record: dict | None = None) -> list[tuple[str, float, str]]:
    """[(html, seconds, effect)] — effect: punch | flash | shake | slide | none."""
    f: list[tuple[str, float, str]] = []
    rate = _rate(record)
    if kind in ("picks_dia", "reel") and rows:
        f.append((reel_frame(tx.get("reel_hook") or "MIRÁ ESTO 👀", tx.get("reel_sub") or "o sea… quédate hasta el #1",
                             kicker=f"Top {len(rows)} · ligas grandes", host="shock"), 1.3, "punch"))
        if rate:
            f.append((reel_frame(f"{rate[0]}/{rate[1]}", f"picks de 75%+ acertados ({rate[2]}%) · fallos incluidos",
                                 color="#d4af37", kicker="Historial público", glitch=False), 1.2, "slide"))
        for i, r in enumerate(rows):
            acc = ACCENT.get(r["league"], "#d4af37")
            p = float(r["p"])
            fail = max(2, round(1 / max(1e-6, 1 - p)))
            f.append((reel_frame(f"#{len(rows) - i}", f"{r['league']} · {when_fn(r)}", accent=acc, top=r["league"], kicker="Pick"), 0.5, "flash"))
            f.append((reel_frame(f"{r['home']} vs {r['away']}", r["label"], accent=acc, glitch=False, badge_names=(r["home"], r["away"]),
                                 top=r["league"], tilt=10), 1.3, "punch"))
            f.append((reel_frame(f"{round(p * 100)}%", r["label"], color=pcolor(p), accent=acc, top=r["league"],
                                 kicker=r.get("group") or "Probabilidad"), 1.0, "shake"))
            f.append((reel_frame(f"1 DE CADA {fail}", "veces NO pasa. Literal, eso también es estadística.", color="#cfc6b2",
                                 accent=acc, top=r["league"], glitch=False, tilt=4), 0.95, "slide"))
        f.append((reel_frame("EL MÁS FUERTE", "de hoy", kicker="Ranking", bars=[(f"{r['home']}–{r['away']}"[:30], float(r["p"]), pcolor(float(r["p"])))
                                                                            for r in rows[:4]]), 1.9, "punch"))
        f.append((reel_frame("¿ENTRA O NO ENTRA?", "decime en comentarios: 1 entra · 2 no entra 👇", color="#d4af37"), 1.3, "shake"))
        f.append((reel_frame("GUARDALO 📌", "y mandáselo a tu amigo del club que 'sabe de fútbol' 🥂",
                             color="#f3ecdc", kicker="📌"), 1.2, "punch"))
    elif kind == "resultados" and rows:
        won = sum(r["status"] == "won" for r in rows)
        f.append((reel_frame("¿CÓMO LE FUE AL MODELO?", "aciertos y fallos, sin filtro", kicker="Resultados"), 1.3, "punch"))
        for r in rows[:6]:
            ok = r["status"] == "won"
            f.append((reel_frame("✓ ACERTÓ" if ok else "✗ FALLÓ", f"{r['label']} · {r['home']} vs {r['away']}",
                                 color="#00f0a0" if ok else "#ff4d6d", kicker=f"{round(float(r['p']) * 100)}%"), 0.9, "shake" if ok else "flash"))
        f.append((reel_frame(f"{won}/{len(rows)}", "picks de 75%+ jugados en las últimas horas", color="#d4af37", kicker="Balance"), 1.4, "punch"))
        if rate:
            f.append((reel_frame(f"{rate[2]}%", f"de acierto histórico ({rate[0]}/{rate[1]})", color="#d4af37", kicker="Historial público"), 1.3, "slide"))
    elif kind == "meme":
        trend = str(tx.get("tendencia_usada") or "")[:40]
        fmt, mm = tx.get("meme_formato") or "", tx.get("meme") or {}
        faces = meme_faces(fmt, mm)
        for i, (big, small) in enumerate(l for l in meme_lines(fmt, mm) if l[0] or l[1]):
            f.append((reel_frame(big, small, glitch=i % 2 == 0, kicker=(f"🔥 {trend}" if trend else "Meme EGG") if i == 0 else "",
                                 tilt=6, face=faces[i] if i < len(faces) else None), 1.4 if i else 1.1,
                      ("punch", "shake", "slide", "flash")[i % 4]))
        f.append((reel_frame("MANDÁSELO 📲", "a ese amigo que necesita verlo 😂", color="#d4af37", host="laugh"), 1.2, "punch"))
    else:
        f.append((reel_frame(tx.get("edu_title") or tx.get("cover_title") or "DATO", "espera al final 👀", kicker="Dato"), 1.5, "punch"))
        for line in [x for x in (tx.get("edu_body") or tx.get("cover_subtitle") or "").split("\n") if x.strip()][:5]:
            f.append((reel_frame(line, "", glitch=False, tilt=4), 1.6, "slide"))
    f.append((reel_frame("LINK EN LA BIO", "todas las probabilidades, gratis. Next level 🥂", color="#d4af37", kicker="EGG · Goldglitch Stats",
                         host="wink"), 1.8, "punch"))
    return f


def beat(path: str, seconds: float, bpm: int = 148, cuts: list[tuple[float, str]] | None = None) -> str:
    """Original percussion loop (kick, clap, hats, sub, riser) synthesized here — no third-party audio."""
    import random
    sr, n = 44100, int(seconds * 44100)
    buf = [0.0] * n
    step = 60 / bpm / 4
    rnd = random.Random(7)

    def add(t0: float, gen, dur: float):
        i0 = int(t0 * sr)
        for k in range(int(dur * sr)):
            if i0 + k < n:
                buf[i0 + k] += gen(k / sr)
    kick = lambda t: math.sin(2 * math.pi * (52 + 150 * math.exp(-t * 30)) * t) * math.exp(-t * 8) * 0.95
    clap = lambda t: (rnd.random() * 2 - 1) * math.exp(-t * 20) * 0.45
    hat = lambda t: (rnd.random() * 2 - 1) * math.exp(-t * 95) * 0.16
    sub = lambda t: math.sin(2 * math.pi * 41.2 * t) * math.exp(-t * 2.5) * 0.4
    riser = lambda t: (rnd.random() * 2 - 1) * (t / 1.2) * 0.12
    # sound design synced to the edit
    whoosh = lambda t: (rnd.random() * 2 - 1) * math.sin(math.pi * min(t / 0.22, 1)) * 0.34
    impact = lambda t: (math.sin(2 * math.pi * (38 + 90 * math.exp(-t * 18)) * t) * 1.1 + (rnd.random() * 2 - 1) * math.exp(-t * 35) * .5) * math.exp(-t * 5)
    zap = lambda t: math.sin(2 * math.pi * (1800 - 1500 * t / .12) * t) * math.exp(-t * 25) * 0.25
    for t0, fx in (cuts or []):
        add(max(0.0, t0 - 0.11), whoosh, 0.24)
        if fx in ("shake", "punch"):
            add(t0, impact, 0.6)
        if fx == "flash":
            add(t0, zap, 0.12)
    i = 0
    while i * step < seconds:
        t, s16 = i * step, i % 16
        bar = i // 16
        if s16 in (0, 6, 8, 11) or (bar % 4 == 3 and s16 in (12, 13, 14, 15)):
            add(t, kick, 0.35)
        if s16 in (4, 12):
            add(t, clap, 0.2)
        if s16 % 2 == 0 or s16 in (13, 15):
            add(t, hat, 0.05)
        if s16 == 0 and bar % 2 == 0:
            add(t, sub, 1.0)
        if s16 == 0 and bar % 4 == 2:
            add(t + 16 * step - 1.2, riser, 1.2)
        i += 1
    peak = max(1e-6, max(abs(x) for x in buf))
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, x / peak * 0.85)) * 32000)) for x in buf))
    return path


TRANSITIONS = ["zoomin", "slideup", "smoothleft", "circleopen", "fadewhite", "slidedown", "radial", "smoothup"]


def R_SCALE() -> float:
    from goldglitch_social_render import SCALE
    return SCALE


def reel_video(frames: list[tuple[str, float, str]], name: str) -> str:
    """Scenes with punch-in zooms, wobble, RGB-split glitches and a moving gold light, joined with varied quick
    transitions, over an original beat. 2160×3840 (4K) with REDES_ESCALA=2 (default), 30 fps, H.264 + AAC."""
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    imgs = render([f[0] for f in frames], 1080, 1920, f"{name}_frames")
    S = max(1, int(round(R_SCALE())))                      # 2 → 2160×3840 (4K vertical)
    W, H = 1080 * S, 1920 * S
    T = 0.14                                                # transition length
    inputs, parts, durs = [], [], []
    for i, (img, (_, secs, fx)) in enumerate(zip(imgs, frames)):
        pace = {"muy_rapido": 0.78, "elegante": 1.25}.get(STYLE["ritmo"], 1.0)
        nfr = max(10, int((secs * pace + T) * 30))
        durs.append(nfr / 30)
        inputs += ["-framerate", "30", "-loop", "1", "-t", f"{nfr / 30:.3f}", "-i", img]
        if fx == "punch":
            z = f"zoompan=z='max(1.22-0.014*on,1.02)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps=30"
        elif fx == "shake":
            z = (f"zoompan=z='1.10':x='iw/2-(iw/zoom/2)+if(lt(on,12),{22 * S}*sin(on*2.9),{3 * S}*sin(on*.5))':"
                 f"y='ih/2-(ih/zoom/2)+if(lt(on,12),{16 * S}*cos(on*3.3),{2 * S}*cos(on*.4))':d=1:s={W}x{H}:fps=30")
        elif fx == "slide":
            z = f"zoompan=z='1.06':x='(iw-iw/zoom)*min(on/{nfr},1)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps=30"
        else:
            z = f"zoompan=z='1.04+0.0015*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps=30"
        wob = "rotate='0.012*sin(2*PI*t*0.9)':fillcolor=black@1," if fx in ("punch", "slide") else ""
        glitch = f",rgbashift=rh=-{8 * S}:bh={8 * S}:enable='lt(t,0.25)'" if fx in ("shake", "flash") else ""
        flash = ",fade=t=in:st=0:d=0.10:color=white" if fx == "flash" else ""
        # moving light sweep (depth) on every scene
        sweep = rf",drawbox=x='-{400 * S}+mod(t*{1500 * S}\,{1900 * S})':y=0:w={150 * S}:h=ih:color=0xd4af37@0.045:t=fill"
        parts.append(f"[{i}:v]scale={1200 * S}:{2134 * S},{z},{wob}format=yuv420p,setsar=1{glitch}{flash}{sweep},"
                     f"vignette=PI/5,trim=duration={nfr / 30:.3f},setpts=PTS-STARTPTS[v{i}]")
    chain, last, off = [], "v0", durs[0] - T
    for i in range(1, len(imgs)):
        tr = TRANSITIONS[i % len(TRANSITIONS)]
        chain.append(f"[{last}][v{i}]xfade=transition={tr}:duration={T}:offset={off:.3f}[x{i}]")
        last, off = f"x{i}", off + durs[i] - T
    total = off + T
    Path(OUT).mkdir(exist_ok=True)
    starts, acc = [], 0.0
    for d, (_, _, fx) in zip(durs, frames):
        starts.append((acc, fx))
        acc += d - T
    audio = beat(os.path.join(OUT, f"{name}_beat.wav"), total + 0.5, cuts=starts)
    graph = ";".join(parts + chain)
    out = os.path.join(OUT, f"{name}.mp4")
    cmd = [ff, "-y", *inputs, "-i", audio, "-filter_complex", graph, "-map", f"[{last}]", "-map", f"{len(imgs)}:a",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-maxrate", "28M", "-bufsize", "56M", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-r", "30", "-movflags", "+faststart", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg: " + r.stderr[-600:])
    return out
