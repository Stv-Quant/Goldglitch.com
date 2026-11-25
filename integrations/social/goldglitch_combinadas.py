"""Combinadas de BetPlay con los picks del modelo: reporte PRIVADO para ti (no se publica y no apuesta nada).

Qué hace:
  1. Trae de la web todos los picks de fútbol con 85 % o más de las próximas 48 h (todos los mercados de cada partido)
     y el historial de cómo le ha ido al modelo en ese rango, por familia de mercado.
  2. Lee las cuotas PÚBLICAS de BetPlay (las mismas que ve cualquiera sin iniciar sesión; BetPlay usa la plataforma
     Kambi). Nunca entra a tu cuenta ni toca tu saldo.
  3. Deja al menos 3 opciones con cuota total mayor a 2: una de 2 o 3 selecciones de UN MISMO partido (en BetPlay:
     'Crea tu apuesta') y dos combinando partidos distintos (máximo 3 selecciones). Si falta de un tipo, completa
     con el otro. Con la probabilidad del modelo y la que ha tenido en la realidad.
Tú revisas el reporte y, si quieres, armas la apuesta en BetPlay. Es información, no una recomendación.

    python goldglitch_combinadas.py                # reporte en reportes\\combinadas_FECHA.html (se abre solo)
Ajustes opcionales en el .env:
    COMB_MIN_P=0.85  COMB_MIN_CUOTA=2.0  COMB_MAX_SEL=3  COMB_OPCIONES=3  COMB_HORAS=48
    BETPLAY_KAMBI=betplay     (código de BetPlay en Kambi; si falla, se detecta solo abriendo betplay.com.co)
"""
from __future__ import annotations

import difflib
import hashlib
import hmac
import html
import itertools
import json
import math
import os
import re
import sys
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
TZ = timezone(timedelta(hours=-5))
CACHE = os.path.join(HERE, "betplay_kambi.json")
OUTDIR = os.path.join(HERE, "reportes")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")
HOSTS = ["eu-offering-api.kambicdn.com", "eu1.offering-api.kambicdn.com", "us1-offering-api.kambicdn.com"]


def load_env() -> None:
    path = os.path.join(HERE, ".env")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def env_f(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name) or default)
    except ValueError:
        return default


# ------------------------------------------------------------------ the model's picks (signed request to the site)
def signed(path: str, body: dict) -> dict:
    url, secret = os.environ.get("GG_INGEST_URL"), os.environ.get("GG_INGEST_SECRET")
    if not url or not secret:
        raise SystemExit("Falta GG_INGEST_URL / GG_INGEST_SECRET en el .env (los mismos que usa SQPC).")
    u = urlsplit(url)
    raw = json.dumps(body, separators=(",", ":"))
    ts = str(int(time.time() * 1000))
    sig = hmac.new(secret.encode(), f"{ts}.{raw}".encode(), hashlib.sha256).hexdigest()
    r = requests.post(f"{u.scheme}://{u.netloc}{path}", data=raw.encode(), timeout=60, headers={
        "content-type": "application/json", "x-gg-timestamp": ts, "x-gg-signature": sig})
    try:
        j = r.json()
    except ValueError:
        raise SystemExit(f"La web respondió {r.status_code} sin datos en {path}. Si acabas de actualizar, la web puede "
                         "tardar unos minutos en publicar el cambio: vuelve a intentar en 5 minutos.")
    if not j.get("ok"):
        raise SystemExit(f"La web respondió {r.status_code}: {j}")
    return j


# ------------------------------------------------------------------ calibration: how ≥85 % picks really did
def family(label: str, group: str | None) -> tuple[str, str]:
    """('Goles de equipo: Menos de 2.5', coarse) — team names out, so history of every club counts together."""
    pre, _, post = label.partition(":")
    pre, post = pre.strip(), post.strip()
    pre = re.sub(r"^(Goles|Tarjetas|Fueras de juego|Córners|Corners|Tiros de esquina) de .+$", r"\1 de equipo", pre)
    if pre == "Doble oportunidad":
        post = (re.search(r"\((1X|X2|12)\)", post) or [None, "?"])[1]
    elif pre in ("Empate no acción", "1X2") or re.match(r"^\d\+ ", pre):
        post = "jugador/equipo"
    fine = f"{pre}: {post}"
    coarse = f"{pre}: {post.split(' de ')[0]}" if " de " in post else fine
    return fine, coarse


