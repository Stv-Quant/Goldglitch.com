"""Comité de crecimiento de Goldglitch: agentes Haiku 5.5 expertos en ventas en línea y crecimiento orgánico.

Se reúne una vez al día (antes del plan de publicaciones) y:
  1. Lee las métricas reales de la web: visitas por origen, cuentas creadas, pagos, tasas de conversión, rendimiento de
     cada enlace ?ref= (todo viene de easygoldglitch.com/api/social/metrics, nada se inventa).
  2. El Director consulta a los miembros que necesite y puede CONTRATAR nuevos especialistas (quedan en la plantilla
     para las siguientes reuniones) o despedir los que no aporten.
  3. Deja el plan de publicaciones de hoy (formato, hora, gancho, llamado a la acción, enlace con ref) que ejecutan los
     agentes de redes, guarda lo aprendido y escribe el acta (redes_comite_actas/AAAA-MM-DD.md).

Solo orgánico: sin pauta pagada. Las reglas de marca (estadística, no apuestas; sin promesas) aplican a todos.

    python goldglitch_growth.py            # reunión de hoy (si no se hizo)
    python goldglitch_growth.py --forzar   # vuelve a reunirse aunque ya lo haya hecho hoy
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime
from typing import Any

from goldglitch_social_agents import BRAND, BANNED, DISRUPT, MODEL, POST_TYPES, VIRAL

HERE = os.path.dirname(os.path.abspath(__file__))
ROSTER = os.path.join(HERE, "redes_comite.json")
PLAN = os.path.join(HERE, "redes_plan_comite.json")
DRAFT = os.path.join(HERE, "redes_borrador_comite.json")   # night extra meetings leave a draft for the morning meeting
MEMORY = os.path.join(HERE, "redes_memoria.md")
ACTAS = os.path.join(HERE, "redes_comite_actas")
MAX_MEMBERS = 10           # the company is exactly these 10 agents (no hiring)
MAX_TURNS = 30
DEPARTMENTS = {   # key: (name, head, members)
    "economia": ("Dirección Económica", "econ_crecimiento", ["econ_crecimiento", "econ_consumidor"]),
    "instagram": ("Instagram", "ig_contenido", ["ig_contenido", "ig_crecimiento"]),
    "facebook": ("Facebook", "fb_contenido", ["fb_contenido", "fb_comunidad"]),
    "tiktok": ("TikTok", "tt_contenido", ["tt_contenido", "tt_crecimiento"]),
    "youtube": ("YouTube", "yt_contenido", ["yt_contenido", "yt_busqueda"]),
}
DEPT_QUESTIONS = {
    "economia": "Con la tabla económica (embudo, países, dispositivos, páginas, botones, métricas por publicación): ¿qué "
                "decisión de asignación del inventario de hoy (formatos, redes, mercados) maximiza cuentas creadas y pagos? "
                "Explica el incentivo y el microfundamento detrás (qué gana el usuario, qué fricción lo frena, qué lo mueve), "
                "qué es dato y qué es supuesto, y un experimento con métrica y criterio.",
    "instagram": "Instagram (público joven que viene por los picks): además de los picks de la mañana y el resultado de la "
                 "noche, ¿qué piezas, ganchos, horarios y hashtags (20 a 30) hoy? Usa las métricas por publicación de Instagram.",
    "facebook": "Facebook (público más adulto): ¿qué piezas de '¿Sabías que…?', datos de partidos y noticias de fútbol reales "
                "(de los titulares de hoy, sin inventar) publicar hoy, con qué ganchos y a qué hora? Usa sus métricas.",
    "tiktok": "TikTok: ¿qué reels con tendencia del día, sonido, gancho de 1 segundo y hashtags (10) hoy? Usa sus métricas.",
    "youtube": "YouTube Shorts: ¿qué Shorts con más datos y búsqueda real (títulos con frases que la gente escribe) hoy, y "
               "cómo mejorar la retención? Usa sus métricas.",
}
SEO_BY = "ig_crecimiento"


# The company: 10 agents. Two economists (PhD) lead; two specialists per network. All on Claude Haiku 5.5, high effort.
BASE = {
    "econ_crecimiento": {"nombre": "Dr. Alejandro Restrepo", "genero": "h", "dep": "economia",
                         "rol": "Director General — PhD en economía, crecimiento económico y microfundamentos",
                         "estilo": "economista sereno y exigente, decide con datos y costo de oportunidad",
                         "perfil": "PhD en Economía (crecimiento económico) con fuertes fundamentos microeconómicos: decisiones "
                                   "de agentes, costo de oportunidad, rendimientos marginales, efectos de red y acumulación.",
                         "mision": "Dirige la empresa: asigna el inventario diario de publicaciones donde el rendimiento marginal "
                                   "(cuentas creadas y pagos por publicación) es mayor, fija metas y experimentos, y revisa cada "
                                   "semana si las decisiones acertaron con los números."},
    "econ_consumidor": {"nombre": "Dra. Carolina Vélez", "dep": "economia",
                        "rol": "Co-directora — PhD en economía del consumidor e incentivos positivos",
                        "perfil": "PhD en Economía del Comportamiento del Consumidor: incentivos positivos, recompensas, "
                                  "reciprocidad, hábito, prueba social, disposición a pagar y diseño de elección.",
                        "mision": "Explica por qué el usuario hace clic, comparte, se registra o paga, y diseña los incentivos "
                                  "positivos y éticos (valor gratis, logro, estatus, pertenencia, sorpresa) que lo mueven; nada "
                                  "de miedo, escasez falsa ni promesas de dinero."},
    "ig_contenido": {"nombre": "Valeria", "dep": "instagram", "rol": "Líder de Instagram — contenido y picks",
                     "perfil": "Estratega de contenido de Instagram para audiencias jóvenes de fútbol: carruseles de picks, reels y memes.",
                     "mision": "Instagram es la puerta de entrada del público joven que viene por los picks: cuida que cada día "
                               "abra con los picks y cierre con el resultado del modelo, y que todo entre se vea profesional."},
    "ig_crecimiento": {"nombre": "Daniela", "dep": "instagram", "rol": "Crecimiento de Instagram — hashtags, SEO y métricas",
                       "perfil": "Especialista en alcance de Instagram: hashtags, búsqueda, horarios y lectura de métricas por publicación.",
                       "mision": "Arma el banco SEO diario (hashtags y palabras clave) que usan todas las redes y dice qué "
                                 "hashtags, horarios y formatos rinden."},
    "fb_contenido": {"nombre": "Martha", "dep": "facebook", "rol": "Líder de Facebook — contenido para público adulto",
                     "perfil": "Editora de contenido deportivo para audiencias adultas: '¿Sabías que…?', datos e historias del fútbol.",
                     "mision": "En Facebook publica videos e imágenes de '¿Sabías que…?', datos de los partidos y noticias "
                               "reales del fútbol, con ganchos de curiosidad y tono cercano."},
    "fb_comunidad": {"nombre": "Jorge", "genero": "h", "dep": "facebook", "rol": "Comunidad y métricas de Facebook",
                     "perfil": "Community manager de páginas deportivas grandes; conoce cómo comenta y comparte el público adulto.",
                     "mision": "Responde a la comunidad de la página, lee sus métricas y propone qué temas generan más conversación."},
    "tt_contenido": {"nombre": "Mía", "dep": "tiktok", "rol": "Líder de TikTok — reels y tendencias",
                     "perfil": "Creadora de reels de fútbol con millones de vistas: tendencias, sonidos y ganchos de 1 segundo.",
                     "mision": "Convierte los datos del día en reels de TikTok montados en tendencias y sonidos del momento."},
    "tt_crecimiento": {"nombre": "Mateo", "genero": "h", "dep": "tiktok", "rol": "Crecimiento de TikTok — métricas y retención",
                       "perfil": "Analista de TikTok: retención, vistas completas, compartidos y hashtags.",
                       "mision": "Lee las métricas de cada video y dice qué duplicar, qué cortar y qué probar mañana."},
    "yt_contenido": {"nombre": "Laura", "dep": "youtube", "rol": "Líder de YouTube — Shorts con datos",
                     "perfil": "Productora de Shorts deportivos: guion claro, retención y datos que se entienden.",
                     "mision": "Hace que cada Short tenga más pronósticos y estadísticas, ritmo claro y un cierre que lleve a la web."},
    "yt_busqueda": {"nombre": "Andrés", "genero": "h", "dep": "youtube", "rol": "Búsqueda y métricas de YouTube",
                    "perfil": "Especialista en SEO de YouTube: títulos con búsquedas reales, descripciones y métricas de retención.",
                    "mision": "Elige títulos y descripciones con frases que la gente realmente busca y lee las métricas del canal."},
}

DIRECTOR = f"""Son la DIRECCIÓN de EGG (Goldglitch Stats), una empresa de marketing de productos digitales de 10 agentes:
el Dr. Alejandro Restrepo (PhD en crecimiento económico, fuertes microfundamentos) y la Dra. Carolina Vélez (PhD en economía
del consumidor e incentivos positivos) dirigen; debajo hay 2 especialistas por red: Instagram (Valeria y Daniela), Facebook
(Martha y Jorge), TikTok (Mía y Mateo) y YouTube (Laura y Andrés). No se contrata a nadie más.
Las decisiones son ECONÓMICAS: cada publicación es inventario escaso que se asigna donde más cuentas creadas y pagos produce
(rendimiento marginal), con incentivos positivos y éticos, datos, experimentos y revisión de si se acertó.
CITAS FIJAS EN TODAS LAS REDES (el sistema las agrega, no las planees): 07:30 estadísticas de la mañana, 14:00
estadísticas de la tarde, 19:30 reel/short de las estadísticas de la noche, 22:00 resultados y 22:45 reel/short de
resultados. Fuera de esas, CADA publicación es para UNA sola red y es distinta: "redes" lleva una sola red. Planea 8 a 10
piezas propias por red al día (32 a 40 en total: al menos 8 en Instagram, 8 en Facebook, 8 en TikTok y 8 en YouTube),
separadas al menos 45 min dentro de la misma red y de las citas fijas (redes distintas pueden coincidir). Con estadísticas reales.
En Instagram y Facebook cada publicación lleva además su HISTORIA (el sistema la hace y la sube).
AUDIENCIAS POR RED:
- Instagram: público joven que viene por los PICKS. Cada día ABRE con "picks_dia" (menos de 5 picks de los equipos más
  famosos de ligas europeas, sudamericanas y la Liga BetPlay) y CIERRA con "resultados" (cómo le fue al modelo con esos
  mismos picks). Esas dos van siempre (el sistema las garantiza) y además las piezas que decidan.
