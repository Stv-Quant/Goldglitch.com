"""Agentes de redes de Goldglitch: Instagram, Facebook y TikTok en automático.

Uso (desde D:\\SoccerPrediction):
    python goldglitch_social.py tick            # lo corre la tarea programada cada 15 min: planea, publica, responde
    python goldglitch_social.py tick --dry-run  # todo menos publicar/responder (revisa redes_salida/ y redes.log)
    python goldglitch_social.py prueba          # arma piezas de ejemplo sin IA ni redes (para ver el diseño)
    python goldglitch_social.py conectar        # modo navegador: abre Chrome para iniciar sesión en las 3 redes (una vez)
    python goldglitch_social.py ensayo          # modo navegador: arma una pieza y recorre cada red SIN el clic final
    python goldglitch_social.py tiktok-login    # (solo modo API) conecta la cuenta de TikTok
    python goldglitch_social.py informe         # informe semanal ya (normalmente: lunes)

Dos formas de llegar a las redes:
    - Modo navegador (por defecto si no hay tokens de API): los agentes usan un Chrome con sesión iniciada por ti
      (`conectar`). No necesita Meta Developers, TikTok for Developers ni suscripciones.
    - Modo API: con los tokens de abajo (Graph API de Meta y Content Posting API de TikTok).

Configuración (líneas en el .env de esta carpeta, junto a GG_INGEST_URL y GG_INGEST_SECRET):
    ANTHROPIC_API_KEY=...       clave de la API de Anthropic (agentes Haiku 5.5: textos y agentes que miran la pantalla)
    REDES_AGENTE_PANTALLA=0     usa pasos automáticos en vez del agente que mira la pantalla
    REDES_MODO=navegador        fuerza el modo navegador aunque haya tokens (o =api para lo contrario)
    META_PAGE_ID=...            id de la página de Facebook
    META_PAGE_TOKEN=...         token de larga duración de la página
    IG_USER_ID=...              id de la cuenta profesional de Instagram vinculada
    TIKTOK_CLIENT_KEY=...       app de TikTok for Developers
    TIKTOK_CLIENT_SECRET=...
    TIKTOK_PRIVACY=PUBLIC_TO_EVERYONE   cuando TikTok apruebe la auditoría (antes queda SELF_ONLY = privado)
    REDES_PAUSA=1               detiene todo sin desinstalar nada
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from goldglitch_social_agents import Agents  # noqa: E402
import goldglitch_social_render as R  # noqa: E402
from goldglitch_social_platforms import Meta, PlatformError, TikTok  # noqa: E402
import goldglitch_social_browser as B  # noqa: E402
import goldglitch_growth as G  # noqa: E402
import goldglitch_social_render2 as V  # noqa: E402
import goldglitch_trends as T  # noqa: E402

TZ = timezone(timedelta(hours=-5))  # Colombia
STATE = os.path.join(HERE, "redes_estado.json")
MEMORY = os.path.join(HERE, "redes_memoria.md")
LOG = os.path.join(HERE, "redes.log")
TIKTOK_REDIRECT = "https://easygoldglitch.com/tiktok/callback"
COMMUNITY_EVERY_MIN = 30
MAX_TRIES = 3


# ------------------------------------------------------------------ basics
def load_env() -> None:
    path = os.path.join(HERE, ".env")
    try:
        with open(path, encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except OSError:
        pass


def log(msg: str) -> None:
    line = f"[{datetime.now(TZ):%Y-%m-%d %H:%M}] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:      # Windows console (cp1252) can't print some symbols the agents quote (☰, emoji)
        enc = getattr(sys.stdout, "encoding", None) or "ascii"
        print(line.encode(enc, "replace").decode(enc, "replace"))
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_json(path: str, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save_json(path: str, data) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def site() -> tuple[str, str]:
    url, secret = os.environ.get("GG_INGEST_URL"), os.environ.get("GG_INGEST_SECRET")
    if not url or not secret:
        raise SystemExit("Falta GG_INGEST_URL / GG_INGEST_SECRET en el .env (los mismos que usa SQPC).")
    u = urlsplit(url)
    return f"{u.scheme}://{u.netloc}", secret


def signed(path: str, body: dict, timeout: float = 60) -> dict:
    origin, secret = site()
    raw = json.dumps(body, separators=(",", ":"))
    ts = str(int(time.time() * 1000))
    sig = hmac.new(secret.encode(), f"{ts}.{raw}".encode(), hashlib.sha256).hexdigest()
    r = requests.post(origin + path, data=raw.encode(), timeout=timeout, headers={
        "content-type": "application/json", "x-gg-timestamp": ts, "x-gg-signature": sig, "user-agent": "goldglitch-social/1.0"})
    j = r.json()
    if not j.get("ok"):
        raise RuntimeError(f"La web respondió {r.status_code}: {j}")
    return j


def upload(path: str) -> str:
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return signed("/api/social/media", {"ct": "image/jpeg", "data": data})["url"]


def when(ms: int, now: datetime) -> str:
    d = datetime.fromtimestamp(ms / 1000, TZ)
    day = "Hoy" if d.date() == now.date() else "Mañana" if d.date() == (now + timedelta(days=1)).date() else d.strftime("%d/%m")
    return f"{day} {d:%H:%M}"


def same_day(r: dict, now: datetime) -> bool:
    """Only matches played on today's date in Colombia (picks of the 24th on the 24th, never tomorrow's)."""
    try:
        return datetime.fromtimestamp(float(r.get("kickoffAt") or 0) / 1000, TZ).date() == now.date()
    except (TypeError, ValueError, OSError):
        return False


# ------------------------------------------------------------------ pieces
SHOWN_HOURS = 24          # a match already shown in picks (feed or reel) is not shown again for 24 h
IG_HASHTAGS = int(os.environ.get("REDES_IG_HASHTAGS", "30") or 30)   # Instagram drops the whole text above 30


def match_key(r: dict) -> str:
    return f"{r.get('home', '')}|{r.get('away', '')}".lower()


def shown_recent(st: dict) -> set[str]:
    cut = time.time() - SHOWN_HOURS * 3600
    return {k for k, t in (st.get("shown") or {}).items() if t >= cut}


def remember_shown(st: dict, piece: dict) -> None:
    keep = {k: t for k, t in (st.get("shown") or {}).items() if t >= time.time() - 72 * 3600}
    for k in piece.get("shown") or []:
        keep[k] = time.time()
    st["shown"] = keep
    # the exact picks shown, so the results video reports on THOSE picks (same match, same market)
    rows = [r for r in st.get("shown_picks") or [] if r.get("ts", 0) >= time.time() - 72 * 3600]
    have = {(r.get("matchId"), r.get("label")) for r in rows}
    for r in piece.get("shown_rows") or []:
        if (r.get("matchId"), r.get("label")) not in have:
            rows.append({**r, "ts": time.time()})
    st["shown_picks"] = rows[-60:]


def shown_results(st: dict | None, results: list[dict]) -> list[dict] | None:
    """Results of the picks we showed in the last 36 h (None if nothing was shown, [] if none has finished yet)."""
    shown = [r for r in (st or {}).get("shown_picks") or [] if r.get("ts", 0) >= time.time() - 36 * 3600]
    if not shown:
        return None
    want = {(str(r.get("matchId")), (r.get("label") or "").lower()) for r in shown}
    keys = {match_key(r) + "|" + (r.get("label") or "").lower() for r in shown}
    return [r for r in results if (str(r.get("matchId")), (r.get("label") or "").lower()) in want
            or match_key(r) + "|" + (r.get("label") or "").lower() in keys]


SPORT_SCENES = {   # luxury, but about the sport — rotated so the feed is not always the same person with champagne
    "futbol": [
        "a football resting on wet grass in the centre circle of a huge empty stadium at night, golden floodlights, light rain, shallow depth of field",
        "silhouette of a striker striking a football mid-air, golden sparks around the ball, night stadium haze, dramatic backlight",
        "goalkeeper diving full stretch in the rain, golden rim light, water droplets frozen in the air, blurred floodlights",
        "black marble locker room with gold-trimmed lockers, a pair of football boots and a ball on a leather bench, warm spotlight",
        "players' tunnel leading to a bright pitch, golden light at the end, smoke, cinematic symmetry, no signage",
        "aerial drone view of a football stadium glowing at blue hour, city lights around, golden floodlight beams",
        "close-up of football boots on the white line of a pitch, morning dew, golden sunrise backlight",
        "corner flag fluttering at sunset in a premium stadium, golden hour, crowd softly blurred",
        "luxury VIP box overlooking a packed night stadium, leather seats and warm lamps, no people in focus",
        "supporters' silhouettes with golden flares and smoke in a stadium stand at night, epic atmosphere",
        "a golden-trimmed football on a black velvet pedestal under a single spotlight, dark museum ambience",
    ],
    "basket": [
        "basketball swishing through the net in a dark arena, golden spotlight, sparks of light, slow motion",
        "silhouette of a player dunking against bright arena lights, golden haze, dramatic low angle",
        "empty courtside leather seats beside polished hardwood, golden reflections, arena lights above",
        "basketball sneakers on glossy hardwood with a golden rim light, shallow depth of field",
        "a basketball on the free-throw line of an empty premium arena, single golden spotlight",
    ],
    "persona": [
        "a stylish young Colombian woman with long dark wavy hair with golden highlights and gold hoop earrings, cheering in a "
        "premium stadium seat at night, golden floodlights",
        "a well-dressed young man celebrating a goal with friends in a luxury rooftop sports lounge at night, golden light",
    ],
}


def scene_theme(post: dict, tag: str) -> str:
    """The theme of the background art for this piece: football or basketball scenes; people only once in a while."""
    h = int(hashlib.md5(tag.encode()).hexdigest()[:8], 16)
    if post["type"] == "nba":
        pool = SPORT_SCENES["basket"]
    elif post["type"] == "meme" or h % 5 == 0:
        pool = SPORT_SCENES["persona"] + SPORT_SCENES["futbol"][:3]
    else:
        pool = SPORT_SCENES["futbol"] + (SPORT_SCENES["basket"][:2] if h % 3 == 0 else [])
    return pool[(h // 7) % len(pool)]


ART_LIB = os.path.join(HERE, "redes_arte")
ART_INDEX = os.path.join(ART_LIB, "indice.json")


def _late(post: dict) -> bool:
    try:
        now = datetime.now(TZ)
        return (now.hour * 60 + now.minute) - G._mins(post.get("time") or "") > 20
    except Exception:
        return False


def _feed_from_reel(reel: str, out: str) -> str:
    """4:5 feed art cut from the 9:16 painting (one painting per piece instead of two: half the time)."""
    from PIL import Image
    im = Image.open(reel)
    w, h = im.size
    fh = int(w * 1.25)
    top = max(0, int((h - fh) * 0.42))
    im.crop((0, top, w, top + fh)).save(out, quality=92)
    return out


def illustrations(post: dict, tx: dict, tag: str) -> tuple[str | None, str | None]:
    """AI illustrations painted on this PC (feed 4:5 and reel 9:16, 4K) for the piece; (None, None) if not installed.
    Speed: one painting per piece (the feed is cut from it), and a library of past paintings by theme that is reused
    when the day is running late or the theme already has several (REDES_ARTE_REUSO=0.6 by default)."""
    import random
    import shutil
    try:
        import goldglitch_ilustrador as IL
        if not IL.available():
            return None, None
        theme = scene_theme(post, tag)
        key = hashlib.md5(f"{post['type'] == 'nba'}|{theme}".encode()).hexdigest()[:10]
        idx = load_json(ART_INDEX, {})
        lib = [e for e in idx.get(key, []) if os.path.exists(e.get("reel", "")) and os.path.exists(e.get("feed", ""))]
        reuse = float(os.environ.get("REDES_ARTE_REUSO", "0.6"))
        fresh = [e for e in lib if time.time() - float(e.get("used") or 0) > 36 * 3600]
        if lib and (_late(post) or (len(lib) >= 2 and random.random() < reuse)):
            e = min(fresh or lib, key=lambda e: float(e.get("used") or 0))
            e["used"] = time.time()
            idx[key] = lib
            save_json(ART_INDEX, idx)
            log("  [Valeria] Ilustrador: uso un arte de la biblioteca (mismo tema, sin esperar)")
            return e["feed"], e["reel"]
        base = str(tx.get("ilustracion") or "").strip() or theme
        log("  [Valeria] Ilustrador: pintando el arte de la pieza…")
        reel = IL.scene(post["type"], base, True, f"{tag}_reel")
        if not reel:
            return None, None
        if os.environ.get("REDES_ARTE_DOS") == "1":
            feed = IL.scene(post["type"], base, False, f"{tag}_feed") or _feed_from_reel(reel, f"{os.path.splitext(reel)[0]}_feed.jpg")
        else:
            feed = _feed_from_reel(reel, f"{os.path.splitext(reel)[0]}_feed.jpg")
        os.makedirs(ART_LIB, exist_ok=True)
        keep = {}
        for kind, path in (("reel", reel), ("feed", feed)):
            dst = os.path.join(ART_LIB, f"{key}_{tag[-20:]}_{kind}{os.path.splitext(path)[1]}")
            shutil.copy2(path, dst)
            keep[kind] = dst
        idx.setdefault(key, []).append({**keep, "used": time.time(), "tema": theme[:80]})
        idx[key] = idx[key][-8:]
        save_json(ART_INDEX, idx)
        return feed, reel
    except Exception as e:
        log(f"  Ilustrador no disponible: {e}")
        return None, None


STORY_KICKER = {"picks_dia": "Picks del día", "resultados": "Así le fue al modelo", "meme": "Meme del día",
                "sabias_que": "¿Sabías que…?", "noticia": "Noticia del día", "nba": "NBA", "pregunta": "Tu turno",
                "mito_dato": "Mito vs dato", "educativo": "Aprende a leer datos", "reel": "Nuevo reel"}


def story_of(post: dict, piece: dict, tag: str) -> str | None:
    """Instagram/Facebook story that announces the new post (1080×1920). Off with REDES_HISTORIAS=0."""
    if os.environ.get("REDES_HISTORIAS", "1") == "0" or not ({"instagram", "facebook"} & set(post.get("redes") or ["instagram", "facebook"])):
        return None
    try:
        tx, is_video = piece["texts"], bool(piece.get("reel")) or not piece.get("feed")
        thumb = V.video_frame(piece["video"]) if is_video and piece.get("video") else (piece.get("feed") or [None])[0]
        head = str(tx.get("story_title") or tx.get("cover_title") or tx.get("reel_hook") or "Nuevo dato")[:70]
        return R.render([V.story(thumb, head, STORY_KICKER.get(post["type"], ""), is_video)], 1080, 1920, f"{tag}_historia")[0]
    except Exception as e:
        log(f"  historia: no se pudo armar ({e})")
        return None


def build(post: dict, facts: dict, ag: Agents, now: datetime, tag: str, shown: set[str] | None = None,
          st: dict | None = None) -> dict:
    piece = _build(post, facts, ag, now, tag, shown, st)
    piece["story"] = story_of(post, piece, tag)
    return piece


def _build(post: dict, facts: dict, ag: Agents, now: datetime, tag: str, shown: set[str] | None = None,
           st: dict | None = None) -> dict:
    """Texts + images + video for one planned post. Returns {feed:[jpg], story:None, video:mp4, reel:bool, texts}.

    Picks come only from top first-division leagues of LATAM and Europe (and their continental cups)."""
    from goldglitch_lenguaje import nice_label
    facts = {k: ([{**r, "label": nice_label(r["label"])} if isinstance(r, dict) and r.get("label") else r for r in v]
                 if isinstance(v, list) else v) for k, v in (facts or {}).items()}     # statistics wording, not betting
    V.set_safe("tiktok" in (post.get("redes") or ["tiktok"]))
    t = post["type"]
    V.set_style(G.art_for(now.strftime("%Y-%m-%d")))       # Martina's art direction for today
    focus = (post.get("liga") or "").strip()
    seo = G.seo_for(now.strftime("%Y-%m-%d"))
    post = {**post, "seo": seo}
    soon = time.time() * 1000 + 20 * 60 * 1000        # never a match that already started (or starts in < 20 min)
    fresh = [r for r in facts.get("upcoming") or [] if match_key(r) not in (shown or set())
             and float(r.get("kickoffAt") or 0) > soon and same_day(r, now)]
    if post.get("obligatorio") == "manana" or (t == "picks_dia" and not focus):
        picks = V.famous_picks(fresh, 4)          # fewer than 5, famous teams of Europe, South America and Liga BetPlay
    else:
        picks = V.top_picks(fresh, 4, focus) or V.top_picks(fresh, 4)
    strong = [r for r in picks if float(r.get("p") or 0) >= ANCHOR_P]
    picks = strong or picks                       # videos show 85%+ picks whenever there are any
    anchor = anchor_pick(facts, now, soon, shown, tag)
    today_res = [r for r in facts.get("results") or [] if same_day(r, now)]      # tonight: only today's matches
    res = sorted([r for r in today_res if V.top_league(r.get("league"))],
                 key=lambda r: (r["status"] != "won", -r["p"])) or sorted(today_res, key=lambda r: (r["status"] != "won", -r["p"]))
    for r in res:
        lg = V.top_league(r.get("league"))
        if lg:
            r["_tag"] = lg[1]
    reel_of = "resultados" if (t == "reel" and (post.get("topic") or "").lower().startswith("result")) else ("picks_dia" if t == "reel" else t)
    if reel_of == "resultados":
        mine = shown_results(st, today_res)
        if mine == []:
            raise SkipPiece("los picks que mostramos todavía no tienen resultado")
        if mine:            # how the engine did with the SAME picks shown earlier (hits and misses)
            res = sorted(mine, key=lambda r: (r["status"] != "won", -r["p"]))
            for r in res:
                lg = V.top_league(r.get("league"))
                if lg:
                    r["_tag"] = lg[1]
        rows = res
        data = {"won": sum(r["status"] == "won" for r in rows), "n": len(rows), "historial": facts["record"],
                "partidos": [f"{r['home']} vs {r['away']}" for r in rows[:6]]}
    elif t == "nba":            # international audience: NBA (and NHL) picks
        intl = [r for r in facts.get("intl") or [] if float(r.get("kickoffAt") or 0) > soon and same_day(r, now)
                and match_key(r) not in (shown or set())]
        rows = [r for r in intl if r.get("sport") == "basketball"][:4] or intl[:4]
        if not rows:
            raise SkipPiece("no quedan partidos de NBA/NHL hoy")
        for r in rows:
            r["_tag"] = "nba" if r.get("sport") == "basketball" else "nhl"
        reel_of = "nba"
        data = {"picks": [{k: r[k] for k in ("league", "home", "away", "label", "p")} | {"cuando": when(r["kickoffAt"], now)} for r in rows],
                "historial": facts["record"], "deporte": "NBA (baloncesto)" if rows[0].get("sport") == "basketball" else "NHL"}
    elif reel_of == "picks_dia":
        rows = picks
        data = {"picks": [{k: r[k] for k in ("league", "home", "away", "label", "p")} | {"cuando": when(r["kickoffAt"], now)} for r in rows],
                "historial": facts["record"]}
    else:
        rows, data = [], {"historial": facts["record"]}
        if t in ("sabias_que", "noticia"):       # real material only: today's headlines and the model's next big matches
            try:
                data["titulares_futbol"] = T.brief(n=6).get("titulares_futbol", [])
            except Exception:
                data["titulares_futbol"] = []
            data["proximos"] = [{k: r[k] for k in ("league", "home", "away", "label", "p")} | {"cuando": when(r["kickoffAt"], now)}
                                for r in V.famous_picks(fresh, 4)]
            if t == "noticia" and not data["titulares_futbol"]:
                raise SkipPiece("no hay titulares reales de fútbol para la noticia")
    if t in ("meme", "reel", "pregunta", "picks_dia"):        # ride what is happening right now
        try:
            data["tendencias_del_momento"] = T.brief(n=6)
        except Exception:
            pass
    if t in ("picks_dia", "resultados") or (t == "reel" and reel_of != "texto"):
        if not rows:
            raise SkipPiece("no quedan partidos de hoy de ligas top sin mostrar (los de mañana se publican mañana)"
                            if reel_of == "picks_dia" else "no hay partidos de ligas top para esta pieza")
    data["ahora"] = now.strftime("%Y-%m-%d %H:%M (hora de Colombia)")
    try:          # real search phrases (YouTube/Google autocomplete) for natural SEO
        seeds = ([f"{r['home']} vs {r['away']}" for r in rows[:2]] + list(dict.fromkeys(f"pronósticos {r['league']}" for r in rows[:3]))
                 + (["nba picks hoy", "pronósticos nba"] if t == "nba" else ["pronósticos fútbol hoy"]))
        data["busquedas_reales"] = T.search_phrases(seeds)
    except Exception:
        pass
    data["tema_ilustracion"] = scene_theme(post, tag)
    modo = piece_mode(post, tag)
    data["modo"] = modo
    data["formato_visual"] = LOOK_BRIEF.get(choose_look(post, tag, st), "")
    if anchor:          # every piece revolves around one 85%+ stat of today
        x12 = {n: round(q * 100) for n, q, _ in V.x12_parts(anchor)}
        data["pick_ancla"] = ({k: anchor[k] for k in ("league", "home", "away", "p")} | {"cuando": when(anchor["kickoffAt"], now),
                              "quien_gana_pct": x12 or None})
        if modo == "fomo":
            data["pick_ancla"] |= {"mercado": "OCULTO: no lo reveles, está en el enlace del perfil",
                                   "datos_extra_del_partido": max(0, int(anchor.get("more") or 0) - 1)}
        else:
            data["pick_ancla"]["mercado"] = anchor["label"]
    tx = ag.write(post, data)
    for k in ("cover_title", "cover_subtitle", "reel_hook", "reel_sub", "edu_title", "edu_body"):
        if isinstance(tx.get(k), str):
            tx[k] = V.strip_emoji(tx[k])
    if isinstance(tx.get("meme"), dict):
        tx["meme"] = {k: (V.strip_emoji(v) if isinstance(v, str) else [V.strip_emoji(x) if isinstance(x, str) else x for x in v]
                          if isinstance(v, list) else v) for k, v in tx["meme"].items()}
    # Hashtags: Daniela's SEO bank first, then leagues/teams of the real picks, then the writer's (Instagram allows 30).
    seen, tags = set(), []
    base_tags = (["memesdefutbol", "futbolmemes", "humorfutbolero"] if t == "meme" else []) \
        + (["nba", "nbapicks", "basketball", "baloncesto", "nbabasketball", "nbaenespañol", "nbalatam"] if t == "nba" else []) \
        + MARKET_TAGS.get((post.get("mercado") or "").upper(), [])
    for h in list(seo.get("hashtags") or [])[:10] + base_tags + V.hashtags_for(rows) + list(tx.get("hashtags") or []) + DEFAULT_TAGS:
        h = re.sub(r"[^\wñÑáéíóúÁÉÍÓÚüÜ]", "", str(h))
        k = h.lower()
        if h and k not in seen:
            seen.add(k)
            tags.append(h)
    tx["hashtags"] = tags[:30]
    # Tagged link so the web can tell which post brought each visit, account and payment.
    tx["fb"] = re.sub(r"https://easygoldglitch\.com(/[\w/-]*)?", lambda m: f"https://easygoldglitch.com{m.group(1) or '/'}?ref=fb_{tag}"[:120],
                      tx["fb"], count=1)
    if "easygoldglitch.com" not in tx["fb"]:
        tx["fb"] += f"\n\nhttps://easygoldglitch.com/?ref=fb_{tag}"

    wfn = lambda r: when(r["kickoffAt"], now) if r.get("kickoffAt") else ""
    tx["_ancla"] = anchor
    tx["_modo"] = modo
    V.set_stats(anchor, modo == "fomo")
    look = choose_look(post, tag, st)
    V.set_look(look)
    tx["_redes"] = list(post.get("redes") or [])
    V.set_bg(*illustrations(post, tx, tag))
    shown_keys = [match_key(r) for r in rows] if reel_of in ("picks_dia", "nba") else []
    shown_rows = [{k: r.get(k) for k in ("matchId", "league", "home", "away", "label", "p", "kickoffAt")}
                  for r in rows] if reel_of in ("picks_dia", "nba") else []
    if t == "reel":
        video = V.reel_video(V.reel_script(reel_of, rows, tx, wfn, facts.get("record")), f"{tag}_reel")
        return {"feed": [], "story": None, "video": video, "reel": True, "texts": tx, "shown": shown_keys, "shown_rows": shown_rows}
    if t == "meme":
        if tx.get("meme_formato") == "noticia" and not data.get("tendencias_del_momento"):   # never a news meme without real news
            tx["meme_formato"], tx["meme"] = "tweet", {"texto": (tx.get("meme") or {}).get("reaccion") or tx.get("cover_title", "")}
        feed = R.render([V.meme(tx.get("meme_formato") or "", tx.get("meme") or {}, 1080, 1350)], 1080, 1350, f"{tag}_feed")
        video = V.reel_video(V.reel_script("meme", [], tx, wfn), f"{tag}_reel")
        return {"feed": feed, "story": None, "video": video, "reel": False, "texts": tx, "shown": []}

    def slides(w: int, h: int) -> list[str]:
        if t == "resultados":
            pages = [V.cover(tx["cover_title"], tx["cover_subtitle"], list(dict.fromkeys(r["league"] for r in rows)), w, h)]
            per = 6 if h > 1400 else 5
            for i in range(0, min(len(rows), per * 3), per):
                pages.append(V.results(rows[i:i + per], data["won"], data["n"], w, h))
            return pages + [V.cta(w, h)]
        if t in ("picks_dia", "nba"):
            pages = [V.cover(tx["cover_title"], tx["cover_subtitle"], list(dict.fromkeys(r["league"] for r in rows)), w, h)]
            pages += [V.pick(r, i + 1, len(rows), wfn(r), w, h) for i, r in enumerate(rows)]
            return pages + [V.cta(w, h)]
        eyebrow = {"pregunta": "Tu turno", "mito_dato": "Mito vs dato", "sabias_que": "¿Sabías que…?",
                   "noticia": "Noticia del día"}.get(t, "Aprende a leer datos")
        return [V.text_card(tx.get("edu_title") or tx["cover_title"], tx.get("edu_body") or tx["cover_subtitle"], eyebrow, w, h)] + (
            [V.cta(w, h)] if h > 1400 else [])

    feed = R.render(slides(1080, 1350), 1080, 1350, f"{tag}_feed")
    # TikTok gets the same piece as a fast reel
    video = V.reel_video(V.reel_script(reel_of if reel_of in ("picks_dia", "resultados", "nba") else "texto", rows, tx, wfn,
                                       facts.get("record")), f"{tag}_reel")
    return {"feed": feed, "story": None, "video": video, "reel": False, "texts": tx, "shown": shown_keys, "shown_rows": shown_rows}


ANCHOR_P = float(os.environ.get("REDES_ANCLA_P", "0.85"))
FOMO_SHARE = {"tiktok": 0.7}        # TikTok: mostly curiosity pieces; elsewhere 35 %


LOOK_BRIEF = {   # one brand voice (a private members' data club), five rooms
    "club": "EL SALÓN DEL CLUB: negro y oro, sello de socio; tono de quien entra sin hacer fila: pocas palabras, "
            "seguras ('Esta noche el dato es uno solo.')",
    "stmoritz": "ST. MORITZ: crema, azul alpino y oro viejo, aire de temporada de invierno; tono sereno y elegante, "
                "como invitación privada ('Temporada de Champions. Reservado para quien mira los números.')",
    "esmeralda": "ESMERALDA: verde profundo con vetas de oro, mucho estilo y calle de lujo; tono con swagger, "
                 "confiado, juvenil, con personalidad propia ('El verde es el color del que ya lo sabía.')",
    "bbc": "CLUB DE MILLONARIOS: azul noche, diamantes y oro; tono de conversación entre socios, ambición sin "
           "gritar ('Los que ganan no adivinan: leen.')",
    "noche": "NOCHE PRIVADA: negro terciopelo y luz de oro, cierre de jornada; tono íntimo, de confidencia "
             "('Te cuento algo antes de que empiece.')",
}


def choose_look(post: dict, tag: str, st: dict | None) -> str:
    """Visual format of the video: rotates by piece and never repeats the last two used today."""
    if st is not None and st.get("_look_tag") == tag and st.get("_look") in V.LOOKS:
        return st["_look"]
    looks = list(V.LOOKS)
    recent = list((st or {}).get("looks_recientes") or [])[-2:]
    h = int(hashlib.md5(f"look|{tag}".encode()).hexdigest()[:6], 16)
    cands = [x for x in looks if x not in recent] or looks
    look = cands[h % len(cands)]
    if st is not None:
        st["_look_tag"], st["_look"] = tag, look
        st["looks_recientes"] = (recent + [look])[-6:]
    return look


def piece_mode(post: dict, tag: str) -> str:
    """'pick' shows the pick; 'fomo' shows the match's numbers but hides the market, to make people want the rest.
    The daily appointments (picks, results, NBA) always show the picks."""
    if post["type"] in ("picks_dia", "resultados", "nba") or post.get("obligatorio"):
        return "pick"
    if post.get("modo") in ("pick", "fomo"):
        return post["modo"]
    nets = post.get("redes") or []
    share = FOMO_SHARE.get(nets[0], 0.35) if len(nets) == 1 else 0.3
    return "fomo" if int(hashlib.md5(f"modo|{tag}".encode()).hexdigest()[:4], 16) / 65535 < share else "pick"


def anchor_pick(facts: dict, now: datetime, soon: float, shown: set[str] | None, tag: str) -> dict | None:
    """The 85%+ pick of today that a video is built around: top leagues first, not shown yet if possible, and varied
    between videos (one of the five strongest)."""
    pool = [r for r in facts.get("upcoming") or [] if float(r.get("p") or 0) >= ANCHOR_P
            and float(r.get("kickoffAt") or 0) > soon and same_day(r, now)]
    pool = [r for r in pool if V.top_league(r.get("league"))] or pool
    if not pool:
        return None
    unshown = [r for r in pool if match_key(r) not in (shown or set())]
    best = sorted(unshown or pool, key=lambda r: -float(r["p"]))[:5]
    return best[int(hashlib.md5(tag.encode()).hexdigest()[:6], 16) % len(best)]


class SkipPiece(RuntimeError):
    pass


MARKET_TAGS = {"MX": ["ligamx", "futbolmexicano"], "US": ["futbolhispano", "mls"], "AR": ["futbolargentino", "ligaprofesional"],
               "ES": ["laliga", "futbolespañol"], "CL": ["futbolchileno"], "PE": ["futbolperuano", "liga1"],
               "CO": ["ligabetplay", "futbolcolombiano"], "LATAM": ["futbollatino", "futbolsudamericano"]}
DEFAULT_TAGS = ["futbol", "estadisticasdefutbol", "datosdefutbol", "futbollatino", "analisisdefutbol"]
SPAM_TAGS = re.compile(r"^(fyp|foryou|foryoupage|parati|paratii|viral|viralvideo|trending|xyzbca|explore|explorepage|tiktok|"
                       r"reels|reel|instagood|followme|follow|like4like|likeforlike|goldglitchstats)$", re.I)
SIGNATURES = {    # who we are + follow, said differently each time (and not on every post)
    "tiktok": ["Datos de cada partido, todos los días. Seguí la cuenta.", "Si te gustan los números del fútbol, quedate.",
               "EGG: el dato antes del partido. Seguinos.", "Mañana hay más. Seguí la cuenta para no perdértelo."],
    "ig": ["EGG · estadística de fútbol con un modelo propio. El historial completo está en el enlace de la bio.",
           "Guardalo para antes del partido. Todos los datos, gratis en la bio.",
           "Seguinos: cada día, el dato que nadie está mirando."],
    "fb": ["En EGG calculamos la probabilidad de cada partido con un modelo propio. Seguí la página y lo comentamos juntos.",
           "¿Usted qué piensa? Lo leemos todo. Seguí la página para el dato de cada día.",
           "Somos EGG: estadística de fútbol, partido por partido."],
    "yt": ["EGG analiza cada partido con un modelo estadístico propio. Suscribite para el dato de cada día.",
           "Estadística de fútbol, partido por partido. Suscribite y activá la campanita."],
}


def caption(tx: dict, key: str) -> str:
    """Text + hashtags. Every '#' counts: Instagram drops the WHOLE caption when a post has more than 30, so numbering
    like '#1' in the text becomes 'Nº1' and hashtags written inside the text move to the hashtag block.
    Instagram: REDES_IG_HASHTAGS (30); TikTok: 10 (big + topic); Facebook: 8. Never empty."""
    text = tx.get(key) or ((tx.get("fb") or "").replace("ref=fb", "ref=yt") if key == "yt" else "")
    if key == "fb":     # Meta allows only 2 posts with links per month to pages without Meta Verified: never put one
        text = re.sub(r"\s*(https?://\S+|(www\.)?easygoldglitch\.com\S*)", "", str(text or "")).rstrip(" :→-👉👇")
        if "perfil" not in text.lower():
            if int(hashlib.md5(text.encode()).hexdigest()[:2], 16) % 2:   # not on every post
                text += "\n\nEl historial completo está en el enlace del perfil."
    body = re.sub(r"#(\d)", r"Nº\1", str(text or ""))
    inline = re.findall(r"(?<![\w&])#([^\W\d][\w]*)", body)
    body = re.sub(r"[ \t]*(?<![\w&])#[^\W\d][\w]*", "", body).rstrip()
    seen, tags = set(), []
    for h in inline + list(tx.get("hashtags") or []) + DEFAULT_TAGS:
        h = re.sub(r"[^\wñÑáéíóúÁÉÍÓÚüÜ]", "", str(h))
        if h and h.lower() not in seen:
            seen.add(h.lower())
            tags.append(h)
    h = int(hashlib.md5(body.encode()).hexdigest()[:6], 16)
    if not re.search(r"segu[íi]|suscrib|follow", body, re.I) and h % 3:      # who we are + follow, 2 of every 3 posts
        pool = SIGNATURES.get(key, SIGNATURES["ig"])
        body += "\n\n" + pool[h % len(pool)]
    tags = [t for t in tags if not SPAM_TAGS.match(t)]
    if key in ("tiktok", "yt"):   # TikTok and YouTube flag betting language: statistics words only, no betting tags
        from goldglitch_lenguaje import safe_tags, safe_text
        body, tags = safe_text(body), safe_tags(tags)
    if key == "yt":       # YouTube: the first 3 hashtags show above the title; more than 15 and it ignores them all
        tags = ["Shorts"] + [t for t in tags if t.lower() != "shorts"]
    # few, specific tags read as a person and rank better than walls of generic ones
    n = {"ig": max(3, min(IG_HASHTAGS, 8)), "tiktok": 5, "fb": 2, "yt": 3}.get(key, 5)
    return f"{body}\n\n{' '.join('#' + h for h in tags[:n])}".strip()


def publish(post: dict, piece: dict, meta: Meta | None, tt: TikTok | None, dry: bool) -> None:
    """Each network separately; what already went out is not repeated on the next try."""
    done = post.setdefault("done", {})
    tx = piece["texts"]
    jobs = []
    local = getattr(meta, "local", False)          # browser mode takes files; the API needs public URLs
    src = (lambda p: p) if local else upload
    for net in (meta, tt):                         # mood for the platform's trending audio (screen agents)
        if net is not None:
            try:
                net.audio_vibe = str(tx.get("audio_vibe") or "")[:60]
            except AttributeError:
                pass
    if meta and meta.ig and piece.get("reel"):
        jobs.append(("instagram", lambda: meta.ig_reel(src(piece["video"]), caption(tx, "ig"))))
    elif meta and meta.ig:
        jobs.append(("instagram", lambda: meta.ig_carousel([src(p) for p in piece["feed"]], caption(tx, "ig"))
                     if len(piece["feed"]) > 1 else meta.ig_image(src(piece["feed"][0]), caption(tx, "ig"))))
    if meta and meta.ig and piece.get("story"):          # story pointing to the new post
        jobs.append(("instagram_historia", lambda: meta.ig_story(src(piece["story"]))))
    if meta and getattr(meta, "fb", True) and (piece.get("reel") or (post["type"] == "sabias_que" and piece.get("video"))):
        jobs.append(("facebook", lambda: meta.fb_video(piece["video"], caption(tx, "fb"), tx.get("cover_title", ""))))
    elif meta and getattr(meta, "fb", True):
        jobs.append(("facebook", lambda: meta.fb_photos(piece["feed"], caption(tx, "fb"))))
    if meta and getattr(meta, "fb", True) and piece.get("story") and hasattr(meta, "fb_story"):
        jobs.append(("facebook_historia", lambda: meta.fb_story(src(piece["story"]))))
    if tt:
        jobs.append(("tiktok", lambda: tt.video(piece["video"], caption(tx, "tiktok"))))
    if YT is not None and piece.get("video"):
        YT.audio_vibe = str(tx.get("audio_vibe") or "")[:60]
        from goldglitch_lenguaje import safe_text
        title = safe_text(str(tx.get("yt_title") or tx.get("reel_hook") or tx.get("cover_title") or "Datos de fútbol"))[:90]
        jobs.append(("youtube", lambda: YT.short(piece["video"], f"{title} #Shorts"[:100], caption(tx, "yt"))))
    nets = post.get("redes") or ["instagram", "facebook", "tiktok", "youtube"]   # each network's audience (plan)
    jobs = [(n, f) for n, f in jobs if n.split("_")[0] in nets]
    for net, fn in jobs:
        if net in done or (net.endswith("_historia") and net.split("_")[0] not in done and not dry):
            continue        # a story only goes up once its post is on the profile
        if dry:
            log(f"  (dry-run) {net}: listo para publicar")
            continue
        try:
            r = fn()
            if r == "ensayo":
                log(f"  {net}: ensayo completo (sin publicar)")
                continue
            done[net] = r
            log(f"  {net}: publicado ({done[net]})")
        except (PlatformError, requests.RequestException, RuntimeError) as e:
            post.setdefault("errors", {})[net] = str(e)[:300]
            log(f"  {net}: ERROR {e}")


# ------------------------------------------------------------------ jobs
BROWSER: B.Browser | None = None


def browser_mode() -> bool:
    mode = os.environ.get("REDES_MODO", "").lower()
    if mode in ("navegador", "api"):
        return mode == "navegador"
    return not (os.environ.get("META_PAGE_TOKEN") or os.environ.get("TIKTOK_CLIENT_KEY"))


YT = None        # YouTube Shorts agent (screen agent with your Claude plan), set by clients()
AGENT = None


def clients(rehearsal: bool = False) -> tuple[Meta | B.BrowserMeta | None, TikTok | B.BrowserTikTok | None]:
    global BROWSER
    meta = tt = None
    if browser_mode():
        if not B.profile_ready():
            log("Modo navegador sin sesión: ejecuta conectar_redes.bat (una vez).")
            return None, None
        cfg = B.load_config()
        sess = B.brave_sessions(cfg)
        BROWSER = B.Browser(rehearsal=rehearsal)
        key = os.environ.get("ANTHROPIC_API_KEY")
        if key and os.environ.get("REDES_AGENTE_PANTALLA", "1") != "0":
            # Haiku agents that look at the screen and act (computer use). Without a key: the scripted steps below.
            import goldglitch_social_computer as C
            ag = C.ScreenAgent(BROWSER, key, log)
            if sess.get("instagram", True) or sess.get("facebook", True):
                meta = C.AgentMeta(ag, cfg.get("facebook_page") if sess.get("facebook", True) else None,
                                   sess.get("instagram", True), rehearsal)
            if sess.get("tiktok", True):
                tt = C.AgentTikTok(ag, rehearsal)
            return meta, tt
        import goldglitch_claude_cli as CLI
        if CLI.available() and os.environ.get("REDES_AGENTE_PANTALLA", "1") != "0":
            # Same Haiku agents, through Claude Code with your Claude plan. The MCP server opens the browser itself.
            import goldglitch_social_computer as C
            BROWSER = None
            ag = C.CliScreenAgent(log)
            global YT, AGENT
            AGENT = ag
            YT = C.AgentYouTube(ag, rehearsal) if sess.get("youtube") else None
            if sess.get("instagram", True) or sess.get("facebook", True):
                meta = C.AgentMeta(ag, cfg.get("facebook_page") if sess.get("facebook", True) else None,
                                   sess.get("instagram", True), rehearsal)
            if sess.get("tiktok", True):
                tt = C.AgentTikTok(ag, rehearsal)
            return meta, tt
        log("Sin ANTHROPIC_API_KEY ni Claude Code: se usan los pasos automáticos sin agente de pantalla.")
        if sess.get("instagram", True) or sess.get("facebook", True):
            meta = B.BrowserMeta(BROWSER, cfg.get("facebook_page") if sess.get("facebook", True) else None,
                                 instagram=sess.get("instagram", True))
        if sess.get("tiktok", True):
            tt = B.BrowserTikTok(BROWSER)
        return meta, tt
    if os.environ.get("META_PAGE_ID") and os.environ.get("META_PAGE_TOKEN"):
        meta = Meta(os.environ["META_PAGE_ID"], os.environ["META_PAGE_TOKEN"], os.environ.get("IG_USER_ID") or None)
    if os.environ.get("TIKTOK_CLIENT_KEY") and os.environ.get("TIKTOK_CLIENT_SECRET"):
        tt = TikTok(os.environ["TIKTOK_CLIENT_KEY"], os.environ["TIKTOK_CLIENT_SECRET"], os.environ.get("TIKTOK_PRIVACY", "SELF_ONLY"))
        try:
            tt.token()
        except PlatformError as e:
            log(f"TikTok sin conectar: {e}")
            tt = None
    return meta, tt


LOCK = os.path.join(HERE, "redes.lock")


def take_lock(wait_s: int = 0) -> bool:
    """One worker at a time (the browser profile can only be open once). Stale locks (>45 min) are ignored."""
    end = time.time() + wait_s
    while True:
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return True
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(LOCK) > 45 * 60:
                    os.remove(LOCK)
                    continue
            except OSError:
                continue
            if time.time() >= end:
                return False
            time.sleep(15)


def drop_lock() -> None:
    try:
        os.remove(LOCK)
    except OSError:
        pass


def publish_now(posts: list[dict]) -> None:
    """Publish the committee's immediate post(s) right away (after an extraordinary meeting)."""
    if not take_lock(wait_s=20 * 60):
        log("Publicación inmediata: los agentes siguen ocupados; queda para la próxima vuelta")
        return
    global BROWSER
    try:
        now = datetime.now(TZ)
        today = now.strftime("%Y-%m-%d")
        st = load_json(STATE, {})
        ag = Agents(os.environ.get("ANTHROPIC_API_KEY"))
        meta, tt = clients()
        for i, post in enumerate(posts[:1]):
            post = {**post, "time": now.strftime("%H:%M"), "inmediata": True}
            log(f"Publicación inmediata del comité: {post['type']} — {post.get('angle', '')}")
            try:
                facts = signed("/api/social/feed", {})
                piece = build(post, facts, ag, now, f"{today}_ya{now:%H%M}_{post['type']}", shown_recent(st), st)
                publish(post, piece, meta, tt, False)
                if post.get("done"):
                    remember_shown(st, piece)
            except SkipPiece as e:
                log(f"  se omite: {e}")
                continue
            except Exception as e:
                log(f"  ERROR en la publicación inmediata: {e}")
                continue
            st.setdefault("history", []).append({"day": today, "type": post["type"], "time": post["time"], "angle": post.get("angle"), "mercado": post.get("mercado"), "segmento": post.get("segmento"),
                                                "inmediata": True, "done": list(post.get("done", {})), "errors": post.get("errors", {})})
        save_json(STATE, st)
    finally:
        if BROWSER:
            BROWSER.close()
            BROWSER = None
        drop_lock()


