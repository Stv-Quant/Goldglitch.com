"""La voz de EGG: narración con voz humana para los reels, GRATIS y en tu PC (sin suscripciones).

Dos motores abiertos:
  - Chatterbox Multilingual (Resemble AI, licencia MIT): voz natural y expresiva, la recomendada. Corre en su propio
    entorno (.venv_voz) con tu tarjeta NVIDIA o la CPU. Si dejas un audio voz_referencia.wav (10-15 s, de una persona
    que te dio permiso), usa ese timbre de voz.
  - Kokoro-82M (licencia Apache 2.0): más liviana, suena más robótica en español (respaldo).
    python goldglitch_voz.py instalar_natural   # instala Chatterbox (unos 4 GB) y prueba
    python goldglitch_voz.py instalar    # instala Kokoro (unos 500 MB con el modelo) y prueba una frase
    python goldglitch_voz.py prueba      # genera redes_salida/voz_prueba.wav
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
    return "chatterbox" if _cfg().get("engine") == "chatterbox" and os.path.exists(VPY) else "kokoro"


def say_many(items: list[tuple[str, str]]) -> list:
    """Narrate several lines at once [(text, wav_path)] → [(path, seconds) | None]. One model load per reel."""
    if engine() != "chatterbox":
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
    cmd = (sys.argv[1:] or ["prueba"])[0]
    sys.exit(install() if cmd == "instalar" else install_natural() if cmd == "instalar_natural" else (0 if test() else 1))
