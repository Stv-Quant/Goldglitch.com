"""
SQPC → Goldglitch sync.

Reads what SQPC already wrote to disk and publishes it to easygoldglitch.com:
  reports/predictions/<fecha>/*.json   → partidos + predicciones (fútbol, NBA, NCAAB, NHL, MLB)
  reports/esports_events.json          → series de e-sports (Valorant, Dota 2); resultados desde data/sqpc.db
  reports/analysis_<fecha>.json        → métricas de validación fuera de muestra (historial público)
  ESPN (gratis)                        → marcador final de los partidos ya publicados
  data/tracked_picks.json              → seguimiento de los picks que el sistema escogió (acertados / fallados)

Nothing is recalculated here: SQPC's numbers are sent as-is. Run from the SQPC folder:
    python goldglitch_sync.py            # publica
    python goldglitch_sync.py --dry-run  # arma el lote y lo guarda en goldglitch_last_batch.json sin enviarlo
Needs .env with GG_INGEST_URL and GG_INGEST_SECRET (Admin → Datos → Conexión con SQPC).
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re
import sys
import time
import unicodedata
import urllib.request
import uuid
from datetime import datetime, timezone
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from goldglitch_publish import load_env, publish  # noqa: E402
from goldglitch_lines import basketball_lines, football_lines, hockey_lines, pack  # noqa: E402

STATE_FILE = os.path.join(HERE, "goldglitch_state.json")
TRACKED_SENT = os.path.join(HERE, "goldglitch_tracked_sent.json")  # id → fingerprint of what the site already has
LAST_BATCH = os.path.join(HERE, "goldglitch_last_batch.json")

# League code → (sport, display name, ESPN slug for results). Football slugs come from each file.
US_LEAGUES = {
    "NBA": ("basketball", "NBA", "basketball/nba"),
    "NHL": ("hockey", "NHL", "hockey/nhl"),
    "MLB": ("baseball", "MLB", "baseball/mlb"),
    "NCAAB": ("basketball", "NCAA Baloncesto", "basketball/mens-college-basketball"),
}
FOOTBALL_NAMES = {
    "COL": "Liga BetPlay", "E0": "Premier League", "E1": "Championship", "SP1": "LaLiga", "SP2": "LaLiga 2",
    "I1": "Serie A", "I2": "Serie B", "D1": "Bundesliga", "D2": "2. Bundesliga", "F1": "Ligue 1", "F2": "Ligue 2",
    "N1": "Eredivisie", "P1": "Primeira Liga", "B1": "Pro League", "T1": "Süper Lig", "SC0": "Premiership",
    "G1": "Super League Grecia", "ARG": "Liga Argentina", "BRA": "Brasileirão", "MEX": "Liga MX", "USA": "MLS",
    "JPN": "J1 League", "UCL": "Champions League", "UEL": "Europa League", "UECL": "Conference League",
    "LIB": "Copa Libertadores", "SUD": "Copa Sudamericana", "AUT": "Bundesliga Austria", "DNK": "Superliga Dinamarca",
    "NOR": "Eliteserien", "SWE": "Allsvenskan", "SWZ": "Super League Suiza", "POL": "Ekstraklasa",
}
ESPORTS = {"valorant": ("VAL", "Valorant"), "dota2": ("DOTA2", "Dota 2")}   # game → (league code, name)
ES_LEAGUE = {code: (game, name) for game, (code, name) in ESPORTS.items()}
NOISE = {"fc", "cf", "sc", "ac", "cd", "club", "deportivo", "deportes", "atletico", "atlético", "de", "la", "el",
         "the", "afc", "sk", "fk", "rj", "real", "sporting", "independiente", "united", "city"}


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def short_code(name: str, sport: str) -> str:
    """3-letter tag: last word for US teams ("New York Knicks" → KNI), main word for football ("Deportivo Cali" → CAL)."""
    words = [w for w in re.split(r"[\s\-\.]+", name) if w]
    if sport != "football":
        pick = words[-1]
    else:
        pick = next((w for w in words if slug(w) not in NOISE), words[0])
    return unicodedata.normalize("NFKD", pick).encode("ascii", "ignore").decode().upper()[:3]


def ms(iso: str | None) -> int | None:
    if not iso:
        return None
    try:
        return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000)
    except ValueError:
        return None


def pt(x: Any) -> float | None:
    """SQPC stores probabilities either as a number or as {point, ci90, ...}."""
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, dict) and isinstance(x.get("point"), (int, float)):
        return float(x["point"])
    return None


def ci(x: Any) -> list[float] | None:
    if isinstance(x, dict) and isinstance(x.get("ci90"), list) and len(x["ci90"]) == 2:
        return [max(0.0, min(1.0, float(v))) for v in x["ci90"]]
    return None


def clamp(p: float) -> float:
    return max(0.0, min(1.0, p))


def market(key: str, label: str, x: Any, group: str | None = None) -> dict | None:
    p = pt(x)
    if p is None:
        return None
    row = {"key": key[:40], "label": label[:60], "p": clamp(p)}
    if group:
        row["group"] = group[:30]
    if ci(x):
        row["interval"] = ci(x)
    return row


def main_line(lines: dict, side: str) -> tuple[str, dict] | None:
    """The line whose probability is closest to 50% (the one the market would quote)."""
    best = None
    for line, v in (lines or {}).items():
        p = pt(v.get(side)) if isinstance(v, dict) else None
        if p is not None and (best is None or abs(p - 0.5) < abs(pt(best[1][side]) - 0.5)):
            best = (line, v)
    return best


PICK_MIN = 0.75


def sqpc_picks(d: dict) -> list[dict]:
    """SQPC's own ranked selections at ≥75% (players, goals, half-time, corners…), best first."""
    out = []
    for pk in d.get("picks") or []:
        p = pk.get("p")
        if not isinstance(p, (int, float)) or not (PICK_MIN <= p < 0.995):
            continue
        row = {"group": str(pk.get("group") or "Otros")[:30], "market": str(pk.get("market") or "")[:80],
               "selection": str(pk.get("selection") or "")[:100], "p": clamp(p)}
        for k in ("lo", "hi"):
            if isinstance(pk.get(k), (int, float)):
                row[k] = clamp(pk[k])
        if isinstance(pk.get("price"), (int, float)) and pk["price"] > 1:
            row["price"] = float(pk["price"])
            if pk.get("book"):
                row["book"] = str(pk["book"])[:40]
            if isinstance(pk.get("ev"), (int, float)):
                row["ev"] = float(pk["ev"])
        if pk.get("grade"):
            row["grade"] = str(pk["grade"])[:20]
        out.append(row)
    out.sort(key=lambda r: -r["p"])
    return out[:80]