- Facebook: público más adulto: "sabias_que" (videos e imágenes de '¿Sabías que…?'), "noticia" (noticias y datos reales de
  fútbol, de los titulares del día, sin inventar) y los picks/resultados.
- TikTok: reels de tendencia, memes y picks en video.
- YouTube: Shorts con más pronósticos y estadísticas, títulos con búsquedas reales.
El mercado es todo el público hispano que necesita datos de fútbol y deportes (hinchas, comentaristas, periodistas,
profesores, analistas, fantasy y adultos +18 que apuestan, siempre con estadística y sin incitar).
Cada lunes la Dirección deja el plan económico de la semana: respétenlo y, si se apartan, justifíquenlo con datos.
En cada reunión responden los 5 equipos (Dirección económica, Instagram, Facebook, TikTok y YouTube).
Objetivo: crecimiento ORGÁNICO y viral (sin pauta pagada) que se convierta en cuentas creadas y en suscripciones Pro/Elite.
PÚBLICO INTERNACIONAL: cuando haya partidos de la NBA (o NHL), incluye al menos 1 pieza "nba" al día (mercado US/LATAM),
en español neutro; el resto, fútbol de ligas top para todo el mundo hispano.
Los HASHTAGS son fundamentales para el alcance: cada publicación lleva el banco SEO de Daniela (20 a 30 en Instagram,
10 en TikTok, 12 en YouTube), mezclando grandes, medianos y de nicho, de la liga, los equipos y el mercado; revisa cuáles
rindieron con Ricardo.
Asigna a cada publicación un "mercado" (CO, MX, US, AR, ES, CL, PE o LATAM) y un "segmento", siguiendo la asignación del
plan económico, y registra 1 a 3 "decisiones" con su razón económica, efecto esperado, métrica y fecha de revisión.

{BRAND}

Producto: plan Free (con cuenta), Pro $50.000/mes, Elite $250.000/mes. La web mide visitas por origen, cuentas y pagos.
Instagram, Facebook (página) y TikTok los publican los agentes de redes con tu plan. En Instagram y TikTok el enlace va
en la bio (ref ig_bio / tt_bio); en Facebook el enlace va en el texto con su propio ref.

{VIRAL}

{DISRUPT}
Construye SERIES con nombre fijo que se repitan cada día a la misma hora (hábito y exposición repetida), alterna formatos
y prioriza lo que genera guardados, compartidos y comentarios.

Cómo trabajas en la reunión:
1. Mira las métricas y el historial (ver_metricas, ver_historial).
2. Consulta a los especialistas que aporten (consultar). La empresa son 10 agentes fijos: no contrates ni despidas.
3. Decide el plan de HOY con definir_plan: 32 a 40 publicaciones repartidas por red (al menos 8 por red) (cada una con su "redes" de UNA red) (volumen alto: el objetivo es crecer rápido), al menos 3 de
   ellas "reel" (video vertical de ritmo rápido, el formato que más alcance orgánico da; topic "resultados" para un reel
   de resultados, si no son picks), solo equipos de ligas top, horas 07:00–23:00 separadas al menos 45 min en la misma red,
   cada una con gancho, ángulo, tema y llamado a la acción. Al menos 1 "meme" al día (idea de Valeria). Los picks no se
   repiten: un partido mostrado en picks (carrusel o reel) no vuelve a salir en 24 h (y el reel o post de resultados de la noche muestra cómo le fue a esos mismos picks), así que no pongas varias piezas
   de picks sin partidos nuevos (usa "liga" distinta, resultados, memes o educativos). Basa las decisiones en datos cuando los haya; cuando no,
   plantea experimentos medibles (por ejemplo, dos ganchos distintos en días distintos).
4. Guarda 1 a 3 aprendizajes concretos y verificables (guardar_aprendizaje).
5. Cierra con terminar y un acta breve: qué viste, qué decidiste, qué experimento corre y cómo se medirá.
6. Si algo merece salir YA (un resultado fresco, una tendencia del momento, una oportunidad que se pierde si se espera),
   pon UNA publicación con time "ahora": se publica apenas termine la reunión. Úsalo solo cuando de verdad valga la pena.
