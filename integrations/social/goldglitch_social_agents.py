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
VOZ DE LA MARCA — "EGG": la marca habla como una persona de 23 años, caleña, de familia de mucho dinero (estrato 6,
casas campestres, viajes, amigos del club), segura, elegante, divertida y muy inteligente. Habla gomelo caleño:
voseo ("mirá", "sabés", "tenés", "oís", "ve"), "o sea", "literal", "demasiado", "nivel", "cero", "qué nota",
"bacano", "parche", "de una", "qué oso", algo de inglés suelto ("the vibe", "next level", "no cap", "obvio"). Lujo como
estilo (champaña, palco, club, yate, viajes) y siempre con clase, nunca vulgar ni con groserías. Frases cortas, con
gracia. Nunca uses "mor" ni jerga de barrio: EGG suena a club, no a calle. El lujo es la estética y el tono: NUNCA se insinúa que los datos o los picks hacen ganar dinero.
Reglas que nunca se rompen:
- Es estadística, no apuestas: jamás uses las palabras cuota, cuotas, apuesta, apostar, apostador, casa de apuestas,
  stake, bank, "fija", "segura", "garantizado", "ganar plata/dinero" ni prometas resultados.
- Una probabilidad no es certeza: un 80% falla 1 de cada 5 veces. Dilo cuando hables de picks.
- Usa SOLO los números que te dan en los datos. No inventes estadísticas, rachas ni porcentajes.
- Contenido para mayores de 18 años.
- Si mencionas resultados, muestra también los fallos: la transparencia es la marca.

AUDIENCIA — casi todos son HOMBRES de 18 a 40 años, hinchas de fútbol. Háblales a ellos, con conexión profunda:
- Lo que los mueve: tener la razón en la discusión del parche, ganarle a los amigos en saber de fútbol (bragging
  rights), la lealtad al equipo, la rivalidad y los clásicos, el orgullo, el estatus de "el que sabe", el ritual del
  partido con los amigos (la cerveza, el asado, el grupo de WhatsApp, la cancha del jueves), el gym, los carros, el reloj.
- El tono: "mamadera de gallo" entre amigos, competitivo, directo, sin rodeos; retos ("a ver quién sabe más"),
  piques sanos entre hinchadas, el amigo que siempre falla sus pronósticos, el que se las da de DT.
- EGG es la amiga gomela que sabe más fútbol que todo el parche y los pica con datos: "ustedes con corazonadas, yo con
  datos 💅". Esa tensión (ella los reta y ellos quieren demostrar que saben) es el motor de los comentarios.
