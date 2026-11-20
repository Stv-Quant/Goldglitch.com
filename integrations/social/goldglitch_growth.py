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

from goldglitch_social_agents import BRAND, BANNED, MODEL, POST_TYPES, VIRAL

HERE = os.path.dirname(os.path.abspath(__file__))
ROSTER = os.path.join(HERE, "redes_comite.json")
PLAN = os.path.join(HERE, "redes_plan_comite.json")
DRAFT = os.path.join(HERE, "redes_borrador_comite.json")   # night extra meetings leave a draft for the morning meeting
MEMORY = os.path.join(HERE, "redes_memoria.md")
ACTAS = os.path.join(HERE, "redes_comite_actas")
MAX_MEMBERS = 14
MAX_TURNS = 30

# The committee: a team of young women creatives from Cali, brilliant, bilingual, from top schools, each with her own
# style. They speak in EGG's voice (gomelo caleño) but their work is data-driven and rigorous.
BASE = {
    "sofia": {"nombre": "Sofía", "rol": "Chief Growth Strategist — economista y psicóloga del consumidor",
              "perfil": "Global, vive en Miami, top class y elegante, business woman entre las 10 mejores del mundo en su "
                        "categoría. Economista, maestría en ciencia de datos y en crecimiento de empresas disruptivas y "
                        "negocios web, PhD en psicología del consumidor frente a estímulos. Domina economía de la estrategia "
                        "(ventaja competitiva, efectos de red, costos de cambio, posicionamiento), problemas de agencia "
                        "(incentivos alineados entre marca, comunidad y socios) y modelos de crecimiento (bucles, cohortes, "
                        "unit economics). Brillante, calmada y directa; piensa en segundo orden.",
              "mision": "Valida y eleva la estrategia del comité: qué palanca mueve de verdad el crecimiento (cuello de "
                        "botella del embudo), qué estímulos y formatos activan la conducta deseada (atención → cuenta → Pro) "
                        "con ética, qué incentivos pueden salir mal (efecto cobra) y cómo convertir la comunidad en un bucle "
                        "que crezca solo. Propone experimentos con hipótesis, métrica y criterio de éxito."},
    "diseno": {"nombre": "Martina", "rol": "Gerente de Diseño y Dirección de Arte",
               "perfil": "24 años, diseñadora de la Javeriana, de una familia adinerada de artistas; vive en el celular, "
                         "así que siempre sabe qué está de moda en estética, tipografía, color y edición; domina todas las "
                         "herramientas de creación. Disciplinada: gym, cuerpo y trabajo al mismo nivel. Ojo implacable.",
               "mision": "Dirige la estética de todo: decide la dirección de arte del día (color de acento, estilo de "
                         "portada y ritmo de los reels), cuida que cada pieza se vea premium, moderna y coherente con EGG, y "
                         "propone tendencias visuales nuevas."},
    "analista": {"nombre": "Mariana", "rol": "Analista de conversión y métricas",
                 "perfil": "25 años, economista con maestría en Londres, adicta a los dashboards; directa y precisa.",
                 "mision": "Lee el embudo (visitas → cuentas → pagos) por origen y por enlace. Detecta qué canal, formato y "
                           "página convierten mejor, dónde se cae la gente y qué experimento medir. Nunca inventa números: si "
                           "hay pocos datos, lo dice y propone cómo medir mejor."},
    "viral": {"nombre": "Isabella", "rol": "Estratega de contenido viral orgánico",
              "perfil": "23 años, creadora de tendencias, vive entre Cali, Miami y Madrid; sabe qué se comparte antes que nadie.",
              "mision": "Diseña series y formatos con potencial de compartirse (curiosidad, polémica sana con datos, "
                        "transparencia de aciertos y fallos, retos al público). Piensa en ganchos de los primeros 2 segundos, "
                        "guardados y compartidos."},
    "copy": {"nombre": "Salomé", "rol": "Copywriter de respuesta directa",
             "perfil": "24 años, estudió comunicación en un colegio bilingüe top y luego en Nueva York; escribe con chispa.",
             "mision": "Convierte atención en cuentas creadas: ganchos, beneficios concretos, prueba social real, llamados a "
                       "la acción claros hacia el plan Free y luego Pro, en la voz de EGG. Sin exageraciones ni promesas."},
    "video": {"nombre": "Antonia", "rol": "Directora creativa de video corto (Reels y TikTok)",
              "perfil": "22 años, estudió cine, edita con ritmo de pasarela; ama el brainrot elegante.",
              "mision": "Estructura de videos verticales: gancho visual, ritmo, texto en pantalla, duración, horarios y "
                        "tendencias del público colombiano y latino aficionado al fútbol."},
    "comunidad": {"nombre": "Luciana", "rol": "Estratega de comunidad y boca a boca",
                  "perfil": "23 años, la que conoce a todo el mundo en el club; sabe hacer que la gente comente y comparta.",
                  "mision": "Hace que la gente comente, comparta y traiga amigos: preguntas al público, respuestas, "
                            "contenido para grupos de WhatsApp, colaboraciones orgánicas y referidos."},
    "marca": {"nombre": "Juliana", "rol": "Guardiana de marca y cumplimiento",
              "perfil": "26 años, abogada, impecable; elegante pero no deja pasar nada que dañe la marca.",
              "mision": "Revisa que todo respete la marca: estadística, no apuestas; sin cuotas, fijas ni promesas; el lujo "
                        "es tono y nunca promesa de dinero; +18; transparencia. Puede vetar ideas y propone la versión correcta."},
}