Sé eficiente: pocas consultas bien hechas. Responde siempre en español."""

TOOLS = [
    {"name": "ver_metricas", "description": "Embudo real de la web (1, 7 y 30 días), por origen y por enlace ref.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "ver_historial", "description": "Publicaciones de los últimos días (tipo, ángulo, redes, errores), datos de picks "
     "disponibles hoy y aprendizajes guardados.", "input_schema": {"type": "object", "properties": {}}},
    {"name": "ver_plantilla", "description": "Miembros actuales del comité (clave, rol, misión).",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "consultar", "description": "Pide su opinión experta a un miembro del comité. Incluye el contexto que necesite.",
     "input_schema": {"type": "object", "properties": {"miembro": {"type": "string"}, "pregunta": {"type": "string"}},
                      "required": ["miembro", "pregunta"]}},
    {"name": "contratar", "description": "Contrata un nuevo agente especialista (queda en la plantilla).",
     "input_schema": {"type": "object", "properties": {
         "clave": {"type": "string", "description": "identificador corto en minúsculas"},
         "rol": {"type": "string", "description": "Nombre — rol (ej. 'Camila — Especialista en tendencias de TikTok')"},
         "mision": {"type": "string"}}, "required": ["clave", "rol", "mision"]}},
    {"name": "despedir", "description": "Saca de la plantilla a un agente contratado (los base no se pueden despedir).",
     "input_schema": {"type": "object", "properties": {"clave": {"type": "string"}, "motivo": {"type": "string"}},
                      "required": ["clave"]}},
    {"name": "guardar_aprendizaje", "description": "Guarda un aprendizaje para próximas reuniones y para los redactores.",
     "input_schema": {"type": "object", "properties": {"texto": {"type": "string"}}, "required": ["texto"]}},
    {"name": "definir_plan", "description": "Plan de publicaciones de HOY.",
     "input_schema": {"type": "object", "properties": {"posts": {"type": "array", "items": {"type": "object", "properties": {
         "type": {"type": "string", "enum": list(POST_TYPES)},
         "time": {"type": "string", "description": "HH:MM entre 07:00 y 23:00, o \"ahora\" para publicar apenas termine la reunión (máx. 1)"},
         "liga": {"type": "string", "description": "opcional para picks_dia: liga o deporte a destacar (ej. Liga BetPlay, Premier League, NBA)"},
         "redes": {"type": "array", "items": {"type": "string", "enum": ["instagram", "facebook", "tiktok", "youtube"]},
                   "description": "redes donde sale (según el público de cada una)"},
         "meme_formato": {"type": "string", "enum": ["tweet", "nadie", "expectativa", "pov", "starter", "no_si", "noticia", "cuando", "tier", "chat", "duelo", "impopular", "reto", "giro"],
                          "description": "solo para meme"},
         "angle": {"type": "string"}, "topic": {"type": "string"},
         "hook": {"type": "string", "description": "primera línea / gancho"},
         "cta": {"type": "string", "description": "llamado a la acción"}},
         "required": ["type", "time", "angle", "hook", "cta"]}},
         "direccion_arte": {"type": "object", "description": "decisión de Martina para hoy", "properties": {
             "acento": {"type": "string", "enum": ["oro", "esmeralda", "rubi", "zafiro", "violeta", "champana"]},
             "portada": {"type": "string", "enum": ["impacto", "editorial"]},
             "ritmo": {"type": "string", "enum": ["rapido", "muy_rapido", "elegante"]}}},
         "seo": {"type": "object", "description": "banco SEO de Daniela para hoy", "properties": {
             "hashtags": {"type": "array", "items": {"type": "string"}, "description": "10 a 20 hashtags sin '#', los más importantes primero"},
             "palabras": {"type": "array", "items": {"type": "string"}, "description": "5 a 10 palabras clave de búsqueda"}}}},
         "required": ["posts"]}},
    {"name": "terminar", "description": "Cierra la reunión con el acta.",
     "input_schema": {"type": "object", "properties": {"acta": {"type": "string"}}, "required": ["acta"]}},
]


def load(path: str, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save(path: str, data) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def now_co() -> datetime:
    from datetime import timedelta, timezone
    return datetime.now(timezone(timedelta(hours=-5)))


def roster() -> dict:
    r = load(ROSTER, {})
    members = dict(BASE)              # exactly the 10 agents of the company (older hires are not loaded)
    return {"miembros": members, "historial": r.get("historial") or []}


class Committee:
    def __init__(self, api_key: str | None, signed, state: dict, facts: dict, log=print):
        self.client = None
        if api_key:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        self.signed, self.state, self.facts, self.log = signed, state, facts, log
        self.r = roster()
        self.metrics: dict | None = None
        self.plan: list[dict] | None = None
        self.learned: list[str] = []
        self.calls = 0

    # ---------------------------------------------------------------- context
    def metrics_text(self) -> str:
        if self.metrics is None:
            try:
                self.metrics = self.signed("/api/social/metrics", {})
            except Exception as e:
                self.metrics = {"error": f"no se pudieron leer las métricas: {e}"}
        return json.dumps(self.metrics, ensure_ascii=False)[:12000]

    def history_text(self) -> str:
        hist = (self.state.get("history") or [])[-30:]
        memory = open(MEMORY, encoding="utf-8").read()[-6000:] if os.path.exists(MEMORY) else ""
        f = self.facts or {}
        draft = load(DRAFT, {})
        draft = draft if draft.get("for_day") == now_co().strftime("%Y-%m-%d") else None
        return json.dumps({"hora_actual_colombia": now_co().strftime("%H:%M"),
                           "borrador_reunion_extraordinaria": draft,
                           "regla": "planea solo horas posteriores a la hora actual",
                           "tendencias_ahora": _trends(),
                           "tabla_economica": economics_table(self.metrics or {}, self.state),
                           "plan_economico_semana": load(ECON_PLAN, {}) or "todavía no hay (la Junta se reúne los lunes)",
                           "publicaciones_recientes": hist,
                           "datos_hoy": {"picks_80_proximas_36h": len(f.get("upcoming") or []),
                                         "picks_jugados_36h": len(f.get("results") or []), "historial": f.get("record")},
                           "aprendizajes": memory or "—"}, ensure_ascii=False)[:12000]

    # ---------------------------------------------------------------- members
    def ask(self, key: str, question: str) -> str:
        m = self.r["miembros"].get(key)
        if not m:
            return f"No existe el miembro '{key}'. Plantilla: {', '.join(self.r['miembros'])}"
        self.calls += 1
        system = (f"Eres {m.get('nombre', '')}, {m['rol']} en el comité de crecimiento de EGG (Goldglitch Stats). "
                  f"{m.get('perfil', '')} Tu misión: {m['mision']}\n\n{BRAND}\n\n"
                  f"Hablas con tu estilo ({m.get('estilo') or 'gomela caleña, segura, con chispa'}) pero tu trabajo es riguroso. "
                  "Responde en español, concreto y accionable (máx. 250 palabras). Basa lo que digas en las métricas "
                  "cuando existan; si no hay datos suficientes, dilo y propone un experimento medible.")
        notes = notebook(key)
        task = (f"Métricas de la web: {self.metrics_text()}\n\nContexto: {self.history_text()}\n\n"
                + (f"Tu cuaderno (lo que has aprendido): {json.dumps(notes[-10:], ensure_ascii=False)}\n\n" if notes else "")
                + f"Pregunta del Director: {question}")
        if self.client is None:
            import goldglitch_claude_cli as CLI
            out = CLI.ask_text(system, task).strip()
        else:
            msg = self.client.messages.create(model=MODEL, max_tokens=1200, system=system,
                                              messages=[{"role": "user", "content": task}])
            out = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
        self.log(f"  [{m.get('nombre') or key}] {out[:160]}")
        return out

    def ask_department(self, dep: str, question: str) -> str:
        """One call per department: the head gathers the team and answers with every member's input."""
        name, head, team = DEPARTMENTS[dep]
        members = self.r["miembros"]
        team = [k for k in team if k in members] + [k for k, v in members.items() if v.get("dep") == dep and k not in team]
        h = members[head]
        roster_txt = "\n".join(f"- {members[k].get('nombre')} — {members[k]['rol']}. {members[k].get('perfil', '')} Misión: "
                               f"{members[k]['mision']}" for k in team)
        self.calls += 1
        system = (f"Eres {h.get('nombre')}, jefe(a) del departamento de {name} de la firma de marketing de EGG (Goldglitch "
                  f"Stats). Tu equipo:\n{roster_txt}\n\n{BRAND}\n\nReúnes a tu equipo y entregas la posición del "
                  "departamento: una línea con el aporte concreto de cada persona (por nombre, en su estilo) y al final la "
                  "RECOMENDACIÓN del departamento. Riguroso y accionable, máx. 380 palabras, en español. Usa las métricas y "
                  "la tabla económica; si los datos no alcanzan, dilo y propone cómo medirlo.")
        notes = [n for k in team for n in notebook(k)[-3:]]
        task = (f"Métricas de la web: {self.metrics_text()}\n\nContexto: {self.history_text()}\n\n"
                + (f"Cuadernos del equipo: {json.dumps(notes, ensure_ascii=False)}\n\n" if notes else "")
                + f"Pregunta de la Directora: {question}")
        if self.client is None:
            import goldglitch_claude_cli as CLI
            out = CLI.ask_text(system, task).strip()
        else:
            msg = self.client.messages.create(model=MODEL, max_tokens=1600, system=system,
                                              messages=[{"role": "user", "content": task}])
            out = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
        self.log(f"  [{h.get('nombre')}] ({name}) {out[:160]}")
        return out

    def hire(self, key: str, rol: str, mision: str, dep: str = "") -> str:
        key = re.sub(r"[^a-z0-9_]", "", key.lower())[:24]
        if not key or key in BASE:
            return "Clave inválida o reservada."
        if len(self.r["miembros"]) >= MAX_MEMBERS and key not in self.r["miembros"]:
            return f"La plantilla está llena ({MAX_MEMBERS}). Despide a alguien primero."
        if BANNED.search(rol + " " + mision):
            return "Ese rol rompe las reglas de marca."
        nombre = rol.split("—")[0].strip() if "—" in rol else ""
        self.r["miembros"][key] = {"nombre": nombre[:40], "rol": rol[:120], "mision": mision[:600],
                                   "perfil": "Experto(a) de primer nivel en su especialidad, contratado(a) por la firma.",
                                   "dep": dep if dep in DEPARTMENTS else "", "desde": time.strftime("%Y-%m-%d")}
        self.r["historial"].append({"fecha": time.strftime("%Y-%m-%d"), "accion": "contratar", "clave": key, "rol": rol[:120]})
        self._save_roster()
        self.log(f"  contratado: {key} — {rol}")
        return f"Contratado '{key}'. Ya puedes consultarlo."

    def fire(self, key: str, motivo: str = "") -> str:
        if key in BASE or key not in self.r["miembros"]:
            return "No se puede despedir a ese miembro."
        self.r["miembros"].pop(key)
        self.r["historial"].append({"fecha": time.strftime("%Y-%m-%d"), "accion": "despedir", "clave": key, "motivo": motivo[:200]})
        self._save_roster()
        self.log(f"  despedido: {key}")
        return f"'{key}' salió de la plantilla."

    def _save_roster(self) -> None:
        extra = {k: v for k, v in self.r["miembros"].items() if k not in BASE}
        save(ROSTER, {"miembros": extra, "historial": self.r["historial"][-200:]})

    # ---------------------------------------------------------------- plan + memory
    def set_plan(self, posts: list[dict]) -> str:
        ok, problems, times = [], [], []
        f = self.facts or {}
        earliest = (now_co() + __import__("datetime").timedelta(minutes=10)).strftime("%H:%M")
        self.now_posts = []
        per_net: dict[str, list[int]] = {}
        for p in posts[:44]:
            t, hhmm = p.get("type"), str(p.get("time", ""))
            if hhmm.strip().lower() in ("ahora", "ya", "now"):
                text = " ".join(str(p.get(k, "")) for k in ("angle", "topic", "hook", "cta"))
                if t in POST_TYPES and not BANNED.search(text) and not self.now_posts:
                    self.now_posts.append({k: str(p.get(k, ""))[:400] for k in ("type", "angle", "topic", "hook", "cta", "liga", "meme_formato", "mercado", "segmento")})
                else:
                    problems.append(f"{t} ahora: solo 1 inmediata, de un formato válido y sin palabras prohibidas")
                continue
            if hhmm and hhmm < earliest and now_co().strftime("%Y-%m-%d") == getattr(self, "today", "") \
                    and getattr(self, "mode", "normal") != "extra_noche":
                problems.append(f"{t} {hhmm}: esa hora ya pasó (ahora son {now_co():%H:%M})")
                continue
            if t not in POST_TYPES or not re.fullmatch(r"\d{2}:\d{2}", hhmm) or not ("07:00" <= hhmm <= "23:00"):
                problems.append(f"{t} {hhmm}: tipo u hora inválidos")
                continue
            if (t == "resultados" and not f.get("results")) or (t in ("picks_dia", "reel") and not (f.get("upcoming") or f.get("results"))):
                problems.append(f"{t}: hoy no hay datos para ese formato")
                continue
            text = " ".join(str(p.get(k, "")) for k in ("angle", "topic", "hook", "cta"))
            if BANNED.search(text):
                problems.append(f"{t} {hhmm}: usa palabras prohibidas por la marca")
                continue
            m = int(hhmm[:2]) * 60 + int(hhmm[3:])
            net = _redes(p.get("redes"), t)[0]                   # one network per piece: each network has its own content
            if any(abs(m - x) < SPACING for x in per_net.get(net, [])):
                problems.append(f"{t} {hhmm}: menos de {SPACING} min de otra publicación en {net}")
                continue
            per_net.setdefault(net, []).append(m)
            times.append(m)
            p = {**p, "redes": [net]}
            ok.append({k: str(p.get(k, ""))[:400] for k in ("type", "time", "angle", "topic", "hook", "cta", "liga", "meme_formato", "mercado", "segmento")}
                      | {"redes": _redes(p.get("redes"), t)})
        ok = self.mandatory(ok, earliest)
        e = now_co() + __import__("datetime").timedelta(minutes=10)
        left = (23 * 60 - (e.hour * 60 + e.minute)) // 60 + 1 if (now_co().strftime("%Y-%m-%d") == getattr(self, "today", "")
                                                                and getattr(self, "mode", "normal") != "extra_noche") else 10
        if len(ok) < (3 if left >= 3 else 1):
            return "Plan rechazado: " + "; ".join(problems or ["menos de 3 publicaciones válidas"])
        self.plan = sorted(ok, key=lambda p: p["time"])
        return "Plan guardado." + (f" Descartadas: {'; '.join(problems)}" if problems else "")

    MORNING, NIGHT = "07:30", "22:00"
    # the daily appointments, on EVERY network: stats twice a day, results at night, and two night reels/shorts
    SLOTS = (
        ("manana", "07:30", "picks_dia", "Los picks del día: menos de 5, equipos famosos de Europa, Sudamérica y Liga BetPlay",
         "picks del día", "Todas las probabilidades, gratis, en el enlace del perfil"),
        ("tarde", "14:00", "picks_dia", "Estadísticas de la tarde: los partidos de hoy que faltan, con sus probabilidades",
         "picks de la tarde", "Todas las probabilidades, gratis, en el enlace del perfil"),
        ("noche_stats", "19:30", "reel", "Reel/short de las estadísticas de los partidos de esta noche",
         "picks de la noche", "Todas las probabilidades, gratis, en el enlace del perfil"),
        ("noche", "22:00", "resultados", "Cómo le fue al modelo con los picks de hoy: aciertos y fallos",
         "resultados", "Historial público en el enlace del perfil"),
        ("noche_reel", "22:45", "reel", "Reel/short de los resultados del día: aciertos y fallos del modelo",
         "resultados del día", "Historial público en el enlace del perfil"),
    )
    MUST_GO = {"manana": "13:00", "noche": "23:30"}      # if the PC was off, these still go (until that hour)

    def mandatory(self, ok: list[dict], earliest: str) -> list[dict]:
        """Every day: morning and afternoon stats, night results, and two night reels — all on every network."""
        today = getattr(self, "today", "")
        live_today = now_co().strftime("%Y-%m-%d") == today and getattr(self, "mode", "normal") != "extra_noche"
        st = self.state or {}
        done_today = {p.get("obligatorio") for p in (st.get("plan") or []) if st.get("day") == today and p.get("status") == "done"}
        out = [p for p in ok if not p.get("obligatorio") and p["type"] != "resultados"]
        MIN = SPACING
        for key, slot, t, angle, topic, cta in self.SLOTS:
            if key in done_today:
                continue
            if live_today and slot < earliest:
                if key in self.MUST_GO and earliest <= self.MUST_GO[key]:
                    slot = earliest
                else:
                    continue
            out = [p for p in out if p.get("obligatorio") or abs(_mins(p["time"]) - _mins(slot)) >= MIN]
            out.append({"type": t, "time": slot, "obligatorio": key, "redes": list(ALL_NETS), "angle": angle,
                        "topic": topic, "hook": "", "cta": cta})
        return sorted(out, key=lambda p: p["time"])

    ART_OPTS = {"acento": ("oro", "esmeralda", "rubi", "zafiro", "violeta", "champana"),
                "portada": ("impacto", "editorial"), "ritmo": ("rapido", "muy_rapido", "elegante")}

    def set_art(self, art) -> None:
        art = art if isinstance(art, dict) else {}
        self.art = {k: (art.get(k) if art.get(k) in v else v[0]) for k, v in self.ART_OPTS.items()}

    def set_seo(self, seo) -> None:
        seo = seo if isinstance(seo, dict) else {}
        clean = lambda xs, n: [x for x in dict.fromkeys(re.sub(r"[^\wñÑáéíóúÁÉÍÓÚüÜ ]", "", str(x)).strip() for x in (xs or []))
                               if x and not BANNED.search(x)][:n]
        self.seo = {"hashtags": [h.replace(" ", "") for h in clean(seo.get("hashtags"), 20)], "palabras": clean(seo.get("palabras"), 10)}

    def learn(self, text: str, member: str = "") -> str:
        text = " ".join(text.split())[:500]
        if not text:
            return "Vacío."
        self.learned.append(text)
        if member in self.r["miembros"]:
            note(member, text)
        return "Guardado."

    # ---------------------------------------------------------------- meeting with the Pro plan (Claude Code)
    def meet_cli(self, today: str) -> dict:
        """Same meeting in three steps (Claude Code has no custom tools here): agenda → consultations → decisions."""
        import goldglitch_claude_cli as CLI
        self.log("Reunión del comité de crecimiento (plan Pro, Haiku 5.5)")
        ctx = (f"Hoy es {today} (hora de Colombia).\nMétricas de la web: {self.metrics_text()}\n\n"
               f"Historial y datos de hoy: {self.history_text()}\n\n"
               f"Plantilla: {json.dumps({k: (v.get('nombre', '') + ' — ' + v['rol']) for k, v in self.r['miembros'].items()}, ensure_ascii=False)}")
        agenda = CLI.ask_json(DIRECTOR, ctx + """

PASO 1 de la reunión. Decide a quién consultar y si hace falta contratar o despedir.
Formato: {"contratar":[{"clave":"...","rol":"Nombre — rol","mision":"...","departamento":"economia|mercados|audiencias|creativo|viralidad|neuro|growth"}], "despedir":[{"clave":"...","motivo":"..."}],
"consultas":[{"miembro":"clave","pregunta":"..."}]}  (los 7 departamentos responden siempre; aquí máximo 1 consulta individual extra, por ejemplo a alguien contratado hoy)""")
        for h in (agenda.get("contratar") or [])[:3]:
            self.log("  " + self.hire(str(h.get("clave", "")), str(h.get("rol", "")), str(h.get("mision", "")), str(h.get("departamento", ""))))
        for d in (agenda.get("despedir") or [])[:2]:
            self.fire(str(d.get("clave", "")), str(d.get("motivo", "")))
        answers = []
        for dep, q in DEPT_QUESTIONS.items():          # every department answers (one call each)
            try:
                answers.append({"departamento": DEPARTMENTS[dep][0], "respuesta": self.ask_department(dep, q)})
            except Exception as e:
                self.log(f"  {DEPARTMENTS[dep][0]}: {e}")
        consultas = [c for c in (agenda.get("consultas") or [])[:1] if str(c.get("miembro")) in self.r["miembros"]]
        for c in consultas:
            k = str(c.get("miembro", ""))
            answers.append({"miembro": k, "pregunta": c.get("pregunta"), "respuesta": self.ask(k, str(c.get("pregunta", "")))})
        types = json.dumps(POST_TYPES, ensure_ascii=False)
        feedback, acta = "", ""
        for _ in range(2):
            dec = CLI.ask_json(DIRECTOR, ctx + f"""

Respuestas de los departamentos: {json.dumps(answers, ensure_ascii=False)}
Formatos disponibles: {types}
{feedback}
PASO 2: decide. Formato:
{{"plan":[{{"type":"...","time":"HH:MM","angle":"...","topic":"...","hook":"...","cta":"...","liga":"(opcional)","mercado":"CO|MX|US|AR|ES|CL|PE|LATAM","segmento":"hinchas|comentaristas|profesores|analistas|fantasy|apostadores18","redes":["instagram","facebook","tiktok","youtube"]}}],
"decisiones":[{{"decision":"...","razon_economica":"...","efecto_esperado":"...","metrica":"...","revisar":"AAAA-MM-DD"}}],
"direccion_arte":{{"acento":"oro|esmeralda|rubi|zafiro|violeta|champana","portada":"impacto|editorial","ritmo":"rapido|muy_rapido|elegante"}},
"seo":{{"hashtags":["15 a 20 sin #, de Daniela, los más importantes primero"],"palabras":["6 a 10 palabras clave"]}},
(para cada "meme" agrega "meme_formato": tweet|nadie|expectativa|pov|starter|no_si|noticia|cuando|tier|chat|duelo|impopular|reto|giro, según Valeria y Mía; puedes
poner 2 memes si hay tendencias fuertes, y si una tendencia explota justo ahora, el meme puede ir con "time":"ahora")
(opcional: UNA publicación del plan puede llevar "time":"ahora" si debe salir apenas termine la reunión)
"aprendizajes":[{{"miembro":"clave de quien lo aprendió","texto":"..."}}], "acta":"qué viste, qué decidiste, qué experimento corre y cómo se mide"}}
32 a 40 publicaciones (al menos 8 por red), CADA UNA PARA UNA SOLA RED ("redes": ["instagram"] o ["facebook"] o ["tiktok"] o ["youtube"]) y
distinta de las demás: 8 a 10 piezas propias por red, horas 07:00–23:00, 45 min
entre piezas de la MISMA red y lejos de las citas fijas. Las citas fijas las agrega el sistema en todas las redes (07:30 y
14:00 estadísticas, 19:30 reel de estadísticas, 22:00 resultados, 22:45 reel de resultados): no las repitas.
Instagram: memes, carruseles de datos, reels de picks con otra liga; Facebook: "sabias_que", "noticia", educativo;
TikTok: "reel" y memes de tendencia; YouTube: "nba", reels de datos con búsqueda real. Al menos 1 "meme" y 1 concepto
disruptivo de Mía (en "angle"). Un partido mostrado en picks no se repite en 24 h: varía la "liga". Todo es del DÍA DE HOY (hora de Colombia): picks, datos y "angle" solo de partidos que se juegan hoy; los de mañana se publican mañana.""")
            res = self.set_plan(dec.get("plan") or [])
            self.set_art(dec.get("direccion_arte"))
            self.set_seo(dec.get("seo"))
            self.log(f"  plan: {res}")
            for t in (dec.get("aprendizajes") or [])[:4]:
                if isinstance(t, dict):
                    self.learn(str(t.get("texto", "")), str(t.get("miembro", "")))
                else:
                    self.learn(str(t))
            acta = str(dec.get("acta") or "")
            self.decisions = [d for d in (dec.get("decisiones") or []) if isinstance(d, dict)][:5]
            if self.plan:
                break
            feedback = f"Tu plan anterior fue rechazado: {res}. Corrígelo."
        return self._close(today, acta)

    # ---------------------------------------------------------------- meeting
    def meet(self, today: str, mode: str = "normal") -> dict:
        """mode: normal (morning) | extra (daytime: replaces the rest of today's plan) | extra_noche (draft only)."""
        self.today, self.mode = today, mode
        if mode == "normal" and (now_co().weekday() == 0 or not load(ECON_PLAN, {})) \
                and (load(ECON_PLAN, {}) or {}).get("semana") != now_co().strftime("%G-W%V"):
            try:                                   # Mondays (or the first time): the Economic Board sets the week
                board(self.client.api_key if self.client else None, self.signed, self.state, self.facts, self.log)
            except Exception as e:
                self.log(f"Junta Económica: {e}")
        if self.client is None:
            return self.meet_cli(today)
        self.log("Reunión del comité de crecimiento")
        messages: list[dict[str, Any]] = [{"role": "user", "content":
            f"Hoy es {today} (hora de Colombia). Inicia la reunión del comité. Plantilla actual: "
            + ", ".join(f"{k}: {v.get('nombre', '')} ({v['rol']})" for k, v in self.r["miembros"].items())}]
        acta = ""
        for _ in range(MAX_TURNS):
            resp = self.client.messages.create(model=MODEL, max_tokens=8000, system=DIRECTOR, tools=TOOLS, messages=messages)
            messages.append({"role": "assistant", "content": resp.content})
            uses = [b for b in resp.content if getattr(b, "type", "") == "tool_use"]
            if not uses:
                break
            results, done = [], False
            for b in uses:
                a = b.input or {}
                n = b.name
                if n == "ver_metricas":
                    out = self.metrics_text()
                elif n == "ver_historial":
                    out = self.history_text()
                elif n == "ver_plantilla":
                    out = json.dumps(self.r["miembros"], ensure_ascii=False)
                elif n == "consultar":
                    out = self.ask(str(a.get("miembro", "")), str(a.get("pregunta", "")))
                elif n == "contratar":
                    out = self.hire(str(a.get("clave", "")), str(a.get("rol", "")), str(a.get("mision", "")))
                elif n == "despedir":
                    out = self.fire(str(a.get("clave", "")), str(a.get("motivo", "")))
                elif n == "guardar_aprendizaje":
                    out = self.learn(str(a.get("texto", "")))
                elif n == "definir_plan":
                    out = self.set_plan(a.get("posts") or [])
                    self.set_art(a.get("direccion_arte"))
                    self.set_seo(a.get("seo"))
                    self.log(f"  plan: {out} · arte: {self.art}")
                elif n == "terminar":
                    if not self.plan:
                        out = "Falta el plan de hoy: usa definir_plan antes de terminar."
                    else:
                        acta, done, out = str(a.get("acta", "")), True, "Reunión cerrada."
                else:
                    out = f"Herramienta desconocida: {n}"
                results.append({"type": "tool_result", "tool_use_id": b.id, "content": out})
            messages.append({"role": "user", "content": results})
            if done:
                break
        return self._close(today, acta)

    def _close(self, today: str, acta: str) -> dict:
        mode = getattr(self, "mode", "normal")
        if mode != "extra_noche":
            log_decisions(today, getattr(self, "decisions", None) or [])
        if self.learned:
            with open(MEMORY, "a", encoding="utf-8") as f:
                for t in self.learned:
                    f.write(f"- {today}: {t}\n")
        if self.plan and mode == "extra_noche":
            save(DRAFT, {"for_day": today, "posts": self.plan, "arte": getattr(self, "art", None) or {},
                         "seo": getattr(self, "seo", None) or {}, "acta": acta[:2000]})
        elif self.plan:
            save(PLAN, {"day": today, "posts": self.plan, "arte": getattr(self, "art", None) or {},
                        "seo": getattr(self, "seo", None) or {}, "v": time.time()})
        os.makedirs(ACTAS, exist_ok=True)
        name = f"{today}.md" if mode == "normal" else f"{today}_extraordinaria_{now_co():%H%M}.md"
        title = {"normal": "Comité de crecimiento", "extra": "Reunión extraordinaria (reemplaza el resto del plan de hoy)",
                 "extra_noche": "Reunión extraordinaria de noche (borrador para la reunión de la mañana)"}[mode]
        with open(os.path.join(ACTAS, name), "w", encoding="utf-8") as f:
            f.write(f"# {title} — {today}\n\n{acta or '(sin acta)'}\n\n## Plan\n")
            for p in self.plan or []:
                f.write(f"- {p['time']} · {p['type']}{' (' + p['meme_formato'] + ')' if p.get('meme_formato') else ''}"
                        f"{' · ' + p['mercado'] if p.get('mercado') else ''}{' · ' + p['segmento'] if p.get('segmento') else ''} · {p['angle']}\n"
                        f"  - Gancho: {p['hook']}\n  - CTA: {p['cta']}\n")
            seo = getattr(self, "seo", None) or {}
            if seo.get("hashtags") or seo.get("palabras"):
                f.write(f"\n## Banco SEO (Daniela)\n- Hashtags: {' '.join('#' + h for h in seo.get('hashtags') or [])}\n"
                        f"- Palabras clave: {', '.join(seo.get('palabras') or [])}\n")
            f.write("\n## Aprendizajes\n" + "".join(f"- {t}\n" for t in self.learned))
            f.write("\n## Plantilla\n" + "".join(f"- {k}: {v.get('nombre', '')} — {v['rol']}\n" for k, v in self.r["miembros"].items()))
            f.write(f"\n_Consultas a miembros: {self.calls}_\n")
        self.log(f"Comité cerrado: {len(self.plan or [])} publicaciones, {len(self.learned)} aprendizajes, {self.calls} consultas")
        if getattr(self, "now_posts", None):
            self.log(f"Publicación inmediata decidida: {self.now_posts[0]['type']} — {self.now_posts[0].get('angle', '')}")
        return {"plan": self.plan, "acta": acta, "ahora": getattr(self, "now_posts", [])}