def calibration(history: list[dict]) -> dict:
    stats: dict[str, list[float]] = {}
    for h in history:
        for key in family(h["label"], h.get("group")):
            s = stats.setdefault(key, [0, 0, 0.0])
            s[0] += 1
            s[1] += 1 if h.get("won") else 0
            s[2] += float(h["p"])
    return stats


def real_p(pick: dict, stats: dict, k: float = 20) -> tuple[float, int, float | None]:
    """Conservative probability: the lower of the model's and the (shrunk) observed hit rate of that market family."""
    p = float(pick["p"])
    for key in family(pick["label"], pick.get("group")):
        n, w, ps = stats.get(key, (0, 0, 0))
        if n >= 10:
            rate = (w + k * (ps / n)) / (n + k)
            return min(p, rate), n, w / n
    return p, 0, None


# ------------------------------------------------------------------ BetPlay odds (Kambi public offering API)
def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\b(fc|cf|sc|ac|afc|cd|club|futbol|sad|ss|us|rj|sp|mg)\b", " ", s)
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s).split())


def sim(a: str, b: str) -> float:
    a, b = _norm(a), _norm(b)
    if not a or not b:
        return 0.0
    if a == b or a in b or b in a:
        return 1.0
    return difflib.SequenceMatcher(None, a, b).ratio()


class Kambi:
    def __init__(self, log=print):
        self.log = log
        cfg = {}
        try:
            cfg = json.load(open(CACHE, encoding="utf-8"))
        except (OSError, ValueError):
            pass
        self.op = os.environ.get("BETPLAY_KAMBI") or cfg.get("operator") or "betplay"
        self.hosts = [cfg["host"]] + HOSTS if cfg.get("host") else list(HOSTS)
        self.host = None
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": UA, "Origin": "https://betplay.com.co", "Referer": "https://betplay.com.co/",
                               "Accept": "application/json"})

    def _get(self, path: str, **params) -> dict:
        q = {"lang": "es_CO", "market": "CO", "client_id": 2, "channel_id": 1, "ncid": int(time.time() * 1000),
             "useCombined": "true", **params}
        last = None
        for host in ([self.host] if self.host else self.hosts):
            try:
                r = self.s.get(f"https://{host}/offering/v2018/{self.op}/{path}", params=q, timeout=25)
                if r.status_code == 200:
                    self.host = host
                    return r.json()
                last = f"{host}: HTTP {r.status_code}"
            except (requests.RequestException, ValueError) as e:
                last = f"{host}: {e}"
        raise RuntimeError(last or "sin respuesta")

    def discover(self) -> bool:
        """Open betplay.com.co in a throwaway headless browser and read which Kambi host/operator it uses."""
        self.log("  detectando el código de BetPlay en Kambi (abro betplay.com.co sin iniciar sesión)…")
        found: dict = {}
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                br = pw.chromium.launch(headless=True)
                try:
                    pg = br.new_page(user_agent=UA, locale="es-CO")

                    def on_req(req):
                        m = re.search(r"https://([^/]*kambicdn\.com)/offering/v2018/([^/]+)/", req.url)
                        if m and not found:
                            found.update(host=m[1], operator=m[2])
                    pg.on("request", on_req)
                    pg.goto("https://betplay.com.co/apuestas#sports-hub/football", wait_until="domcontentloaded",
                            timeout=60_000)
                    for _ in range(30):
                        if found:
                            break
                        pg.wait_for_timeout(1000)
                finally:
                    br.close()
        except Exception as e:
            self.log(f"  no se pudo abrir BetPlay: {e}")
        if found:
            json.dump(found, open(CACHE, "w", encoding="utf-8"))
            self.op, self.hosts, self.host = found["operator"], [found["host"]] + HOSTS, None
            self.log(f"  BetPlay usa {found['host']} / {found['operator']}")
        return bool(found)

    def events(self) -> list[dict]:
        try:
            j = self._get("listView/football/all/all/all/matches.json")
        except RuntimeError as e:
            self.log(f"  cuotas: {e}")
            if not self.discover():
                raise SystemExit("No pude leer las cuotas públicas de BetPlay. Revisa tu internet y vuelve a intentar.")
            j = self._get("listView/football/all/all/all/matches.json")
        out = []
        for e in j.get("events") or []:
            ev = e.get("event") or {}
            if ev.get("state", "NOT_STARTED") == "NOT_STARTED" and ev.get("homeName"):
                out.append(ev)
        return out

    def offers(self, event_id) -> list[dict]:
        return self._get(f"betoffer/event/{event_id}.json").get("betOffers") or []


