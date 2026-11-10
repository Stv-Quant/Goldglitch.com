"""
SQPC → Goldglitch sync.

Reads what SQPC already wrote to disk and publishes it to easygoldglitch.com:
  reports/predictions/<fecha>/*.json   → partidos + predicciones (fútbol, NBA, NHL, MLB)
  reports/analysis_<fecha>.json        → métricas de validación fuera de muestra (historial público)
  ESPN (gratis)                        → marcador final de los partidos ya publicados

Nothing is recalculated here: SQPC's numbers are sent as-is. Run from the SQPC folder:
    python goldglitch_sync.py            # publica
    python goldglitch_sync.py --dry-run  # arma el lote y lo guarda en goldglitch_last_batch.json sin enviarlo
Needs .env with GG_INGEST_URL and GG_INGEST_SECRET (Admin → Datos → Conexión con SQPC).
"""
from __future__ import annotations

import argparse
import glob
import json
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
from goldglitch_lines import basketball_lines, football_lines, hockey_lines  # noqa: E402

STATE_FILE = os.path.join(HERE, "goldglitch_state.json")
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
SKIP_PREFIXES = {"NCAAB"}  # dozens of games a day; enable with --include-ncaab
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


def market(key: str, label: str, x: Any) -> dict | None:
    p = pt(x)
    if p is None:
        return None
    row = {"key": key[:40], "label": label[:60], "p": clamp(p)}
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


# ---------- per-sport converters ----------

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

    markets = [market("btts_yes", "Ambos marcan", mk.get("btts", {}).get("yes"))]
    for line in ("1.5", "2.5", "3.5"):
        markets.append(market(f"over_{line.replace('.', '_')}", f"Más de {line} goles", mk.get("totals", {}).get(line, {}).get("over")))
    dc = mk.get("extra", {}).get("double_chance", {})
    for k, label in (("1X", "Doble oportunidad 1X"), ("X2", "Doble oportunidad X2"), ("12", "Doble oportunidad 12")):
        markets.append(market(f"dc_{k.lower()}", label, dc.get(k)))
    for key, act in (d.get("actions") or {}).items():
        best = main_line(act.get("total_lines") or {}, "over")
        if best:
            markets.append(market(f"{key}_over_{best[0].replace('.', '_')}", f"{act.get('label', key)}: más de {best[0]}", best[1]["over"]))
    markets = [r for r in markets if r][:40]

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
    ):
        if isinstance(src_h.get(key), (int, float)) and isinstance(src_a.get(key), (int, float)):
            features.append({"label": label, "home": round(src_h[key], 2), "away": round(src_a[key], 2), "better": better})
    if comp.get("home", {}).get("form") and comp.get("away", {}).get("form"):
        features.append({"label": "Forma (V/E/D)", "home": comp["home"]["form"].replace("W", "V").replace("D", "E").replace("L", "D"),
                         "away": comp["away"]["form"].replace("W", "V").replace("D", "E").replace("L", "D")})

    players = []
    for side in ("home", "away"):
        rows = [p for p in (d.get("players") or {}).get(side, []) if (p.get("p_play") or 0) >= 0.3 and isinstance(p.get("p"), dict)]
        rows.sort(key=lambda p: p["p"].get("goal") or 0, reverse=True)
        for p in rows[:8]:
            r = {"name": str(p.get("player", ""))[:80], "side": side}
            if p.get("pos"):
                r["role"] = str(p["pos"])[:30]
            if isinstance(p.get("exp_minutes"), (int, float)):
                r["expectedMinutes"] = round(min(120.0, max(0.0, p["exp_minutes"])), 1)
            if isinstance(p["p"].get("goal"), (int, float)):
                r["pScore"] = clamp(p["p"]["goal"])
            if isinstance(p["p"].get("assist"), (int, float)):
                r["pAssist"] = clamp(p["p"]["assist"])
            players.append(r)

    edges = []
    for pk in d.get("picks") or []:
        if pk.get("price") and pk.get("book") and isinstance(pk.get("ev"), (int, float)) and pk["price"] > 1:
            edges.append({"market": str(pk.get("market", ""))[:40], "selection": str(pk.get("selection", ""))[:60],
                          "modelP": clamp(pk["p"]), "bookmaker": str(pk["book"])[:40], "odds": float(pk["price"]),
                          "ev": float(pk["ev"]), "capturedAt": generated})
    pred: dict[str, Any] = {"outcome": outcome, "features": features[:40], "markets": markets, "players": players[:60], "edges": edges[:40],
                            "lines": football_lines(d)}
    eg = d.get("expected_goals") or {}
    if pt(eg.get("home")) is not None and pt(eg.get("away")) is not None:
        pred["xg"] = {"home": round(pt(eg["home"]), 3), "away": round(pt(eg["away"]), 3)}
    sm = d.get("score_matrix")
    if isinstance(sm, list) and sm and all(isinstance(r, list) for r in sm):
        pred["scoreMatrix"] = [[round(clamp(float(v)), 6) for v in r[:11]] for r in sm[:11]]
    info = {"home": m["home"], "away": m["away"], "league": m["league"], "kickoff": m.get("kickoff"),
            "event": m.get("espn_event"), "slug": m.get("espn_slug"), "sport": "football"}
    return info, pred