NOTEBOOKS = os.path.join(HERE, "redes_cuadernos.json")   # each member's own learnings (the office library)
ECON_PLAN = os.path.join(HERE, "redes_plan_economico.json")   # weekly plan from the Economic Board
DECISIONS = os.path.join(HERE, "redes_decisiones.json")       # decision log: what was decided, why, and if it worked


def economics_table(metrics: dict, state: dict) -> dict:
    """Numbers computed by code (agents never do the arithmetic): funnel, unit economics and the daily content mix vs
    results, with the sample size so nobody over-reads small data."""
    f = (metrics or {}).get("funnel") or {}
    d30 = f.get("d30") or {}
    daily = (metrics or {}).get("daily14") or []
    hist = state.get("history") or []
    mix: dict[str, dict] = {}
    for h in hist:
        if h.get("done"):
            day = mix.setdefault(h.get("day", ""), {"posts": 0, "formatos": {}, "mercados": {}})
            day["posts"] += 1
            day["formatos"][h.get("type", "?")] = day["formatos"].get(h.get("type", "?"), 0) + 1
            if h.get("mercado"):
                day["mercados"][h["mercado"]] = day["mercados"].get(h["mercado"], 0) + 1
    rows = [{"dia": d.get("day"), "visitas": d.get("visits"), "cuentas": d.get("signups"), "pagos": d.get("payments"),
             "ingresosCOP": d.get("revenueCOP"), **mix.get(d.get("day"), {"posts": 0})} for d in daily]
    lift = {}
    for fmt in {k for r in rows for k in (r.get("formatos") or {})}:
        on = [r["visitas"] or 0 for r in rows if (r.get("formatos") or {}).get(fmt)]
        off = [r["visitas"] or 0 for r in rows if not (r.get("formatos") or {}).get(fmt) and r.get("posts")]
        if on:
            lift[fmt] = {"dias_con": len(on), "visitas_prom_con": round(sum(on) / len(on), 1),
                         "dias_sin": len(off), "visitas_prom_sin": round(sum(off) / len(off), 1) if off else None}
    rev, signups, buyers = d30.get("revenueCOP") or 0, d30.get("signups") or 0, d30.get("buyers") or 0
    posts30 = sum(1 for h in hist if h.get("done"))
    return {"embudo_30d": {k: d30.get(k) for k in ("visits", "signups", "buyers", "revenueCOP", "visitToSignupPct",
                                                    "signupToPaidPct", "visitToPaidPct")},
            "unit_economics": {"ingreso_por_cuenta_COP": round(rev / signups) if signups else None,
                               "ingreso_por_comprador_COP": round(rev / buyers) if buyers else None,
                               "publicaciones_registradas": posts30,
                               "visitas_por_publicacion_30d": round((d30.get("visits") or 0) / posts30, 2) if posts30 else None,
                               "cuentas_por_publicacion_30d": round(signups / posts30, 3) if posts30 else None},
            "dias": rows[-14:], "formato_vs_visitas": lift,
            "paises_30d": ((metrics or {}).get("analytics30") or {}).get("countries", [])[:12],
            "dispositivos_30d": ((metrics or {}).get("analytics30") or {}).get("devices", []),
            "canal_por_pais_30d": ((metrics or {}).get("analytics30") or {}).get("sourceByCountry", [])[:15],
            "paginas_30d": ((metrics or {}).get("analytics30") or {}).get("pages", [])[:10],
            "botones_mas_clicados_30d": ((metrics or {}).get("analytics30") or {}).get("ctas", [])[:10],
            "metricas_por_publicacion": (load(os.path.join(HERE, "redes_metricas_redes.json"), []) or [])[-40:],
            "advertencia": "Muestra pequeña: trata las diferencias como hipótesis hasta tener 2+ semanas y repeticiones."}


