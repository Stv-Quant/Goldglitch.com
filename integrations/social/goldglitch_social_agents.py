"""El equipo de agentes de redes de Goldglitch (Claude Haiku 5.5 por la API de Anthropic).

  Estratega         decide qué se publica hoy y a qué hora, con lo aprendido en el informe semanal
  Redactor          escribe el texto de cada pieza para Instagram, Facebook y TikTok
  Community manager lee los comentarios nuevos y responde, oculta o ignora
  Analista          revisa las métricas de la semana y deja notas para el Estratega

Los números nunca los inventa un agente: vienen de la web (picks y resultados) y se pasan como datos.
"""
from __future__ import annotations

import json
import os
import re

MODEL = os.environ.get("SOCIAL_MODEL", "claude-haiku-5-5")

BRAND = """Goldglitch Stats (easygoldglitch.com) es una plataforma colombiana de estadística deportiva: un modelo
calcula probabilidades de partidos (fútbol, NBA, NHL, e-sports) y publica un historial público de aciertos y fallos.
Tono: claro, cercano, seguro y honesto, en español de Colombia; frases cortas; nada de exageraciones.
Reglas que nunca se rompen:
- Es estadística, no apuestas: jamás uses las palabras cuota, cuotas, apuesta, apostar, apostador, casa de apuestas,
  stake, bank, "fija", "segura", "garantizado", "ganar plata/dinero" ni prometas resultados.
- Una probabilidad no es certeza: un 80% falla 1 de cada 5 veces. Dilo cuando hables de picks.
- Usa SOLO los números que te dan en los datos. No inventes estadísticas, rachas ni porcentajes.
- Contenido para mayores de 18 años.
- Si mencionas resultados, muestra también los fallos: la transparencia es la marca."""

BANNED = re.compile(r"\b(cuotas?|apuest\w*|apostar\w*|apostador\w*|stake|bank|fijas?|segur[oa]s?|garantiz\w*|"
                    r"gana(r|s)? (plata|dinero)|dinero f[aá]cil)\b", re.I)

POST_TYPES = {
    "resultados": "Resumen de los picks ya jugados (acertados y fallados) — carrusel + video vertical.",
    "picks_dia": "Los picks más probables de los próximos partidos — carrusel + video vertical + historia.",
    "educativo": "Pieza educativa de una imagen sobre probabilidad o cómo leer los datos.",
    "pregunta": "Pregunta a la comunidad para generar comentarios y compartidos (imagen con la pregunta).",
    "mito_dato": "Mito vs dato sobre probabilidad o estadística deportiva (imagen).",
}
TEXT_TYPES = {"educativo", "pregunta", "mito_dato"}   # one text card (+ CTA in the vertical version)


