"""Statistics wording, not betting wording. TikTok (and Meta) flag gambling content: 'picks', 'mercados', 'over 2.5',
'+18' and 'entra o no entra' read like betting tips. The same numbers, said as football statistics, are fine.

    nice_label("Total de goles: Más de 1.5")  -> "2 o más goles en el partido"
    safe_text("Pick bloqueado · +18")         -> "Dato bloqueado"
"""
from __future__ import annotations

import re

_NOUN = {"Goles": ("gol", "goles"), "Tarjetas": ("tarjeta", "tarjetas"), "Fueras de juego": ("fuera de juego", "fueras de juego"),
         "Córners": ("córner", "córners"), "Corners": ("córner", "córners"), "Tiros de esquina": ("córner", "córners")}


def _n(word: tuple[str, str], k: int) -> str:
    return word[0] if k == 1 else word[1]


def nice_label(label: str) -> str:
    """A model market label as a plain football statistic."""
    s = str(label or "").strip()
    pre, _, post = s.partition(":")
    pre, post = pre.strip(), post.strip()
    ou = re.match(r"^(Más|Menos) de (\d+)(?:[.,]5)?$", post)
    m = re.match(r"^(Goles|Tarjetas|Fueras de juego|Córners|Corners|Tiros de esquina)( de (.+)| totales)?$", pre)
    if (m or pre == "Total de goles") and ou:
        noun = _NOUN["Goles" if pre == "Total de goles" else m.group(1)]
        team = m.group(3) if m and pre != "Total de goles" else None
        n = int(ou[2])
        if ou[1] == "Más":
            k = n + 1
            if team:
                if noun[1] == "goles" and k == 1:
                    return f"{team} marca"
                return f"{team}: al menos 1 {noun[0]}" if k == 1 else f"{team}: {k} o más {noun[1]}"
            return f"Al menos 1 {noun[0]} en el partido" if k == 1 else f"{k} o más {noun[1]} en el partido"
        if team:
            return f"{team}: {n} {_n(noun, n)} o menos" if n else f"{team} no marca" if noun[1] == "goles" else f"{team}: sin {noun[1]}"
        return f"{n} {_n(noun, n)} o menos en el partido" if n else f"Sin {noun[1]} en el partido"
    if pre == "Goles 1er tiempo" and ou:
        n = int(ou[2])
        return "Gol en el primer tiempo" if ou[1] == "Más" and n == 0 else \
            f"{n + 1} o más goles en el primer tiempo" if ou[1] == "Más" else f"{n} goles o menos en el primer tiempo"
    if pre == "Doble oportunidad":
        t = re.match(r"^(.+?) o empate", post)
        if t:
            return f"{t[1]} no pierde"
        if "(12)" in post:
            return "No hay empate"
    if pre == "Empate no acción" and post:
        return f"{post} gana (sin contar el empate)"
    if pre == "1X2":
        g = re.sub(r"^Gana\s+", "", post)
        return "Empate" if g.lower().startswith("empate") else f"Gana {g}"
    m2 = re.match(r"^(\d)\+ (remates?|remate al arco)$", pre)
    if m2 and post:
        return f"{post}: {m2[1]} o más {'remates al arco' if 'arco' in pre else 'remates'}"
    return s


BRAND_SWAPS = [   # bookmaker names, including league sponsors: never on screen, in the voice or in tags (any network)
    (r"\bLiga\s+Bet\s?[Pp]lay(\s+Dimayor)?\b", "Liga Colombiana"), (r"\bLIGA\s+BET\s?PLAY(\s+DIMAYOR)?\b", "LIGA COLOMBIANA"),
    (r"\bTorneo\s+Bet\s?[Pp]lay\b", "Torneo Colombiano"), (r"\bCopa\s+Bet\s?[Pp]lay\b", "Copa Colombia"),
    (r"\bligabetplay\b", "futbolcolombiano"), (r"\b(Bet\s?[Pp]lay|BETPLAY|betplay|Wplay|WPLAY|Rushbet|Codere|Betsson|bet365|1xbet|Stake)\b", "Colombia"),
]


def brand_clean(text: str) -> str:
    out = str(text or "")
    for pat, rep in BRAND_SWAPS:
        out = re.sub(pat, rep, out)
    return out


_SWAPS = [
    (r"\bpicks bloqueados\b", "datos bloqueados"), (r"\bPick bloqueado\b", "Dato bloqueado"), (r"\bPICK BLOQUEADO\b", "DATO BLOQUEADO"),
    (r"\bpick bloqueado\b", "dato bloqueado"), (r"\bmercado oculto\b", "dato oculto"), (r"\bel mercado\b", "el dato"),
    (r"\bmercados?\b", "datos"), (r"\bPicks\b", "Datos"), (r"\bPICKS\b", "DATOS"), (r"\bpicks\b", "datos"),
    (r"\bPick\b", "Dato"), (r"\bPICK\b", "DATO"), (r"\bpick\b", "dato"), (r"\bpronósticos\b", "predicciones"),
    (r"\bPronósticos\b", "Predicciones"), (r"\bpronóstico\b", "predicción"), (r"\bPronóstico\b", "Predicción"),
    (r"¿\s*[Ee]ntra o no entra\s*\?", "¿Se cumple o no?"), (r"\b[Ee]ntra o no entra\b", "se cumple o no"),
    (r"\bcuotas?\b", "números"), (r"\bapuestas?\b", "jugadas"), (r"\bapostar\b", "jugar"), (r"\bparlays?\b", "combinaciones"),
    (r"\b(fijas?|seguras?)\b", "fuertes"), (r"\bRASP[ÁA]\b", "EL DATO"), (r"\b[Rr]asp[áa]\b", "mirá"), (r"\s*[·|-]?\s*\+18\b", ""), (r"\+ ?18\s*·\s*", ""),
]
BAD_TAGS = re.compile(r"^(picks?|pronosticos?|pronósticos?|apuestas?|apuesta|betting|bet|bets|parlay|cuotas?|tipster|"
                      r"fijas?|stake|apuestasdeportivas|ligabetplay|betplay|wplay|rushbet|codere|bet365|1xbet|raspa|raspadita|loteria|lotería|apuestadeportiva|sportsbetting|odds)$", re.I)


def safe_text(text: str) -> str:
    """Betting words out, statistics words in (TikTok)."""
    out = brand_clean(text)
    for pat, rep in _SWAPS:
        out = re.sub(pat, rep, out)
    return re.sub(r"[ \t]{2,}", " ", out)


def safe_tags(tags: list[str]) -> list[str]:
    return [t for t in tags if not BAD_TAGS.match(str(t).lstrip("#"))]


if __name__ == "__main__":
    for x in ["Total de goles: Más de 1.5", "Total de goles: Menos de 2.5", "Goles de AS Roma: Menos de 2.5",
              "Goles de Real Madrid: Más de 0.5", "Tarjetas totales: Más de 3.5", "Fueras de juego totales: Menos de 3.5",
              "Doble oportunidad: Arsenal o empate (1X)", "Empate no acción: Napoli", "1X2: Gana Barcelona",
              "Goles 1er tiempo: Más de 0.5", "2+ remates: Lamine Yamal (Barcelona)", "Tarjetas de Napoli: Más de 0.5"]:
        print(f"{x:45s} -> {nice_label(x)}")
    print(safe_text("Pick bloqueado · +18 ¿Entra o no entra? Los picks del día, pronósticos y el mercado oculto"))