def log_decisions(today: str, decisions: list[dict]) -> None:
    if not decisions:
        return
    log = load(DECISIONS, []) or []
    for d in decisions:
        log.append({"dia": today, **{k: str(v)[:300] for k, v in d.items()}})
    save(DECISIONS, log[-200:])


def board(api_key: str | None, signed, state: dict, facts: dict, log=print) -> dict:
    """Weekly Economic Board (Mondays): every economist plus Markets and Growth, then the Director turns it into the
    week's economic plan: allocation of the content inventory, targets, experiments, decisions and a review of last
    week's decisions against the numbers."""
    import goldglitch_claude_cli as CLI
    c = Committee(api_key, signed, state, facts, log)
    week = now_co().strftime("%G-W%V")
    log(f"Junta Económica semanal ({week})")
    past = [d for d in (load(DECISIONS, []) or [])][-20:]
    q = ("Junta Económica semanal. Con la tabla económica, las métricas de 7 y 30 días y el registro de decisiones "
         f"anteriores {json.dumps(past, ensure_ascii=False)[:3000]}: 1) ¿qué decisiones de la semana pasada acertaron y cuáles "
         "no (con el número)? 2) desde tu especialidad, ¿cómo asignar el inventario de la semana (unas 35 publicaciones) "
         "entre formatos, mercados y segmentos, y por qué? 3) un experimento con hipótesis, métrica y criterio.")
    answers = []
    for k in ("econ_crecimiento", "econ_consumidor", "ig_crecimiento", "tt_crecimiento", "yt_busqueda", "fb_comunidad"):
        try:
            answers.append({"miembro": c.r["miembros"][k].get("nombre"), "respuesta": c.ask(k, q)})
        except Exception as e:
            log(f"  {k}: {e}")
    plan = CLI.ask_json(DIRECTOR, f"""Métricas: {c.metrics_text()}
Tabla económica: {json.dumps(economics_table(c.metrics or {}, state), ensure_ascii=False)[:5000]}
Respuestas de la Junta: {json.dumps(answers, ensure_ascii=False)}

Deja el PLAN ECONÓMICO de la semana {week}. Formato JSON:
{{"objetivo":"meta principal de la semana (cuentas creadas) con número","north_star":"métrica",
"asignacion":{{"formatos":{{"reel":40,"meme":20,"...":0}},"mercados":{{"CO":50,"MX":20,"...":0}},"segmentos":{{"hinchas":60,"...":0}}}},
"metas":[{{"metrica":"...","valor":"..."}}],
"experimentos":[{{"hipotesis":"...","variante":"...","metrica":"...","criterio":"...","fin":"AAAA-MM-DD"}}],
"decisiones":[{{"decision":"...","razon_economica":"...","efecto_esperado":"...","metrica":"...","revisar":"AAAA-MM-DD"}}],
"revision_semana_anterior":"qué acertó y qué no, con números", "acta":"resumen de la Junta"}}
Los porcentajes de cada grupo suman 100. Sé conservador con conclusiones de muestras pequeñas.""")
    plan = {"semana": week, **{k: v for k, v in (plan or {}).items()}}
    save(ECON_PLAN, plan)
    log_decisions(now_co().strftime("%Y-%m-%d"), [d for d in plan.get("decisiones") or [] if isinstance(d, dict)])
    os.makedirs(ACTAS, exist_ok=True)
    with open(os.path.join(ACTAS, f"junta_economica_{week}.md"), "w", encoding="utf-8") as fh:
        fh.write(f"# Junta Económica — {week}\n\n{plan.get('acta', '')}\n\n## Plan económico\n```json\n"
                 f"{json.dumps(plan, ensure_ascii=False, indent=1)}\n```\n\n## Respuestas\n"
                 + "\n".join(f"### {a['miembro']}\n{a['respuesta']}\n" for a in answers))
    log(f"Junta cerrada: objetivo {str(plan.get('objetivo', ''))[:120]}")
    return plan