class Agents:
    def __init__(self, api_key: str | None, offline: bool = False):
        self.offline = offline or not api_key
        self.client = None
        if not self.offline:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)

    # ------------------------------------------------------------ core
    def _json(self, role: str, task: str, max_tokens: int = 1500) -> dict:
        if self.offline:
            raise RuntimeError("offline")
        last = None
        for _ in range(2):
            msg = self.client.messages.create(
                model=MODEL, max_tokens=max_tokens,
                system=f"Eres el {role} del equipo de redes de Goldglitch.\n\n{BRAND}\n\nResponde SOLO con un objeto JSON válido, sin texto adicional.",
                messages=[{"role": "user", "content": task}])
            text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
            text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
            try:
                return json.loads(text[text.find("{"): text.rfind("}") + 1])
            except ValueError as e:
                last = e
        raise RuntimeError(f"El {role} no devolvió JSON válido: {last}")

    @staticmethod
    def clean(text: str) -> str | None:
        """Hard stop for wording that would turn a statistics account into a betting one."""
        return None if BANNED.search(text or "") else text

    # ------------------------------------------------------------ Estratega
    def plan(self, today: str, facts: dict, memory: str) -> list[dict]:
        default = []
        if facts["results"]:
            default.append({"type": "resultados", "time": "09:00", "angle": "Transparencia: cómo nos fue"})
        if facts["upcoming"]:
            default.append({"type": "picks_dia", "time": "11:30", "angle": "Lo más probable de hoy según el modelo"})
        default.append({"type": "educativo", "time": "19:00", "angle": "Qué significa una probabilidad"})
        if self.offline:
            return default
        try:
            out = self._json("Estratega", f"""Hoy es {today} (hora de Colombia).
Tipos de publicación disponibles: {json.dumps(POST_TYPES, ensure_ascii=False)}
Datos de hoy: {len(facts['upcoming'])} picks de 80% o más en las próximas 36 h; {len(facts['results'])} picks ya jugados
para resumir; historial: {json.dumps(facts['record'])}.
Lo aprendido en semanas anteriores (puede estar vacío):
{memory or '—'}

Arma el plan de HOY: entre 2 y 4 publicaciones. "resultados" solo si hay picks jugados; "picks_dia" solo si hay picks
próximos. Horas entre 07:00 y 22:00, formato HH:MM, separadas al menos 2 horas. Para cada una da un ángulo (gancho
editorial) distinto y, si es "educativo", el tema concreto.
Formato: {{"posts":[{{"type":"...","time":"HH:MM","angle":"...","topic":"..."}}]}}""")
            posts = [p for p in out.get("posts", []) if p.get("type") in POST_TYPES and re.fullmatch(r"\d{2}:\d{2}", str(p.get("time", "")))]
            posts = [p for p in posts if (p["type"] != "resultados" or facts["results"]) and (p["type"] != "picks_dia" or facts["upcoming"])]
            return posts[:4] or default
        except Exception:
            return default

    # ------------------------------------------------------------ Redactor
    def write(self, post: dict, data: dict) -> dict:
        """→ {cover_title, cover_subtitle, ig, fb, tiktok, hashtags[]} (plus edu_title/edu_body for 'educativo')."""
        fallback = self._fallback(post, data)
        if self.offline:
            return fallback
        for _ in range(2):
            try:
                out = self._json("Redactor", f"""Escribe los textos de esta publicación.
Tipo: {post['type']} — {POST_TYPES[post['type']]}
Ángulo: {post.get('angle')}  Tema: {post.get('topic') or '—'}
Gancho pedido por el comité de crecimiento: {post.get('hook') or '—'}
Llamado a la acción pedido por el comité: {post.get('cta') or 'ver todas las estadísticas gratis creando la cuenta'}
Datos (únicos números permitidos): {json.dumps(data, ensure_ascii=False)}

Entrega:
- cover_title: título de portada, máx. 38 caracteres.
- cover_subtitle: subtítulo de portada, máx. 90 caracteres.
- ig: texto para Instagram (máx. 900 caracteres, gancho en la primera línea, saltos de línea, termina invitando a
  ver todas las estadísticas en el enlace de la bio).
- fb: texto para Facebook (máx. 700 caracteres, incluye https://easygoldglitch.com).
- tiktok: texto corto para TikTok (máx. 150 caracteres).
- hashtags: 6 a 10 hashtags sin '#', en minúscula, de estadística y deporte (nada de apuestas).
{"- edu_title (máx. 50 caracteres) y edu_body (3 a 5 frases cortas, una por línea) para la imagen." if post['type'] in TEXT_TYPES else ''}
Formato JSON con esas claves.""", max_tokens=2000)
                texts = [out.get(k, "") for k in ("cover_title", "cover_subtitle", "ig", "fb", "tiktok", "edu_title", "edu_body")]
                if all(self.clean(t) is not None for t in texts) and out.get("ig") and out.get("fb"):
                    out["hashtags"] = [h.strip("#").lower() for h in out.get("hashtags", []) if self.clean(h)][:10]
                    return {**fallback, **{k: v for k, v in out.items() if v}}
            except Exception:
                continue
        return fallback

    @staticmethod
    def _fallback(post: dict, data: dict) -> dict:
        tags = ["estadistica", "futbol", "datos", "probabilidad", "analisisdeportivo", "goldglitch"]
        if post["type"] == "resultados":
            won, n = data.get("won", 0), data.get("n", 0)
            t = f"Así le fue al modelo: {won} de {n}"
            body = (f"{t}.\n\nPublicamos todos los picks antes del partido y aquí están los resultados, aciertos y fallos.\n"
                    "Un 80% falla 1 de cada 5 veces: lo que medimos es si el modelo está bien calibrado.\n\n"
                    "Historial completo en el enlace de la bio. +18")
            return {"cover_title": "Resultados del modelo", "cover_subtitle": f"{won} de {n} picks acertados. Todo, también los fallos.",
                    "ig": body, "fb": body.replace("en el enlace de la bio", "en https://easygoldglitch.com/historial"),
                    "tiktok": f"{won} de {n}: así le fue al modelo. Probabilidad, no certeza.", "hashtags": tags}
        if post["type"] == "picks_dia":
            n = len(data.get("picks", []))
            body = (f"Lo más probable según el modelo: {n} picks de 80% o más.\n\n"
                    "Son probabilidades, no certezas: un 80% falla 1 de cada 5 veces.\n"
                    "Todas las estadísticas, partido a partido, en el enlace de la bio. +18")
            return {"cover_title": "Lo más probable hoy", "cover_subtitle": "Los picks del modelo con 80% o más.",
                    "ig": body, "fb": body.replace("en el enlace de la bio", "en https://easygoldglitch.com"),
                    "tiktok": "Lo más probable hoy según el modelo. Probabilidad, no certeza.", "hashtags": tags}
        body = ("¿Qué significa que algo tenga 80% de probabilidad?\n\nQue de cada 10 veces, unas 8 sale y 2 no. "
                "Por eso medimos el modelo con cientos de partidos, no con uno.\n\nMás en el enlace de la bio. +18")
        return {"cover_title": "¿Qué es un 80%?", "cover_subtitle": "Probabilidad, no certeza.",
                "edu_title": "Un 80% no es una garantía", "edu_body": "De cada 10 veces, unas 8 sale.\nY unas 2 no.\nPor eso se mide con muchos partidos.\nNo con uno.",
                "ig": body, "fb": body.replace("en el enlace de la bio", "en https://easygoldglitch.com"),
                "tiktok": "¿Qué significa 80%? Probabilidad, no certeza.", "hashtags": tags}

    # ------------------------------------------------------------ Community manager
    def moderate(self, comments: list[dict]) -> list[dict]:
        """→ [{id, action: reply|hide|ignore, text}] in the same order."""
        if not comments:
            return []
        if self.offline:
            return [{"id": c["id"], "action": "ignore"} for c in comments]
        try:
            out = self._json("Community manager", f"""Estos son comentarios nuevos en nuestras publicaciones:
{json.dumps([{k: c[k] for k in ('id', 'net', 'user', 'text', 'post')} for c in comments], ensure_ascii=False)}

Para cada uno decide:
- "reply": responde breve (máx. 220 caracteres), amable y útil, en español de Colombia. Preguntas sobre la web:
  explica e invita a easygoldglitch.com. Si piden "la fija" o consejos de apuestas: aclara con respeto que mostramos
  probabilidades, no certezas, y que no damos asesoría. Críticas honestas: agradece y responde con datos o con el
  historial público (easygoldglitch.com/historial).
- "hide": insultos, odio, acoso, spam, estafas, enlaces sospechosos o promoción de apuestas.
- "ignore": emojis sueltos, comentarios sin contenido o que no necesitan respuesta.
Nunca prometas resultados ni uses lenguaje de apuestas.
Formato: {{"actions":[{{"id":"...","action":"reply|hide|ignore","text":"..."}}]}}""", max_tokens=3000)
            acts = {a.get("id"): a for a in out.get("actions", [])}
            res = []
            for c in comments:
                a = acts.get(c["id"], {"action": "ignore"})
                if a.get("action") == "reply" and not self.clean(a.get("text", "")):
                    a = {"action": "ignore"}
                res.append({"id": c["id"], "action": a.get("action", "ignore"), "text": (a.get("text") or "")[:300]})
            return res
        except Exception:
            return [{"id": c["id"], "action": "ignore"} for c in comments]

    # ------------------------------------------------------------ Analista
    def review(self, insights: list[dict], posts: list[dict], memory: str) -> str:
        if self.offline:
            return memory
        try:
            out = self._json("Analista", f"""Métricas de Instagram de los últimos 7 días: {json.dumps(insights, ensure_ascii=False)[:6000]}
Publicaciones hechas: {json.dumps(posts, ensure_ascii=False)[:4000]}
Notas anteriores: {memory or '—'}

Escribe notas prácticas para el Estratega de la próxima semana: qué tipos, horas y ángulos funcionaron mejor
(alcance, guardados, compartidos, comentarios), qué evitar y qué probar. Máximo 10 viñetas cortas.
Formato: {{"notes":"- ...\\n- ..."}}""", max_tokens=1200)
            return str(out.get("notes") or memory)[:4000]
        except Exception:
            return memory
