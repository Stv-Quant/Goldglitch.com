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
import re
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


FAMOUS = ("real madrid", "barcelona", "atletico madrid", "atlético madrid", "manchester city", "manchester united", "liverpool",
          "arsenal", "chelsea", "tottenham", "newcastle", "bayern", "dortmund", "leverkusen", "paris saint", "psg", "marseille",
          "juventus", "milan", "inter", "napoli", "roma", "benfica", "porto", "sporting", "ajax", "boca juniors", "river plate",
          "racing club", "independiente", "san lorenzo", "flamengo", "palmeiras", "corinthians", "sao paulo", "são paulo",
          "santos", "gremio", "grêmio", "internacional", "fluminense", "botafogo", "atletico mineiro", "atlético mineiro",
          "atletico nacional", "atlético nacional", "millonarios", "america de cali", "américa de cali", "deportivo cali",
          "junior", "santa fe", "once caldas", "independiente medellin", "independiente medellín", "tolima", "america", "chivas",
          "tigres", "monterrey", "cruz azul")
EUROPE = {"Champions League", "Europa League", "Premier League", "LaLiga", "Serie A", "Bundesliga", "Ligue 1", "Primeira Liga", "Eredivisie"}
SOUTH = {"Copa Libertadores", "Copa Sudamericana", "Brasileirão", "Liga Profesional Argentina"}


def famous_picks(rows: list[dict], n: int = 4) -> list[dict]:
    """The morning picks: fewer than 5, the most famous teams, mixing Europe, South America and Liga BetPlay."""
    cands = top_picks(rows, 60)
    fame = lambda r: sum(f in (r["home"] + " " + r["away"]).lower() for f in FAMOUS)
    cands.sort(key=lambda r: (-fame(r), r["_rank"], -float(r["p"])))
    out: list[dict] = []
    for pool in (lambda r: r["league"] == "Liga BetPlay", lambda r: r["league"] in SOUTH, lambda r: r["league"] in EUROPE):
        pick = next((r for r in cands if pool(r) and r not in out and fame(r)), None) or next((r for r in cands if pool(r) and r not in out), None)
        if pick:
            out.append(pick)
    for r in cands:
        if len(out) >= n:
            break
        if r not in out:
            out.append(r)
    out = out[:n]
    load_colors([r["league"] for r in out])
    return sorted(out, key=lambda r: -float(r["p"]))


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
# House typography (EGG identity): Big Shoulders Display for headlines (condensed, stadium signage), Instrument Serif
# italic for the editorial accent, Inter for text and JetBrains Mono for every number (data feel).
FONTS = ("@import url('https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@700;800;900&family=Anton"
         "&family=Instrument+Serif:ital@0;1&family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@500;700&display=swap');")
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


