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

from goldglitch_social_agents import BRAND, BANNED, MODEL, POST_TYPES

HERE = os.path.dirname(os.path.abspath(__file__))
ROSTER = os.path.join(HERE, "redes_comite.json")
PLAN = os.path.join(HERE, "redes_plan_comite.json")
MEMORY = os.path.join(HERE, "redes_memoria.md")
ACTAS = os.path.join(HERE, "redes_comite_actas")
MAX_MEMBERS = 14
MAX_TURNS = 30

BASE = {
    "analista": {"rol": "Analista de conversión y métricas",
                 "mision": "Lee el embudo (visitas → cuentas → pagos) por origen y por enlace. Detecta qué canal, formato y "
                           "página convierten mejor, dónde se cae la gente y qué experimento medir. Nunca inventa números: si "
                           "hay pocos datos, lo dice y propone cómo medir mejor."},
    "viral": {"rol": "Estratega de contenido viral orgánico",
              "mision": "Diseña series y formatos con potencial de compartirse (curiosidad, polémica sana con datos, "
                        "transparencia de aciertos y fallos, retos al público). Piensa en ganchos de los primeros 2 segundos, "
                        "guardados y compartidos."},
    "copy": {"rol": "Copywriter de respuesta directa",
             "mision": "Convierte atención en cuentas creadas: ganchos, beneficios concretos, prueba social real, llamados a "
                       "la acción claros hacia el plan Free y luego Pro. Sin exageraciones ni promesas."},
    "video": {"rol": "Especialista en video corto (Reels y TikTok)",
              "mision": "Estructura de videos verticales: gancho visual, ritmo, texto en pantalla, duración, horarios y "
                        "tendencias del público colombiano y latino aficionado al fútbol."},
    "comunidad": {"rol": "Estratega de comunidad y boca a boca",
                  "mision": "Hace que la gente comente, comparta y traiga amigos: preguntas al público, respuestas, "
                            "contenido para grupos de WhatsApp, colaboraciones orgánicas y referidos."},
    "marca": {"rol": "Guardián de marca y cumplimiento",
              "mision": "Revisa que todo respete la marca: estadística, no apuestas; sin cuotas, fijas ni promesas; "
                        "+18; transparencia. Puede vetar ideas y propone la versión correcta."},
}

DIRECTOR = f"""Eres el Director de Crecimiento de Goldglitch Stats y presides su comité de expertos en ventas en línea.
Objetivo: crecimiento ORGÁNICO y viral (sin pauta pagada) que se convierta en cuentas creadas y en suscripciones Pro/Elite.

{BRAND}

Producto: plan Free (con cuenta), Pro $50.000/mes, Elite $250.000/mes. La web mide visitas por origen, cuentas y pagos.
Instagram, Facebook (página) y TikTok los publican los agentes de redes con tu plan. En Instagram y TikTok el enlace va
en la bio (ref ig_bio / tt_bio); en Facebook el enlace va en el texto con su propio ref.

Cómo trabajas en la reunión:
1. Mira las métricas y el historial (ver_metricas, ver_historial).
2. Consulta a los miembros que aporten (consultar). Si falta una especialidad, CONTRATA un agente nuevo con un rol y
   misión precisos (contratar) y consúltalo; despide a quien no aporte. Máximo {MAX_MEMBERS} miembros.
3. Decide el plan de HOY con definir_plan: 4 a 7 publicaciones (volumen alto: el objetivo es crecer rápido), horas 07:00–23:00 separadas al menos 90 min,
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
         "rol": {"type": "string"}, "mision": {"type": "string"}}, "required": ["clave", "rol", "mision"]}},
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
         "required": ["type", "time", "angle", "hook", "cta"]}}}, "required": ["posts"]}},
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
        return json.dumps({"hora_actual_colombia": now_co().strftime("%H:%M"),
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
        system = (f"Eres {m['rol']} en el comité de crecimiento de Goldglitch Stats. Tu misión: {m['mision']}\n\n{BRAND}\n\n"
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
        self.log(f"  [{key}] {out[:160]}")
        return out

    def hire(self, key: str, rol: str, mision: str) -> str:
        key = re.sub(r"[^a-z0-9_]", "", key.lower())[:24]
        if not key or key in BASE:
            return "Clave inválida o reservada."
        if len(self.r["miembros"]) >= MAX_MEMBERS and key not in self.r["miembros"]:
            return f"La plantilla está llena ({MAX_MEMBERS}). Despide a alguien primero."
        if BANNED.search(rol + " " + mision):
            return "Ese rol rompe las reglas de marca."
        self.r["miembros"][key] = {"rol": rol[:120], "mision": mision[:600], "desde": time.strftime("%Y-%m-%d")}
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
            if hhmm and hhmm < earliest and now_co().strftime("%Y-%m-%d") == getattr(self, "today", ""):
                problems.append(f"{t} {hhmm}: esa hora ya pasó (ahora son {now_co():%H:%M})")
                continue
            if t not in POST_TYPES or not re.fullmatch(r"\d{2}:\d{2}", hhmm) or not ("07:00" <= hhmm <= "23:00"):
                problems.append(f"{t} {hhmm}: tipo u hora inválidos")
                continue
            if (t == "resultados" and not f.get("results")) or (t == "picks_dia" and not f.get("upcoming")):
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
        left = (23 * 60 - (e.hour * 60 + e.minute)) // 90 + 1 if now_co().strftime("%Y-%m-%d") == getattr(self, "today", "") else 7
        if len(ok) < (3 if left >= 3 else 1):
            return "Plan rechazado: " + "; ".join(problems or ["menos de 3 publicaciones válidas"])
        self.plan = sorted(ok, key=lambda p: p["time"])
        return "Plan guardado." + (f" Descartadas: {'; '.join(problems)}" if problems else "")

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
               f"Plantilla: {json.dumps({k: v['rol'] for k, v in self.r['miembros'].items()}, ensure_ascii=False)}")
        agenda = CLI.ask_json(DIRECTOR, ctx + """