def publish_tiktok(n: int, want: str = "") -> None:
    """Manual TikTok round: n videos, only on TikTok, rotating formats (reel, news, did-you-know, picks, myth vs fact…)."""
    if not take_lock(wait_s=20 * 60):
        log("TikTok manual: los agentes siguen ocupados; inténtalo en unos minutos.")
        return
    global BROWSER
    try:
        _, tt = clients()
        if not tt:
            sess = B.brave_sessions(B.load_config())
            log(f"TikTok manual: no hay sesión de TikTok (Brave: {'sí' if B.uses_brave('tiktok') else 'no'}, "
                f"sesión: {sess.get('tiktok')}). Corre conectar_tiktok_brave.bat.")
            return
        st = load_json(STATE, {})
        ag = Agents(os.environ.get("ANTHROPIC_API_KEY"))
        types = [want] if want else G.FILL_TYPES["tiktok"]
        start = int(st.get("tiktok_manual_i") or 0)
        ok = 0
        for i in range(n):
            now = datetime.now(TZ)
            today = now.strftime("%Y-%m-%d")
            t = types[(start + i) % len(types)]
            post = {"type": t, "time": now.strftime("%H:%M"), "redes": ["tiktok"], "inmediata": True,
                    "angle": "", "topic": "", "hook": "", "cta": "Datos gratis en el enlace del perfil"}
            log(f"TikTok manual {i + 1}/{n}: {t}")
            try:
                facts = signed("/api/social/feed", {})
                piece = build(post, facts, ag, now, f"{today}_tt{now:%H%M%S}_{t}", shown_recent(st), st)
                piece["story"] = None
                publish(post, piece, None, tt, False)
                if "tiktok" in (post.get("done") or {}):
                    ok += 1
                    remember_shown(st, piece)
            except SkipPiece as e:
                log(f"  se omite: {e}")
            except Exception as e:
                log(f"  ERROR: {e}")
            st.setdefault("history", []).append({"day": today, "type": t, "time": post["time"], "inmediata": True,
                                                "manual_tiktok": True, "done": list(post.get("done", {})),
                                                "errors": post.get("errors", {})})
        st["tiktok_manual_i"] = start + n
        save_json(STATE, st)
        log(f"TikTok manual: {ok} de {n} publicados")
    finally:
        if BROWSER:
            BROWSER.close()
            BROWSER = None
        drop_lock()