KNOWN_COLORS = {   # kit colours of big clubs (fallback when ESPN's colour data is missing)
    "milan": ("#c8102e", "#111111"), "inter": ("#0a2fa3", "#111111"), "juventus": ("#111111", "#f5f5f5"),
    "napoli": ("#1e90ff", "#f5f5f5"), "roma": ("#8e1f2f", "#f0bc42"), "lazio": ("#87d8f7", "#f5f5f5"),
    "real madrid": ("#f5f5f5", "#d4af37"), "barcelona": ("#a50044", "#004d98"), "atletico": ("#cb3524", "#f5f5f5"),
    "sevilla": ("#f5f5f5", "#d71920"), "betis": ("#0bb363", "#f5f5f5"), "athletic": ("#ee2523", "#f5f5f5"),
    "manchester city": ("#6cabdd", "#f5f5f5"), "manchester united": ("#da291c", "#111111"), "liverpool": ("#c8102e", "#f5f5f5"),
    "arsenal": ("#ef0107", "#f5f5f5"), "chelsea": ("#034694", "#f5f5f5"), "tottenham": ("#f5f5f5", "#132257"),
    "newcastle": ("#111111", "#f5f5f5"), "bayern": ("#dc052d", "#f5f5f5"), "dortmund": ("#fde100", "#111111"),
    "psg": ("#004170", "#da291c"), "paris saint": ("#004170", "#da291c"), "river plate": ("#f5f5f5", "#d6001c"),
    "boca": ("#0b2a6f", "#f6c200"), "flamengo": ("#c8102e", "#111111"), "palmeiras": ("#006437", "#f5f5f5"),
    "america de cali": ("#d3122a", "#f5f5f5"), "deportivo cali": ("#0b8a3b", "#f5f5f5"), "atletico nacional": ("#0b8a3b", "#f5f5f5"),
    "millonarios": ("#0a3a8a", "#f5f5f5"), "atletico junior": ("#d3122a", "#f5f5f5"), "boca juniors": ("#0b2a6f", "#f6c200"), "santa fe": ("#d3122a", "#f5f5f5"),
    "club america": ("#f6d500", "#0b2a6f"), "chivas": ("#d3122a", "#f5f5f5"), "tigres": ("#f6b500", "#0b2a6f"),
    "monterrey": ("#0b2a6f", "#f5f5f5"),
    # NBA
    "lakers": ("#552583", "#fdb927"), "celtics": ("#007a33", "#f5f5f5"), "warriors": ("#1d428a", "#ffc72c"),
    "bulls": ("#ce1141", "#111111"), "heat": ("#98002e", "#111111"), "knicks": ("#006bb6", "#f58426"), "nets": ("#111111", "#f5f5f5"),
    "bucks": ("#00471b", "#eee1c6"), "76ers": ("#006bb6", "#ed174c"), "sixers": ("#006bb6", "#ed174c"), "raptors": ("#ce1141", "#111111"),
    "cavaliers": ("#860038", "#fdbb30"), "pistons": ("#c8102e", "#1d42ba"), "pacers": ("#002d62", "#fdbb30"), "hawks": ("#e03a3e", "#f5f5f5"),
    "hornets": ("#1d1160", "#00788c"), "magic": ("#0077c0", "#111111"), "wizards": ("#002b5c", "#e31837"), "nuggets": ("#0e2240", "#fec524"),
    "timberwolves": ("#0c2340", "#78be20"), "thunder": ("#007ac1", "#ef3b24"), "trail blazers": ("#e03a3e", "#111111"),
    "jazz": ("#002b5c", "#f9a01b"), "suns": ("#1d1160", "#e56020"), "clippers": ("#c8102e", "#1d428a"), "kings": ("#5a2d81", "#63727a"),
    "mavericks": ("#00538c", "#b8c4ca"), "rockets": ("#ce1141", "#f5f5f5"), "grizzlies": ("#5d76a9", "#12173f"),
    "pelicans": ("#0c2340", "#c8102e"), "spurs": ("#111111", "#c4ced4"),
}


def club_colors(name: str) -> tuple[str, str]:
    c = (_COLORS or {}).get(_norm(name))
    if not c:
        n = _norm(name)
        c = next((v for k, v in (_COLORS or {}).items() if k != "_leagues" and isinstance(v, list) and k and (k in n or n in k)), None)
    if c:
        return c[0], c[1]
    n = _norm(name)
    for k in sorted(KNOWN_COLORS, key=len, reverse=True):
        if k in n:
            return KNOWN_COLORS[k]
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


KIT_PATTERN = {   # well-known kit layouts (colours come from the club's real colours; no crests, no sponsors)
    "stripes": ["juventus", "barcelona", "inter", "milan", "atletico", "atlético", "athletic", "newcastle", "sporting",
                "estudiantes", "san lorenzo", "porto", "brentford", "sunderland", "deportivo cali", "santos", "botafogo",
                "atalanta", "udinese", "club brugge", "independiente santa fe", "junior", "colo colo", "penarol", "peñarol"],
    "sash": ["river plate", "vasco", "rayo vallecano", "racing club"],
    "band": ["boca juniors", "boca"],
    "hoops": ["celtic", "queens park", "shamrock"],
    "halves": ["blackburn", "huracan", "huracán"],
}


def kit_pattern(name: str) -> str:
    n = str(name or "").lower()
    for club, pat in sorted(((c, p) for p, cs in KIT_PATTERN.items() for c in cs), key=lambda x: -len(x[0])):
        if re.search(rf"\b{re.escape(club)}\b", n):   # whole words, longest first ("boca juniors" before "junior")
            return pat
    return ("plain", "trim", "panel")[sum(map(ord, n)) % 3]


