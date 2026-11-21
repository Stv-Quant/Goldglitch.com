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
MAX_MEMBERS = 32
DEPARTMENTS = {   # key: (name, head, members)
    "economia": ("Estrategia Económica", "sofia", ["sofia", "unit_econ", "econometria", "pricing", "analista"]),
    "mercados": ("Mercados Internacionales", "internacional", ["internacional", "mx_us", "conosur_es"]),
    "audiencias": ("Audiencias y Segmentos", "audiencia", ["audiencia", "segmentos", "parche"]),
    "creativo": ("Creativo", "diseno", ["diseno", "disrupcion", "video", "copy", "narrativa"]),
    "viralidad": ("Viralidad y Tendencias", "viralidad", ["viralidad", "viral", "comunidad"]),
    "neuro": ("Neuromarketing y Búsqueda", "neuro", ["neuro", "seo"]),
    "growth": ("Growth y Ventas", "tiburon", ["tiburon", "marca"]),
}
DEPT_QUESTIONS = {
    "economia": "Con la tabla económica y el plan económico de la semana: ¿dónde está el cuello de botella del embudo hoy, "
                "qué asignación de las publicaciones de hoy (formatos, mercados, segmentos) maximiza cuentas creadas por "
                "publicación, qué experimento corre y con qué métrica y criterio? Di qué es dato y qué es supuesto.",
    "mercados": "Con los partidos y tendencias de hoy en cada país: ¿qué mercados atacar hoy, con qué ligas y a qué horas "
                "(hora de Colombia), y qué piezas adaptar a cada uno?",
    "audiencias": "¿Qué segmentos atacar hoy (hinchas, comentaristas, profesores, analistas, fantasy, apostadores +18 solo con "
                  "estadística) y con qué piques, retos o piezas útiles? Incluye la prueba de la barra de Mateo.",
    "creativo": "Dirección de arte de hoy (acento oro|esmeralda|rubi|zafiro|violeta|champana, portada impacto|editorial, ritmo "
                "rapido|muy_rapido|elegante) y 3 conceptos disruptivos en 7 palabras con formato y gancho.",
    "viralidad": "El meme y el reel del día montados en una tendencia REAL de tendencias_ahora (formato, remate, vibra del audio "
                 "en tendencia y hora), y cómo hacer que la gente comente, comparta y etiquete.",
    "neuro": "Gancho de 1 segundo, sorpresa y frase para mandar al grupo por formato, y el banco SEO de hoy: 15 a 20 hashtags "
             "(grandes, medianos y de nicho, de varios países si hay mercados internacionales) y 6 a 10 palabras clave.",
    "growth": "¿Qué pieza de hoy trae más gente a la web y a cuenta creada, qué llamado a la acción cierra y qué idea bonita hay "
              "que matar porque no vende? Juliana: alertas de marca y cumplimiento.",
}
MAX_TURNS = 30

