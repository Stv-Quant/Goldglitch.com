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
    ANTHROPIC_API_KEY=...       clave de la API de Anthropic (agentes Haiku 5.5)
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
    print(line)
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


# ------------------------------------------------------------------ pieces
def build(post: dict, facts: dict, ag: Agents, now: datetime, tag: str) -> dict:
    """Texts + images + video for one planned post. Returns {feed:[jpg], story:jpg|None, video:mp4, texts}."""
    t = post["type"]
    if t == "resultados":
        rows = sorted(facts["results"], key=lambda r: (r["status"] != "won", -r["p"]))
        won = sum(r["status"] == "won" for r in rows)
        data = {"won": won, "n": len(rows), "historial": facts["record"]}
    elif t == "picks_dia":
        rows = facts["upcoming"][:5]
        data = {"picks": [{k: r[k] for k in ("league", "home", "away", "label", "p")} | {"cuando": when(r["kickoffAt"], now)} for r in rows],
                "historial": facts["record"]}
    else:
        rows, data = [], {"historial": facts["record"]}
    tx = ag.write(post, data)

    def slides(w: int, h: int) -> list[str]:
        if t == "resultados":
            pages = [R.cover(tx["cover_title"], tx["cover_subtitle"], "Resultados del modelo", w, h)]
            per = 6 if h > 1400 else 5
            for i in range(0, min(len(rows), per * 3), per):
                pages.append(R.results_slide(rows[i:i + per], data["won"], data["n"], "Picks de 75% o más ya jugados", w, h))
            return pages + [R.cta_slide(w, h)]
        if t == "picks_dia":
            pages = [R.cover(tx["cover_title"], tx["cover_subtitle"], "Probabilidades del modelo", w, h)]
            pages += [R.pick_slide(r, i + 1, len(rows), when(r["kickoffAt"], now), w, h) for i, r in enumerate(rows)]
            return pages + [R.cta_slide(w, h)]
        return [R.text_slide(tx.get("edu_title") or tx["cover_title"], tx.get("edu_body") or tx["cover_subtitle"], "Aprende a leer datos", w, h)] + (
            [R.cta_slide(w, h)] if h > 1400 else [])

    feed = R.render(slides(1080, 1350), 1080, 1350, f"{tag}_feed")
    vert = R.render(slides(1080, 1920), 1080, 1920, f"{tag}_vert")
    vid = R.video(vert, f"{tag}_video", seconds=3.4 if t != "educativo" else 5.0)
    story = None
    if t == "picks_dia" and rows:
        story = R.render([R.pick_slide(rows[0], 1, 1, when(rows[0]["kickoffAt"], now), 1080, 1920)], 1080, 1920, f"{tag}_story")[0]
    return {"feed": feed, "story": story, "video": vid, "texts": tx}


def caption(tx: dict, key: str) -> str:
    tags = " ".join(f"#{h}" for h in tx.get("hashtags", []))
    return f"{tx[key]}\n\n{tags}".strip() if key != "fb" else tx["fb"]


def publish(post: dict, piece: dict, meta: Meta | None, tt: TikTok | None, dry: bool) -> None:
    """Each network separately; what already went out is not repeated on the next try."""
    done = post.setdefault("done", {})
    tx = piece["texts"]
    jobs = []
    local = getattr(meta, "local", False)          # browser mode takes files; the API needs public URLs
    src = (lambda p: p) if local else upload
    if meta and meta.ig:
        jobs.append(("instagram", lambda: meta.ig_carousel([src(p) for p in piece["feed"]], caption(tx, "ig"))
                     if len(piece["feed"]) > 1 else meta.ig_image(src(piece["feed"][0]), caption(tx, "ig"))))
        if piece["story"] and not local:
            jobs.append(("instagram_historia", lambda: meta.ig_story(upload(piece["story"]))))
    if meta and getattr(meta, "fb", True):
        jobs.append(("facebook", lambda: meta.fb_photos(piece["feed"], caption(tx, "fb"))))
    if tt:
        jobs.append(("tiktok", lambda: tt.video(piece["video"], caption(tx, "tiktok"))))
    for net, fn in jobs:
        if net in done:
            continue
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


def clients(rehearsal: bool = False) -> tuple[Meta | B.BrowserMeta | None, TikTok | B.BrowserTikTok | None]:
    global BROWSER
    meta = tt = None
    if browser_mode():
        if not B.profile_ready():
            log("Modo navegador sin sesión: ejecuta conectar_redes.bat (una vez).")
            return None, None
        cfg = B.load_config()
        sess = cfg.get("sessions") or {}
        BROWSER = B.Browser(rehearsal=rehearsal)
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


def tick(dry: bool) -> None:
    if os.environ.get("REDES_PAUSA") == "1":
        log("En pausa (REDES_PAUSA=1).")
        return
    now = datetime.now(TZ)
    st = load_json(STATE, {})
    ag = Agents(os.environ.get("ANTHROPIC_API_KEY"))
    if ag.offline:
        log("Sin ANTHROPIC_API_KEY: los textos salen de plantillas (sin IA).")
    meta, tt = clients()
    today = now.strftime("%Y-%m-%d")

    # 1) plan of the day (after 07:00)
    if st.get("day") != today and now.hour >= 7:
        facts = signed("/api/social/feed", {})
        memory = open(MEMORY, encoding="utf-8").read() if os.path.exists(MEMORY) else ""
        plan = ag.plan(f"{now:%A %d/%m/%Y}", facts, memory)
        st = {**st, "day": today, "plan": plan, "history": (st.get("history") or [])[-60:]}
        log("Plan de hoy: " + ", ".join(f"{p['time']} {p['type']}" for p in plan))
        save_json(STATE, st)

    # 2) posts that are due
    for i, post in enumerate(st.get("plan") or []):
        if post.get("status") in ("done", "skipped") or post["time"] > now.strftime("%H:%M"):
            continue
        hh, mm = map(int, post["time"].split(":"))
        if now - now.replace(hour=hh, minute=mm, second=0, microsecond=0) > timedelta(hours=2) and not post.get("tries"):
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
            piece = build(post, facts, ag, now, f"{today}_{i}_{post['type']}")
            publish(post, piece, meta, tt, dry)
            nets = {"instagram"} if meta and meta.ig else set()
            nets |= {"facebook"} if meta and getattr(meta, "fb", True) else set()
            nets |= {"tiktok"} if tt else set()
            if dry or nets <= set(post.get("done", {})) or post["tries"] >= MAX_TRIES:
                post["status"] = "done"
                st.setdefault("history", []).append({"day": today, "type": post["type"], "time": post["time"], "angle": post.get("angle"),
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

    # 4) weekly report (Mondays from 09:00)
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
        elif cmd == "ensayo":
            ensayo()
        elif cmd == "tiktok-login":
            tiktok_login()
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
