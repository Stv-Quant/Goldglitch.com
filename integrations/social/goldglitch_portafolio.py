"""Portafolio de combinadas: reparte TODO el monto X entre boletos de tres niveles y lo mide con simulación.

  · Seguras  (cuota 2–3):    pocas selecciones muy probables; sostienen la banca.
  · Medias   (cuota 3–10):   el término medio.
  · Profit   (cuota 10–100): acumuladas largas; casi siempre fallan, pero una sola multiplica el monto.

Cómo reparte: simula 20.000 jornadas con la probabilidad REAL de cada selección (la del modelo ajustada a su historial)
y asigna el dinero de $500 en $500 (mínimo de BetPlay) al boleto que más sube el crecimiento esperado de la banca
(E[log(resultado)], el criterio de Kelly para un portafolio). Ese criterio diversifica solo: poner todo en un boleto
deja muchas jornadas en cero, y eso es lo que más castiga.

No existe un reparto que garantice terminar con 2X: el reporte dice la probabilidad real de cada resultado.
"""
from __future__ import annotations

import html
import math
import os
import random
from datetime import datetime

import numpy as np

MIN_STAKE = 500
TIERS = (("segura", "Seguras", 2.0, 3.0), ("media", "Medias", 3.0, 10.0), ("profit", "Profit", 10.0, 100.0))
SAME_HAIRCUT = 0.85        # BetPlay prices same-match combos below the multiplied odds
SIMS = 20000
SIMS_TXT = "20.000"
MAX_TICKETS = 15           # boletos candidatos que entran al reparto (más es imposible de montar a mano)
MAX_LEGS = 12


def _tier(odds: float) -> str | None:
    for key, _, lo, hi in TIERS:
        if lo <= odds < hi or (key == "profit" and odds == hi):
            return key
    return None


def build_tickets(legs: list[dict], same_opts: list[dict], seed: int = 7) -> list[dict]:
    """Candidate tickets in the three tiers. Mixed tickets: one selection per match, drawn with weight on value
    (real probability × odds) until the target odds of the tier; same-match tickets come from combos_same."""
    rng = random.Random(seed)
    best_per_event: dict = {}
    for l in legs:                                   # several selections per match: keep the 3 best by value
        best_per_event.setdefault(l["event"], []).append(l)
    pool = [l for ls in best_per_event.values() for l in sorted(ls, key=lambda x: -x["p_real"] * x["odds"])[:3]]
    if not pool:
        return []
    w = [math.exp(6 * (l["p_real"] * l["odds"] - 1)) for l in pool]
    seen, cands = set(), []
    for x in same_opts:                              # same match (estimated odds, haircut)
        odds = x["odds"] * SAME_HAIRCUT
        t = _tier(odds)
        key = tuple(sorted(id(l) for l in x["legs"]))
        if t and key not in seen:
            seen.add(key)
            cands.append({"legs": list(x["legs"]), "odds": odds, "same": True, "tier": t})
    for _ in range(3000):
        key_t, _, lo, hi = TIERS[rng.randrange(3)]
        target = math.exp(rng.uniform(math.log(lo * 1.02), math.log(hi * 0.98)))
        order = rng.choices(range(len(pool)), weights=w, k=len(pool) * 2)
        legs_t, evs, odds = [], set(), 1.0
        for i in order:
            l = pool[i]
            if l["event"] in evs:
                continue
            if odds * l["odds"] > hi:
                continue
            legs_t.append(l)
            evs.add(l["event"])
            odds *= l["odds"]
            if odds >= target or len(legs_t) >= MAX_LEGS:
                break
        if not (lo <= odds <= hi) or not legs_t:
            continue
        key = tuple(sorted(id(l) for l in legs_t))
        if key in seen:
            continue
        seen.add(key)
        cands.append({"legs": legs_t, "odds": odds, "same": False, "tier": key_t})
    for c in cands:
        c["p_real"] = math.prod(l["p_real"] for l in c["legs"])
        c["ev"] = c["p_real"] * c["odds"] - 1
    # the best few per tier, without repeating the same selections too much
    out = []
    for key_t, _, _, _ in TIERS:
        tier = sorted((c for c in cands if c["tier"] == key_t), key=lambda c: -c["ev"])
        uses: dict = {}
        take = 0
        for c in tier:
            if take >= MAX_TICKETS // 3:
                break
            if all(uses.get(id(l), 0) < 2 for l in c["legs"]):
                out.append(c)
                take += 1
                for l in c["legs"]:
                    uses[id(l)] = uses.get(id(l), 0) + 1
    return out