def match_event(pick: dict, events: list[dict]) -> dict | None:
    ko = float(pick["kickoffAt"]) / 1000
    best, score = None, 0.0
    for ev in events:
        try:
            start = datetime.fromisoformat(str(ev["start"]).replace("Z", "+00:00")).timestamp()
        except (KeyError, ValueError):
            continue
        if abs(start - ko) > 3 * 3600:
            continue
        a, b = sim(pick["home"], ev["homeName"]), sim(pick["away"], ev["awayName"])
        if min(a, b) >= 0.6 and max(a, b) >= 0.75 and a + b > score:
            best, score = ev, a + b
    return best


BAD = re.compile(r"\d+:\d+|half|1st|2nd|first|second|period|interval|minute|exact|odd|even|handicap|asian|race|player|both|"
                 r"&| and |3-way|three|win to nil|clean|margin|method|first to|last|next|scorer|range", re.I)


def find_odds(pick: dict, ev: dict, offers: list[dict]) -> tuple[float, str] | None:
    """Decimal odds of the BetPlay outcome that is exactly this pick, or None."""
    label = pick["label"]
    pre, _, post = label.partition(":")
    pre, post = pre.strip(), post.strip()
    side = None
    m = re.match(r"^(Goles|Tarjetas|Fueras de juego|Córners|Tiros de esquina) (de (.+)|totales|1er tiempo)$|^Total de goles$", pre)
    ou = re.match(r"^(Más|Menos) de ([\d.]+)$", post)
    if (m or pre == "Total de goles") and ou:
        metric = "goal" if pre.startswith(("Goles", "Total de goles")) else "card" if pre.startswith("Tarjetas") else \
            "offside" if pre.startswith("Fueras") else "corner"
        half = "1er tiempo" in pre
        if m and m.group(3):
            team = m.group(3)
            side = "home" if sim(team, pick["home"]) >= sim(team, pick["away"]) else "away"
        want_type, line = ("OT_OVER" if ou[1] == "Más" else "OT_UNDER"), round(float(ou[2]) * 1000)
        for bo in offers:
            lab = str((bo.get("criterion") or {}).get("englishLabel") or (bo.get("criterion") or {}).get("label") or "")
            low = lab.lower()
            if metric not in low and not (metric == "card" and "booking" in low):
                continue
            if half != bool(re.search(r"1st half|first half", low)):
                continue
            rest = re.sub(r"1st half|first half", "", low)
            if BAD.search(rest):
                continue
            nl, nh, na = _norm(lab), _norm(ev["homeName"]), _norm(ev["awayName"])
            names = [n for n in (nh, na, _norm(pick["home"]), _norm(pick["away"])) if n]
            is_team = any(x in low for x in (" by ", "home team", "away team")) or any(n in nl for n in names) or \
                bool(re.search(r" - [a-z]", rest))
            if side is None and is_team:
                continue
            if side is not None:
                if not is_team:
                    continue
                who = lab.split(" by ", 1)[1] if " by " in lab else lab.rsplit(" - ", 1)[-1]
                if "home team" in low or "away team" in low:
                    offer_side = "home" if "home team" in low else "away"
                else:
                    sh = max(sim(who, ev["homeName"]), sim(who, pick["home"]))
                    sa = max(sim(who, ev["awayName"]), sim(who, pick["away"]))
                    offer_side = "home" if sh >= sa else "away"
                if offer_side != side:
                    continue
            for o in bo.get("outcomes") or []:
                if o.get("type") == want_type and int(o.get("line") or -1) == line and o.get("status", "OPEN") == "OPEN" \
                        and o.get("odds"):
                    return o["odds"] / 1000, lab
        return None
    if pre == "Doble oportunidad":
        t = {"1X": "OT_ONE_OR_CROSS", "X2": "OT_CROSS_OR_TWO", "12": "OT_ONE_OR_TWO"}.get(
            (re.search(r"\((1X|X2|12)\)", post) or [None, ""])[1])
        crit = lambda low: "double chance" in low and not BAD.search(low)
    elif pre in ("Empate no acción", "1X2"):
        team = re.sub(r"^Gana\s+", "", post)
        if pre == "1X2" and post.lower().startswith("empate"):
            t = "OT_CROSS"
        else:
            t = "OT_ONE" if sim(team, pick["home"]) >= sim(team, pick["away"]) else "OT_TWO"
        crit = (lambda low: "draw no bet" in low and not BAD.search(low)) if pre == "Empate no acción" else \
               (lambda low: low in ("full time", "match", "1x2", "match odds", "fulltime result", "full time result"))
    else:
        return None                      # player props and anything else: not matched automatically
    for bo in offers:
        lab = str((bo.get("criterion") or {}).get("englishLabel") or (bo.get("criterion") or {}).get("label") or "")
        if crit(lab.lower()):
            for o in bo.get("outcomes") or []:
                if o.get("type") == t and o.get("status", "OPEN") == "OPEN" and o.get("odds"):
                    return o["odds"] / 1000, lab
    return None


