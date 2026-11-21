"""Lo que está pasando AHORA: el insumo de Valeria (viralidad) y Daniela (SEO) para memes y ganchos del momento.

Fuentes gratis y sin cuenta (cache de 2 horas en redes_tendencias.json):
  - Google Trends: búsquedas en tendencia en Colombia y otros países latinos (RSS público);
  - ESPN: titulares de fútbol de las ligas top (API pública);
  - TikTok Creative Center: hashtags populares en Colombia (página pública, leída con un navegador aparte; si falla,
    se omite).
Se descartan tragedias, muertes, violencia y política: con eso no se hace humor.

    python goldglitch_trends.py        # muestra las tendencias de ahora
"""
from __future__ import annotations

import json
import os
import re
import time
import xml.etree.ElementTree as ET

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "redes_tendencias.json")
TTL = 2 * 3600
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"}

GEOS = {"CO": "Colombia", "MX": "México", "AR": "Argentina", "ES": "España", "US": "EE. UU."}
LEAGUES = {"eng.1": "Premier League", "esp.1": "LaLiga", "ita.1": "Serie A", "ger.1": "Bundesliga", "fra.1": "Ligue 1",
           "uefa.champions": "Champions League", "col.1": "Liga BetPlay", "conmebol.libertadores": "Libertadores",
           "arg.1": "Liga Argentina", "mex.1": "Liga MX", "bra.1": "Brasileirão"}
# no jokes about these
SENSITIVE = re.compile(r"\b(muer\w*|muri\w*|fallec\w*|asesin\w*|homicid\w*|accident\w*|tragedi\w*|víctima\w*|victima\w*|"
                       r"herid\w*|ataque\w*|atentad\w*|guerra|bomba\w*|terremoto|sismo|incendi\w*|secuestr\w*|violac\w*|"
                       r"abuso\w*|suicid\w*|cáncer|cancer|hospitaliz\w*|luto|velorio|funeral|elecci\w*|president\w*|"
                       r"petro|trump|congreso|senado|partido polític\w*|died|death|dead|killed|shooting|crash)\b", re.I)


def _safe(text: str) -> bool:
    return bool(text) and not SENSITIVE.search(text)


def google_trends(geo: str) -> list[dict]:
    r = requests.get(f"https://trends.google.com/trending/rss?geo={geo}", headers=UA, timeout=20)
    r.raise_for_status()
    return parse_trends_rss(r.text)


def parse_trends_rss(xml: str) -> list[dict]:
    ns = {"ht": "https://trends.google.com/trending/rss"}
    out = []
    for it in ET.fromstring(xml).iter("item"):
        title = (it.findtext("title") or "").strip()
        traffic = (it.findtext("ht:approx_traffic", namespaces=ns) or "").strip()
        news = [(n.findtext("ht:news_item_title", namespaces=ns) or "").strip() for n in it.findall("ht:news_item", ns)]
        news = [n for n in news if n][:2]
        if _safe(title) and all(_safe(n) for n in news):
            out.append({"busqueda": title, "trafico": traffic, "noticias": news})
    return out[:15]


def espn_news(slug: str) -> list[dict]:
    j = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/news?limit=6", headers=UA, timeout=15).json()
    out = []
    for a in j.get("articles") or []:
        h = (a.get("headline") or "").strip()
        if _safe(h) and _safe(a.get("description") or ""):
            out.append({"liga": LEAGUES[slug], "titular": h, "resumen": (a.get("description") or "")[:200],
                        "fecha": (a.get("published") or "")[:16]})
    return out[:4]