def notebook(member: str) -> list[dict]:
    return (load(NOTEBOOKS, {}) or {}).get(member) or []


def note(member: str, text: str) -> None:
    nb = load(NOTEBOOKS, {}) or {}
    nb.setdefault(member, []).append({"dia": now_co().strftime("%Y-%m-%d"), "texto": text[:500]})
    nb[member] = nb[member][-40:]
    save(NOTEBOOKS, nb)


def study(api_key: str | None, signed, state: dict, facts: dict, log=print) -> int:
    """Weekly study session in the library: each member reviews the week (metrics, posts, trends, her notebook) and
    writes what she learned and one thing she will try. Returns how many notes were written."""
    c = Committee(api_key, signed, state, facts, log)
    log("Sesión de estudio semanal en la biblioteca de la oficina")
    n = 0
    for key, m in c.r["miembros"].items():
        try:
            out = c.ask(key, "Sesión de estudio de la semana. Revisa métricas, publicaciones, tendencias y tu cuaderno. "
                             "Escribe en 2 líneas: 1) el aprendizaje más importante de tu especialidad esta semana (concreto y "
                             "verificable) y 2) qué vas a probar la próxima semana y cómo se medirá.")
            if out:
                note(key, "Estudio semanal: " + " ".join(out.split())[:480])
                n += 1
        except Exception as e:
            log(f"  {m.get('nombre', key)} no pudo estudiar: {e}")
    return n