def week_of(now: datetime) -> str:
    return now.strftime("%G-W%V")


def office() -> None:
    try:
        import goldglitch_oficina as O
        O.build()
    except Exception as e:
        log(f"Oficina: no se pudo actualizar ({e})")


def tick(dry: bool) -> None:
    if os.environ.get("REDES_PAUSA") == "1":
        log("En pausa (REDES_PAUSA=1).")
        return
    if not take_lock():
        log("Otra tarea de redes está trabajando (reunión o publicación inmediata); esta vuelta se salta.")
        return
    try:
        _tick(dry)
    finally:
        drop_lock()
        office()


def _tick(dry: bool) -> None:
    now = datetime.now(TZ)
    st = load_json(STATE, {})
    ag = Agents(os.environ.get("ANTHROPIC_API_KEY"))
    if ag.offline:
        log("Sin ANTHROPIC_API_KEY ni Claude Code: los textos salen de plantillas (sin IA).")
    elif ag.cli:
        log("Agentes con tu plan de Claude (Claude Code, Haiku 5.5).")
    meta, tt = clients()
    today = now.strftime("%Y-%m-%d")
    try:                                   # what is trending now (cached 2 h) for the committee, memes and hooks
        T.get(log)
    except Exception as e:
        log(f"Tendencias no disponibles: {e}")

    # 1) plan of the day (after 07:00): the growth committee decides it; the Estratega is the fallback
    if st.get("day") != today and now.hour >= 7:
        facts = signed("/api/social/feed", {})
        memory = open(MEMORY, encoding="utf-8").read() if os.path.exists(MEMORY) else ""
        plan = G.plan_for(today)
        if plan is None and not ag.offline and os.environ.get("REDES_COMITE", "1") != "0":
            try:
                res = G.Committee(os.environ.get("ANTHROPIC_API_KEY"), signed, st, facts, log).meet(today)
                plan = G.plan_for(today)
                if plan is not None and res.get("ahora"):
                    plan = [{**res["ahora"][0], "time": datetime.now(TZ).strftime("%H:%M"), "inmediata": True}] + plan
            except Exception as e:
                log(f"El comité no pudo reunirse ({e}); planea el Estratega")
        plan = plan or ag.plan(f"{now:%A %d/%m/%Y}", facts, memory)
        plan = G.with_mandatory(plan, today, st)        # morning picks + night results always go
        plan = G.fill_per_network(plan, today)          # at least 8 own pieces per network
        st = {**st, "day": today, "plan": plan, "plan_v": G.plan_version(today), "history": (st.get("history") or [])[-60:]}
        log("Plan de hoy: " + ", ".join(f"{p['time']} {p['type']}" for p in plan))
        save_json(STATE, st)
    elif st.get("day") == today and G.plan_version(today) > float(st.get("plan_v") or 0):
        # an extraordinary meeting changed today's plan: keep what already went out, take the new pending posts
        kept = [p for p in st.get("plan") or [] if p.get("status") in ("done", "skipped")]
        new = [p for p in G.fill_per_network(G.plan_for(today) or [], today) if p["time"] > now.strftime("%H:%M")]
        st["plan"], st["plan_v"] = kept + new, G.plan_version(today)
        log("Plan actualizado por reunión extraordinaria: " + ", ".join(f"{p['time']} {p['type']}" for p in new))
        save_json(STATE, st)

    # 2) posts that are due
    for i, post in enumerate(st.get("plan") or []):
        if post.get("status") in ("done", "skipped") or post["time"] > now.strftime("%H:%M"):
            continue
        hh, mm = map(int, post["time"].split(":"))
        if now - now.replace(hour=hh, minute=mm, second=0, microsecond=0) > timedelta(hours=2) and not post.get("tries") \
                and not (post.get("obligatorio") and (post["type"] == "resultados" or now.hour < 20)):
            post["status"] = "skipped"  # the PC was off: publishing a 9 a.m. piece at night makes no sense
            log(f"Se omite {post['type']} de las {post['time']}: ya pasó su hora")
            continue
        post["tries"] = post.get("tries", 0) + 1
        log(f"Publicando {post['type']} ({post['time']}), intento {post['tries']}")
        try:
            facts = signed("/api/social/feed", {})
            if (post["type"] == "resultados" and not facts["results"]) or (post["type"] == "picks_dia" and not facts["upcoming"]):
                post["status"] = "skipped"
                log("  sin datos para esta pieza: se omite")
                continue
            try:
                piece = build(post, facts, ag, now, f"{today}_{i}_{post['type']}", shown_recent(st), st)
            except SkipPiece as e:
                post["status"] = "skipped"
                log(f"  se omite: {e}")
                save_json(STATE, st)
                continue
            publish(post, piece, meta, tt, dry)
            if post.get("done") and not dry:
                remember_shown(st, piece)
            nets = {"instagram"} if meta and meta.ig else set()
            nets |= {"facebook"} if meta and getattr(meta, "fb", True) else set()
            nets |= {"tiktok"} if tt else set()
            nets |= {"youtube"} if YT is not None else set()
            nets &= set(post.get("redes") or ["instagram", "facebook", "tiktok", "youtube"])
            if dry or nets <= set(post.get("done", {})) or post["tries"] >= MAX_TRIES:
                post["status"] = "done"
                st.setdefault("history", []).append({"day": today, "type": post["type"], "time": post["time"], "angle": post.get("angle"), "mercado": post.get("mercado"), "segmento": post.get("segmento"),
                                                    "done": list(post.get("done", {})), "errors": post.get("errors", {})})
        except Exception as e:  # keep the loop alive; the next tick retries
            post.setdefault("errors", {})["build"] = str(e)[:300]
            log(f"  ERROR armando la pieza: {e}")
            if post["tries"] >= MAX_TRIES:
                post["status"] = "skipped"
        save_json(STATE, st)

    # 3) comments
    last = st.get("community_at", 0)
    if meta and not getattr(meta, "local", False) and time.time() - last >= COMMUNITY_EVERY_MIN * 60 and 7 <= now.hour <= 23:
        community(st, meta, ag, dry)
        st["community_at"] = time.time()
        save_json(STATE, st)

    # 3c) community management: replies and likes on every network, every REDES_COMUNIDAD_HORAS between 10:00 and 22:00
    every = float(os.environ.get("REDES_COMUNIDAD_HORAS", "4") or 4)
    if AGENT is not None and not dry and 10 <= now.hour < 22 and time.time() - float(st.get("community_at") or 0) > every * 3600:
        import goldglitch_social_computer as C
        sess = B.brave_sessions(B.load_config())
        nets = [n for n in ("youtube", "instagram", "facebook", "tiktok") if sess.get(n, n != "youtube")]
        res = C.community_round(AGENT, nets, B.load_config().get("facebook_page"), log)
        st["community_at"] = time.time()
        st.setdefault("community", []).append({"at": now.strftime("%Y-%m-%d %H:%M"),
                                               **{k: f"{v[0]}: {v[1][:300]}" for k, v in res.items()}})
        st["community"] = st["community"][-30:]
        save_json(STATE, st)

    # 4) weekly study session in the office library (Sundays from 15:00)
    if now.weekday() == 6 and now.hour >= 15 and st.get("study_week") != week_of(now) and not ag.offline:
        try:
            G.study(os.environ.get("ANTHROPIC_API_KEY"), signed, st, signed("/api/social/feed", {}), log)
        except Exception as e:
            log(f"Sesión de estudio: {e}")
        st["study_week"] = week_of(now)
        save_json(STATE, st)

    # 5) weekly report (Mondays from 09:00)
    week = now.strftime("%G-W%V")
    if now.weekday() == 0 and now.hour >= 9 and st.get("report_week") != week:
        report(st, meta, ag)
        st["report_week"] = week
        save_json(STATE, st)