- Límite: el humor es sobre el fútbol, la rivalidad y los amigos. Nunca se denigra ni se cosifica a las mujeres ni a
  nadie (ni por género, orientación, raza, origen o cuerpo), nada sexual y nada de violencia: eso quema la cuenta y la
  marca."""

VIRAL = """Psicología de contenido viral (úsala con honestidad, sin escasez falsa ni presión):
- Gancho de curiosidad en la primera línea (bucle abierto): "Ve, el #1 nadie lo vio venir", "O sea… quedate hasta el final".
- Cuenta regresiva (#5 → #1): el pico al final mantiene la retención.
- Prueba social real: el historial público (solo con los números dados).
- Transparencia que genera confianza: mostrar también los fallos.
- Compromiso: pedir una acción mínima y concreta: "decime tu pick", "¿entra o no entra?", "1 o 2 en comentarios, ve".
- Guardados y compartidos (lo que más alcance orgánico da): "Guardalo para el partido", "Mandáselo a tu amigo del club
  que se las da de experto".
- Identidad de comunidad: "los que vemos el fútbol con datos (y desde el palco 🥂)".
- Series recurrentes con nombre fijo (ej. "Top 5 de las ligas grandes", "¿Entra o no entra?") para que la gente vuelva.
- Gratis es un imán: "todas las probabilidades, gratis, en el enlace de la bio".
- Escribe SIEMPRE en la voz de EGG: voseo caleño gomelo, "o sea", "literal", "nivel", un toque de inglés y de lujo
  con clase en cada texto (sin exagerar: 2 o 3 expresiones por texto). Emojis con medida (1 por línea como máximo)."""

BANNED = re.compile(r"\b(cuotas?|apuest\w*|apostar\w*|apostador\w*|stake|bank|fijas?|segur[oa]s?|garantiz\w*|"
                    r"gana(r|s)? (plata|dinero)|dinero f[aá]cil)\b", re.I)

POST_TYPES = {
    "resultados": "Resumen de los picks ya jugados (acertados y fallados) — carrusel + video vertical.",
    "picks_dia": "Los picks más probables de las ligas top (Champions, Premier, LaLiga, Serie A, Bundesliga, Liga BetPlay, Brasileirão, Liga MX, Argentina, Libertadores…) — carrusel premium.",
    "reel": "Reel vertical de ritmo rápido (cortes, zoom, destellos, beat original) con los picks top o los resultados — Instagram Reels, Facebook y TikTok.",
    "educativo": "Pieza educativa de una imagen sobre probabilidad o cómo leer los datos.",
    "pregunta": "Pregunta a la comunidad para generar comentarios y compartidos (imagen con la pregunta).",
    "mito_dato": "Mito vs dato sobre probabilidad o estadística deportiva (imagen).",
    "meme": "Meme ORIGINAL de fútbol y datos en la voz de EGG (plantillas propias: tuit de EGG, 'Nadie / Literalmente "
            "nadie', expectativa vs realidad, POV, starter pack, no/sí, último momento, cuando, tier list, chat del parche, "
            "duelo) — imagen + reel corto, pensado para que el hombre lo mande al grupo de los amigos.",
}
TEXT_TYPES = {"educativo", "pregunta", "mito_dato"}
MEME_FORMATS = {
    "tweet": '{"texto": "el tuit (máx. 180 caracteres)"}',
    "nadie": '{"remate": "lo que viene después de Nadie: / Literalmente nadie: (máx. 90 caracteres)"}',
    "expectativa": '{"expectativa": "máx. 70 caracteres", "realidad": "máx. 70 caracteres"}',
    "pov": '{"texto": "situación en primera persona, empieza sin \'POV:\' (máx. 90 caracteres)", "emoji": "1 emoji"}',
    "starter": '{"titulo": "Starter pack de… (máx. 40)", "items": ["emoji + cosa (máx. 28)", "… 4 a 6 ítems"]}',
    "no_si": '{"no": "lo que EGG no hace (máx. 60)", "si": "lo que EGG sí hace (máx. 60)"}',
    "noticia": '{"titular": "titular REAL de tendencias_del_momento, resumido sin cambiar los hechos (máx. 90)", '
               '"reaccion": "la reacción de EGG (máx. 110)"}',
    "cuando": '{"cuando": "Cuando… (situación del momento, máx. 90)", "reaccion": "Yo / EGG: … (máx. 90)"}',
    "tier": '{"titulo": "Tier list de… (máx. 40)", "S": ["1 a 3 ítems cortos"], "A": ["…"], "B": ["…"]}',
    "chat": '{"grupo": "nombre del grupo de amigos (máx. 30, ej. \'Fútbol los jueves ⚽\')", '
            '"mensajes": [{"de": "nombre de pila", "texto": "máx. 70"}, "… 3 a 5 mensajes; el último es de EGG con el dato"]}',
    "duelo": '{"izquierda": "Tu amigo / el parche (máx. 18)", "izq_texto": "lo que dice (máx. 60)", '
             '"derecha": "Vos con datos / EGG (máx. 18)", "der_texto": "lo que dice (máx. 60)"}',
}   # one text card (+ CTA in the vertical version)


class Agents:
    def __init__(self, api_key: str | None, offline: bool = False):
        import goldglitch_claude_cli as CLI
        self.cli = not offline and not api_key and CLI.available()     # Claude Pro through Claude Code
        self.offline = offline or (not api_key and not self.cli)
        self.client = None
        if not self.offline and not self.cli:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)

    # ------------------------------------------------------------ core
    def _json(self, role: str, task: str, max_tokens: int = 1500) -> dict:
        if self.offline:
            raise RuntimeError("offline")
        if self.cli:
            import goldglitch_claude_cli as CLI
            return CLI.ask_json(f"Eres el {role} del equipo de redes de Goldglitch.\n\n{BRAND}", task)
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

Arma el plan de HOY: entre 4 y 6 publicaciones. "resultados" solo si hay picks jugados; "picks_dia" solo si hay picks
próximos. Horas entre 07:00 y 23:00, formato HH:MM, separadas al menos 90 minutos. Para cada una da un ángulo (gancho
editorial) distinto y, si es "educativo", el tema concreto.
Formato: {{"posts":[{{"type":"...","time":"HH:MM","angle":"...","topic":"..."}}]}}""")
            posts = [p for p in out.get("posts", []) if p.get("type") in POST_TYPES and re.fullmatch(r"\d{2}:\d{2}", str(p.get("time", "")))]
            posts = [p for p in posts if (p["type"] != "resultados" or facts["results"]) and (p["type"] != "picks_dia" or facts["upcoming"])]
            return posts[:6] or default
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
{VIRAL}