def badge(name: str, size: int) -> str:
    """A shirt in the club's real colours and a kit layout like theirs (stripes, sash, hoops…). Never a crest or logo."""
    c1, c2 = club_colors(name)
    if c2.lower() == c1.lower():
        c2 = "#f5f5f4" if _lum(c1) < 0.6 else "#111111"
    pat = kit_pattern(name)
    uid = abs(hash((name, size))) % 999999
    body = "M30 14 L42 9 Q50 17 58 9 L70 14 L91 29 L81 46 L72 40 L72 91 Q50 95 28 91 L28 40 L19 46 L9 29 Z"
    deco = {
        "stripes": "".join(f"<rect x='{x}' y='0' width='7' height='100' fill='{c2}'/>" for x in (33, 47, 61)),
        "sash": f"<path d='M20 30 L36 14 L82 82 L68 96 Z' fill='{c2}'/>",
        "band": f"<rect x='0' y='44' width='100' height='15' fill='{c2}'/>",
        "hoops": "".join(f"<rect x='0' y='{y}' width='100' height='8' fill='{c2}'/>" for y in (26, 42, 58, 74)),
        "halves": f"<rect x='50' y='0' width='50' height='100' fill='{c2}'/>",
        "panel": f"<rect x='28' y='38' width='6' height='60' fill='{c2}'/><rect x='66' y='38' width='6' height='60' fill='{c2}'/>",
        "trim": f"<rect x='0' y='84' width='100' height='12' fill='{c2}' opacity='.9'/>",
        "plain": "",
    }[pat]
    return f"""<svg width='{size}' height='{size}' viewBox='0 0 100 100' style='flex:none;filter:drop-shadow(0 {max(3, size // 18)}px {max(6, size // 7)}px rgba(0,0,0,.6))'>
<defs><clipPath id='k{uid}'><path d='{body}'/></clipPath>
<linearGradient id='s{uid}' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#fff' stop-opacity='.28'/><stop offset='.45' stop-color='#fff' stop-opacity='0'/>
<stop offset='1' stop-color='#000' stop-opacity='.32'/></linearGradient></defs>
<g clip-path='url(#k{uid})'><rect width='100' height='100' fill='{c1}'/>{deco}
<path d='M9 29 L19 46 L28 40 L28 36 L14 24 Z M91 29 L81 46 L72 40 L72 36 L86 24 Z' fill='{c2}' opacity='.95'/>
<path d='M36 30 Q40 60 34 92 M64 30 Q60 60 66 92' stroke='#000' stroke-opacity='.12' stroke-width='1.6' fill='none'/>
<rect width='100' height='100' fill='url(#s{uid})'/></g>
<path d='M42 9 Q50 19 58 9' fill='none' stroke='{c2}' stroke-width='3.4' stroke-linecap='round'/>
<path d='{body}' fill='none' stroke='rgba(0,0,0,.45)' stroke-width='1.2'/></svg>"""