def optimize(tickets: list[dict], bank: float, seed: int = 11) -> dict:
    """Spend ALL of `bank` in $500 steps, each step to the ticket that most raises E[log(result)] over simulated days."""
    legs = sorted({id(l): l for t in tickets for l in t["legs"]}.values(), key=lambda l: id(l))
    idx = {id(l): i for i, l in enumerate(legs)}
    rng = np.random.default_rng(seed)
    p = np.array([l["p_real"] for l in legs])
    won = rng.random((SIMS, len(legs))) < p                       # one simulated day per row
    pay = np.zeros((SIMS, len(tickets)))
    for j, t in enumerate(tickets):
        cols = [idx[id(l)] for l in t["legs"]]
        pay[:, j] = np.all(won[:, cols], axis=1) * t["odds"]      # what $1 on ticket j returns that day
    units = int(bank // MIN_STAKE)
    step = max(1, units // 300)                                   # at most ~300 decisions
    stake = np.zeros(len(tickets))
    W = np.zeros(SIMS)
    floor = 0.02 * bank                                           # a day at zero weighs a lot, but not infinitely
    left = units
    while left > 0:
        k = min(step, left)
        amt = k * MIN_STAKE
        score = np.log(W[:, None] + amt * pay + floor).mean(axis=0)
        j = int(np.argmax(score))
        stake[j] += amt
        W += amt * pay[:, j]
        left -= k
    rest = bank - stake.sum()                                     # under $500 that cannot go anywhere
    if rest > 0:
        j = int(np.argmax(stake))
        stake[j] += rest
        W += rest * pay[:, j]
    for t, s in zip(tickets, stake):
        t["stake"] = float(s)
    return {"W": W, "bank": bank, "stake": stake}


def summary(res: dict) -> dict:
    W, X = res["W"], res["bank"]
    return {"mean": float(W.mean()), "median": float(np.median(W)), "p10": float(np.percentile(W, 10)),
            "p90": float(np.percentile(W, 90)), "p_gain": float((W > X).mean()), "p_2x": float((W >= 2 * X).mean()),
            "p_zero": float((W < 1).mean()), "p_half": float((W >= 0.5 * X).mean())}


def money(v: float) -> str:
    return "$" + f"{v:,.0f}".replace(",", ".")


def when(ms: float) -> str:
    from datetime import timezone, timedelta
    d = datetime.fromtimestamp(ms / 1000, timezone(timedelta(hours=-5)))
    return f"{('lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom')[d.weekday()]} {d:%d · %H:%M}"


def report(tickets: list[dict], res: dict, outdir: str, info: dict) -> str:
    s = summary(res)
    X = res["bank"]
    used = [t for t in tickets if t.get("stake", 0) > 0]
    by_tier = {k: sum(t["stake"] for t in used if t["tier"] == k) for k, _, _, _ in TIERS}
    cards = []
    for key, name, lo, hi in TIERS:
        ts = sorted((t for t in used if t["tier"] == key), key=lambda t: -t["stake"])
        if not ts:
            continue
        rows = []
        for t in ts:
            legs = "".join(f"<li>{html.escape(l['home'])} vs {html.escape(l['away'])} <span>({when(l['kickoffAt'])})</span> — "
                           f"<b>{html.escape(l['label'])}</b> @ {l['odds']:.2f} <span>· real {l['p_real'] * 100:.0f}%</span></li>"
                           for l in t["legs"])
            note = " <span>(mismo partido: ármala en 'Crea tu apuesta'; cuota estimada)</span>" if t["same"] else ""
            rows.append(f"<div class=t><div class=h><b>{money(t['stake'])}</b> · cuota {t['odds']:.2f} · "
                        f"sale {t['p_real'] * 100:.1f}% de las veces · si sale: <b>{money(t['stake'] * t['odds'])}</b>{note}</div>"
                        f"<ul>{legs}</ul></div>")
        cards.append(f"<section><h2>{name} <span>cuota {lo:g}–{hi:g} · {money(by_tier[key])} "
                     f"({by_tier[key] / X * 100:.0f}%)</span></h2>{''.join(rows)}</section>")
    head = (f"<section class=sum><h2>Cómo queda {money(X)} repartido en {len(used)} boletos</h2>"
            f"<div class=g><div><b>{s['p_gain'] * 100:.0f}%</b><span>termina con más de lo que pusiste</span></div>"
            f"<div><b>{s['p_2x'] * 100:.0f}%</b><span>llega a 2X o más ({money(2 * X)})</span></div>"
            f"<div><b>{s['p_half'] * 100:.0f}%</b><span>recupera al menos la mitad</span></div>"
            f"<div><b>{s['p_zero'] * 100:.1f}%</b><span>lo pierde todo</span></div></div>"
            f"<p>Resultado típico (mediana): <b>{money(s['median'])}</b> · promedio {money(s['mean'])} · "
            f"9 de cada 10 jornadas entre {money(s['p10'])} y {money(s['p90'])}.</p>"
            f"<p class=n>Ningún reparto garantiza terminar con 2X: si existiera, la casa no lo dejaría hacer. Este reparto es el que "
            f"más hace crecer la banca jornada tras jornada según las probabilidades reales (criterio de Kelly sobre "
            f"{SIMS_TXT} jornadas simuladas). Las seguras sostienen el monto; las de profit son las que pueden multiplicarlo. "
            f"Probabilidades del modelo ajustadas a su historial ({html.escape(info.get('hit', ''))}); las cuotas cambian: "
            f"confírmalas en BetPlay antes de apostar.</p></section>")
    page = f"""<!doctype html><html lang=es><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Portafolio de combinadas</title><style>
:root{{--bg:#0a0907;--ink:#ede6d6;--mid:#a59f90;--gold:#d4af37;--line:rgba(237,230,214,.14)}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,Segoe UI,sans-serif;padding:24px 16px}}
main{{max-width:920px;margin:auto}}h1{{font-size:26px;margin:0 0 6px}}h2{{font-size:19px;margin:0 0 12px}}h2 span{{color:var(--mid);font-weight:400;font-size:14px}}
section{{border:1px solid var(--line);border-radius:14px;padding:18px;margin:18px 0}}.g{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px}}
.g div{{border:1px solid var(--line);border-radius:10px;padding:12px}}.g b{{font-size:28px;color:var(--gold);display:block}}.g span,.n,li span,.h span{{color:var(--mid);font-size:13px}}
.t{{border-top:1px solid var(--line);padding:10px 0}}.t:first-of-type{{border-top:0}}ul{{margin:6px 0 0;padding-left:18px}}li{{margin:2px 0}}</style>
<main><h1>Portafolio de combinadas</h1><p class=n>{datetime.now().strftime('%d/%m/%Y %H:%M')} · picks de {info.get('min_p', .8) * 100:.0f}%+ ·
cuotas públicas de BetPlay · mínimo {money(MIN_STAKE)} por boleto</p>{head}{''.join(cards)}</main></html>"""
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f"portafolio_{datetime.now().strftime('%Y%m%d_%H%M')}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    return path


def run(legs: list[dict], same_opts: list[dict], bank: float, outdir: str, info: dict) -> str | None:
    tickets = build_tickets(legs, same_opts)
    if not tickets or bank < MIN_STAKE:
        return None
    res = optimize(tickets, bank)
    s = summary(res)
    used = [t for t in tickets if t.get("stake", 0) > 0]
    print(f"\nPortafolio: {money(bank)} en {len(used)} boletos · " +
          " · ".join(f"{name.lower()} {money(sum(t['stake'] for t in used if t['tier'] == k))}" for k, name, _, _ in TIERS))
    print(f"  termina con más de lo que pusiste: {s['p_gain'] * 100:.0f}% · llega a 2X: {s['p_2x'] * 100:.0f}% · "
          f"pierde todo: {s['p_zero'] * 100:.1f}% · mediana {money(s['median'])}")
    return report(tickets, res, outdir, info)