def community(st: dict, meta: Meta, ag: Agents, dry: bool) -> None:
    seen = set(st.get("seen_comments") or [])
    comments = []
    for fn in (meta.ig_recent_comments, meta.fb_recent_comments):
        try:
            comments += [c for c in fn() if c["id"] not in seen]
        except (PlatformError, requests.RequestException) as e:
            log(f"Comentarios: no se pudieron leer ({e})")
    if not comments:
        return
    actions = ag.moderate(comments[:40])
    for c, a in zip(comments[:40], actions):
        try:
            if a["action"] == "reply" and a.get("text"):
                if not dry:
                    meta.reply(c, a["text"])
                log(f"Comentario {c['net']} de {c.get('user')}: respondido")
            elif a["action"] == "hide":
                if not dry:
                    meta.hide(c)
                log(f"Comentario {c['net']} de {c.get('user')}: oculto")
        except (PlatformError, requests.RequestException) as e:
            log(f"Comentario {c['id']}: ERROR {e}")
        seen.add(c["id"])
    st["seen_comments"] = list(seen)[-3000:]


def report(st: dict, meta: Meta | None, ag: Agents) -> None:
    insights = []
    if meta:
        try:
            insights = meta.ig_insights(7)
        except (PlatformError, requests.RequestException) as e:
            log(f"Informe: sin métricas de Instagram ({e})")
    memory = open(MEMORY, encoding="utf-8").read() if os.path.exists(MEMORY) else ""
    notes = ag.review(insights, (st.get("history") or [])[-30:], memory)
    with open(MEMORY, "w", encoding="utf-8") as f:
        f.write(notes)
    log("Informe semanal listo (redes_memoria.md):\n" + notes)