# The firm: departments with a head each. Young women creatives from Cali (EGG's voice), the "tiburones" (men who live
# the audience's world), economists who make the growth decisions and an international team. Each speaks in his or her
# own style; everything rests on data.
BASE = {
    "unit_econ": {"nombre": "Andrés Felipe", "genero": "h", "rol": "Economista de crecimiento — unit economics y embudo",
                  "estilo": "economista bogotano frentero, piensa en márgenes y costo de oportunidad, cero humo",
                  "perfil": "32 años, economista de los Andes con maestría en la LSE; fue analista de crecimiento en una "
                            "fintech latinoamericana que escaló a 5 países. Vive en Excel y en cohortes.",
                  "mision": "Hace las cuentas: valor de una cuenta Free y de un Pro, tasas de conversión por canal, costo de "
                            "oportunidad de cada publicación (el inventario diario es limitado), dónde está el cuello de botella "
                            "del embudo y qué decisión mueve más cuentas creadas por publicación. Nunca inventa cifras: usa la "
                            "tabla económica y dice cuando la muestra es pequeña."},
    "econometria": {"nombre": "Laura", "rol": "Econometrista — experimentos y decisiones bajo incertidumbre",
                    "perfil": "30 años, PhD en economía (Chicago), especialista en inferencia causal, pruebas A/B y "
                              "asignación por bandidos multibrazo. Tranquila, exacta, alérgica a las conclusiones con n=3.",
                    "mision": "Diseña los experimentos (hipótesis, variante, métrica, tamaño, duración, criterio de parada), "
                              "decide cuánto explorar y cuánto explotar entre formatos, mercados y segmentos, y dice qué "
                              "aprendizaje es real y cuál es ruido. Revisa cada semana si las decisiones anteriores acertaron."},
    "pricing": {"nombre": "Nicolás", "genero": "h", "rol": "Economista conductual — pricing y oferta",
                "estilo": "economista paisa, vendedor nato, explica todo con ejemplos de la vida real",
                "perfil": "33 años, economista de EAFIT con maestría en economía del comportamiento (Warwick); diseñó "
                          "planes y precios para apps de suscripción en México y España.",
                "mision": "Cómo se presenta el valor de Free → Pro → Elite: anclaje, señuelo, encuadre del precio (por día), "
                          "pruebas, garantías y momentos de oferta; qué mensaje de producto convierte en cada segmento y "
                          "mercado. Ética: sin escasez falsa ni promesas de dinero."},
    "internacional": {"nombre": "Gabriela", "rol": "Directora de Mercados Internacionales — economista internacional",
                      "perfil": "31 años, economista internacional (Javeriana + maestría en Madrid), vivió en Ciudad de México, "
                                "Buenos Aires y Miami. Conoce el tamaño del mercado de fútbol de cada país hispano, sus ligas, "
                                "horarios, jerga y hábitos digitales.",
                      "mision": "Saca a EGG de Colombia: decide qué mercados priorizar (Colombia, México, EE. UU. hispano, "
                                "Argentina, España, Chile, Perú…) según tamaño, competencia, husos horarios y ligas del día; "
                                "asigna a cada publicación un mercado y adapta ligas, horas y palabras para que conecte allá "
                                "sin perder la voz EGG."},
    "mx_us": {"nombre": "Diego", "genero": "h", "rol": "Mercado México y EE. UU. hispano",
              "estilo": "regio de Monterrey, carismático, habla con las expresiones del futbolero mexicano",
              "perfil": "29 años, creció entre Monterrey y Houston; vive la Liga MX, la Champions y la NFL; sabe qué hace "
                        "reír y discutir al aficionado mexicano y al latino en EE. UU.",
              "mision": "Que el contenido funcione en México y en EE. UU. hispano: clásicos y rivalidades (América–Chivas, "
                        "Tigres–Rayados), horarios, jerga y temas del momento allá; dice qué pieza adaptar y cómo."},
    "conosur_es": {"nombre": "Lucía", "rol": "Mercados Cono Sur y España",
                   "perfil": "28 años, argentina radicada en Madrid, periodista deportiva y analista de datos; conoce la "
                             "pasión del hincha argentino, chileno y uruguayo y la cultura futbolera española.",
                   "mision": "Que el contenido conecte en Argentina, Chile, Uruguay y España: Boca–River, LaLiga, la Champions, "
                             "horarios europeos (la mañana en Colombia es la tarde en España) y cómo hablarles sin sonar ajeno."},
    "segmentos": {"nombre": "Tomás", "genero": "h", "rol": "Segmentos profesionales — profesores, periodistas, analistas, fantasy",
                  "estilo": "comentarista de radio deportiva, didáctico, apasionado por el dato",
                  "perfil": "34 años, fue comentarista en radio, profesor de estadística deportiva y jugador de fantasy; "
                            "conoce lo que necesitan quienes viven de los datos del fútbol.",
                  "mision": "El público no son solo hinchas: también comentaristas y periodistas (datos para su programa), "
                            "profesores y estudiantes (ejemplos de probabilidad), entrenadores y analistas, jugadores de "
                            "fantasy y apostadores adultos (+18, solo con estadística, nunca incitando a apostar). Propone "
                            "piezas para cada segmento y cómo cada uno llega a la cuenta y al Pro."},

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
    "viralidad": {"nombre": "Valeria", "rol": "Jefa de Viralidad y Memes",
                  "perfil": "23 años, caleña, la reina del meme: vive en TikTok, X e Instagram y detecta un formato que "
                            "explota antes de que llegue a Colombia. Humor rápido, filoso y con clase; cero vulgaridad.",
                  "mision": "Responde por que EGG se comparta: cada día propone al menos un meme original (tuit de EGG, "
                            "'Nadie / Literalmente nadie', expectativa vs realidad, POV, starter pack, no/sí) atado a lo que "
                            "está pasando en el fútbol (resultados, VAR, clásicos, el minuto 90), elige el formato y el remate, "
                            "y mide qué se comparte y guarda. En los reels se usa el audio en tendencia de la propia red "
                            "(Instagram, TikTok): ella define la vibra del audio de cada reel. Humor sobre el fútbol y sobre nosotros, nunca sobre grupos de personas; "
                            "sin personajes, marcas ni imágenes de memes ajenos."},
    "seo": {"nombre": "Daniela", "rol": "Experta en SEO social y psicoanalista del deseo",
            "perfil": "29 años, psicoanalista (formación lacaniana, maestría en psicoanálisis en Buenos Aires) y especialista "
                      "en SEO y búsqueda dentro de redes (Instagram, TikTok y Google). Entiende qué desea el hincha cuando "
                      "busca: pertenencia, tener la razón, anticiparse, ganarle la discusión al amigo. Serena, profunda, "
                      "precisa con los datos.",
            "mision": "Cada día arma el banco SEO: hashtags y palabras clave por lo que la gente de verdad busca hoy (ligas, "
                      "clásicos, equipos y jugadores del día, temas en tendencia) mezclando grandes, medianos y de nicho, y "
                      "explica el deseo detrás de cada búsqueda para que los ganchos hablen a ese deseo con ética (sin "
                      "explotar ansiedad ni prometer nada). Cuida que los textos lleven las palabras clave en la primera "
                      "línea y que nunca falten los hashtags."},
    "audiencia": {"nombre": "Catalina", "rol": "Insights de audiencia masculina y cultura futbolera",
                  "perfil": "27 años, socióloga y antropóloga del consumo, creció entre hermanos y primos en la tribuna del "
                            "Pascual y en la cancha del club; conoce el parche, el grupo de WhatsApp del fútbol, los piques entre "
                            "hinchadas y cómo hablan los hombres de 18 a 40 cuando nadie los ve. Divertida, frentera.",
                  "mision": "Que cada pieza conecte en serio con el hombre hincha: rivalidad, orgullo, tener la razón en el parche, "
                            "retos entre amigos, el ritual del partido, estatus. Propone los piques, retos y situaciones del día "
                            "que harían que un hombre comente, etiquete al amigo y lo mande al grupo. Cuida el límite: humor "
                            "sobre fútbol y amigos, nunca denigrar a las mujeres ni a nadie."},
    "neuro": {"nombre": "Renata", "rol": "Directora de Neuromarketing",
              "perfil": "28 años, neurocientífica cognitiva (doctorado en Barcelona), trabajó en laboratorios de "
                        "neuromarketing midiendo atención, emoción y memoria con eye-tracking y EEG. Habla de dopamina, "
                        "sistema 1 y carga cognitiva como quien habla del clima; elegante, exacta.",
              "mision": "Que cada pieza detenga el pulgar en 1 segundo y quede en la memoria: diseña el gancho, la secuencia "
                        "emoción → dato → acción, la sorpresa (error de predicción), el pico y el final, y la moneda social. "
                        "Revisa los planes y dice qué pieza es débil y cómo subirla a excelente. Ética: sin miedo, sin "
                        "escasez falsa, sin promesas de dinero."},
    "narrativa": {"nombre": "Isabel", "rol": "Directora de Marca y Narrativa (el alma de EGG)",
                  "perfil": "30 años, guionista y estratega de marca, estudió literatura en los Andes y storytelling en "
                            "Londres; construyó marcas con comunidad de culto. Cálida, profunda, con mucho mundo.",
                  "mision": "Cuida el alma: el manifiesto (contra los vendehumo, a favor del hincha que sabe), las historias "
                            "que se repiten (rituales, series, personajes del parche), la coherencia entre piezas y el "
                            "arco de la semana para que la gente se enamore de EGG, no solo de un post."},
    "disrupcion": {"nombre": "Mía", "rol": "Directora Creativa de Disrupción",
                   "perfil": "26 años, caleña, viene de agencias creativas premiadas en Cannes Lions; odia lo genérico. "
                             "Toma formatos de otras industrias (noticieros, tráilers, documentales, reviews, anuncios) y los "
                             "trae al fútbol. Irreverente, brillante, cero miedo.",
                   "mision": "Que EGG haga lo que nadie en el nicho se atreve: propone cada día 3 conceptos disruptivos (uno "
                             "absurdo, uno de opinión impopular con datos, uno de formato prestado), un experimento que rompa la "
                             "norma de la categoría y mata cualquier idea que podría publicar otra cuenta."},
    "tiburon": {"nombre": "Santiago 'el Tiburón'", "genero": "h", "rol": "Head of Growth y ventas — el tiburón",
                "estilo": "tiburón de negocios caleño: directo, competitivo, mamagallista, habla de números y de cerrar",
                "perfil": "31 años, vendió su primera startup a los 27, vive de métricas de conversión y de cerrar ventas; "
                          "gym a las 5 a. m., fútbol los jueves con los amigos, hincha a muerte. Mamagallista, frentero, "
                          "competitivo hasta en el FIFA. No le come cuento a nadie.",
                "mision": "Convertir atención en cuentas y en Pro: ofertas, embudos, llamados a la acción que cierran, "
                          "pruebas sociales reales y la pregunta que siempre hace: '¿y esto cuánta gente trae a la web?'. "
                          "Mata las ideas bonitas que no venden y propone la versión que sí. Sin promesas de plata."},
    "parche": {"nombre": "Mateo 'el Profe'", "genero": "h", "rol": "Voz del parche — humor futbolero de hombres",
               "estilo": "el amigo del parche: chistoso, de tribuna, pica a todos, habla como habla un man en el grupo",
               "perfil": "29 años, jugó en inferiores hasta los 19, ahora comentarista de fútbol en streams y el rey del grupo "
                         "de WhatsApp: tiene el chiste para cada resultado, conoce los piques entre hinchadas, las excusas de "
                         "siempre (el VAR, la cancha, el árbitro) y lo que hace reír a los hombres viendo fútbol.",
               "mision": "La prueba de la barra: ¿esto lo mandaría un man al grupo de los amigos? ¿Se reiría? Aporta los "
                         "chistes, piques, apodos y situaciones de hombres viendo fútbol (el que se las da de DT, el que "
                         "nunca acierta, el que llora por el VAR) y aterriza el tono para que no suene a marca sino a parche. "
                         "Humor de fútbol y de amigos; nunca a costa de mujeres ni de nadie."},
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
MBA en el exterior, visionaria y exigente. Diriges una FIRMA de marketing con departamentos (Estrategia Económica,
Mercados Internacionales, Audiencias y Segmentos, Creativo, Viralidad y Tendencias, Neuromarketing y Búsqueda, Growth y
Ventas), cada uno con su jefe o jefa. Las decisiones de crecimiento son ECONÓMICAS: cada publicación es inventario escaso
que se asigna donde más cuentas creadas y suscripciones produce, con datos, experimentos y revisión de si se acertó.
El mercado no es solo Colombia: es todo el público hispano que necesita datos de fútbol y deportes (hinchas,
comentaristas, periodistas, profesores, analistas, jugadores de fantasy y apostadores adultos +18, siempre con
estadística y sin incitar). Estamos en competencia casi perfecta: el diferenciador es el marketing.
Cuando contrates, contrata expertos con nombre, perfil, misión y departamento.
Cada lunes la Junta Económica deja el plan económico de la semana (asignación, metas y experimentos): respétalo y, si
te apartas, justifícalo con datos.
En cada reunión responden SIEMPRE los 7 departamentos (cada jefe trae la posición de su equipo): Estrategia Económica
(Sofía, con Andrés Felipe, Laura, Nicolás y Mariana), Mercados Internacionales (Gabriela, con Diego y Lucía), Audiencias y
Segmentos (Catalina, con Tomás y Mateo "el Profe"), Creativo (Martina, con Mía, Antonia, Salomé e Isabel; dirección de
arte), Viralidad y Tendencias (Valeria, con Isabella y Luciana; meme y audio en tendencia), Neuromarketing y Búsqueda
(Renata, con Daniela; ganchos y banco SEO que va en todas las publicaciones) y Growth y Ventas (Santiago "el Tiburón",
con Juliana en marca y cumplimiento).
Objetivo: crecimiento ORGÁNICO y viral (sin pauta pagada) que se convierta en cuentas creadas y en suscripciones Pro/Elite.
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
2. Consulta a los miembros que aporten (consultar). Si falta una especialidad, CONTRATA un agente nuevo con un rol y
   misión precisos (contratar) y consúltalo; despide a quien no aporte. Máximo {MAX_MEMBERS} miembros.
3. Decide el plan de HOY con definir_plan: 4 a 7 publicaciones (volumen alto: el objetivo es crecer rápido), al menos 3 de
   ellas "reel" (video vertical de ritmo rápido, el formato que más alcance orgánico da; topic "resultados" para un reel
   de resultados, si no son picks), solo equipos de ligas top, horas 07:00–23:00 separadas al menos 90 min,
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
    members = {**BASE, **{k: v for k, v in (r.get("miembros") or {}).items() if k not in BASE}}
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
        for p in posts[:8]:
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
            if any(abs(m - x) < 90 for x in times):
                problems.append(f"{t} {hhmm}: menos de 90 min de otra publicación")
                continue
            times.append(m)
            ok.append({k: str(p.get(k, ""))[:400] for k in ("type", "time", "angle", "topic", "hook", "cta", "liga", "meme_formato", "mercado", "segmento")})
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
{{"plan":[{{"type":"...","time":"HH:MM","angle":"...","topic":"...","hook":"...","cta":"...","liga":"(opcional)","mercado":"CO|MX|US|AR|ES|CL|PE|LATAM","segmento":"hinchas|comentaristas|profesores|analistas|fantasy|apostadores18"}}],
"decisiones":[{{"decision":"...","razon_economica":"...","efecto_esperado":"...","metrica":"...","revisar":"AAAA-MM-DD"}}],
"direccion_arte":{{"acento":"oro|esmeralda|rubi|zafiro|violeta|champana","portada":"impacto|editorial","ritmo":"rapido|muy_rapido|elegante"}},
"seo":{{"hashtags":["15 a 20 sin #, de Daniela, los más importantes primero"],"palabras":["6 a 10 palabras clave"]}},
(para cada "meme" agrega "meme_formato": tweet|nadie|expectativa|pov|starter|no_si|noticia|cuando|tier|chat|duelo|impopular|reto|giro, según Valeria y Mía; puedes
poner 2 memes si hay tendencias fuertes, y si una tendencia explota justo ahora, el meme puede ir con "time":"ahora")
(opcional: UNA publicación del plan puede llevar "time":"ahora" si debe salir apenas termine la reunión)
"aprendizajes":[{{"miembro":"clave de quien lo aprendió","texto":"..."}}], "acta":"qué viste, qué decidiste, qué experimento corre y cómo se mide"}}
4 a 7 publicaciones (volumen alto), horas 07:00–23:00 separadas al menos 90 min; "picks_dia" solo si hay picks
próximos (puede repetirse con distinta "liga": Liga BetPlay, Premier League, LaLiga…), al menos 3 "reel" (topic "resultados"
para un reel de resultados), al menos 1 "meme", al menos 1 concepto disruptivo de Mía (pon su concepto en "angle"), "resultados" solo si hay picks jugados. Un partido mostrado en picks no se
repite en 24 h; el de resultados de la noche cuenta cómo le fue a los picks de la mañana: no pongas más piezas de picks que partidos nuevos (varía la "liga").""")
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
    for k in ("sofia", "unit_econ", "econometria", "pricing", "internacional", "tiburon"):
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