# ---------- per-sport converters ----------

PLAYER_EXP = ("goals", "assists", "shots", "sot", "fouls", "fouled", "yellow", "offsides", "saves")
PLAYER_PROBS = ("goal2", "shots1", "shots2", "shots3", "sot1", "sot2", "fouls1", "fouls2", "fouled1", "card", "offside1",
                "saves2", "saves3", "saves4")
SEASON_KEYS = ("apps", "starts", "minutes", "goals", "assists", "shots", "sot", "fouls", "fouled", "yellow", "offsides", "saves")
VS_KEYS = ("minutes", "goals", "assists", "shots", "sot", "fouls", "yellow")


def _num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def football_players(d: dict, side: str, limit: int = 22) -> list[dict]:
    """Everyone likely to play (≥30%), most minutes first, with every per-player number SQPC computed."""
    rows = [p for p in (d.get("players") or {}).get(side, []) if (p.get("p_play") or 0) >= 0.3 and isinstance(p.get("p"), dict)]
    rows.sort(key=lambda p: (p.get("exp_minutes") or 0, p["p"].get("goal") or 0), reverse=True)
    out = []
    for p in rows[:limit]:
        pr, ex = p["p"], p.get("expected") or {}
        r: dict[str, Any] = {"name": str(p.get("player", ""))[:80], "side": side}
        if p.get("pos"):
            r["role"] = str(p["pos"])[:30]
        for src, dst in (("p_start", "pStart"), ("p_play", "pPlay")):
            if _num(p.get(src)):
                r[dst] = round(clamp(p[src]), 3)
        if _num(p.get("exp_minutes")):
            r["expectedMinutes"] = round(min(120.0, max(0.0, p["exp_minutes"])), 1)
        if _num(pr.get("goal")):
            r["pScore"] = round(clamp(pr["goal"]), 4)
        if _num(pr.get("assist")):
            r["pAssist"] = round(clamp(pr["assist"]), 4)
        exp = {k: round(min(1000.0, max(0.0, ex[k])), 3) for k in PLAYER_EXP if _num(ex.get(k))}
        if exp:
            r["exp"] = exp
        probs = {k: round(clamp(pr[k]), 4) for k in PLAYER_PROBS if _num(pr.get(k))}
        if probs:
            r["probs"] = probs
        ss = p.get("season") or {}
        season = {k: int(ss[k]) for k in SEASON_KEYS if _num(ss.get(k)) and ss[k] >= 0}
        if season:
            r["season"] = season
        vs = p.get("vs_opp") or {}
        if _num(vs.get("games")) and vs["games"] > 0:
            tot = vs.get("totals") or {}
            v: dict[str, Any] = {"games": int(vs["games"])}
            if _num(vs.get("minutes")):
                v["minutes"] = int(vs["minutes"])
            t = {k: int(tot[k]) for k in VS_KEYS if _num(tot.get(k)) and tot[k] >= 0}
            if t:
                v["totals"] = t
            recent = []
            for g in sorted(vs.get("games_list") or [], key=lambda g: str(g.get("date", "")), reverse=True)[:5]:
                row: dict[str, Any] = {"date": str(g.get("date", ""))[:10]}
                if g.get("comp"):
                    row["comp"] = str(g["comp"])[:20]
                if _num(g.get("starter")):
                    row["starter"] = bool(g["starter"])
                row.update({k: int(g[k]) for k in VS_KEYS if _num(g.get(k)) and g[k] >= 0})
                recent.append(row)
            if recent:
                v["recent"] = recent
            r["vsOpp"] = v
        out.append(r)
    return out


