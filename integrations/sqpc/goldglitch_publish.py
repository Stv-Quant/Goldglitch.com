"""
Goldglitch publisher for SQPC.

Pushes a batch (competitions, teams, matches, predictions, metrics) to the PWA's
POST /api/ingest, signed with HMAC-SHA256. Stdlib only, so it drops into SQPC as-is.

    from goldglitch_publish import publish
    publish(batch_dict, url="https://easygoldglitch.com/api/ingest", secret=os.environ["GG_INGEST_SECRET"])

Setup: Admin → Datos → Conexión con SQPC → "Generar clave", save the .env it shows next to this file.

CLI:
    python goldglitch_publish.py --ping                 # test the key, writes nothing
    python goldglitch_publish.py --file batch.json      # publish a batch built by SQPC
    python goldglitch_publish.py --dump demo.json --demo  # sample batch to see the format

Batch contract: next/lib/contracts.ts (ingestBatchSchema). Times are epoch milliseconds UTC.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from typing import Any


def sign(secret: str, timestamp_ms: int, raw_body: str) -> str:
    msg = f"{timestamp_ms}.{raw_body}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def publish(batch: dict[str, Any], url: str, secret: str, timeout: float = 30.0) -> dict[str, Any]:
    """Send one batch. The exact bytes signed are the bytes sent."""
    batch.setdefault("batchId", str(uuid.uuid4()))
    batch.setdefault("source", "sqpc")
    raw = json.dumps(batch, separators=(",", ":"), ensure_ascii=False)
    ts = int(time.time() * 1000)
    req = urllib.request.Request(
        url,
        data=raw.encode("utf-8"),
        method="POST",
        headers={
            "content-type": "application/json",
            "x-gg-timestamp": str(ts),
            "x-gg-signature": sign(secret, ts, raw),
            "user-agent": "sqpc-publisher/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"ingest failed HTTP {e.code}: {body[:500]}") from None


# ----------------------------------------------------------------------------- demo data

def _poisson(k: int, lam: float) -> float:
    return math.exp(-lam) * lam**k / math.factorial(k)


def _score_matrix(lh: float, la: float, n: int = 7) -> list[list[float]]:
    m = [[_poisson(h, lh) * _poisson(a, la) for a in range(n)] for h in range(n)]
    total = sum(sum(r) for r in m)
    return [[round(v / total, 5) for v in r] for r in m]


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def demo_batch(now_ms: int | None = None) -> dict[str, Any]:
    now = now_ms or int(time.time() * 1000)
    hour = 3_600_000
    comp = {"id": "col-primera-a", "sport": "football", "name": "Liga BetPlay", "country": "Colombia", "season": "2026-II"}
    comp2 = {"id": "eng-premier", "sport": "football", "name": "Premier League", "country": "Inglaterra", "season": "2026/27"}
    teams_raw = [
        ("col-amer", "América de Cali", "AME", 1.55, 0.95), ("col-depcal", "Deportivo Cali", "CAL", 1.25, 1.10),
        ("col-nal", "Atlético Nacional", "NAL", 1.70, 0.85), ("col-mill", "Millonarios", "MIL", 1.45, 1.00),
        ("col-jun", "Junior", "JUN", 1.40, 1.05), ("col-tol", "Deportes Tolima", "TOL", 1.30, 0.95),
        ("eng-ars", "Arsenal", "ARS", 2.05, 0.80), ("eng-liv", "Liverpool", "LIV", 2.15, 0.95),
        ("eng-mci", "Manchester City", "MCI", 2.10, 0.90), ("eng-che", "Chelsea", "CHE", 1.75, 1.10),
    ]
    teams = [
        {"id": i, "sport": "football", "name": n, "shortName": s, "country": "Colombia" if i.startswith("col") else "Inglaterra"}
        for i, n, s, *_ in teams_raw
    ]
    strength = {i: (att, dfn) for i, _, _, att, dfn in teams_raw}
    fixtures = [
        ("col-amer", "col-depcal", comp["id"], 2), ("col-nal", "col-mill", comp["id"], 5),
        ("col-jun", "col-tol", comp["id"], 26), ("eng-ars", "eng-liv", comp2["id"], 20),
        ("eng-mci", "eng-che", comp2["id"], 44),
    ]
    matches, preds = [], []
    for k, (h, a, cid, in_h) in enumerate(fixtures):
        mid = f"m-{h}-{a}-{now // 86_400_000}"
        matches.append({
            "id": mid, "sport": "football", "competitionId": cid, "homeTeamId": h, "awayTeamId": a,
            "kickoffAt": now + in_h * hour, "status": "scheduled",
        })
        lh = strength[h][0] * strength[a][1] * 0.62 + 0.25   # home advantage folded in
        la = strength[a][0] * strength[h][1] * 0.55
        sm = _score_matrix(lh, la)
        ph = sum(sm[i][j] for i in range(7) for j in range(7) if i > j)
        pd = sum(sm[i][i] for i in range(7))
        pa = 1 - ph - pd
        w = 0.035 + 0.01 * (k % 3)   # demo uncertainty half-width
        over = sum(sm[i][j] for i in range(7) for j in range(7) if i + j > 2)
        btts = sum(sm[i][j] for i in range(1, 7) for j in range(1, 7))
        hn, an = teams_raw[[t[0] for t in teams_raw].index(h)][1], teams_raw[[t[0] for t in teams_raw].index(a)][1]
        odds_home = round(1 / _clamp(ph + 0.03 - 0.06 * (k % 2)) * 0.95, 2)
        preds.append({
            "matchId": mid, "modelVersion": "sqpc-dc-1.4", "generatedAt": now,
            "outcome": {
                "home": round(ph, 4), "draw": round(pd, 4), "away": round(pa, 4),
                "interval": {
                    "home": [round(_clamp(ph - w), 4), round(_clamp(ph + w), 4)],
                    "draw": [round(_clamp(pd - w * 0.7), 4), round(_clamp(pd + w * 0.7), 4)],
                    "away": [round(_clamp(pa - w), 4), round(_clamp(pa + w), 4)],
                },
            },
            "features": [
                {"label": "Puntos últimos 5", "home": 9 + k % 4, "away": 7 + (k * 2) % 5, "better": "higher"},
                {"label": "Goles a favor / partido", "home": round(strength[h][0], 2), "away": round(strength[a][0], 2), "better": "higher"},
                {"label": "Goles en contra / partido", "home": round(strength[h][1], 2), "away": round(strength[a][1], 2), "better": "lower"},
                {"label": "Posesión media %", "home": 52 + k, "away": 49 - k, "better": "higher"},
                {"label": "Tiros a puerta / partido", "home": round(4.1 + k * 0.3, 1), "away": round(3.6 + k * 0.2, 1), "better": "higher"},
            ],
            "xg": {"home": round(lh, 2), "away": round(la, 2)},
            "scoreMatrix": sm,
            "markets": [
                {"key": "over_2_5", "label": "Más de 2.5 goles", "p": round(over, 4), "interval": [round(_clamp(over - 0.04), 4), round(_clamp(over + 0.04), 4)]},
                {"key": "btts_yes", "label": "Ambos marcan", "p": round(btts, 4), "interval": [round(_clamp(btts - 0.04), 4), round(_clamp(btts + 0.04), 4)]},
            ],
            "players": [
                {"name": f"Delantero {hn.split()[0]}", "side": "home", "role": "DEL", "expectedMinutes": 82, "pScore": round(_clamp(lh * 0.32), 3), "pAssist": 0.12, "xg90": round(lh * 0.38, 2)},
                {"name": f"Extremo {hn.split()[0]}", "side": "home", "role": "EXT", "expectedMinutes": 75, "pScore": round(_clamp(lh * 0.18), 3), "pAssist": 0.19, "xg90": round(lh * 0.21, 2)},
                {"name": f"Delantero {an.split()[0]}", "side": "away", "role": "DEL", "expectedMinutes": 85, "pScore": round(_clamp(la * 0.34), 3), "pAssist": 0.10, "xg90": round(la * 0.40, 2)},
            ],
            "edges": [
                {"market": "1X2", "selection": hn, "modelP": round(ph, 4), "bookmaker": "Casa A", "odds": odds_home,
                 "ev": round(ph * odds_home - 1, 4), "capturedAt": now - 20 * 60_000},
            ],
        })
    # Calibration of past predictions: well-calibrated model with sampling noise.
    calib = []
    for b in range(10):
        pred = (b + 0.5) / 10
        noise = ((b * 37) % 7 - 3) * 0.008
        calib.append({"bin": b, "predicted": round(pred, 3), "observed": round(_clamp(pred + noise), 3), "n": 40 + (b * 53) % 90})
    metrics = [{
        "id": "football-all-sqpc-dc-1.4-90d", "sport": "football", "modelVersion": "sqpc-dc-1.4",
        "windowStart": now - 90 * 86_400_000, "windowEnd": now - 86_400_000,
        "n": sum(c["n"] for c in calib), "brier": 0.198, "logLoss": 0.981, "baselineBrier": 0.222,
        "calibration": calib, "generatedAt": now,
    }]
    return {"batchId": str(uuid.uuid4()), "source": "sqpc-demo", "competitions": [comp, comp2],
            "teams": teams, "matches": matches, "predictions": preds, "metrics": metrics}


DEFAULT_URL = "https://easygoldglitch.com/api/ingest"


def load_env(path: str | None = None) -> None:
    """Read KEY=VALUE lines from a .env next to this script (or `path`) without overriding real env vars."""
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def ping_batch() -> dict[str, Any]:
    """Empty, signed batch: proves URL + key work without touching any data."""
    return {"batchId": str(uuid.uuid4()), "source": "sqpc-ping"}


def main() -> int:
    load_env()
    ap = argparse.ArgumentParser(description="Publish SQPC batches to Goldglitch")
    ap.add_argument("--url", default=os.environ.get("GG_INGEST_URL", DEFAULT_URL))
    ap.add_argument("--secret", default=os.environ.get("GG_INGEST_SECRET"))
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--file", help="JSON batch file to send")
    g.add_argument("--demo", action="store_true", help="generate a demo batch (do NOT send to production)")
    g.add_argument("--ping", action="store_true", help="send an empty signed batch to test the connection")
    ap.add_argument("--dump", help="write the batch to this path instead of sending")
    a = ap.parse_args()

    if a.ping:
        batch = ping_batch()
    elif a.demo:
        batch = demo_batch()
    else:
        with open(a.file, encoding="utf-8") as f:
            batch = json.load(f)

    if a.dump:
        with open(a.dump, "w", encoding="utf-8") as f:
            json.dump(batch, f, ensure_ascii=False, indent=2)
        print(f"wrote {a.dump}")
        return 0
    if not a.secret:
        ap.error("missing key: put GG_INGEST_SECRET in .env (generate it in Admin → Datos → Conexión con SQPC)")
    if a.demo and "easygoldglitch.com" in a.url:
        ap.error("--demo writes fake matches; refusing to send it to production")
    try:
        res = publish(batch, a.url, a.secret)
    except RuntimeError as e:
        print(f"ERROR {e}", file=sys.stderr)
        return 1
    if a.ping:
        print("OK: Goldglitch acepta la clave. Conexión lista." if res.get("ok") else res)
    else:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
