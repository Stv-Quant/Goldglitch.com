"""
Stat lines for Goldglitch: turns SQPC outputs into full distributions (P(X = k) for each integer k), so the site
can show Más/Menos for any .5 line. Every distribution is checked against the lines SQPC itself published;
if they disagree by more than MAX_ERR the stat is dropped instead of shown wrong.
"""
from __future__ import annotations

import math
from typing import Any

MAX_ERR = 0.025         # max abs gap vs SQPC's own published line probabilities
TAIL = 5e-4             # trim mass below this at each tail
R_GRID = [0.3 * (5000 / 0.3) ** (i / 59) for i in range(60)]


def nb_pmf(mean: float, r: float, kmax: int) -> list[float]:
    """Negative binomial with mean `mean` and size `r` (r → ∞ is Poisson)."""
    if mean <= 0:
        return [1.0] + [0.0] * kmax
    p = r / (r + mean)
    out = [math.exp(r * math.log(p))]
    for k in range(kmax):
        out.append(out[-1] * (k + r) / (k + 1) * (1 - p))
    return out


def normal_pmf(mean: float, sd: float, kmax: int) -> list[float]:
    cdf = lambda x: 0.5 * (1 + math.erf((x - mean) / (sd * math.sqrt(2))))  # noqa: E731
    return [cdf(k + 0.5) - cdf(k - 0.5) for k in range(kmax + 1)]


def p_over(pmf: list[float], line: float) -> float:
    return sum(p for k, p in enumerate(pmf) if k > line)


def err(pmf: list[float], lines: dict[float, float]) -> float:
    return max((abs(p_over(pmf, L) - o) for L, o in lines.items()), default=0.0)


def parse_lines(raw: dict | None, side: str = "over") -> dict[float, float]:
    out = {}
    for k, v in (raw or {}).items():
        try:
            L = float(str(k).split("_")[-1].lstrip("o"))
        except ValueError:
            continue
        val = v.get(side) if isinstance(v, dict) else v
        if isinstance(val, dict):
            val = val.get("point")
        if isinstance(val, (int, float)):
            out[L] = float(val)
    return out


def fit_nb(mean: float, lines: dict[float, float]) -> list[float] | None:
    kmax = max(12, int(mean * 4 + 12))
    best = None
    for r in R_GRID:
        pmf = nb_pmf(mean, r, kmax)
        e = err(pmf, lines) if lines else 0.0
        if best is None or e < best[0]:
            best = (e, pmf)
        if not lines:
            break
    return best[1] if best and best[0] <= MAX_ERR else None


def fit_normal(mean: float, sd: float | None, lines: dict[float, float]) -> list[float] | None:
    kmax = int(mean + 6 * (sd or mean ** 0.5) + 10)
    sds = [sd] if sd else [mean ** 0.5 * f for f in (0.5, 0.7, 1, 1.4, 2)]
    if lines and sd:
        sds = [sd * f for f in (0.8, 0.9, 1.0, 1.1, 1.2)]
    best = None
    for s in sds:
        pmf = normal_pmf(mean, s, kmax)
        e = err(pmf, lines) if lines else 0.0
        if best is None or e < best[0]:
            best = (e, pmf)
    return best[1] if best and best[0] <= MAX_ERR else None


def pack(key: str, label: str, group: str, pmf: list[float] | None, free: bool = False) -> dict[str, Any] | None:
    """Trim tails, renormalise, round. Site gets {start, pmf} with pmf[i] = P(X = start + i)."""
    if not pmf:
        return None
    total = sum(pmf)
    if total <= 0:
        return None
    pmf = [p / total for p in pmf]
    lo, hi, acc = 0, len(pmf) - 1, 0.0
    while lo < hi and acc + pmf[lo] < TAIL:
        acc += pmf[lo]; lo += 1
    acc = 0.0
    while hi > lo and acc + pmf[hi] < TAIL:
        acc += pmf[hi]; hi -= 1
    core = pmf[lo:hi + 1]
    s = sum(core)
    core = [round(p / s, 4) for p in core]
    if len(core) > 400 or len(core) < 2:
        return None
    mean = sum((lo + i) * p for i, p in enumerate(core))
    row = {"key": key[:40], "label": label[:60], "group": group[:30], "mean": round(mean, 2), "start": lo, "pmf": core}
    if free:
        row["free"] = True
    return row


# ---------------------------------------------------------------- per sport