def prueba() -> None:
    """Sample pieces with fake data, no AI and no networks: to look at the design."""
    now = datetime.now(TZ)
    k = int((now + timedelta(hours=5)).timestamp() * 1000)
    facts = {"upcoming": [
        {"league": "LaLiga", "home": "Real Madrid", "away": "Sevilla", "kickoffAt": k, "label": "Total de goles: Más de 1.5", "group": "Goles", "p": 0.88},
        {"league": "Liga BetPlay", "home": "Millonarios", "away": "Nacional", "kickoffAt": k, "label": "Córners totales: Más de 6.5", "group": "Córners", "p": 0.82}],
        "results": [{"home": "Cali", "away": "América", "label": "Tarjetas totales: Más de 2.5", "p": 0.86, "status": "won"},
                    {"home": "Junior", "away": "Santa Fe", "label": "Total de goles: Menos de 3.5", "p": 0.81, "status": "lost"}],
        "record": {"d7": {"won": 30, "n": 37}}}
    ag = Agents(None, offline=True)
    for t in ("resultados", "picks_dia", "educativo"):
        p = build({"type": t, "time": "09:00", "angle": "prueba"}, facts, ag, now, f"prueba_{t}")
        log(f"prueba {t}: {len(p['feed'])} imágenes, video {p['video']}")
    log(f"Mira las piezas en {R.OUT}")