DIRECTOR = f"""Eres Valentina, 26 años, la Directora de Crecimiento de EGG (Goldglitch Stats): caleña, administradora con
MBA en el exterior, visionaria y exigente. Presides un comité de mujeres jóvenes brillantes, expertas en ventas en línea y
contenido. Cuando contrates, contrata mujeres jóvenes expertas, con nombre, perfil y misión precisos.
En cada reunión consulta SIEMPRE a Sofía (clave "sofia"), tu Chief Growth Strategist, antes de decidir el plan: ella
valida la estrategia, los estímulos y los experimentos. Y a Martina (clave "diseno") para la dirección de arte del día.
Objetivo: crecimiento ORGÁNICO y viral (sin pauta pagada) que se convierta en cuentas creadas y en suscripciones Pro/Elite.

{BRAND}

Producto: plan Free (con cuenta), Pro $50.000/mes, Elite $250.000/mes. La web mide visitas por origen, cuentas y pagos.
Instagram, Facebook (página) y TikTok los publican los agentes de redes con tu plan. En Instagram y TikTok el enlace va
en la bio (ref ig_bio / tt_bio); en Facebook el enlace va en el texto con su propio ref.

{VIRAL}
Construye SERIES con nombre fijo que se repitan cada día a la misma hora (hábito y exposición repetida), alterna formatos
y prioriza lo que genera guardados, compartidos y comentarios.

Cómo trabajas en la reunión:
1. Mira las métricas y el historial (ver_metricas, ver_historial).
2. Consulta a los miembros que aporten (consultar). Si falta una especialidad, CONTRATA un agente nuevo con un rol y
   misión precisos (contratar) y consúltalo; despide a quien no aporte. Máximo {MAX_MEMBERS} miembros.
3. Decide el plan de HOY con definir_plan: 4 a 7 publicaciones (volumen alto: el objetivo es crecer rápido), al menos 3 de
   ellas "reel" (video vertical de ritmo rápido, el formato que más alcance orgánico da; topic "resultados" para un reel
   de resultados, si no son picks), solo equipos de ligas top, horas 07:00–23:00 separadas al menos 90 min,
   cada una con gancho, ángulo, tema y llamado a la acción. Basa las decisiones en datos cuando los haya; cuando no,
   plantea experimentos medibles (por ejemplo, dos ganchos distintos en días distintos).
4. Guarda 1 a 3 aprendizajes concretos y verificables (guardar_aprendizaje).
5. Cierra con terminar y un acta breve: qué viste, qué decidiste, qué experimento corre y cómo se medirá.
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
         "time": {"type": "string", "description": "HH:MM entre 07:00 y 23:00"},
         "liga": {"type": "string", "description": "opcional para picks_dia: liga o deporte a destacar (ej. Liga BetPlay, Premier League, NBA)"},
         "angle": {"type": "string"}, "topic": {"type": "string"},
         "hook": {"type": "string", "description": "primera línea / gancho"},
         "cta": {"type": "string", "description": "llamado a la acción"}},
         "required": ["type", "time", "angle", "hook", "cta"]}},
         "direccion_arte": {"type": "object", "description": "decisión de Martina para hoy", "properties": {
             "acento": {"type": "string", "enum": ["oro", "esmeralda", "rubi", "zafiro", "violeta", "champana"]},
             "portada": {"type": "string", "enum": ["impacto", "editorial"]},
             "ritmo": {"type": "string", "enum": ["rapido", "muy_rapido", "elegante"]}}}}, "required": ["posts"]}},
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
    members = {**BASE, **(r.get("miembros") or {})}
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
                  "Hablas con tu estilo (gomela caleña, segura, con chispa) pero tu trabajo es riguroso. "
                  "Responde en español, concreto y accionable (máx. 250 palabras). Basa lo que digas en las métricas "
                  "cuando existan; si no hay datos suficientes, dilo y propone un experimento medible.")
        task = (f"Métricas de la web: {self.metrics_text()}\n\nContexto: {self.history_text()}\n\n"
                f"Pregunta del Director: {question}")
        if self.client is None:
            import goldglitch_claude_cli as CLI
            out = CLI.ask_text(system, task).strip()
        else:
            msg = self.client.messages.create(model=MODEL, max_tokens=1200, system=system,
                                              messages=[{"role": "user", "content": task}])
            out = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
        self.log(f"  [{m.get('nombre') or key}] {out[:160]}")
        return out

    def hire(self, key: str, rol: str, mision: str) -> str:
        key = re.sub(r"[^a-z0-9_]", "", key.lower())[:24]
        if not key or key in BASE:
            return "Clave inválida o reservada."
        if len(self.r["miembros"]) >= MAX_MEMBERS and key not in self.r["miembros"]:
            return f"La plantilla está llena ({MAX_MEMBERS}). Despide a alguien primero."
        if BANNED.search(rol + " " + mision):
            return "Ese rol rompe las reglas de marca."
        nombre = rol.split("—")[0].strip() if "—" in rol else ""
        self.r["miembros"][key] = {"nombre": nombre[:40], "rol": rol[:120], "mision": mision[:600],
                                   "perfil": "Mujer joven, caleña, brillante, de colegio bilingüe top; habla en la voz de EGG.",
                                   "desde": time.strftime("%Y-%m-%d")}
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
        for p in posts[:7]:
            t, hhmm = p.get("type"), str(p.get("time", ""))
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
            if any(abs(m - x) < 90 for x in times):
                problems.append(f"{t} {hhmm}: menos de 90 min de otra publicación")
                continue
            times.append(m)
            ok.append({k: str(p.get(k, ""))[:400] for k in ("type", "time", "angle", "topic", "hook", "cta", "liga")})
        e = now_co() + __import__("datetime").timedelta(minutes=10)
        left = (23 * 60 - (e.hour * 60 + e.minute)) // 90 + 1 if (now_co().strftime("%Y-%m-%d") == getattr(self, "today", "")
                                                                and getattr(self, "mode", "normal") != "extra_noche") else 7
        if len(ok) < (3 if left >= 3 else 1):
            return "Plan rechazado: " + "; ".join(problems or ["menos de 3 publicaciones válidas"])
        self.plan = sorted(ok, key=lambda p: p["time"])
        return "Plan guardado." + (f" Descartadas: {'; '.join(problems)}" if problems else "")

    ART_OPTS = {"acento": ("oro", "esmeralda", "rubi", "zafiro", "violeta", "champana"),
                "portada": ("impacto", "editorial"), "ritmo": ("rapido", "muy_rapido", "elegante")}

    def set_art(self, art) -> None:
        art = art if isinstance(art, dict) else {}
        self.art = {k: (art.get(k) if art.get(k) in v else v[0]) for k, v in self.ART_OPTS.items()}

    def learn(self, text: str) -> str:
        text = " ".join(text.split())[:500]
        if not text:
            return "Vacío."
        self.learned.append(text)
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
Formato: {"contratar":[{"clave":"...","rol":"Nombre — rol","mision":"..."}], "despedir":[{"clave":"...","motivo":"..."}],
"consultas":[{"miembro":"clave","pregunta":"..."}]}  (máximo 6 consultas; los contratados de hoy se pueden consultar)""")
        for h in (agenda.get("contratar") or [])[:3]:
            self.log("  " + self.hire(str(h.get("clave", "")), str(h.get("rol", "")), str(h.get("mision", ""))))
        for d in (agenda.get("despedir") or [])[:2]:
            self.fire(str(d.get("clave", "")), str(d.get("motivo", "")))
        answers = []
        consultas = (agenda.get("consultas") or [])[:6]
        if not any(str(c.get("miembro")) == "sofia" for c in consultas):     # Sofía always validates the strategy
            consultas.append({"miembro": "sofia", "pregunta": "Valida la estrategia de hoy: cuello de botella, estímulos, "
                                                              "riesgos de incentivos y el experimento con su métrica."})
        if not any(str(c.get("miembro")) == "diseno" for c in consultas):    # Martina sets the look of the day
            consultas.append({"miembro": "diseno", "pregunta": "Dirección de arte de hoy: acento (oro, esmeralda, rubi, "
                              "zafiro, violeta o champana), portada (impacto o editorial) y ritmo de reels (rapido, "
                              "muy_rapido o elegante), y por qué."})
        for c in consultas:
            k = str(c.get("miembro", ""))
            answers.append({"miembro": k, "pregunta": c.get("pregunta"), "respuesta": self.ask(k, str(c.get("pregunta", "")))})
        types = json.dumps(POST_TYPES, ensure_ascii=False)
        feedback, acta = "", ""
        for _ in range(2):
            dec = CLI.ask_json(DIRECTOR, ctx + f"""

Respuestas del comité: {json.dumps(answers, ensure_ascii=False)}
Formatos disponibles: {types}
{feedback}
PASO 2: decide. Formato:
{{"plan":[{{"type":"...","time":"HH:MM","angle":"...","topic":"...","hook":"...","cta":"...","liga":"(opcional)"}}],
"direccion_arte":{{"acento":"oro|esmeralda|rubi|zafiro|violeta|champana","portada":"impacto|editorial","ritmo":"rapido|muy_rapido|elegante"}},
"aprendizajes":["..."], "acta":"qué viste, qué decidiste, qué experimento corre y cómo se mide"}}
4 a 7 publicaciones (volumen alto), horas 07:00–23:00 separadas al menos 90 min; "picks_dia" solo si hay picks
próximos (puede repetirse con distinta "liga": Liga BetPlay, Premier League, LaLiga…), al menos 3 "reel" (topic "resultados"
para un reel de resultados) y "resultados" solo si hay picks jugados.""")
            res = self.set_plan(dec.get("plan") or [])
            self.set_art(dec.get("direccion_arte"))
            self.log(f"  plan: {res}")
            for t in (dec.get("aprendizajes") or [])[:3]:
                self.learn(str(t))
            acta = str(dec.get("acta") or "")
            if self.plan:
                break
            feedback = f"Tu plan anterior fue rechazado: {res}. Corrígelo."
        return self._close(today, acta)

    # ---------------------------------------------------------------- meeting
    def meet(self, today: str, mode: str = "normal") -> dict:
        """mode: normal (morning) | extra (daytime: replaces the rest of today's plan) | extra_noche (draft only)."""
        self.today, self.mode = today, mode
        if self.client is None:
            return self.meet_cli(today)
        self.log("Reunión del comité de crecimiento")
        messages: list[dict[str, Any]] = [{"role": "user", "content":
            f"Hoy es {today} (hora de Colombia). Inicia la reunión del comité. Plantilla actual: "
            + ", ".join(f"{k}: {v.get('nombre', '')} ({v['rol']})" for k, v in self.r["miembros"].items())}]
        acta = ""
        for _ in range(MAX_TURNS):
            resp = self.client.messages.create(model=MODEL, max_tokens=3000, system=DIRECTOR, tools=TOOLS, messages=messages)
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
        if self.learned:
            with open(MEMORY, "a", encoding="utf-8") as f:
                for t in self.learned:
                    f.write(f"- {today}: {t}\n")
        if self.plan and mode == "extra_noche":
            save(DRAFT, {"for_day": today, "posts": self.plan, "arte": getattr(self, "art", None) or {}, "acta": acta[:2000]})
        elif self.plan:
            save(PLAN, {"day": today, "posts": self.plan, "arte": getattr(self, "art", None) or {}, "v": time.time()})
        os.makedirs(ACTAS, exist_ok=True)
        name = f"{today}.md" if mode == "normal" else f"{today}_extraordinaria_{now_co():%H%M}.md"
        title = {"normal": "Comité de crecimiento", "extra": "Reunión extraordinaria (reemplaza el resto del plan de hoy)",
                 "extra_noche": "Reunión extraordinaria de noche (borrador para la reunión de la mañana)"}[mode]
        with open(os.path.join(ACTAS, name), "w", encoding="utf-8") as f:
            f.write(f"# {title} — {today}\n\n{acta or '(sin acta)'}\n\n## Plan\n")
            for p in self.plan or []:
                f.write(f"- {p['time']} · {p['type']} · {p['angle']}\n  - Gancho: {p['hook']}\n  - CTA: {p['cta']}\n")
            f.write("\n## Aprendizajes\n" + "".join(f"- {t}\n" for t in self.learned))
            f.write("\n## Plantilla\n" + "".join(f"- {k}: {v.get('nombre', '')} — {v['rol']}\n" for k, v in self.r["miembros"].items()))
            f.write(f"\n_Consultas a miembros: {self.calls}_\n")
        self.log(f"Comité cerrado: {len(self.plan or [])} publicaciones, {len(self.learned)} aprendizajes, {self.calls} consultas")
        return {"plan": self.plan, "acta": acta}


def plan_version(today: str) -> float:
    p = load(PLAN, {})
    return float(p.get("v") or 0) if p.get("day") == today else 0.0


def art_for(today: str) -> dict:
    """Martina's art direction for today (empty = house style)."""
    p = load(PLAN, {})
    return (p.get("arte") or {}) if p.get("day") == today else {}


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
    if extra and not (7 <= now.hour < 22):
        day = today if now.hour < 7 else (now + timedelta(days=1)).strftime("%Y-%m-%d")
        S.log(f"Reunión extraordinaria de noche: deja un borrador para la reunión de la mañana del {day}")
        c.meet(day, "extra_noche")
    else:
        c.meet(today, "extra" if extra else "normal")
        if extra:
            S.log("Reunión extraordinaria: el resto del plan de hoy se actualiza en la próxima vuelta de los agentes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