def _old_badge(name: str, size: int) -> str:
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
.grain{{position:absolute;inset:0;background-image:radial-gradient(rgba(255,255,255,.07) 1.1px,transparent 1.3px);background-size:14px 14px;
 -webkit-mask-image:linear-gradient(160deg,#000 0%,transparent 55%);mask-image:linear-gradient(160deg,#000 0%,transparent 55%)}}
.slab{{position:absolute;left:-10%;width:120%;transform:rotate(-9deg);pointer-events:none}}
.streak{{position:absolute;left:-20%;top:12%;width:140%;height:180px;transform:rotate(-14deg);background:linear-gradient(90deg,transparent,{accent}22,#d4af3722,transparent);filter:blur(30px)}}
.wrap{{position:relative;height:100%;display:flex;flex-direction:column;padding:70px 72px}}
.top{{display:flex;justify-content:space-between;align-items:center}}
.brand{{display:flex;align-items:center;gap:14px;font-weight:800;letter-spacing:.14em;font-size:24px;text-transform:uppercase}}
.chip{{display:inline-flex;align-items:center;gap:10px;border-radius:99px;padding:10px 22px;font-family:'JetBrains Mono',monospace;font-size:24px;letter-spacing:.12em;text-transform:uppercase}}
.anton{{font-family:'Big Shoulders Display',Anton,Impact,sans-serif;font-weight:900;text-transform:uppercase;letter-spacing:.005em}}
.serif{{font-family:'Instrument Serif',serif;font-style:italic;text-transform:none;letter-spacing:0}}
.rule{{height:2px;background:linear-gradient(90deg,#d4af37,rgba(212,175,55,.15));margin:18px 0 0}}
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
    import datetime as _dt
    d = _dt.datetime.now(_dt.timezone(_dt.timedelta(hours=-5)))
    days = ["LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB", "DOM"]
    months = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]
    edition = f"Nº {d.timetuple().tm_yday:03d} · {days[d.weekday()]} {d.day} {months[d.month - 1]}"
    return (f"<div><div class='top'><div class='brand'>{MARK.format(s=44)}<span>EGG <span style='color:#d4af37'>·</span> "
            f"<span style='font-weight:600;letter-spacing:.2em'>El Dato</span></span></div>"
            f"<div style='font-family:JetBrains Mono,monospace;font-size:22px;letter-spacing:.14em;color:#b9ad92'>{edition}</div></div>"
            f"<div class='rule'></div><div style='margin-top:14px;font-family:JetBrains Mono,monospace;font-size:20px;letter-spacing:.24em;"
            f"color:{accent};text-transform:uppercase'>{esc(strip_emoji(right))}</div></div>")


FOOT = ("<div class='foot' style='border-top:1px solid rgba(212,175,55,.25);padding-top:18px'><span style='letter-spacing:.12em'>"
        "GOLDGLITCH STATS · easygoldglitch.com</span><span>Probabilidad, no certeza · +18</span></div>")


def strip_emoji(s) -> str:
    """Images carry no emoji (they read as 'AI template'); captions keep a few."""
    import re as _re
    return _re.sub("[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200D\u2B50\u2B06\u2934\u2935\u25B6\u25C0\u23E9-\u23FA]", "",
                   str(s or "")).replace("  ", " ").strip()


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
    teams = "".join(f"<div style='display:flex;align-items:center;gap:26px'>{badge(t, 132)}<div class='anton' style='font-size:{int(w * .075)}px;line-height:1'>{esc(t)}</div></div>"
                    for t in (pk["home"], pk["away"]))
    h1, a1 = club_colors(pk["home"])[0], club_colors(pk["away"])[0]
    teams = (f"<div style='position:relative'><div class='slab' style='top:40px;height:230px;background:linear-gradient(90deg,{h1}55,{h1}22 45%,{a1}22 55%,{a1}55);"
             f"border-top:3px solid {h1}aa;border-bottom:3px solid {a1}aa'></div><div style='position:relative;display:flex;flex-direction:column;gap:18px'>{teams}</div></div>")
    return base(f"""{top_bar(f"Pick {idx}/{total}", acc)}
      <div style='display:flex;gap:16px;align-items:center;margin-top:46px;flex-wrap:wrap'>
        <div class='chip' style='background:{acc}22;border:2px solid {acc};color:{acc}'>{esc(pk['league'])}</div>
        <div class='chip' style='border:2px solid #3a352b;color:#cfc6b2'>{esc(when)}</div>{hot}
      </div>
      <div style='margin-top:44px'>{teams}</div>
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
    # Drawn avatars are banned from the posts (they looked cheap). Only the AI-painted gallery may appear, and only if
    # it is explicitly enabled with REDES_PERSONAJES=1; otherwise no character is drawn at all.
    if os.environ.get("REDES_PERSONAJES", "0") != "1":
        return ""
    from goldglitch_art import ALIASES
    try:
        import goldglitch_ilustrador as IL
        key = ALIASES.get(str(who or "").strip().lower().replace("'", ""), "")
        painted = IL.character_path(key, mood) if key in IL.CHARACTER_DESC else None
    except Exception:
        painted = None
    if painted:
        return (f"<img src='{_data_uri(painted, 1024)}' style='flex:none;width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;"
                f"box-shadow:0 0 0 {max(3, size // 34)}px #d4af37,0 {size // 12}px {size // 5}px #000b'>")
    return ""


def meme(fmt: str, m: dict, w: int, h: int) -> str:
    """Original meme layouts (no third-party images or characters): EGG's tweet, Nadie/Literalmente nadie,
    expectativa vs realidad, POV, starter pack and no/sí."""
    m = m if isinstance(m, dict) else {}
    big = int(w * .062)
    if fmt == "tweet":
        body = (f"<div style='margin:auto 0;background:#0e0c09;border:2px solid #2a261f;border-radius:44px;padding:56px 54px'>"
                f"<div style='display:flex;align-items:center;gap:22px'>{avatar('egg', 104, 'smug')}<div><div style='font-size:38px;font-weight:800'>"
                f"EGG</div><div style='font-size:28px;color:#8e877a'>@easygoldglitch</div></div></div>"
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
                f"{avatar('egg', int(w * .26), 'shock')}<div style='font-size:{int(w * .14)}px'>{esc(strip_emoji(m.get('emoji') or ''))}</div></div>"
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
                f"padding:12px 26px;border-radius:12px;letter-spacing:.06em'>ÚLTIMO MOMENTO</div>"
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
             f"<div style='font-size:24px;font-weight:800;opacity:.7'>EGG</div><div style='font-size:{int(w * .042)}px;font-weight:700;line-height:1.25'>{esc(x.get('texto') or '')}</div></div>"
             f"{avatar('egg', 84, 'smug')}</div>")
            if i == len(msgs) - 1 else
            (f"<div style='align-self:flex-start;display:flex;gap:16px;align-items:flex-end;max-width:88%'>{avatar(x.get('de') or 'Parce', 76, ('shock', 'laugh', 'neutral', 'wink')[i % 4])}"
             f"<div style='background:#1b1813;border:2px solid #2a261f;border-radius:30px 30px 30px 6px;padding:22px 30px'>"
             f"<div style='font-size:24px;font-weight:800;color:{('#00e5ff', '#ff8a3d', '#a78bfa', '#00f0a0')[i % 4]}'>{esc(x.get('de') or 'Parce')}</div>"
             f"<div style='font-size:{int(w * .04)}px;line-height:1.25'>{esc(x.get('texto') or '')}</div></div></div>")
            for i, x in enumerate(msgs))
        body = (f"<div style='margin:auto 0;display:flex;flex-direction:column;gap:18px'>"
                f"<div style='text-align:center;font-size:30px;font-weight:800;color:#cfc6b2;margin-bottom:10px'>{esc(strip_emoji(m.get('grupo') or 'El parche'))}</div>{bubbles}</div>")
    elif fmt == "duelo":
        side = lambda who, txt, c, e: (f"<div style='flex:1;border:2px solid {c}66;background:{c}12;border-radius:34px;padding:34px 30px;text-align:center'>"
                                       f"<div style='display:flex;justify-content:center'>{e}</div><div class='anton' style='font-size:{int(w * .05)}px;color:{c};margin-top:18px'>{esc(who)}</div>"
                                       f"<div style='font-size:{int(w * .038)}px;font-weight:700;line-height:1.25;margin-top:18px'>{esc(txt)}</div></div>")
        body = (f"<div style='margin:auto 0;display:flex;gap:22px;align-items:stretch'>{side(m.get('izquierda') or 'Tu amigo', m.get('izq_texto') or '', '#9a9384', avatar(m.get('izquierda') or 'Tu amigo', int(w * .2), 'shock'))}"
                f"<div class='anton' style='align-self:center;font-size:70px;color:#d4af37'>VS</div>"
                f"{side(m.get('derecha') or 'Vos con datos', m.get('der_texto') or '', '#d4af37', avatar('egg', int(w * .2), 'smug'))}</div>")
    elif fmt == "impopular":
        body = (f"<div style='margin:auto 0'><div class='chip' style='border:2px solid #ff4d6d;color:#ff4d6d'>Opinión impopular</div>"
                f"<div class='anton' style='font-size:{int(w * .08)}px;line-height:1.05;margin-top:34px'>{esc(m.get('opinion') or '')}</div>"
                f"<div style='margin-top:40px;display:flex;gap:16px;align-items:center;font-size:{int(w * .042)}px;color:#cfc6b2'>"
                f"<span style='display:inline-block;width:10px;height:{int(w * .06)}px;background:#d4af37'></span>{esc(m.get('dato') or '')}</div>"
                f"<div style='margin-top:34px;font-size:30px;color:#d4af37;font-weight:800'>¿De acuerdo o te dolió?</div></div>")
    elif fmt == "reto":
        qs = "".join(f"<div style='background:#0e0c09;border:2px solid #2a261f;border-radius:26px;padding:22px 28px;margin-top:18px;"
                     f"font-size:{int(w * .04)}px;font-weight:700'><span style='color:#d4af37'>{i + 1}.</span> {esc(q)}</div>"
                     for i, q in enumerate((m.get("opciones") or [])[:3]))
        body = (f"<div style='margin:auto 0'><div class='chip' style='border:2px solid #00f0a0;color:#00f0a0'>Reto</div>"
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
        body = f"<div style='margin:auto 0'>{row('NO', m.get('no') or '', '#9a9384')}{row('SÍ', m.get('si') or '', '#f3ecdc')}</div>"
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
        return [("NO", m.get("no") or ""), ("SÍ", m.get("si") or "")]
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


# ------------------------------------------------------------------ stories (1080×1920): teaser of the new post
def video_frame(video: str, at: float = 1.6) -> str | None:
    """One still from a reel (for the story teaser)."""
    import imageio_ffmpeg
    out = os.path.splitext(video)[0] + "_frame.jpg"
    r = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-ss", str(at), "-i", video, "-frames:v", "1", "-q:v", "3", out],
                       capture_output=True)
    return out if r.returncode == 0 and os.path.exists(out) else None


def story(thumb: str | None, headline: str, kicker: str, is_video: bool, w: int = 1080, h: int = 1920) -> str:
    """The post, tilted like a printed page, under 'Nuevo en el feed'. Meant to send story viewers to the post."""
    label = "Nuevo reel" if is_video else "Nuevo en el feed"
    card_h = int(w * .62 * (16 / 9 if is_video else 1.25))
    card = (f"<div style='margin:46px auto 0;width:{int(w * .62)}px;height:{card_h}px;border-radius:26px;overflow:hidden;"
            f"transform:rotate(-3deg);box-shadow:0 40px 90px rgba(0,0,0,.75),0 0 0 3px rgba(212,175,55,.55);"
            f"background:#111 url({_data_uri(thumb, 1200)}) center/cover no-repeat;position:relative'>"
            + ("<div style='position:absolute;left:50%;top:50%;width:150px;height:150px;margin:-75px 0 0 -75px;border-radius:50%;"
               "background:rgba(5,4,3,.55);border:3px solid #f3ecdc'><div style='position:absolute;left:58px;top:42px;width:0;height:0;"
               "border-left:52px solid #f3ecdc;border-top:33px solid transparent;border-bottom:33px solid transparent'></div></div>"
               if is_video else "") + "</div>") if thumb and os.path.exists(thumb) else ""
    return base(f"""{top_bar(label)}
      <div style='margin:auto 0;text-align:center'>
        <div class='chip' style='border:2px solid #d4af37;color:#d4af37;font-size:26px'>{esc(strip_emoji(kicker) or label)}</div>
        <div class='anton' style='font-size:{int(w * .088)}px;line-height:1;margin-top:30px'>{esc(strip_emoji(headline))}</div>
        {card}
        <div class='anton' style='margin:70px auto 0;display:inline-block;background:#d4af37;color:#050403;border-radius:99px;
          padding:24px 46px;font-size:{int(w * .046)}px;letter-spacing:.04em'>Míralo en el perfil</div>
      </div>{FOOT}""", w, h)


# ------------------------------------------------------------------ reel frames (1080×1920)
def reel_frame(big: str, small: str = "", color: str = "#f3ecdc", accent: str | None = None, glitch: bool = True,
               badge_names: tuple[str, str] | None = None, top: str = "", kicker: str = "", tilt: int = 8,
               bars: list[tuple[str, float, str]] | None = None, host: str | None = None,
               face: tuple[str, str] | None = None) -> str:
    """One scene. Depth: blurred giant echo of the text behind, 3D tilt, glow and floating light.
    host: mood of EGG's avatar presenting the scene (bottom-left), e.g. shock | smug | wink | laugh."""
    accent = accent or house()
    w, h = 1080, 1920
    glitch = glitch and STYLE.get("ritmo") == "muy_rapido"      # chromatic glitch only on the most frantic days
    big, small, kicker = strip_emoji(big), strip_emoji(small), strip_emoji(kicker)
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
    if face and avatar(face[0], 10, face[1]):      # the character who speaks in this beat, big and centered
        kick += f"<div style='display:flex;justify-content:center;margin-bottom:46px'>{avatar(face[0], 420, face[1])}</div>"
    if host and avatar("egg", 10, host):
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


def _say_pct(p: float) -> str:
    return f"{round(p * 100)} por ciento"


def reel_script(kind: str, rows: list[dict], tx: dict, when_fn, record: dict | None = None) -> list[tuple]:
    """[(html, seconds, effect, narration)] — slower scenes that can be read, each with its voice-over line.
    effect: punch | flash | shake | slide | none. The seconds are a minimum: the voice can make a scene longer."""
    f: list[tuple] = []
    rate = _rate(record)
    hook = strip_emoji(tx.get("reel_hook") or "")
    if kind in ("picks_dia", "reel", "nba") and rows:
        rows = rows[:4]
        intl = kind == "nba"
        f.append((reel_frame(hook or "LOS DATOS DE HOY", strip_emoji(tx.get("reel_sub") or ""), host="shock",
                             kicker=("NBA · esta noche" if intl else f"Top {len(rows)} · ligas grandes")), 2.2, "punch",
                  tx.get("voz_hook") or hook))
        if rate:
            f.append((reel_frame(f"{rate[0]}/{rate[1]}", f"picks de 75%+ acertados ({rate[2]}%), fallos incluidos",
                                 color="#d4af37", kicker="Historial público", glitch=False), 2.4, "slide",
                      f"Nuestro historial es público: {rate[0]} aciertos en {rate[1]} picks de alta probabilidad."))
        for i, r in enumerate(rows):
            acc = ACCENT.get(r["league"], "#d4af37")
            p = float(r["p"])
            when = when_fn(r)
            f.append((reel_frame(f"{r['home']} vs {r['away']}", f"{r['league']} · {when}", accent=acc, glitch=False,
                                 badge_names=(r["home"], r["away"]), top=r["league"], tilt=8, kicker=f"Pick {i + 1} de {len(rows)}"),
                      2.3, "punch", f"{r['home']} contra {r['away']}, {when}."))
            fail = max(2, round(1 / max(1e-6, 1 - p)))
            f.append((reel_frame(f"{round(p * 100)}%", r["label"], color=pcolor(p), accent=acc, top=r["league"],
                                 kicker=r.get("group") or "Probabilidad",
                                 bars=[(r["label"][:28], p, pcolor(p)), ("No pasa", 1 - p, "#5a544a")]), 2.6, "slide",
                      f"{r['label']}: {_say_pct(p)}. Una de cada {fail} veces no pasa."))
        best = max(rows, key=lambda r: float(r["p"]))
        f.append((reel_frame("EL MÁS FUERTE", "de hoy", kicker="Ranking",
                             bars=[(f"{r['home']}–{r['away']}"[:30], float(r["p"]), pcolor(float(r["p"]))) for r in rows]), 2.6, "punch",
                  f"El más fuerte del día: {best['home']} contra {best['away']}, con {_say_pct(float(best['p']))}."))
    elif kind == "resultados" and rows:
        won = sum(r["status"] == "won" for r in rows)
        f.append((reel_frame(hook or "¿CÓMO LE FUE AL MODELO?", "aciertos y fallos, sin filtro", kicker="Resultados"), 2.2, "punch",
                  tx.get("voz_hook") or "Así le fue al modelo. Aciertos y fallos, sin filtro."))
        for r in rows[:5]:
            ok = r["status"] == "won"
            f.append((reel_frame("ACERTÓ" if ok else "FALLÓ", f"{r['label']} · {r['home']} vs {r['away']}",
                                 color="#00f0a0" if ok else "#ff4d6d", kicker=f"{round(float(r['p']) * 100)}%"), 2.0, "slide",
                      f"{r['home']} contra {r['away']}, {r['label']}: {'acertó' if ok else 'falló'}."))
        f.append((reel_frame(f"{won}/{len(rows)}", "picks de 75%+ jugados en las últimas horas", color="#d4af37", kicker="Balance"), 2.2,
                  "punch", f"Balance: {won} de {len(rows)}."))
        if rate:
            f.append((reel_frame(f"{rate[2]}%", f"de acierto histórico ({rate[0]}/{rate[1]})", color="#d4af37", kicker="Historial público"),
                      2.2, "slide", f"Y en el histórico, {rate[2]} por ciento de acierto."))
    elif kind == "meme":
        trend = strip_emoji(str(tx.get("tendencia_usada") or ""))[:40]
        fmt, mm = tx.get("meme_formato") or "", tx.get("meme") or {}
        faces = meme_faces(fmt, mm)
        for i, (big, small) in enumerate(l for l in meme_lines(fmt, mm) if strip_emoji(l[0]) or strip_emoji(l[1])):
            say = " ".join(x for x in (strip_emoji(big), strip_emoji(small)) if x and len(x) > 1)
            f.append((reel_frame(big, small, glitch=i % 2 == 0, kicker=(trend or "Meme EGG") if i == 0 else "",
                                 tilt=6, face=faces[i] if i < len(faces) else None), 2.0 if i else 1.8,
                      ("punch", "slide", "shake", "slide")[i % 4], say))
    else:
        title = strip_emoji(tx.get("edu_title") or tx.get("cover_title") or "DATO")
        f.append((reel_frame(hook or title, "", kicker="Dato"), 2.2, "punch", tx.get("voz_hook") or hook or title))
        for line in [x for x in (tx.get("edu_body") or tx.get("cover_subtitle") or "").split("\n") if x.strip()][:4]:
            f.append((reel_frame(line, "", glitch=False, tilt=4), 2.6, "slide", strip_emoji(line)))
    f.append((reel_frame("ENLACE EN EL PERFIL", "todas las probabilidades, gratis", color="#d4af37", kicker="EGG · Goldglitch Stats",
                         host="wink"), 2.4, "punch", tx.get("voz_cierre") or "Todas las probabilidades, gratis, en el enlace del perfil."))
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


def _voiceover(frames: list[tuple], name: str) -> list:
    """Human-sounding voice-over (goldglitch_voz: Kokoro, open model running on this PC). None per scene if off."""
    try:
        import goldglitch_voz as VZ
        if not VZ.available():
            return [None] * len(frames)
    except Exception:
        return [None] * len(frames)
    items = [(strip_emoji(fr[3] or "").strip(), os.path.join(OUT, f"{name}_voz_{i}.wav")) for i, fr in enumerate(frames)]
    return VZ.say_many(items)


def R_SCALE() -> float:
    from goldglitch_social_render import SCALE
    return SCALE


def reel_video(frames: list[tuple[str, float, str]], name: str) -> str:
    """Scenes with punch-in zooms, wobble, RGB-split glitches and a moving gold light, joined with varied quick
    transitions, over an original beat. 2160×3840 (4K) with REDES_ESCALA=2 (default), 30 fps, H.264 + AAC."""
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    frames = [tuple(fr) + ("",) * (4 - len(fr)) for fr in frames]
    voice = _voiceover(frames, name)            # [(path, seconds) | None] per scene
    imgs = render([f[0] for f in frames], 1080, 1920, f"{name}_frames")
    S = max(1, int(round(R_SCALE())))                      # 2 → 2160×3840 (4K vertical)
    W, H = 1080 * S, 1920 * S
    T = 0.14                                                # transition length
    inputs, parts, durs = [], [], []
    for i, (img, (_, secs, fx, _say)) in enumerate(zip(imgs, frames)):
        pace = {"muy_rapido": 0.9, "elegante": 1.2}.get(STYLE["ritmo"], 1.0)
        need = (voice[i][1] + 0.45) if voice[i] else 0          # the scene lasts at least as long as its line
        nfr = max(10, int((max(secs * pace, need) + T) * 30))
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
    for d, (_, _, fx, _s) in zip(durs, frames):
        starts.append((acc, fx))
        acc += d - T
    audio = beat(os.path.join(OUT, f"{name}_beat.wav"), total + 0.5, cuts=starts)
    out = os.path.join(OUT, f"{name}.mp4")
    a_in, a_parts, mix = ["-i", audio], [], []
    has_voice = any(voice)
    a_parts.append(f"[{len(imgs)}:a]volume={0.16 if has_voice else 1.0}[bg]")
    k = len(imgs) + 1
    for (st, _), v in zip(starts, voice):
        if v:
            a_in += ["-i", v[0]]
            ms = int((st + 0.12) * 1000)
            a_parts.append(f"[{k}:a]aresample=44100,aformat=channel_layouts=stereo,adelay={ms}|{ms},volume=1.5[v{k}]")
            mix.append(f"[v{k}]")
            k += 1
    a_parts.append(f"[bg]{''.join(mix)}amix=inputs={1 + len(mix)}:duration=first:normalize=0[aout]")
    graph = ";".join(parts + chain + a_parts)
    cmd = [ff, "-y", *inputs, *a_in, "-filter_complex", graph, "-map", f"[{last}]", "-map", "[aout]",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-maxrate", "28M", "-bufsize", "56M", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-r", "30", "-movflags", "+faststart", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg: " + r.stderr[-600:])
    return out