def football(d: dict, generated: int) -> tuple[dict, dict] | None:
    m = d["match"]
    mk = d.get("markets", {})
    one = mk.get("1x2", {})
    h, x, a = pt(one.get("home")), pt(one.get("draw")), pt(one.get("away"))
    if None in (h, x, a):
        return None
    outcome: dict[str, Any] = {"home": clamp(h), "draw": clamp(x), "away": clamp(a)}
    if ci(one.get("home")) and ci(one.get("draw")) and ci(one.get("away")):
        outcome["interval"] = {"home": ci(one["home"]), "draw": ci(one["draw"]), "away": ci(one["away"])}

    H, A = m["home"], m["away"]
    ex = mk.get("extra", {})
    markets = []
    add = lambda *r: markets.append(market(*r))  # noqa: E731
    dc = ex.get("double_chance", {})
    add("dc_1x", "Doble oportunidad 1X", dc.get("1X"), "Resultado")
    add("dc_x2", "Doble oportunidad X2", dc.get("X2"), "Resultado")
    add("dc_12", "Doble oportunidad 12", dc.get("12"), "Resultado")
    dnb = ex.get("draw_no_bet", {})
    add("dnb_home", f"{H} (empate no apuesta)", dnb.get("home"), "Resultado")
    add("dnb_away", f"{A} (empate no apuesta)", dnb.get("away"), "Resultado")
    mg = ex.get("margin", {})
    for k, lab in (("home_1", f"{H} gana por 1"), ("home_2", f"{H} gana por 2"), ("home_3+", f"{H} gana por 3+"),
                   ("away_1", f"{A} gana por 1"), ("away_2", f"{A} gana por 2"), ("away_3+", f"{A} gana por 3+")):
        add(f"margin_{k.replace('+', 'p')}", lab, mg.get(k), "Margen")
    add("btts_yes", "Ambos marcan", mk.get("btts", {}).get("yes"), "Goles")
    for line in ("0.5", "1.5", "2.5", "3.5", "4.5"):
        add(f"over_{line.replace('.', '_')}", f"Más de {line} goles", mk.get("totals", {}).get(line, {}).get("over"), "Goles")
    for side, name in (("home", H), ("away", A)):
        for line in ("0.5", "1.5", "2.5"):
            add(f"tt_{side}_over_{line.replace('.', '_')}", f"{name}: más de {line} goles", (ex.get("team_totals", {}).get(side) or {}).get(line), "Goles por equipo")
    cs = ex.get("clean_sheet", {})
    add("cs_home", f"{H} no recibe gol", cs.get("home"), "Goles por equipo")
    add("cs_away", f"{A} no recibe gol", cs.get("away"), "Goles por equipo")
    for k, v in sorted((ex.get("exact_total") or {}).items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 99)[:7]:
        add(f"exact_total_{k}", f"Exactamente {k} gol{'es' if k != '1' else ''}", v, "Total exacto")
    ah = mk.get("asian_handicap_home") or {}
    for line in ("-1.50", "-0.50", "+0.50", "+1.50", "-1.5", "-0.5", "+0.5", "+1.5", "0.50", "1.50"):
        row = ah.get(line)
        if isinstance(row, dict) and pt(row.get("win")) is not None:
            add(f"ah_home_{line.replace('.', '_').replace('+', 'p').replace('-', 'm')}", f"Hándicap {H} {line.rstrip('0').rstrip('.') if '.' in line else line}", row["win"], "Hándicap")
    names = {"btts_over2.5": "Ambos marcan y más de 2.5", "btts_home": f"Ambos marcan y gana {H}", "btts_away": f"Ambos marcan y gana {A}",
             "btts_draw": "Ambos marcan y empate", "home_over1.5": f"Gana {H} y más de 1.5", "away_over1.5": f"Gana {A} y más de 1.5",
             "home_under3.5": f"Gana {H} y menos de 3.5", "away_under3.5": f"Gana {A} y menos de 3.5"}
    for k, v in (ex.get("combos") or {}).items():
        add(f"combo_{k}".replace(".", "_"), names.get(k, k.replace("_", " ")), v, "Combinadas")
    fh = mk.get("first_half") or ex.get("first_half") or {}
    for k, v in (fh.items() if isinstance(fh, dict) else []):
        if pt(v) is not None:
            add(f"ht_{k}".replace(".", "_"), f"1er tiempo: {k}", v, "Medio tiempo")
    for key, act in (d.get("actions") or {}).items():
        best = main_line(act.get("total_lines") or {}, "over")
        if best:
            add(f"{key}_over_{best[0].replace('.', '_')}", f"{act.get('label', key)}: más de {best[0]}", best[1]["over"], act.get("label", key))
    markets = [r for r in markets if r][:120]

    features = []
    comp = d.get("comparison") or {}
    hf, af = (comp.get("home") or {}).get("for", {}), (comp.get("away") or {}).get("for", {})
    ha, aa = (comp.get("home") or {}).get("against", {}), (comp.get("away") or {}).get("against", {})
    for label, src_h, src_a, key, better in (
        ("Goles a favor (últ. 10)", hf, af, "gf", "higher"),
        ("Goles en contra (últ. 10)", hf, af, "ga", "lower"),
        ("Remates", hf, af, "shots", "higher"),
        ("Remates al arco", hf, af, "sot", "higher"),
        ("Remates al arco recibidos", ha, aa, "sot", "lower"),
        ("Córners", hf, af, "corners", "higher"),
        ("Posesión %", hf, af, "possession", "higher"),
        ("Tarjetas", hf, af, "cards", "lower"),
        ("Precisión de pase %", hf, af, "pass_pct", "higher"),
        ("Entradas", hf, af, "tackles", "higher"),
        ("Faltas cometidas", hf, af, "fouls", "lower"),
        ("Fueras de juego", hf, af, "offsides", None),
        ("Atajadas", hf, af, "saves", "higher"),
        ("Remates recibidos", ha, aa, "shots", "lower"),
        ("Córners concedidos", ha, aa, "corners", "lower"),
    ):
        if isinstance(src_h.get(key), (int, float)) and isinstance(src_a.get(key), (int, float)):
            hv, av = src_h[key], src_a[key]
            if key == "pass_pct" and hv <= 1 and av <= 1:  # SQPC stores it as a fraction
                hv, av = hv * 100, av * 100
            row = {"label": label, "home": round(hv, 2), "away": round(av, 2)}
            if better:
                row["better"] = better
            features.append(row)
    if comp.get("home", {}).get("form") and comp.get("away", {}).get("form"):
        features.append({"label": "Forma (V/E/D)", "home": comp["home"]["form"].replace("W", "V").replace("D", "E").replace("L", "D"),
                         "away": comp["away"]["form"].replace("W", "V").replace("D", "E").replace("L", "D")})

    players = [r for side in ("home", "away") for r in football_players(d, side)]

    edges = []
    for pk in d.get("picks") or []:
        if pk.get("price") and pk.get("book") and isinstance(pk.get("ev"), (int, float)) and pk["price"] > 1:
            edges.append({"market": str(pk.get("market", ""))[:40], "selection": str(pk.get("selection", ""))[:60],
                          "modelP": clamp(pk["p"]), "bookmaker": str(pk["book"])[:40], "odds": float(pk["price"]),
                          "ev": float(pk["ev"]), "capturedAt": generated})
    pred: dict[str, Any] = {"outcome": outcome, "features": features[:40], "markets": markets, "players": players[:60], "edges": edges[:40],
                            "lines": football_lines(d), "picks": sqpc_picks(d)}
    st = football_stakes(d.get("stakes"))
    if st:
        pred["stakes"] = st
    eg = d.get("expected_goals") or {}
    if pt(eg.get("home")) is not None and pt(eg.get("away")) is not None:
        pred["xg"] = {"home": round(pt(eg["home"]), 3), "away": round(pt(eg["away"]), 3)}
    sm = d.get("score_matrix")
    if isinstance(sm, list) and sm and all(isinstance(r, list) for r in sm):
        pred["scoreMatrix"] = [[round(clamp(float(v)), 6) for v in r[:11]] for r in sm[:11]]
    info = {"home": m["home"], "away": m["away"], "league": m["league"], "kickoff": m.get("kickoff"),
            "event": m.get("espn_event"), "slug": m.get("espn_slug"), "sport": "football"}
    return info, pred