def us_sport(d: dict, league: str) -> tuple[dict, dict] | None:
    sport, _, slug_ = US_LEAGUES[league]
    m, mk = d["match"], d.get("markets", {})
    ml = mk.get("moneyline", {})
    h, a = pt(ml.get("home")), pt(ml.get("away"))
    if h is None or a is None:
        return None
    markets = []
    reg = mk.get("regulation") or {}
    if pt(reg.get("draw")) is not None:  # hockey 60-minute 1X2
        markets += [market("reg_home", "Gana local en 60'", reg.get("home")), market("reg_draw", "Empate en 60'", reg.get("draw")),
                    market("reg_away", "Gana visitante en 60'", reg.get("away"))]
    best = main_line(mk.get("spread") or {}, "home")
    if best:
        markets.append(market("spread_home", f"Local cubre {best[0]}", best[1]["home"]))
    for k, v in (mk.get("puck_line") or {}).items():
        if k in ("home_-1.5", "away_-1.5"):
            markets.append(market(f"pl_{k.split('_')[0]}", f"{'Local' if k.startswith('home') else 'Visitante'} -1.5", v))
    best = main_line(mk.get("totals") or {}, "over")
    if best:
        markets.append(market("total_over", f"Más de {best[0]}", best[1]["over"]))
    features = []
    mod = d.get("model") or {}
    if isinstance(mod.get("mh"), (int, float)) and isinstance(mod.get("ma"), (int, float)):
        features.append({"label": "Puntos esperados", "home": round(mod["mh"], 1), "away": round(mod["ma"], 1), "better": "higher"})
    inj = m.get("injuries") or {}
    if inj:
        features.append({"label": "Lesionados reportados", "home": len(inj.get("home") or []), "away": len(inj.get("away") or []), "better": "lower"})
    lines = basketball_lines(d) if sport == "basketball" else hockey_lines(d) if sport == "hockey" else []
    pred = {"outcome": {"home": clamp(h), "draw": None, "away": clamp(a)}, "features": features, "lines": lines,
            "markets": [r for r in markets if r][:40], "players": [], "edges": []}
    info = {"home": m["home"], "away": m["away"], "league": league, "kickoff": m.get("kickoff"),
            "event": m.get("event_id"), "slug": slug_, "sport": sport}
    return info, pred


# ---------- batch assembly ----------

