"""La voz de EGG: narración con voz humana para los reels, GRATIS y en tu PC (sin suscripciones).

Dos motores abiertos:
  - Chatterbox Multilingual (Resemble AI, licencia MIT): voz natural y expresiva, la recomendada. Corre en su propio
    entorno (.venv_voz) con tu tarjeta NVIDIA o la CPU. Si dejas un audio voz_referencia.wav (10-15 s, de una persona
    que te dio permiso), usa ese timbre de voz.
  - Kokoro-82M (licencia Apache 2.0): más liviana, suena más robótica en español (respaldo).
    python goldglitch_voz.py instalar_natural   # instala Chatterbox (unos 4 GB) y prueba
    python goldglitch_voz.py instalar    # instala Kokoro (unos 500 MB con el modelo) y prueba una frase
    python goldglitch_voz.py prueba      # genera redes_salida/voz_prueba.wav
    python goldglitch_voz.py elevenlabs  # voz de pago de ElevenLabs (por defecto "Valentino"; ELEVENLABS_API_KEY en el .env)
Voz por defecto: ef_dora (femenina, español). Cambiable con REDES_VOZ=em_alex (masculina) en el .env.
Si no está instalada o falla, los reels salen con el ritmo de siempre, sin voz.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(HERE, "redes_voz.json")
_PIPE = None


VENV = os.path.join(HERE, ".venv_voz")
VPY = os.path.join(VENV, "Scripts", "python.exe") if os.name == "nt" else os.path.join(VENV, "bin", "python")
REF = os.path.join(HERE, "voz_referencia.wav")


def _cfg() -> dict:
    try:
        return json.load(open(CFG, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def available() -> bool:
    return bool(_cfg().get("ok")) and os.environ.get("REDES_VOZ_ACTIVA", "1") != "0"


def engine() -> str:
    if os.environ.get("ELEVENLABS_API_KEY") and os.environ.get("REDES_VOZ_MOTOR", "elevenlabs") == "elevenlabs" \
            and _cfg().get("eleven_voice_id"):
        return "elevenlabs"
    return "chatterbox" if _cfg().get("engine") == "chatterbox" and os.path.exists(VPY) else "kokoro"


# ------------------------------------------------------------------ ElevenLabs (paid voices such as "Valentino")
EL = "https://api.elevenlabs.io/v1"


def _el_headers() -> dict:
    return {"xi-api-key": os.environ.get("ELEVENLABS_API_KEY", ""), "accept": "application/json"}


def eleven_find(name: str) -> str | None:
    """Voice id of `name`: from your ElevenLabs voices, or from the public Voice Library (added to your voices)."""
    import requests
    mine = requests.get(f"{EL}/voices", headers=_el_headers(), timeout=30).json().get("voices") or []
    for v in mine:
        if str(v.get("name", "")).strip().lower().startswith(name.lower()):
            return v["voice_id"]
    found = []
    for lang in ("es", ""):
        r = requests.get(f"{EL}/shared-voices", headers=_el_headers(), timeout=30,
                         params={"search": name, "page_size": 30, **({"language": lang} if lang else {})}).json()
        found += r.get("voices") or []
        if found:
            break
    exact = [v for v in found if str(v.get("name", "")).strip().lower().startswith(name.lower())] or found
    if not exact:
        return None
    v = sorted(exact, key=lambda v: -(v.get("cloned_by_count") or v.get("usage_character_count_1y") or 0))[0]
    added = requests.post(f"{EL}/voices/add/{v['public_owner_id']}/{v['voice_id']}", headers=_el_headers(), timeout=30,
                          json={"new_name": name}).json()
    return added.get("voice_id") or v["voice_id"]


def eleven_left() -> int:
    import requests
    try:
        sub = requests.get(f"{EL}/user/subscription", headers=_el_headers(), timeout=20).json()
        return int(sub.get("character_limit", 0)) - int(sub.get("character_count", 0))
    except Exception:
        return 10**9


def eleven_say(text: str, path: str) -> tuple[str, float] | None:
    import requests
    import wave
    vid = _cfg().get("eleven_voice_id")
    r = requests.post(f"{EL}/text-to-speech/{vid}", params={"output_format": "pcm_24000"}, timeout=120,
                      headers={**_el_headers(), "accept": "audio/pcm", "content-type": "application/json"},
                      json={"text": text, "model_id": os.environ.get("ELEVENLABS_MODELO", "eleven_multilingual_v2"),
                            "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.35,
                                               "use_speaker_boost": True}})
    if r.status_code != 200:
        raise RuntimeError(f"ElevenLabs {r.status_code}: {r.text[:200]}")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(r.content)
    return path, len(r.content) / 2 / 24000


def install_eleven() -> int:
    name = os.environ.get("ELEVENLABS_VOZ", "Valentino")
    if not os.environ.get("ELEVENLABS_API_KEY"):
        print("Falta ELEVENLABS_API_KEY en el .env (tu clave de elevenlabs.io > Developers > API Keys).")
        return 1
    try:
        vid = eleven_find(name)
    except Exception as e:
        print(f"No pude consultar ElevenLabs: {e}")
        return 1
    if not vid:
        print(f"No encontré la voz '{name}' en ElevenLabs.")
        return 1
    json.dump({**_cfg(), "ok": True, "eleven_voice_id": vid, "eleven_voz": name}, open(CFG, "w", encoding="utf-8"))
    os.makedirs(os.path.join(HERE, "redes_salida"), exist_ok=True)
    try:
        out = eleven_say("Hola, soy EGG. Hoy el modelo ve tres partidos con más del ochenta por ciento, y uno te va a "
                         "sorprender.", os.path.join(HERE, "redes_salida", "voz_prueba_valentino.wav"))
    except Exception as e:
        print(f"La voz se encontró pero la prueba falló: {e}")
        return 1
    print(f"Voz '{name}' lista ({vid}). Prueba: {out[0]} ({out[1]:.1f} s). Caracteres que te quedan este mes: {eleven_left()}")
    return 0


def say_many(items: list[tuple[str, str]]) -> list:
    """Narrate several lines at once [(text, wav_path)] → [(path, seconds) | None]. One model load per reel."""
    if engine() == "elevenlabs":
        need = sum(len(t) for t, _ in items if t)
        if eleven_left() >= need:
            out = []
            try:
                for t, p in items:
                    out.append(eleven_say(t, p) if t else None)
                return out
            except Exception as e:
                print(f"Voz ElevenLabs falló ({e}); uso la voz local")
        else:
            print("ElevenLabs: no quedan caracteres este mes; uso la voz local")
        if _cfg().get("engine") != "chatterbox" or not os.path.exists(VPY):
            return [say(t, p) if t else None for t, p in items]
    elif engine() != "chatterbox":
        return [say(t, p) if t else None for t, p in items]
    import tempfile
    jobs = [{"text": t, "path": p} for t, p in items if t]
    if not jobs:
        return [None] * len(items)
    fd, spec = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"jobs": jobs, "ref": REF if os.path.exists(REF) else None,
                   "exaggeration": float(os.environ.get("REDES_VOZ_EMOCION", "0.6"))}, f, ensure_ascii=False)
    try:
        r = subprocess.run([VPY, os.path.join(HERE, "goldglitch_voz_worker.py"), spec], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=1800, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            durs = json.loads(r.stdout.strip().splitlines()[-1])["durations"]
        except (IndexError, ValueError, KeyError):
            raise RuntimeError((r.stderr or r.stdout or "sin salida")[-900:])
    except Exception as e:
        print(f"Voz natural falló ({e}); uso Kokoro")
        return [say(t, p) if t else None for t, p in items]
    finally:
        os.remove(spec)
    it = iter(durs)
    return [((p, d) if (d := next(it)) else None) if t else None for t, p in items]


def install_natural() -> int:
    print("Creando el entorno de la voz natural (.venv_voz)…")
    if not os.path.exists(VPY) and subprocess.run([sys.executable, "-m", "venv", VENV]).returncode:
        print("No se pudo crear el entorno."); return 1
    pip = [VPY, "-m", "pip", "install", "--upgrade"]
    subprocess.run(pip + ["pip"])
    print("Instalando PyTorch con CUDA para la voz (unos 2,5 GB)…")
    if subprocess.run(pip + ["torch==2.6.0", "torchaudio==2.6.0", "--index-url", "https://download.pytorch.org/whl/cu124"]).returncode:
        print("No se pudo instalar PyTorch."); return 1
    print("Instalando Chatterbox…")
    if subprocess.run(pip + ["chatterbox-tts"]).returncode:
        print("No se pudo instalar Chatterbox."); return 1
    json.dump({"ok": True, "engine": "chatterbox"}, open(CFG, "w", encoding="utf-8"))
    os.makedirs(os.path.join(HERE, "redes_salida"), exist_ok=True)
    out = say_many([("Hola, soy EGG. Hoy el modelo ve tres partidos con más del ochenta por ciento, y uno de ellos te va a "
                     "sorprender. Te lo cuento.", os.path.join(HERE, "redes_salida", "voz_prueba_natural.wav"))])[0]
    ok = bool(out)
    json.dump({"ok": ok or _cfg().get("ok", False), "engine": "chatterbox" if ok else "kokoro"}, open(CFG, "w", encoding="utf-8"))
    print(f"Prueba de voz natural: {out[0] + f' ({out[1]:.1f} s)' if out else 'falló'}")
    return 0 if ok else 1


def _pipe():
    global _PIPE
    if _PIPE is None:
        from kokoro import KPipeline
        _PIPE = KPipeline(lang_code="e")          # Spanish
    return _PIPE


def say(text: str, path: str, speed: float = 1.0) -> tuple[str, float] | None:
    """Speak one line to a WAV file. Returns (path, seconds) or None."""
    try:
        import numpy as np
        import soundfile as sf
        voice = os.environ.get("REDES_VOZ", "ef_dora")
        chunks = [a for _, _, a in _pipe()(text, voice=voice, speed=speed)]
        if not chunks:
            return None
        audio = np.concatenate([c.numpy() if hasattr(c, "numpy") else c for c in chunks])
        sf.write(path, audio, 24000)
        return path, len(audio) / 24000
    except Exception as e:
        print(f"Voz: {e}")
        return None


def install() -> int:
    pip = [sys.executable, "-m", "pip", "install", "--upgrade"]
    print("Instalando Kokoro (voz abierta, en tu PC)…")
    if subprocess.run(pip + ["kokoro>=0.9", "soundfile", "espeakng-loader", "phonemizer-fork"]).returncode:
        print("No se pudo instalar Kokoro.")
        return 1
    return 0 if test() else 1


def test() -> bool:
    os.makedirs(os.path.join(HERE, "redes_salida"), exist_ok=True)
    out = say("Hola, soy EGG. Hoy el modelo ve tres partidos con más del ochenta por ciento. Te los cuento.",
              os.path.join(HERE, "redes_salida", "voz_prueba.wav"))
    ok = bool(out)
    json.dump({**_cfg(), "ok": ok or _cfg().get("ok", False), "voz": os.environ.get("REDES_VOZ", "ef_dora")}, open(CFG, "w", encoding="utf-8"))
    print(f"Prueba de voz: {out[0] + f' ({out[1]:.1f} s)' if out else 'falló'}")
    if not ok:
        print("Si el error menciona espeak, instala espeak-ng para Windows (https://github.com/espeak-ng/espeak-ng/releases, "
              "archivo .msi) y vuelve a correr instalar_voz.bat.")
    return ok


if __name__ == "__main__":
    _env = os.path.join(HERE, ".env")
    if os.path.exists(_env):
        for _line in open(_env, encoding="utf-8"):
            if "=" in _line and not _line.lstrip().startswith("#"):
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))
    cmd = (sys.argv[1:] or ["prueba"])[0]
    sys.exit(install() if cmd == "instalar" else install_natural() if cmd == "instalar_natural" else
             install_eleven() if cmd == "elevenlabs" else (0 if test() else 1))