def _f(x: Any, lo: float, hi: float) -> float | None:
    return round(min(hi, max(lo, float(x))), 4) if _num(x) else None


def football_stakes(s: Any) -> dict | None:
    """SQPC's "what each side plays for" block (models/stakes.py) in the site's shape."""
    if not isinstance(s, dict):
        return None
    out: dict[str, Any] = {}
    f = s.get("format") or {}
    if all(_num(f.get(k)) for k in ("teams", "games", "top", "zone", "releg")):
        out["format"] = {"teams": int(f["teams"]), "games": int(f["games"]), "top": int(f["top"]), "zone": int(f["zone"]),
                         "releg": int(f["releg"]), "topLabel": str(f.get("top_label") or "Título")[:40],
                         "zoneLabel": str(f.get("zone_label") or "Europa")[:40]}
    if _num(s.get("progress")):
        out["progress"] = _f(s["progress"], 0, 1)
    for side in ("home", "away"):
        x = s.get(side)
        if not isinstance(x, dict) or not all(_num(x.get(k)) for k in ("pos", "pts", "gp", "gd", "p_top", "p_zone", "p_releg")):
            continue
        out[side] = {"team": str(x.get("team") or "")[:120], "pos": max(1, int(x["pos"])), "pts": max(0, int(x["pts"])),
                     "gp": max(0, int(x["gp"])), "gd": int(max(-200, min(200, x["gd"]))),
                     "pTop": _f(x["p_top"], 0, 1), "pZone": _f(x["p_zone"], 0, 1), "pReleg": _f(x["p_releg"], 0, 1),
                     "levTop": _f(x.get("lev_top", 0), -1, 1), "levZone": _f(x.get("lev_zone", 0), -1, 1),
                     "levDown": _f(x.get("lev_dn", 0), -1, 1), "dead": bool(x.get("dead")), "need": str(x.get("need") or "")[:120]}
    mood = {}
    for side, mo in ((s.get("mood") or {}).items()):
        if side in ("home", "away") and isinstance(mo, dict) and _num(mo.get("form")):
            mood[side] = {"form": _f(mo["form"], -3, 3), "slump": bool(mo.get("slump")), "last": str(mo.get("last") or "")[:10]}
    if mood:
        out["mood"] = mood
    e = s.get("effect") or {}
    if _num(e.get("home")) and _num(e.get("away")):
        out["effect"] = {"home": _f(e["home"], 0.5, 2), "away": _f(e["away"], 0.5, 2), "applied": bool(e.get("applied"))}
    return out if (out.get("home") or out.get("away") or out.get("mood")) else None


def esports(e: dict) -> tuple[dict, dict] | None:
    """One Valorant / Dota 2 series from reports/esports_events.json (map-rating model, no bookmaker prices)."""
    game = e.get("game")
    if game not in ESPORTS or e.get("live"):
        return None
    mk, t1, t2, bo = e.get("markets") or {}, e["team1"], e["team2"], int(e.get("bo") or 3)
    w1, w2 = pt(mk.get("win1")), pt(mk.get("win2"))
    if w1 is None or w2 is None:
        return None
    markets = []
    add = lambda *r: markets.append(market(*r))  # noqa: E731
    add("series_1", f"Gana {t1}", w1, "Ganador de la serie")
    add("series_2", f"Gana {t2}", w2, "Ganador de la serie")
    if bo >= 3:
        h = mk.get("hcp") or {}
        for k, lab in (("t1_-1.5", f"{t1} −1.5 mapas"), ("t1_+1.5", f"{t1} +1.5 mapas"),
                       ("t2_-1.5", f"{t2} −1.5 mapas"), ("t2_+1.5", f"{t2} +1.5 mapas")):
            add(f"hcp_{k}".replace(".", "_").replace("-", "m").replace("+", "p"), lab, h.get(k), "Hándicap de mapas")
        T = mk.get("total") or {}
        if _num(T.get("line")):
            add("maps_over", f"Más de {T['line']:g} mapas", T.get("over"), "Total de mapas")
            add("maps_under", f"Menos de {T['line']:g} mapas", T.get("under"), "Total de mapas")
        for sc, p in sorted((mk.get("scores") or {}).items(), key=lambda kv: -(kv[1] or 0)):
            a, b = sc.split("-")
            add(f"score_{a}_{b}", f"{t1} {a}-{b} {t2}", p, "Marcador de la serie")
    if _num(mk.get("p_map")):
        add("map_1", f"{t1} gana un mapa cualquiera", mk["p_map"], "Por mapa")
    features = []
    if _num(e.get("r1")) and _num(e.get("r2")):
        features.append({"label": "Rating por mapas (Elo)", "home": round(e["r1"]), "away": round(e["r2"]), "better": "higher"})
    if _num(e.get("n1")) and _num(e.get("n2")):
        features.append({"label": "Mapas en el historial", "home": int(e["n1"]), "away": int(e["n2"]), "better": "higher"})
    lines = []
    if bo >= 3 and mk.get("scores"):
        pmf = [0.0] * (bo + 1)
        for sc, p in mk["scores"].items():
            a, b = (int(x) for x in sc.split("-"))
            if _num(p) and a + b <= bo:
                pmf[a + b] += p
        ln = pack("maps_total", "Mapas jugados", "Mapas", pmf, free=True)
        if ln:
            lines.append(ln)
    pred = {"outcome": {"home": clamp(w1), "draw": None, "away": clamp(w2)}, "features": features, "markets": [r for r in markets if r][:120],
            "lines": lines, "picks": sqpc_picks(e), "players": [], "edges": []}
    code, _ = ESPORTS[game]
    venue = " · ".join(x for x in (str(e.get("event") or ""), str(e.get("stage") or ""), f"Bo{bo}") if x)
    info = {"home": t1, "away": t2, "league": code, "kickoff": e.get("date"), "event": str(e["match_id"]), "slug": "esports",
            "sport": "esports", "game": game, "venue": venue[:120]}
    return info, pred