def build(reports: str, days: int, include_ncaab: bool, now_ms: int) -> tuple[dict, dict]:
    dirs = sorted(glob.glob(os.path.join(reports, "predictions", "20*")))[-days:]
    latest: dict[str, tuple[int, dict, dict]] = {}
    for d_ in dirs:
        for path in glob.glob(os.path.join(d_, "*.json")):
            name = os.path.basename(path)
            if name in ("picks.json", "sharp_meta.json"):
                continue
            prefix = name.split("_", 1)[0]
            if prefix in SKIP_PREFIXES and not include_ncaab:
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
            mid = f"espn-{info['event']}" if info.get("event") else slug(f"{info['league']}-{kickoff}-{info['home']}-{info['away']}")
            if mid not in latest or generated > latest[mid][0]:
                latest[mid] = (generated, info | {"kickoff_ms": kickoff}, pred)

    comps, teams, matches, preds, state_add = {}, {}, [], [], {}
    for mid, (generated, info, pred) in latest.items():
        sport, league = info["sport"], info["league"]
        comp_id = f"{sport}-{league.lower()}"
        comps[comp_id] = {"id": comp_id, "sport": sport,
                          "name": FOOTBALL_NAMES.get(league, league) if sport == "football" else US_LEAGUES[league][1]}
        ids = []
        for side in ("home", "away"):
            tid = f"{sport}-{slug(info[side])}"
            teams[tid] = {"id": tid, "sport": sport, "name": info[side][:120], "shortName": short_code(info[side], sport)}
            ids.append(tid)
        match = {"id": mid, "sport": sport, "competitionId": comp_id, "homeTeamId": ids[0], "awayTeamId": ids[1],
                 "kickoffAt": info["kickoff_ms"], "status": "scheduled"}
        matches.append(match)
        preds.append({"matchId": mid, "modelVersion": f"sqpc-{sport}", "generatedAt": generated, **pred})
        if info.get("event") and info.get("slug"):
            state_add[mid] = {"event": str(info["event"]), "slug": info["slug"], "match": match}
    return {"competitions": list(comps.values()), "teams": list(teams.values()), "matches": matches,
            "predictions": preds}, state_add


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
            r = espn_result(s["slug"], s["event"])
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


def main() -> int:
    load_env(os.path.join(HERE, ".env"))
    ap = argparse.ArgumentParser(description="Publica en easygoldglitch.com lo que SQPC ya calculó")
    ap.add_argument("--reports", default=os.path.join(HERE, "reports"))
    ap.add_argument("--days", type=int, default=3, help="carpetas de predicciones recientes a leer")
    ap.add_argument("--include-ncaab", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--results-limit", type=int, default=80)
    a = ap.parse_args()

    now = int(time.time() * 1000)
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, ValueError):
        state = {}

    batch, state_add = build(a.reports, a.days, a.include_ncaab, now)
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
    batch["batchId"] = str(uuid.uuid4())
    batch["source"] = "sqpc"

    print(f"Lote: {len(batch['matches']) - len(finished)} próximos · {len(batch['predictions'])} predicciones · "
          f"{len(finished)} resultados · {len(batch['metrics'])} métricas")
    if a.dry_run:
        with open(LAST_BATCH, "w", encoding="utf-8") as f:
            json.dump(batch, f, ensure_ascii=False)
        print(f"(dry-run) guardado en {LAST_BATCH}")
        return 0

    url, secret = os.environ.get("GG_INGEST_URL"), os.environ.get("GG_INGEST_SECRET")
    if not url or not secret:
        print("Falta .env con GG_INGEST_URL y GG_INGEST_SECRET (Admin → Datos → Conexión con SQPC).", file=sys.stderr)
        return 2
    try:
        res = publish(batch, url, secret)
    except RuntimeError as e:
        print(f"ERROR al publicar: {e}", file=sys.stderr)
        return 1
    print(json.dumps(res, ensure_ascii=False))
    if res.get("ok"):
        # Keep state small: drop matches finalized more than 14 days ago.
        cutoff = now - 14 * 86400_000
        state = {k: v for k, v in state.items() if not (v.get("final") and v["match"]["kickoffAt"] < cutoff)}
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