def tiktok_hashtags() -> list[str]:
    """Popular hashtags in Colombia from TikTok Creative Center (public page). Uses its own throwaway browser, never
    the social profile (the screen agents may have that one open)."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        try:
            pg = br.new_page(user_agent=UA["User-Agent"], locale="es-CO")
            pg.goto("https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/es?region=CO&period=7",
                    wait_until="domcontentloaded", timeout=45_000)
            pg.wait_for_timeout(7000)
            text = pg.inner_text("body")
        finally:
            br.close()
    tags = re.findall(r"#\s?([^\W\d_][\w]{2,40})", text)
    return [t for t in dict.fromkeys(tags) if _safe(t)][:25]


def spotify_colombia() -> list[str]:
    """Most-played songs in Colombia today (kworb.net mirrors Spotify's public daily chart)."""
    r = requests.get("https://kworb.net/spotify/country/co_daily.html", headers=UA, timeout=20)
    r.raise_for_status()
    rows = re.findall(r"<td class=\"text mp\"><div>(.*?)</div></td>", r.text, re.S)
    out = []
    for cell in rows[:20]:
        txt = re.sub(r"<[^>]+>", "", cell)
        txt = html_unescape(" ".join(txt.split()))
        if txt and _safe(txt):
            out.append(txt)
    return out


def tiktok_songs() -> list[str]:
    """Popular songs on TikTok in Colombia (TikTok Creative Center, public page)."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        try:
            pg = br.new_page(user_agent=UA["User-Agent"], locale="es-CO")
            pg.goto("https://ads.tiktok.com/business/creativecenter/inspiration/popular/music/pc/es?region=CO&period=7",
                    wait_until="domcontentloaded", timeout=45_000)
            pg.wait_for_timeout(7000)
            items = pg.eval_on_selector_all("[class*='music'] [class*='title'], [class*='Music'] [class*='Title']",
                                            "els => els.map(e => e.innerText.trim())")
        finally:
            br.close()
    return [t for t in dict.fromkeys(i for i in items if 2 < len(i) < 80) if _safe(t)][:15]


def html_unescape(s: str) -> str:
    import html
    return html.unescape(s)


def songs(data: dict | None = None) -> list[str]:
    """Trending songs/sounds to look up in the platform's own audio library (TikTok first, then Spotify Colombia)."""
    data = data if data is not None else get()
    return list(dict.fromkeys((data.get("canciones_tiktok") or [])[:8] + (data.get("canciones") or [])[:10]))


def collect(log=print) -> dict:
    data: dict = {"ts": time.time(), "google": {}, "futbol": [], "tiktok": [], "canciones": [], "canciones_tiktok": []}
    try:
        data["canciones"] = spotify_colombia()
    except Exception as e:
        log(f"  canciones Spotify Colombia: {e}")
    try:
        data["canciones_tiktok"] = tiktok_songs()
    except Exception as e:
        log(f"  canciones TikTok: {e}")
    for geo, name in GEOS.items():
        try:
            data["google"][name] = google_trends(geo)
        except Exception as e:
            log(f"  tendencias Google {geo}: {e}")
    for slug in LEAGUES:
        try:
            data["futbol"] += espn_news(slug)
        except Exception as e:
            log(f"  titulares {slug}: {e}")
    try:
        data["tiktok"] = tiktok_hashtags()
    except Exception as e:
        log(f"  hashtags TikTok: {e}")
    return data


def get(log=print, force: bool = False) -> dict:
    try:
        cached = json.load(open(CACHE, encoding="utf-8"))
    except (OSError, ValueError):
        cached = {}
    if not force and time.time() - float(cached.get("ts") or 0) < TTL:
        return cached
    data = collect(log)
    if not (data["google"] or data["futbol"]) and cached:      # offline: keep the last good snapshot
        return cached
    for k in ("tiktok", "canciones", "canciones_tiktok"):
        if not data.get(k) and cached.get(k):
            data[k] = cached[k]
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    return data


def brief(data: dict | None = None, n: int = 8) -> dict:
    """Compact version for prompts (agents read it to tie memes and hooks to what is happening now)."""
    data = data if data is not None else get()
    age = int((time.time() - float(data.get("ts") or 0)) / 60) if data.get("ts") else None
    return {"actualizado_hace_min": age,
            "busquedas_en_tendencia": {k: [f"{t['busqueda']} ({t['trafico']})" + (f" — {t['noticias'][0]}" if t["noticias"] else "")
                                           for t in v[:n]] for k, v in (data.get("google") or {}).items()},
            "titulares_futbol": [f"{a['liga']}: {a['titular']}" for a in (data.get("futbol") or [])[:20]],
            "hashtags_tiktok_colombia": (data.get("tiktok") or [])[:20],
            "canciones_en_tendencia": songs(data)[:12]}


if __name__ == "__main__":
    print(json.dumps(brief(get(force=True)), ensure_ascii=False, indent=1))