# ------------------------------------------------------------------ combinations
def _ou(label: str) -> tuple[str, str, float] | None:
    m = re.match(r"^(.+?):\s*(Más|Menos) de (\d+(?:\.\d+)?)", label or "")
    return (m[1].strip(), m[2], float(m[3])) if m else None


def same_match_ok(c: tuple) -> bool:
    """Selections of one match that make sense together: no two lines of the same market (redundant or contradictory)
    and no selection that is already implied by another one (team over X implies total over X)."""
    pres = [str(l["label"]).partition(":")[0].strip().lower() for l in c]
    if len(set(pres)) < len(pres):
        return False
    for a in c:
        for b in c:
            if a is b:
                continue
            oa, ob = _ou(a["label"]), _ou(b["label"])
            if oa and ob and oa[1] == ob[1] == "Más" and oa[0].lower().startswith("total de goles") \
                    and ob[0].lower().startswith("goles de") and ob[2] >= oa[2]:
                return False                                 # team scores > X  ⇒  match has > X goals
            if str(a["label"]).startswith("1X2") and str(b["label"]).startswith("Doble oportunidad"):
                return False                                 # a win already covers "win or draw"
    return True


def _pick(out: list[dict], want: int) -> list[dict]:
    chosen, uses = [], {}
    for x in out:                                         # variety: one selection appears in at most 2 options
        if all(uses.get(id(l), 0) < 2 for l in x["legs"]):
            chosen.append(x)
            for l in x["legs"]:
                uses[id(l)] = uses.get(id(l), 0) + 1
        if len(chosen) >= want:
            break
    return chosen


def combos_same(legs: list[dict], min_odds: float, max_sel: int, want: int) -> list[dict]:
    """First choice: 2 or 3 selections of the SAME match (BetPlay 'Crea tu apuesta'), total odds above min_odds."""
    by_ev: dict = {}
    for l in legs:
        by_ev.setdefault(l["event"], []).append(l)
    out = []
    for ev_legs in by_ev.values():
        for k in range(2, min(max_sel, len(ev_legs)) + 1):
            for c in itertools.combinations(ev_legs, k):
                if not same_match_ok(c):
                    continue
                odds = math.prod(l["odds"] for l in c)
                if odds <= min_odds:
                    continue
                pm, pr = math.prod(l["p"] for l in c), math.prod(l["p_real"] for l in c)
                out.append({"legs": c, "odds": odds, "p_model": pm, "p_real": pr, "ev": pr * odds - 1, "same": True})
    out.sort(key=lambda x: (-x["p_real"], -x["ev"]))       # same match: the most likely first
    return _pick(out, want)


def combos(legs: list[dict], min_odds: float, max_sel: int, want: int) -> list[dict]:
    """Fallback: 1 to max_sel selections of DIFFERENT matches."""
    out = []
    for k in range(1, max_sel + 1):
        for c in itertools.combinations(legs, k):
            if len({l["event"] for l in c}) < k:
                continue
            odds = math.prod(l["odds"] for l in c)
            if odds <= min_odds:
                continue
            pm, pr = math.prod(l["p"] for l in c), math.prod(l["p_real"] for l in c)
            out.append({"legs": c, "odds": odds, "p_model": pm, "p_real": pr, "ev": pr * odds - 1, "same": False})
    out.sort(key=lambda x: (-x["ev"], -x["p_real"]))
    chosen = _pick(out, want)
    for x in out:                                         # not enough variety: fill with the next best ones
        if len(chosen) >= want:
            break
        if x not in chosen:
            chosen.append(x)
    return chosen