def ensayo() -> None:
    """Browser mode check: a real piece (templates, no AI cost) walked through every network WITHOUT the final click."""
    now = datetime.now(TZ)
    try:
        facts = signed("/api/social/feed", {})
    except Exception as e:
        log(f"ensayo: sin datos de la web ({e}); uso datos de ejemplo")
        facts = None
    if not facts or not facts.get("upcoming"):
        k = int((now + timedelta(hours=5)).timestamp() * 1000)
        facts = {"upcoming": [{"league": "Liga BetPlay", "home": "Millonarios", "away": "Nacional", "kickoffAt": k,
                               "label": "Córners totales: Más de 6.5", "group": "Córners", "p": 0.82}],
                 "results": [], "record": {"d7": {"won": 0, "n": 0}}}
    piece = build({"type": "picks_dia", "time": now.strftime("%H:%M"), "angle": "ensayo"}, facts, Agents(None, offline=True), now, "ensayo")
    meta, tt = clients(rehearsal=True)
    if not meta and not tt:
        return
    publish({"type": "ensayo"}, piece, meta, tt, dry=False)
    log("Ensayo terminado. Si algún paso falló, la captura está en redes_salida/errores.")


def tiktok_login() -> None:
    key, secret = os.environ.get("TIKTOK_CLIENT_KEY"), os.environ.get("TIKTOK_CLIENT_SECRET")
    if not key or not secret:
        raise SystemExit("Agrega TIKTOK_CLIENT_KEY y TIKTOK_CLIENT_SECRET al .env primero.")
    state = hashlib.sha256(os.urandom(16)).hexdigest()[:16]
    url = TikTok.auth_url(key, TIKTOK_REDIRECT, state)
    print("\n1) Abre este enlace, entra con la cuenta de TikTok de Goldglitch y autoriza:\n\n" + url)
    try:
        import webbrowser
        webbrowser.open(url)
    except Exception:
        pass
    code = input("\n2) Pega aquí el código que muestra la página: ").strip()
    TikTok(key, secret).exchange(code, TIKTOK_REDIRECT)
    print("TikTok conectado.")