def _trends() -> dict:
    try:
        import goldglitch_trends as T
        return T.brief(n=6)
    except Exception:
        return {}


def plan_version(today: str) -> float:
    p = load(PLAN, {})
    return float(p.get("v") or 0) if p.get("day") == today else 0.0


def art_for(today: str) -> dict:
    """Martina's art direction for today (empty = house style)."""
    p = load(PLAN, {})
    return (p.get("arte") or {}) if p.get("day") == today else {}


def seo_for(today: str) -> dict:
    """Daniela's SEO bank for today (hashtags + keywords); empty if the committee has not met."""
    p = load(PLAN, {})
    return (p.get("seo") or {}) if p.get("day") == today else {}


ALL_NETS = ("instagram", "facebook", "tiktok", "youtube")
SPACING = 45            # minutes between two pieces on the same network


def with_mandatory(plan: list[dict], today: str, state: dict) -> list[dict]:
    """Add the daily morning picks and night results to any plan (also the fallback one)."""
    c = Committee.__new__(Committee)
    c.today, c.mode, c.state = today, "extra_noche", state
    return c.mandatory([{**p, "redes": _redes(p.get("redes"), p.get("type", ""))} for p in plan or []], "00:00")
NET_DEFAULT = {"sabias_que": ["facebook"], "noticia": ["facebook"], "nba": ["youtube"], "meme": ["instagram"], "reel": ["tiktok"],
               "educativo": ["facebook"], "mito_dato": ["instagram"], "pregunta": ["instagram"], "picks_dia": ["instagram"]}