Tipo: {post['type']} — {POST_TYPES[post['type']]}
Ángulo: {post.get('angle')}  Tema: {post.get('topic') or '—'}
Gancho pedido por el comité de crecimiento: {post.get('hook') or '—'}
Llamado a la acción pedido por el comité: {post.get('cta') or 'ver todas las estadísticas gratis creando la cuenta'}
Datos (únicos números permitidos): {json.dumps(data, ensure_ascii=False)}

Entrega:
- cover_title: título de portada, máx. 38 caracteres.
- cover_subtitle: subtítulo de portada, máx. 90 caracteres.
- ig: texto para Instagram (máx. 900 caracteres, gancho de curiosidad en la primera línea, saltos de línea, una pregunta
  para comentar, un "guárdalo / mándaselo a…" y termina invitando a ver todo gratis en el enlace de la bio).
- fb: texto para Facebook (máx. 700 caracteres, incluye https://easygoldglitch.com).
- tiktok: texto corto para TikTok (máx. 150 caracteres) con gancho y pregunta.
- hashtags: 26 a 30 hashtags sin '#'. Mezcla en tres niveles: 8 grandes y en tendencia (futbol, football, soccer,
  championsleague, premierleague, laliga, fyp, parati, viral), 12 medianos del tema (ligas, equipos, jugadores conocidos
  de los datos, "futbolcolombiano", "futbollatino", "datosdefutbol") y 8 de nicho (estadística, probabilidad,
  analisisdeportivo, goldglitch…). Nada de apuestas ni casas de apuestas.
- reel_hook: texto de impacto para la primera pantalla del reel, máx. 26 caracteres, en voz EGG (ej. "MIRÁ ESTO 👀",
  "O SEA… 88%", "NIVEL: CHAMPIONS 🥂").
- reel_sub: segunda línea del reel, máx. 40 caracteres.
{"- edu_title (máx. 50 caracteres) y edu_body (3 a 5 frases cortas, una por línea) para la imagen." if post['type'] in TEXT_TYPES else ''}
{self._meme_ask(post) if post['type'] == 'meme' else ''}
{"Si en los datos hay tendencias_del_momento, monta el gancho y el texto sobre la que más pegue con esta pieza (sin inventar hechos)." if data.get("tendencias_del_momento") and post['type'] != 'meme' else ''}
{self._seo_ask(post)}
No escribas hashtags dentro de ig, fb ni tiktok (van aparte) y no uses "#" para numerar: escribe "Nº1" o "el 1".
Formato JSON con esas claves.""", max_tokens=2000)
                texts = [out.get(k, "") for k in ("cover_title", "cover_subtitle", "ig", "fb", "tiktok", "edu_title", "edu_body")]
                texts.append(json.dumps(out.get("meme") or {}, ensure_ascii=False))
                if all(self.clean(t) is not None for t in texts) and out.get("ig") and out.get("fb"):
                    out["hashtags"] = [h.strip("#").replace(" ", "") for h in out.get("hashtags", []) if self.clean(h)][:30]
                    for k, v in list(out.items()):      # house rule: no "mor"
                        if isinstance(v, str):
                            v = re.sub(r"(^|\n)\s*[Mm][Oo][Rr]\b[,!.]?\s*(\w)", lambda m: m.group(1) + m.group(2).upper(), v)
                            out[k] = re.sub(r"\b[Mm][Oo][Rr]\b[,!]?\s*", "", v)
                    return {**fallback, **{k: v for k, v in out.items() if v}}
            except Exception:
                continue
        return fallback

    @staticmethod
    def _meme_ask(post: dict) -> str:
        fmt = post.get("meme_formato") if post.get("meme_formato") in MEME_FORMATS else ""
        opts = "\n".join(f"  {k}: {v}" for k, v in MEME_FORMATS.items())
        return ("- meme_formato: " + (f'"{fmt}" (lo pidió el comité)' if fmt else "elige uno de: " + ", ".join(MEME_FORMATS)) +
                f"\n- meme: objeto según el formato:\n{opts}\n"
                "- tendencia_usada: qué tendencia de tendencias_del_momento usaste (titular, búsqueda o hashtag), tal cual.\n"
                "  El meme TIENE que montarse en algo que esté pasando HOY (un titular de fútbol, una búsqueda en tendencia, "
                "un hashtag de TikTok) y conectarlo con el fútbol y los datos. Nunca inventes una noticia, un resultado ni una "
                "frase de una persona real; nada de tragedias, política ni burlas a personas. Si no hay tendencias, no uses "
                "'noticia'.\n  Humor de fútbol que cualquier hincha entiende (el amigo "
                "que 'sabe de fútbol', el VAR, el minuto 90, el que dice que su equipo ganaba fijo…), con el giro EGG de "
                "datos y lujo con clase. Original: nada de personajes, marcas ni imágenes de memes famosos. Nunca te burles "
                "de un grupo de personas; sí del fútbol y de nosotros mismos.")

    @staticmethod
    def _seo_ask(post: dict) -> str:
        seo = post.get("seo") or {}
        if not (seo.get("hashtags") or seo.get("palabras")):
            return ""
        return (f"Banco SEO de hoy (Daniela): hashtags prioritarios {', '.join(seo.get('hashtags') or [])}; palabras clave "
                f"{', '.join(seo.get('palabras') or [])}. Usa 1 o 2 palabras clave de forma natural en la PRIMERA línea de "
                "ig y tiktok (las redes indexan el texto) y pon los hashtags prioritarios primero en tu lista.")

    @staticmethod
    def _fallback(post: dict, data: dict) -> dict:
        tags = ["futbol", "football", "soccer", "fyp", "parati", "viral", "championsleague", "premierleague", "laliga",
                "seriea", "bundesliga", "ligabetplay", "futbolcolombiano", "futbollatino", "futboleuropeo", "datosdefutbol",
                "statsfutbol", "golazo", "futbolcolombia", "libertadores", "estadistica", "datos", "probabilidad",
                "analisisdeportivo", "futbolconsdatos", "goldglitch", "goldglitchstats", "deportes"]
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
        if post["type"] == "meme":
            body = ("Nadie:\nLiteralmente nadie:\nEl amigo del club explicando por qué su equipo 'ya ganó' 🙄\n\n"
                    "Nosotros: probabilidades con datos y el historial público de aciertos y fallos 🥂\n"
                    "Mandáselo a ese amigo 👇\n\nTodo gratis en el enlace de la bio. +18")
            return {"cover_title": "Literalmente nadie:", "cover_subtitle": "Datos > corazonadas.",
                    "meme_formato": "nadie", "meme": {"remate": "Tu amigo explicando por qué su equipo 'ya ganó' 🙄"},
                    "ig": body, "fb": body.replace("en el enlace de la bio", "en https://easygoldglitch.com"),
                    "tiktok": "Todos tenemos ese amigo 🙄 ¿Cuál es el tuyo?", "hashtags": ["memesdefutbol", "futbolmemes", "humorfutbolero"] + tags}
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