def main() -> int:
    load_env()
    args = sys.argv[1:]
    cmd = args[0] if args and not args[0].startswith("-") else "tick"
    dry = "--dry-run" in args
    try:
        if cmd == "tick":
            tick(dry)
        elif cmd == "prueba":
            prueba()
        elif cmd == "conectar":
            B.connect()
        elif cmd == "conectar_brave":       # e.g. conectar_brave tiktok
            B.connect_brave(sys.argv[2:] or ["tiktok"])
        elif cmd == "ensayo":
            ensayo()
        elif cmd == "tiktok-login":
            tiktok_login()
        elif cmd == "ya":                   # publish one piece right now: the next pending one of today's plan, else a meme
            want = sys.argv[2] if len(sys.argv) > 2 else ""
            st = load_json(STATE, {})
            today = datetime.now(TZ).strftime("%Y-%m-%d")
            pending = [p for p in (st.get("plan") or []) if st.get("day") == today and p.get("status") not in ("done", "skipped")]
            post = next((p for p in pending if not want or p.get("type") == want), None)
            post = dict(post) if post else {"type": want or "meme", "angle": "Pieza inmediata: lo que está pasando hoy en el fútbol",
                                            "topic": "tendencia del día", "hook": "", "cta": "Datos gratis en el enlace del perfil"}
            publish_now([post])
            if post.get("time") and pending:     # mark the plan item as handled so the tick does not repeat it
                st = load_json(STATE, {})
                for p in st.get("plan") or []:
                    if p.get("time") == post.get("time") and p.get("type") == post.get("type"):
                        p["status"] = "done"
                save_json(STATE, st)
        elif cmd == "tiktok":               # publish N TikToks now: tiktok [n] [tipo]
            args = sys.argv[2:]
            n = int(next((a for a in args if a.isdigit()), "1"))
            want = next((a for a in args if not a.isdigit()), "")
            publish_tiktok(min(max(n, 1), 10), want)
        elif cmd == "comunidad":            # one community round now (replies + likes on every connected network)
            clients()
            if AGENT is None:
                print("Necesitas Claude Code con tu sesión de Claude (probar_claude_pro.bat).")
                return 1
            import goldglitch_social_computer as C
            if not take_lock(wait_s=20 * 60):
                log("Comunidad: los agentes están ocupados; inténtalo en unos minutos.")
                return 1
            try:
                sess = B.brave_sessions(B.load_config())
                nets = [n for n in ("youtube", "instagram", "facebook", "tiktok") if sess.get(n, n != "youtube")]
                for net, (r, d) in C.community_round(AGENT, nets, B.load_config().get("facebook_page"), log).items():
                    log(f"Comunidad · {net}: {r} — {d[:400]}")
                st = load_json(STATE, {})
                st["community_at"] = time.time()
                save_json(STATE, st)
            finally:
                drop_lock()
        elif cmd == "informe":
            meta, _ = clients()
            st = load_json(STATE, {})
            report(st, meta, Agents(os.environ.get("ANTHROPIC_API_KEY")))
        else:
            print(__doc__)
            return 2
    except SystemExit:
        raise
    except Exception:
        log("ERROR inesperado:\n" + traceback.format_exc())
        return 1
    finally:
        if BROWSER:
            BROWSER.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