def us_sport(d: dict, league: str) -> tuple[dict, dict] | None:
    sport, _, slug_ = US_LEAGUES[league]
    m, mk = d["match"], d.get("markets", {})
    ml = mk.get("moneyline", {})
    h, a = pt(ml.get("home")), pt(ml.get("away"))
    if h is None or a is None:
        return None
    H, A = m["home"], m["away"]
    markets = []
    add = lambda *r: markets.append(market(*r))  # noqa: E731
    reg = mk.get("regulation") or {}
    if pt(reg.get("draw")) is not None:  # hockey 60-minute 1X2
        add("reg_home", f"Gana {H} en 60'", reg.get("home"), "Tiempo regular")
        add("reg_draw", "Empate en 60'", reg.get("draw"), "Tiempo regular")
        add("reg_away", f"Gana {A} en 60'", reg.get("away"), "Tiempo regular")
    for line, v in sorted((mk.get("spread") or {}).items(), key=lambda kv: float(kv[0]))[:9]:
        add(f"spread_home_{line}".replace(".", "_").replace("-", "m").replace("+", "p"), f"{H} {line}", (v or {}).get("home"), "Hándicap")
    for k, v in (mk.get("puck_line") or {}).items():
        side, line = (k.split("_", 1) + [""])[:2]
        add(f"pl_{k}".replace(".", "_").replace("-", "m").replace("+", "p"), f"{H if side == 'home' else A} {line}", v, "Hándicap")
    for line, v in sorted((mk.get("totals") or {}).items(), key=lambda kv: float(kv[0]))[:9]:
        add(f"total_over_{line}".replace(".", "_"), f"Más de {line}", (v or {}).get("over"), "Total")
    for side, name in (("home", H), ("away", A)):
        best = main_line((mk.get("team_totals") or {}).get(side) or {}, "over")
        if best:
            add(f"tt_{side}_over", f"{name}: más de {best[0]}", best[1]["over"], "Total por equipo")
    for k, v in (mk.get("margin") or {}).items() if isinstance(mk.get("margin"), dict) else []:
        add(f"margin_{k}".replace(" ", "_")[:40], k.replace("Local", H).replace("Visita", A), v, "Margen")
    if pt((mk.get("btts") or {}).get("yes")) is not None:
        add("btts_yes", "Ambos marcan", mk["btts"]["yes"], "Goles")
    features = []
    mod = d.get("model") or {}
    if isinstance(mod.get("mh"), (int, float)) and isinstance(mod.get("ma"), (int, float)):
        features.append({"label": "Puntos esperados", "home": round(mod["mh"], 1), "away": round(mod["ma"], 1), "better": "higher"})
    inj = m.get("injuries") or {}
    if inj:
        features.append({"label": "Lesionados reportados", "home": len(inj.get("home") or []), "away": len(inj.get("away") or []), "better": "lower"})
    lines = basketball_lines(d) if sport == "basketball" else hockey_lines(d) if sport == "hockey" else []
    pred = {"outcome": {"home": clamp(h), "draw": None, "away": clamp(a)}, "features": features, "lines": lines, "picks": sqpc_picks(d),
            "markets": [r for r in markets if r][:120], "players": [], "edges": []}
    info = {"home": m["home"], "away": m["away"], "league": league, "kickoff": m.get("kickoff"),
            "event": m.get("event_id"), "slug": slug_, "sport": sport}
    return info, pred


# ---------- batch assembly ----------

def match_id(info: dict, kickoff: int) -> str:
    """Same id SQPC's tracker gives the match (sqpc/tracker.py site_match_id)."""
    if info.get("sport") == "esports":
        return f"es-{info['event']}"
    return f"espn-{info['event']}" if info.get("event") else slug(f"{info['league']}-{kickoff}-{info['home']}-{info['away']}")


def build(reports: str, days: int, include_ncaab: bool, now_ms: int) -> tuple[dict, dict]:
    dirs = sorted(glob.glob(os.path.join(reports, "predictions", "20*")))[-days:]
    latest: dict[str, tuple[int, dict, dict]] = {}
    ep = os.path.join(reports, "esports_events.json")
    if os.path.exists(ep):
        try:
            with open(ep, encoding="utf-8") as f:
                events = json.load(f)
            generated = int(os.path.getmtime(ep) * 1000)
        except (OSError, ValueError):
            events = []
        for e in events if isinstance(events, list) else []:
            try:
                res = esports(e)
            except (KeyError, TypeError, ValueError) as err:
                print(f"  omitido e-sports {e.get('match_id')}: {err}")
                continue
            kickoff = ms(res[0]["kickoff"]) if res else None
            if res and kickoff and kickoff > now_ms:
                latest[match_id(res[0], kickoff)] = (generated, res[0] | {"kickoff_ms": kickoff}, res[1])
    for d_ in dirs:
        for path in glob.glob(os.path.join(d_, "*.json")):
            name = os.path.basename(path)
            if name in ("picks.json", "sharp_meta.json"):
                continue
            prefix = name.split("_", 1)[0]
            if prefix == "NCAAB" and not include_ncaab:
                continue
            try:
                with open(path, encoding="utf-8") as f:
                    d = json.load(f)
            except (OSError, ValueError):
                continue
            generated = ms(d.get("generated_at")) or int(os.path.getmtime(path) * 1000)
            try:
                if d.get("schema") == "sqpc.prediction.v1":
                    res = football(d, generated)
                elif prefix in US_LEAGUES:
                    res = us_sport(d, prefix)
                else:
                    res = None  # e-sports and unknown formats are not published
            except (KeyError, TypeError, ValueError) as e:
                print(f"  omitido {name}: {e}")
                continue
            if not res:
                continue
            info, pred = res
            kickoff = ms(info["kickoff"])
            if not kickoff or kickoff <= now_ms:
                continue  # the site only accepts predictions made before kickoff
            mid = match_id(info, kickoff)
            if mid not in latest or generated > latest[mid][0]:
                latest[mid] = (generated, info | {"kickoff_ms": kickoff}, pred)

    comps, teams, matches, preds, state_add = {}, {}, [], [], {}
    for mid, (generated, info, pred) in latest.items():
        sport, league = info["sport"], info["league"]
        comp_id, comp_name = competition(sport, league)
        comps[comp_id] = {"id": comp_id, "sport": sport, "name": comp_name}
        ids = []
        for side in ("home", "away"):
            # e-sports clubs field teams in several games (Team Liquid, Team Spirit…): keep them apart per game
            tid = f"esports-{info['game']}-{slug(info[side])}" if sport == "esports" else f"{sport}-{slug(info[side])}"
            teams[tid] = {"id": tid, "sport": sport, "name": info[side][:120], "shortName": short_code(info[side], sport)}
            ids.append(tid)
        match = {"id": mid, "sport": sport, "competitionId": comp_id, "homeTeamId": ids[0], "awayTeamId": ids[1],
                 "kickoffAt": info["kickoff_ms"], "status": "scheduled"}
        if info.get("venue"):
            match["venue"] = info["venue"]
        matches.append(match)
        preds.append({"matchId": mid, "modelVersion": f"sqpc-{sport}", "generatedAt": generated, **pred})
        if info.get("event") and info.get("slug"):
            state_add[mid] = {"event": str(info["event"]), "slug": info["slug"], "match": match}
    return {"competitions": list(comps.values()), "teams": list(teams.values()), "matches": matches,
            "predictions": preds}, state_add