# ------------------------------------------------------------------ report
def when(ms: float) -> str:
    d = datetime.fromtimestamp(float(ms) / 1000, TZ)
    days = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
    return f"{days[d.weekday()]} {d.day} · {d.strftime('%H:%M')}"


def report(opts: list[dict], info: dict) -> str:
    os.makedirs(OUTDIR, exist_ok=True)
    e = html.escape
    cards = []
    for i, x in enumerate(opts, 1):
        rows = "".join(
            f"<tr><td>{e(l['home'])} vs {e(l['away'])}<div class=s>{e(l['league'])} · {when(l['kickoffAt'])}</div></td>"
            f"<td>{e(l['label'])}<div class=s>BetPlay: {e(l['market'])}</div></td><td class=n>{l['odds']:.2f}</td>"
            f"<td class=n>{l['p'] * 100:.0f}%</td><td class=n>{l['p_real'] * 100:.0f}%"
            f"<div class=s>{'historial ' + str(l['hist_n']) if l['hist_n'] else 'sin historial'}</div></td></tr>"
            for l in x["legs"])
        tone = "pos" if x["ev"] > 0 else "neg"
        tag = (f"mismo partido · {len(x['legs'])} selecciones" if x.get("same")
               else f"{len(x['legs'])} {'selecciones' if len(x['legs']) > 1 else 'selección'} de partidos distintos")
        same_note = ("<div class=s>Mismo partido: ármala en BetPlay con 'Crea tu apuesta'. BetPlay calcula su propia cuota "
                     "para selecciones del mismo partido (suele ser menor que la multiplicación de abajo), y la probabilidad "
                     "conjunta no es exactamente el producto porque los eventos están relacionados.</div>") if x.get("same") else ""
        cards.append(f"""<section><h2>Opción {i} <span>{tag}</span></h2>{same_note}
<table><tr><th>Partido</th><th>Mercado</th><th class=n>Cuota</th><th class=n>Modelo</th><th class=n>Real</th></tr>{rows}</table>
<div class=tot><b>Cuota total {'estimada ' if x.get('same') else ''}{x['odds']:.2f}</b> · probabilidad modelo {x['p_model'] * 100:.0f}% · ajustada a la realidad
{x['p_real'] * 100:.0f}% · implícita de la cuota {100 / x['odds']:.0f}% ·
<b class={tone}>valor esperado {x['ev'] * 100:+.0f}%</b></div></section>""")
    body = "".join(cards)
    if not body:
        bt = math.prod(l["odds"] for l in info.get("best") or []) if info.get("best") else 0
        body = (f"<p>No encontré combinaciones de {info['max_sel']} selecciones o menos con cuota total mayor a "
                f"{info['min_odds']:.2f}. Lo máximo posible hoy con estos picks es <b>{bt:.2f}</b>.</p>")
    if info.get("top"):
        body += ("<section><h2>Picks con cuota en BetPlay <span>las cuotas más altas</span></h2><table><tr><th>Partido</th>"
                 "<th>Mercado</th><th class=n>Cuota</th><th class=n>Modelo</th><th class=n>Real</th></tr>" + "".join(
                     f"<tr><td>{e(l['home'])} vs {e(l['away'])}<div class=s>{e(l['league'])} · {when(l['kickoffAt'])}</div></td>"
                     f"<td>{e(l['label'])}<div class=s>BetPlay: {e(l['market'])}</div></td><td class=n>{l['odds']:.2f}</td>"
                     f"<td class=n>{l['p'] * 100:.0f}%</td><td class=n>{l['p_real'] * 100:.0f}%</td></tr>" for l in info["top"])
                 + "</table></section>")
    stamp = datetime.now(TZ)
    path = os.path.join(OUTDIR, f"combinadas_{stamp.strftime('%Y%m%d_%H%M')}.html")
    open(path, "w", encoding="utf-8").write(f"""<!doctype html><html lang=es><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Combinadas {stamp:%d/%m %H:%M}</title><style>
body{{font:15px/1.45 system-ui,Segoe UI,sans-serif;background:#0b0a08;color:#eee6d4;margin:0;padding:24px;max-width:980px}}
h1{{margin:0 0 4px;font-size:26px}} .s{{color:#9b927f;font-size:12.5px}} section{{background:#16140f;border:1px solid #3a3122;
border-radius:14px;padding:16px 18px;margin:18px 0}} h2{{margin:0 0 10px;font-size:18px;color:#e7c25a}} h2 span{{color:#9b927f;
font-size:13px;font-weight:400;margin-left:8px}} table{{width:100%;border-collapse:collapse}} th,td{{text-align:left;padding:8px 6px;
border-bottom:1px solid #2a251b;vertical-align:top}} th{{color:#9b927f;font-weight:500;font-size:12.5px}} .n{{text-align:right;
white-space:nowrap;font-variant-numeric:tabular-nums}} .tot{{margin-top:10px}} .pos{{color:#7fd48a}} .neg{{color:#e58a7a}}
.note{{color:#b9ad92;font-size:13px;border-left:3px solid #d4af37;padding-left:12px;margin:14px 0}}</style></head><body>
<h1>Combinadas con picks de {info['min_p'] * 100:.0f}% o más</h1>
<div class=s>{stamp:%d/%m/%Y %H:%M} · cuotas públicas de BetPlay · {info['picks']} picks del modelo, {info['matched']} con cuota en
BetPlay · máximo {info['max_sel']} selecciones · cuota total mayor a {info['min_odds']:.2f}</div>
<div class=note>"Real" es la probabilidad ajustada a cómo le ha ido al modelo en ese tipo de mercado (últimos 180 días).
Valor esperado positivo significa que, si esa probabilidad es correcta, la cuota paga más de lo que debería. Las cuotas
cambian: revísalas en BetPlay antes de decidir. Es información estadística, no una recomendación; apuesta solo lo que
puedas perder. +18.</div>
{body}
<div class=note>Sin cuota en BetPlay: {info['unmatched']} picks (partido no encontrado o mercado que BetPlay no ofrece).
Calibración general del modelo en picks de {info['min_p'] * 100:.0f}%+: {info['hit']}.</div></body></html>""")
    return path