def football_lines(d: dict) -> list[dict]:
    rows: list[dict | None] = []
    sm = d.get("score_matrix")
    if isinstance(sm, list) and sm:
        n = len(sm)
        tot = [0.0] * (2 * n - 1)
        home = [0.0] * n
        away = [0.0] * n
        for h, row in enumerate(sm):
            for a, p in enumerate(row):
                tot[h + a] += p; home[h] += p; away[a] += p
        names = d.get("match", {})
        rows += [
            pack("goals_total", "Goles en total", "Goles", tot, free=True),
            pack("goals_home", f"Goles de {names.get('home', 'local')}", "Goles", home),
            pack("goals_away", f"Goles de {names.get('away', 'visitante')}", "Goles", away),
        ]
    for key, act in (d.get("actions") or {}).items():
        label, m = act.get("label", key), d.get("match", {})
        for part, lines_key, name in (("total", "total_lines", f"{label} en total"),
                                      ("home", "home_lines", f"{label} de {m.get('home', 'local')}"),
                                      ("away", "away_lines", f"{label} de {m.get('away', 'visitante')}")):
            mean = (act.get(part) or {}).get("mean")
            if isinstance(mean, (int, float)):
                rows.append(pack(f"{key}_{part}", name, label, fit_nb(mean, parse_lines(act.get(lines_key))), free=(key == "corners" and part == "total")))
    # Players: shots and shots on target for the three most active per side.
    for side in ("home", "away"):
        ps = [p for p in (d.get("players") or {}).get(side, []) if isinstance(p.get("expected"), dict) and (p.get("p_play") or 0) >= 0.5]
        ps.sort(key=lambda p: p["expected"].get("shots") or 0, reverse=True)
        for p in ps[:3]:
            ex, pr = p["expected"], p.get("p") or {}
            for stat, lab, keys in (("shots", "remates", {0.5: "shots1", 1.5: "shots2", 2.5: "shots3"}),
                                    ("sot", "remates al arco", {0.5: "sot1", 1.5: "sot2"})):
                if isinstance(ex.get(stat), (int, float)):
                    lines = {L: pr[k] for L, k in keys.items() if isinstance(pr.get(k), (int, float))}
                    rows.append(pack(f"pl_{side}_{p.get('player_id', p.get('player'))}_{stat}"[:40],
                                     f"{p.get('player', '')}: {lab}", "Jugadores", fit_nb(ex[stat], lines)))
    return [r for r in rows if r][:80]


def basketball_lines(d: dict) -> list[dict]:
    mk, m = d.get("markets", {}), d.get("match", {})
    ex = mk.get("expected") or {}
    rows: list[dict | None] = []
    if isinstance(ex.get("total"), (int, float)):
        rows.append(pack("pts_total", "Puntos en total", "Puntos", fit_normal(ex["total"], ex.get("sd_total"), parse_lines(mk.get("totals"))), free=True))
    tt = mk.get("team_totals") or {}
    sd_team = (d.get("sim") or {}).get("sd")
    for side in ("home", "away"):
        if isinstance(ex.get(side), (int, float)):
            rows.append(pack(f"pts_{side}", f"Puntos de {m.get(side, side)}", "Puntos", fit_normal(ex[side], sd_team, parse_lines(tt.get(side)))))
    names = {"pts": "puntos", "reb": "rebotes", "ast": "asistencias", "fg3m": "triples", "pra": "puntos+rebotes+asistencias"}
    for side in ("home", "away"):
        ps = [p for p in (d.get("players") or {}).get(side, []) if isinstance(p.get("expected"), dict) and (p.get("p_play") or 0) >= 0.5]
        ps.sort(key=lambda p: p.get("minutes") or 0, reverse=True)
        for p in ps[:8]:  # the rotation: 2 × 8 players × 4 stats + 3 team lines ≤ 80
            for stat in ("pts", "reb", "ast", "fg3m"):
                mean = p["expected"].get(stat)
                if not isinstance(mean, (int, float)):
                    continue
                lines = {float(k.split("_o")[1]): v for k, v in (p.get("p") or {}).items() if k.startswith(f"{stat}_o") and isinstance(v, (int, float))}
                rows.append(pack(f"pl_{side}_{p.get('player_id')}_{stat}"[:40], f"{p.get('player', '')}: {names[stat]}", "Jugadores", fit_nb(mean, lines)))
    return [r for r in rows if r][:80]


def hockey_lines(d: dict) -> list[dict]:
    mk, m = d.get("markets", {}), d.get("match", {})
    ex = mk.get("expected") or {}
    rows: list[dict | None] = []
    if isinstance(ex.get("total"), (int, float)):
        rows.append(pack("goals_total", "Goles en total", "Goles", fit_nb(ex["total"], parse_lines(mk.get("totals"))), free=True))
    tt = mk.get("team_totals") or {}
    for side in ("home", "away"):
        if isinstance(ex.get(side), (int, float)):
            rows.append(pack(f"goals_{side}", f"Goles de {m.get(side, side)}", "Goles", fit_nb(ex[side], parse_lines(tt.get(side)))))
    return [r for r in rows if r][:80]