def competition(sport: str, league: str) -> tuple[str, str]:
    if sport == "esports":
        game, name = ES_LEAGUE.get(league, (league.lower(), league))
        return f"esports-{game}", name
    name = FOOTBALL_NAMES.get(league, league) if sport == "football" else US_LEAGUES.get(league, (None, league))[1]
    return f"{sport}-{league.lower()}", str(name)


def metrics_from_analysis(reports: str) -> list[dict]:
    files = sorted(glob.glob(os.path.join(reports, "analysis_20*.json")))
    if not files:
        return []
    try:
        with open(files[-1], encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return []
    out, now = [], int(time.time() * 1000)
    for a in data if isinstance(data, list) else []:
        r = (a.get("report_model_only") or a.get("report") or {})
        one = r.get("1x2") or {}
        if not r.get("n") or not isinstance(one.get("brier"), (int, float)) or not isinstance(one.get("log_loss"), (int, float)):
            continue
        cal = [{"bin": int(b.get("bin", i)), "predicted": clamp(b["p_mean"]), "observed": clamp(b["freq"]), "n": int(b.get("n", 0))}
               for i, b in enumerate((r.get("calibration_home") or {}).get("table") or []) if "p_mean" in b and "freq" in b]
        league = a.get("league", "")
        out.append({"id": f"football-{league.lower()}-sqpc", "sport": "football", "competitionId": f"football-{league.lower()}",
                    "modelVersion": "sqpc-football", "windowStart": ms(f"{a.get('test_start')}T00:00:00+00:00") or now,
                    "windowEnd": now, "n": int(r["n"]), "brier": float(one["brier"]), "logLoss": float(one["log_loss"]),
                    "calibration": cal[:50], "generatedAt": int(os.path.getmtime(files[-1]) * 1000)})
    if out:
        # Pooled football row (weighted by n) so the public history shows all leagues together, not just one.
        n = sum(m["n"] for m in out)
        bins: dict[int, list[float]] = {}
        for m in out:
            for c in m["calibration"]:
                acc = bins.setdefault(c["bin"], [0.0, 0.0, 0.0])
                acc[0] += c["predicted"] * c["n"]; acc[1] += c["observed"] * c["n"]; acc[2] += c["n"]
        out.append({"id": "football-all-sqpc", "sport": "football", "modelVersion": "sqpc-football",
                    "windowStart": min(m["windowStart"] for m in out), "windowEnd": now, "n": n,
                    "brier": sum(m["brier"] * m["n"] for m in out) / n, "logLoss": sum(m["logLoss"] * m["n"] for m in out) / n,
                    "calibration": [{"bin": k, "predicted": v[0] / v[2], "observed": v[1] / v[2], "n": int(v[2])}
                                    for k, v in sorted(bins.items()) if v[2] > 0],
                    "generatedAt": max(m["generatedAt"] for m in out) + 1})
    return out


def espn_result(slug_: str, event: str) -> tuple[str, int, int] | None:
    url = f"https://site.api.espn.com/apis/site/v2/sports/{slug_}/summary?event={event}"
    req = urllib.request.Request(url, headers={"user-agent": "sqpc-goldglitch-sync/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.load(r)
    comp = ((d.get("header") or {}).get("competitions") or [{}])[0]
    st = ((comp.get("status") or {}).get("type") or {})
    sides = {c.get("homeAway"): c for c in comp.get("competitors") or []}
    if "home" not in sides or "away" not in sides:
        return None
    try:
        hs, as_ = int(float(sides["home"].get("score"))), int(float(sides["away"].get("score")))
    except (TypeError, ValueError):
        return None
    if st.get("completed"):
        return "finished", hs, as_
    if st.get("state") == "in":
        return "live", hs, as_
    if (st.get("name") or "").endswith("POSTPONED"):
        return "postponed", hs, as_
    return None


_ES_DB: Any = None


def esports_result(series_id: str) -> tuple[str, int, int] | None:
    """Final maps score of a series from SQPC's database (VLR.gg / OpenDota, refreshed by "Otros deportes")."""
    global _ES_DB
    if _ES_DB is None:
        try:
            from sqpc.pipeline import Config
            _ES_DB = Config(data_dir=os.path.join(HERE, "data"), reports_dir=os.path.join(HERE, "reports")).wh
        except Exception as e:
            print(f"  resultados e-sports no disponibles: {e}")
            _ES_DB = False
    if not _ES_DB:
        return None
    from sqpc.esports.predict import final_outcome
    o = final_outcome(_ES_DB, series_id)
    return ("finished", int(o["g_home"]), int(o["g_away"])) if o else None


def results(state: dict, comps: dict, teams: dict, now_ms: int, limit: int) -> list[dict]:
    """Final scores for published matches whose kickoff has passed."""
    out, checked = [], 0
    for mid, s in sorted(state.items(), key=lambda kv: kv[1]["match"]["kickoffAt"]):
        m = s["match"]
        if s.get("final") or m["kickoffAt"] > now_ms - 2 * 3600_000 or checked >= limit:
            continue
        if m["kickoffAt"] < now_ms - 10 * 86400_000:
            s["final"] = True  # give up on very old ones
            continue
        checked += 1
        try:
            r = esports_result(s["event"]) if s["slug"] == "esports" else espn_result(s["slug"], s["event"])
        except Exception as e:  # network errors: retry next run
            print(f"  resultado {mid}: {e}")
            continue
        if not r:
            continue
        status, hs, as_ = r
        out.append({**m, "status": status, "homeScore": hs, "awayScore": as_})
        if status == "finished":
            s["final"] = True
        for t in (m["homeTeamId"], m["awayTeamId"]):
            teams.setdefault(t, s.get("teams", {}).get(t))
        comps.setdefault(m["competitionId"], s.get("comp"))
    return out


def tracked_picks(reports: str, days: int, limit: int = 100_000) -> tuple[list[dict], dict]:
    """Register this run's picks (before kickoff), settle finished ones and export them for /historial."""
    import hashlib
    try:
        from sqpc import tracker
    except Exception as e:  # SQPC not importable (e.g. run from another folder): publish without tracking
        print(f"  seguimiento de picks no disponible: {e}")
        return [], {}
    data_dir = os.path.join(HERE, "data")
    stats = {}
    try:
        stats["record"] = tracker.record(reports, data_dir, days=days)
    except Exception as e:
        print(f"  seguimiento (registro): {e}")
    try:
        from sqpc.ingest import espn
        from sqpc.pipeline import Config, other_outcome
        from sqpc.mlb.ingest import final_outcome
        from sqpc.ingest.http import CachedClient
        es, cfg = espn.Espn(), Config(data_dir=data_dir, reports_dir=reports)
        cc = CachedClient(os.path.join(data_dir, "raw"))
        stats["settled"] = tracker.settle(data_dir, lambda slug_, eid: es.summary(slug_, eid),
                                          mlb_fetch=lambda pk: final_outcome(cc, pk), other_fetch=lambda lg: other_outcome(cfg, lg))
    except Exception as e:
        print(f"  seguimiento (liquidación): {e}")
    rows = tracker.TrackStore(data_dir).load()
    cutoff = int(time.time() * 1000) - 180 * 86400_000
    rows = sorted([r for r in rows if r.get("kickoff_ms", 0) >= cutoff], key=lambda r: -r.get("updated_ms", 0))[:limit]
    out = []
    for r in rows:
        st = r.get("status", "pending")
        st = "void" if st == "no_data" else st
        if st not in ("pending", "won", "lost", "void"):
            continue
        sport, league = r["sport"], r["league"]
        comp_id, name = competition(sport, league)
        row = {"id": "tp-" + hashlib.sha1(r["id"].encode()).hexdigest()[:24], "kind": r["kind"], "sport": sport,
               "competitionId": comp_id, "competitionName": str(name)[:120], "matchId": r["match_id"][:128],
               "home": r["home"][:120], "away": r["away"][:120], "kickoffAt": int(r["kickoff_ms"]),
               "group": str(r.get("group") or "Otros")[:30], "label": str(r["label"])[:140], "p": clamp(float(r["p"])),
               "status": st, "pickedAt": int(r.get("updated_ms") or r.get("created_ms")), "updatedAt": int(r.get("updated_ms") or 0)}
        for k_src, k_dst in (("lo", "lo"), ("hi", "hi")):
            if isinstance(r.get(k_src), (int, float)):
                row[k_dst] = clamp(float(r[k_src]))
        if isinstance(r.get("price"), (int, float)) and r["price"] > 1:
            row["price"] = float(r["price"])
        if isinstance(r.get("ev"), (int, float)):
            row["ev"] = float(r["ev"])
        if r.get("actual"):
            row["result"] = str(r["actual"])[:60]
        if r.get("settled_ms"):
            row["settledAt"] = int(r["settled_ms"])
        if isinstance(r.get("profit"), (int, float)):
            row["profit"] = float(r["profit"])
        out.append(row)
    return out, stats


def split_sport(batch: dict, sport: str) -> tuple[dict, dict | None]:
    """(batch without `sport`, batch with only `sport` or None). Competitions/teams follow their sport."""
    ids = {m["id"] for m in batch["matches"] if m["sport"] == sport}
    tps = [t for t in batch.get("trackedPicks", []) if t["sport"] == sport]
    if not ids and not tps:
        return batch, None
    pick = lambda rows, keep: [r for r in rows if (r["sport"] == sport) == keep]  # noqa: E731
    main_b = {**batch, "competitions": pick(batch["competitions"], False), "teams": pick(batch["teams"], False),
              "matches": pick(batch["matches"], False), "predictions": [p for p in batch["predictions"] if p["matchId"] not in ids],
              "metrics": pick(batch.get("metrics", []), False), "trackedPicks": pick(batch.get("trackedPicks", []), False)}
    side = {**batch, "batchId": str(uuid.uuid4()), "competitions": pick(batch["competitions"], True), "teams": pick(batch["teams"], True),
            "matches": pick(batch["matches"], True), "predictions": [p for p in batch["predictions"] if p["matchId"] in ids],
            "metrics": [], "trackedPicks": tps}
    return main_b, side


MAX_PART_BYTES = 1_500_000  # the site accepts up to 5 MB; smaller parts keep each request quick


TRACKED_PER_PART = 1000


def split_batch(batch: dict, limit: int = MAX_PART_BYTES) -> list[dict]:
    """Split a large batch into several, each carrying whole matches with their predictions.
    Competitions and teams travel in every part (small); metrics in the first; tracked picks in slices of 1000."""
    size = lambda x: len(json.dumps(x, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))  # noqa: E731
    tps = batch.get("trackedPicks", [])
    if size(batch) <= limit and len(tps) <= TRACKED_PER_PART:
        return [batch]
    preds: dict[str, list] = {}
    for p in batch["predictions"]:
        preds.setdefault(p["matchId"], []).append(p)
    base = {k: v for k, v in batch.items() if k not in ("matches", "predictions", "metrics", "trackedPicks", "batchId")}
    parts: list[dict] = []
    cur = {**base, "matches": [], "predictions": [], "metrics": batch.get("metrics", []), "trackedPicks": []}
    cur_size = size(cur)
    for m in batch["matches"]:
        extra = [m] + preds.pop(m["id"], [])
        add = size(extra)
        if cur["matches"] and cur_size + add > limit:
            parts.append(cur)
            cur = {**base, "matches": [], "predictions": [], "metrics": [], "trackedPicks": []}
            cur_size = size(cur)
        cur["matches"].append(m)
        cur["predictions"] += extra[1:]
        cur_size += add
    parts.append(cur)
    for i in range(0, len(tps), TRACKED_PER_PART):          # after the matches, so their kickoffs are known first
        parts.append({**base, "competitions": [], "teams": [], "matches": [], "predictions": [], "metrics": [],
                      "trackedPicks": tps[i:i + TRACKED_PER_PART]})
    for p in parts:
        p["batchId"] = str(uuid.uuid4())
    return [p for p in parts if p["matches"] or p["predictions"] or p["metrics"] or p["trackedPicks"]]


def main() -> int:
    load_env(os.path.join(HERE, ".env"))
    ap = argparse.ArgumentParser(description="Publica en easygoldglitch.com lo que SQPC ya calculó")
    ap.add_argument("--reports", default=os.path.join(HERE, "reports"))
    ap.add_argument("--days", type=int, default=3, help="carpetas de predicciones recientes a leer")
    ap.add_argument("--skip-ncaab", action="store_true", help="no publicar NCAA baloncesto (decenas de partidos al día)")
    ap.add_argument("--include-ncaab", action="store_true", help=argparse.SUPPRESS)  # compat: NCAAB is published by default
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--results-limit", type=int, default=80)
    a = ap.parse_args()

    now = int(time.time() * 1000)
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, ValueError):
        state = {}

    batch, state_add = build(a.reports, a.days, not a.skip_ncaab, now)
    comps = {c["id"]: c for c in batch["competitions"]}
    teams = {t["id"]: t for t in batch["teams"]}
    for mid, s in state_add.items():
        prev = state.get(mid, {})
        state[mid] = {**s, "final": prev.get("final", False),
                      "comp": comps[s["match"]["competitionId"]],
                      "teams": {t: teams[t] for t in (s["match"]["homeTeamId"], s["match"]["awayTeamId"])}}
    finished = results(state, comps, teams, now, a.results_limit)
    batch["matches"] += finished
    batch["competitions"] = [c for c in comps.values() if c]
    batch["teams"] = [t for t in teams.values() if t]
    batch["metrics"] = metrics_from_analysis(a.reports)
    all_tracked, tstats = tracked_picks(a.reports, a.days)
    try:
        with open(TRACKED_SENT, encoding="utf-8") as f:
            sent = json.load(f)
    except (OSError, ValueError):
        sent = {}
    fp = lambda t: f"{t['status']}|{t['p']:.6f}|{t['label']}|{t.get('result', '')}|{t.get('pickedAt')}"  # noqa: E731
    batch["trackedPicks"] = [t for t in all_tracked if sent.get(t["id"]) != fp(t)]
    tstats = {**(tstats or {}), "total": len(all_tracked), "nuevos_o_cambiados": len(batch["trackedPicks"])}
    batch["batchId"] = str(uuid.uuid4())
    batch["source"] = "sqpc"

    by_sport: dict[str, int] = {}
    for m in batch["matches"]:
        if m.get("status") == "scheduled":
            by_sport[m["sport"]] = by_sport.get(m["sport"], 0) + 1
    print(f"Lote: {len(batch['matches']) - len(finished)} próximos {by_sport} · {len(batch['predictions'])} predicciones · "
          f"{len(batch['competitions'])} competiciones · {len(finished)} resultados · {len(batch['metrics'])} métricas · "
          f"{len(batch['trackedPicks'])} picks en seguimiento {tstats or ''}")
    if a.dry_run:
        with open(LAST_BATCH, "w", encoding="utf-8") as f:
            json.dump(batch, f, ensure_ascii=False)
        print(f"(dry-run) guardado en {LAST_BATCH}")
        return 0

    url, secret = os.environ.get("GG_INGEST_URL"), os.environ.get("GG_INGEST_SECRET")
    if not url or not secret:
        print("Falta .env con GG_INGEST_URL y GG_INGEST_SECRET (Admin → Datos → Conexión con SQPC).", file=sys.stderr)
        return 2
    res: dict[str, Any] = {"ok": True}
    main_batch, side = split_sport(batch, "esports")
    parts = split_batch(main_batch)
    for i, part in enumerate(parts, 1):
        try:
            r = publish(part, url, secret)
        except RuntimeError as e:
            print(f"ERROR al publicar (parte {i}/{len(parts)}): {e}", file=sys.stderr)
            return 1
        print(f"Parte {i}/{len(parts)}: {json.dumps(r, ensure_ascii=False)}")
        if not r.get("ok"):
            res = r
            break
    # E-sports travel apart: a site without e-sports yet (deploy or migration 0009 pending) must never block the rest.
    if res.get("ok") and side:
        for part in split_batch(side):
            try:
                r = publish(part, url, secret)
                print(f"E-sports: {json.dumps(r, ensure_ascii=False)}")
            except RuntimeError as e:
                print(f"  e-sports no publicados (¿falta desplegar la web o aplicar la migración 0010?): {e}")
                break
    if res.get("ok"):
        keep = {t["id"] for t in all_tracked}
        sent = {k: v for k, v in sent.items() if k in keep}
        sent.update({t["id"]: fp(t) for t in batch["trackedPicks"]})
        with open(TRACKED_SENT, "w", encoding="utf-8") as f:
            json.dump(sent, f)
        # Keep state small: drop matches finalized more than 14 days ago.
        cutoff = now - 14 * 86400_000
        state = {k: v for k, v in state.items() if not (v.get("final") and v["match"]["kickoffAt"] < cutoff)}
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