# ------------------------------------------------------------------ main
def main() -> int:
    load_env()
    min_p, min_odds = env_f("COMB_MIN_P", 0.85), env_f("COMB_MIN_CUOTA", 2.0)
    max_sel, want, hours = int(env_f("COMB_MAX_SEL", 3)), int(env_f("COMB_OPCIONES", 3)), env_f("COMB_HORAS", 48)
    print(f"Picks de {min_p * 100:.0f}% o más de las próximas {hours:.0f} h…")
    data = signed("/api/social/candidatos", {"min": min_p, "hours": hours})
    picks, stats = data["picks"], calibration(data["history"])
    n_hist = len(data["history"])
    hit = f"{sum(1 for h in data['history'] if h['won']) / n_hist * 100:.0f}% de {n_hist}" if n_hist else "sin historial"
    print(f"  {len(picks)} picks · historial {hit}")
    if not picks:
        print("No hay picks que cumplan el mínimo en ese rango de horas.")
        return 0
    k = Kambi()
    print("Leyendo cuotas públicas de BetPlay…")
    events = k.events()
    print(f"  {len(events)} partidos de fútbol en BetPlay")
    by_match: dict[str, dict | None] = {}
    offers: dict = {}
    legs, unmatched, seen = [], 0, set()
    diag: dict = {"partido_no_encontrado": {}, "mercado_no_encontrado": {}, "mercados_betplay": {}, "sospechosas": []}
    for p in picks:
        if p["matchId"] not in by_match:
            by_match[p["matchId"]] = match_event(p, events)
        ev = by_match[p["matchId"]]
        if not ev:
            unmatched += 1
            ko = float(p["kickoffAt"]) / 1000
            near = [f"{e['homeName']} - {e['awayName']}" for e in events
                    if abs(datetime.fromisoformat(str(e["start"]).replace("Z", "+00:00")).timestamp() - ko) < 3 * 3600][:12]
            diag["partido_no_encontrado"][f"{p['home']} vs {p['away']} ({p['league']}, {when(p['kickoffAt'])})"] = near
            continue
        if ev["id"] not in offers:
            try:
                offers[ev["id"]] = k.offers(ev["id"])
            except RuntimeError as e:
                print(f"  {ev.get('name')}: {e}")
                offers[ev["id"]] = []
            time.sleep(0.25)
        hit_o = find_odds(p, ev, offers[ev["id"]])
        if not hit_o:
            unmatched += 1
            name = f"{ev['homeName']} - {ev['awayName']}"
            diag["mercado_no_encontrado"].setdefault(name, []).append(p["label"])
            diag["mercados_betplay"].setdefault(name, sorted({
                str((b.get("criterion") or {}).get("englishLabel") or (b.get("criterion") or {}).get("label")) + " | " +
                ",".join(sorted({f"{o.get('type')}@{(o.get('line') or 0) / 1000:g}" for o in b.get("outcomes") or []}))[:160]
                for b in offers[ev["id"]]}))
            continue
        pr, hn, _ = real_p(p, stats)
        if hit_o[0] * float(p["p"]) > 1.5 or hit_o[0] > 1.0 / max(0.05, float(p["p"]) - 0.3):
            print(f"  descarto cuota sospechosa: {p['home']} vs {p['away']} · {p['label']} @ {hit_o[0]:.2f} ({hit_o[1]})")
            diag["sospechosas"].append(f"{p['home']} vs {p['away']} · {p['label']} @ {hit_o[0]:.2f} ({hit_o[1]})")
            unmatched += 1
            continue
        key = (ev["id"], hit_o[1], hit_o[0])
        if key in seen:                     # the same BetPlay selection twice (duplicated pick rows)
            continue
        seen.add(key)
        legs.append({**p, "event": ev["id"], "odds": hit_o[0], "market": hit_o[1], "p_real": pr, "hist_n": hn})
    print(f"  {len(legs)} picks con cuota · {sum(1 for v in by_match.values() if v)} de {len(by_match)} partidos encontrados")
    os.makedirs(OUTDIR, exist_ok=True)
    with open(os.path.join(OUTDIR, "diagnostico_combinadas.json"), "w", encoding="utf-8") as f:
        json.dump(diag, f, ensure_ascii=False, indent=1)
    same = combos_same(legs, min_odds, max_sel, want)          # 2-3 selections of one match
    mixed = combos(legs, min_odds, max_sel, want)              # selections of different matches
    opts = same[:1] + mixed[:max(2, want - 1)]                 # at least: 1 of one match + 2 of mixed matches
    for x in same[1:] + mixed[max(2, want - 1):]:              # short on one kind: fill with the other
        if len(opts) >= want:
            break
        opts.append(x)
    print(f"  {sum(1 for x in opts if x.get('same'))} de un mismo partido · {sum(1 for x in opts if not x.get('same'))} de partidos distintos")
    top = sorted(legs, key=lambda l: -l["odds"])
    best, used = [], set()
    for l in top:                                   # the highest total possible with max_sel matches
        if l["event"] not in used and len(best) < max_sel:
            best.append(l)
            used.add(l["event"])
    path = report(opts, {"top": top[:12], "best": best, "min_p": min_p, "picks": len(picks), "matched": len(legs), "max_sel": max_sel,
                         "min_odds": min_odds, "unmatched": unmatched, "hit": hit})
    for i, x in enumerate(opts, 1):
        print(f"\nOpción {i} ({'mismo partido' if x.get('same') else 'partidos distintos'}): cuota {x['odds']:.2f} · real {x['p_real'] * 100:.0f}% · VE {x['ev'] * 100:+.0f}%")
        for l in x["legs"]:
            print(f"   {l['home']} vs {l['away']} ({when(l['kickoffAt'])}) — {l['label']} @ {l['odds']:.2f}")
    if len(opts) < want:
        print(f"\nSolo encontré {len(opts)} opciones que cumplen todo (con picks de {min_p * 100:.0f}%+ las cuotas suelen ser bajas).")
    print(f"\nReporte: {path}")
    if os.name == "nt":
        os.startfile(path)  # type: ignore[attr-defined]
    return 0


if __name__ == "__main__":
    sys.exit(main())