FILL_TYPES = {   # what each network gets when the committee planned fewer than the daily minimum
    "instagram": ["meme", "mito_dato", "pregunta", "reel", "meme", "picks_dia", "mito_dato", "reel"],
    "facebook": ["sabias_que", "noticia", "educativo", "pregunta", "sabias_que", "reel", "noticia", "educativo"],
    "tiktok": ["reel", "meme", "mito_dato", "reel", "meme", "pregunta", "reel", "meme"],
    "youtube": ["reel", "nba", "educativo", "reel", "mito_dato", "reel", "sabias_que", "reel"],
}
MIN_PER_NET = 8


def fill_per_network(plan: list[dict], today: str, minimum: int = MIN_PER_NET) -> list[dict]:
    """Guarantee at least `minimum` own pieces per network today (besides the fixed appointments), evenly spread
    from now to 23:00 and at least SPACING minutes from anything else on that network."""
    live = now_co().strftime("%Y-%m-%d") == today
    start = max(_mins("07:00"), (now_co().hour * 60 + now_co().minute + 10) if live else 0)
    end = _mins("23:00")
    out = list(plan or [])
    for net in ALL_NETS:
        own = [p for p in out if not p.get("obligatorio") and net in (p.get("redes") or [])]
        if live:
            own = [p for p in own if p.get("time", "") > now_co().strftime("%H:%M") or p.get("status") == "done"]
        need = minimum - len(own)
        if need <= 0 or end - start < SPACING:
            continue
        busy = [_mins(p["time"]) for p in out if net in (p.get("redes") or []) and re.fullmatch(r"\d{2}:\d{2}", str(p.get("time")))]
        step = max(SPACING, (end - start) // (need + 1))
        types = FILL_TYPES[net]
        k = len(own)
        t = start + step // 2
        while need > 0 and t <= end:
            m = min(range(t, min(end, t + step) + 1, 5), key=lambda x: (any(abs(x - b) < SPACING for b in busy), abs(x - t)))
            if not any(abs(m - b) < SPACING for b in busy):
                out.append({"type": types[k % len(types)], "time": f"{m // 60:02d}:{m % 60:02d}", "redes": [net],
                            "angle": "", "topic": "", "hook": "", "cta": "", "relleno": True})
                busy.append(m)
                k += 1
                need -= 1
            t += step
    return sorted(out, key=lambda p: p["time"])


def _redes(val, t: str) -> list[str]:
    nets = [n for n in (val if isinstance(val, list) else str(val or "").replace(",", " ").split()) if n in ALL_NETS]
    return nets or NET_DEFAULT.get(t, list(ALL_NETS))


def _mins(hhmm: str) -> int:
    return int(hhmm[:2]) * 60 + int(hhmm[3:5])


def plan_for(today: str) -> list[dict] | None:
    """The committee's plan for today, if it met."""
    p = load(PLAN, {})
    return p.get("posts") if p.get("day") == today else None


def main() -> int:
    """Normal: today's meeting if it has not happened. --extra: extraordinary meeting now:
    between 07:00 and 22:00 it replaces the rest of today's plan; at night it leaves a draft that the morning meeting
    takes into account (the morning meeting still happens)."""
    import goldglitch_social as S
    from datetime import timedelta
    S.load_env()
    key = os.environ.get("ANTHROPIC_API_KEY")
    import goldglitch_claude_cli as CLI
    if not key and not CLI.available():
        print("Falta Claude Code con tu sesión de Claude (o ANTHROPIC_API_KEY en el .env)")
        return 1
    now = datetime.now(S.TZ)
    today = now.strftime("%Y-%m-%d")
    extra = "--extra" in sys.argv or "--forzar" in sys.argv
    if not extra and plan_for(today):
        print("El comité ya se reunió hoy (usa reunion_extra.bat para una reunión extraordinaria).")
        return 0
    facts = S.signed("/api/social/feed", {})
    c = Committee(key, S.signed, S.load_json(S.STATE, {}), facts, S.log)
    if "--ya" in sys.argv:            # meeting now (any hour) + publish right away on every network
        S.log("Reunión inmediata de la firma con publicación inmediata")
        res = c.meet(today, "extra")
        posts = res.get("ahora") or (res.get("plan") or plan_for(today) or [])[:1]
        if not posts:
            posts = [{"type": "meme", "angle": "Pieza inmediata decidida en la reunión", "topic": "tendencia del día"}]
        S.publish_now(posts[:1])
        if posts and not res.get("ahora"):     # the published plan item does not repeat later
            st = S.load_json(S.STATE, {})
            for p in st.get("plan") or []:
                if p.get("time") == posts[0].get("time") and p.get("type") == posts[0].get("type"):
                    p["status"] = "done"
            S.save_json(S.STATE, st)
        return 0
    if extra and not (7 <= now.hour < 22):
        day = today if now.hour < 7 else (now + timedelta(days=1)).strftime("%Y-%m-%d")
        S.log(f"Reunión extraordinaria de noche: deja un borrador para la reunión de la mañana del {day}")
        res = c.meet(day, "extra_noche")
    else:
        res = c.meet(today, "extra" if extra else "normal")
        if extra:
            S.log("Reunión extraordinaria: el resto del plan de hoy se actualiza en la próxima vuelta de los agentes")
    if res.get("ahora"):
        S.publish_now(res["ahora"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