PASO 1 de la reunión. Decide a quién consultar y si hace falta contratar o despedir.
Formato: {"contratar":[{"clave":"...","rol":"...","mision":"..."}], "despedir":[{"clave":"...","motivo":"..."}],
"consultas":[{"miembro":"clave","pregunta":"..."}]}  (máximo 6 consultas; los contratados de hoy se pueden consultar)""")
        for h in (agenda.get("contratar") or [])[:3]:
            self.log("  " + self.hire(str(h.get("clave", "")), str(h.get("rol", "")), str(h.get("mision", ""))))
        for d in (agenda.get("despedir") or [])[:2]:
            self.fire(str(d.get("clave", "")), str(d.get("motivo", "")))
        answers = []
        for c in (agenda.get("consultas") or [])[:6]:
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
"aprendizajes":["..."], "acta":"qué viste, qué decidiste, qué experimento corre y cómo se mide"}}
4 a 7 publicaciones (volumen alto), horas 07:00–23:00 separadas al menos 90 min; "picks_dia" solo si hay picks
próximos (puede repetirse con distinta "liga": Liga BetPlay, Premier League, NBA…) y "resultados" solo si hay picks jugados.""")
            res = self.set_plan(dec.get("plan") or [])
            self.log(f"  plan: {res}")
            for t in (dec.get("aprendizajes") or [])[:3]:
                self.learn(str(t))
            acta = str(dec.get("acta") or "")
            if self.plan:
                break
            feedback = f"Tu plan anterior fue rechazado: {res}. Corrígelo."
        return self._close(today, acta)

    # ---------------------------------------------------------------- meeting
    def meet(self, today: str) -> dict:
        self.today = today
        if self.client is None:
            return self.meet_cli(today)
        self.log("Reunión del comité de crecimiento")
        messages: list[dict[str, Any]] = [{"role": "user", "content":
            f"Hoy es {today} (hora de Colombia). Inicia la reunión del comité. Plantilla actual: "
            + ", ".join(f"{k} ({v['rol']})" for k, v in self.r["miembros"].items())}]
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
                    self.log(f"  plan: {out}")
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
        if self.learned:
            with open(MEMORY, "a", encoding="utf-8") as f:
                for t in self.learned:
                    f.write(f"- {today}: {t}\n")
        if self.plan:
            save(PLAN, {"day": today, "posts": self.plan})
        os.makedirs(ACTAS, exist_ok=True)
        with open(os.path.join(ACTAS, f"{today}.md"), "w", encoding="utf-8") as f:
            f.write(f"# Comité de crecimiento — {today}\n\n{acta or '(sin acta)'}\n\n## Plan\n")
            for p in self.plan or []:
                f.write(f"- {p['time']} · {p['type']} · {p['angle']}\n  - Gancho: {p['hook']}\n  - CTA: {p['cta']}\n")
            f.write("\n## Aprendizajes\n" + "".join(f"- {t}\n" for t in self.learned))
            f.write("\n## Plantilla\n" + "".join(f"- {k}: {v['rol']}\n" for k, v in self.r["miembros"].items()))
            f.write(f"\n_Consultas a miembros: {self.calls}_\n")
        self.log(f"Comité cerrado: {len(self.plan or [])} publicaciones, {len(self.learned)} aprendizajes, {self.calls} consultas")
        return {"plan": self.plan, "acta": acta}


def plan_for(today: str) -> list[dict] | None:
    """The committee's plan for today, if it met."""
    p = load(PLAN, {})
    return p.get("posts") if p.get("day") == today else None


def main() -> int:
    import goldglitch_social as S
    S.load_env()
    key = os.environ.get("ANTHROPIC_API_KEY")
    import goldglitch_claude_cli as CLI
    if not key and not CLI.available():
        print("Falta Claude Code con tu sesión de Claude (o ANTHROPIC_API_KEY en el .env)")
        return 1
    today = datetime.now(S.TZ).strftime("%Y-%m-%d")
    if plan_for(today) and "--forzar" not in sys.argv:
        print("El comité ya se reunió hoy (usa --forzar para repetir).")
        return 0
    facts = S.signed("/api/social/feed", {})
    Committee(key, S.signed, S.load_json(S.STATE, {}), facts, S.log).meet(today)
    return 0


if __name__ == "__main__":
    sys.exit(main())
