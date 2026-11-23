"""La voz de EGG: narración con voz humana para los reels, GRATIS y en tu PC (sin suscripciones).

Usa Kokoro-82M (modelo abierto, licencia Apache 2.0) con voces en español; corre en la CPU o en tu tarjeta NVIDIA.
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


def available() -> bool:
    try:
        ok = json.load(open(CFG, encoding="utf-8")).get("ok")
    except (OSError, ValueError):
        ok = False
    return bool(ok) and os.environ.get("REDES_VOZ_ACTIVA", "1") != "0"


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
    json.dump({"ok": ok, "voz": os.environ.get("REDES_VOZ", "ef_dora")}, open(CFG, "w", encoding="utf-8"))
    print(f"Prueba de voz: {out[0] + f' ({out[1]:.1f} s)' if out else 'falló'}")
    if not ok:
        print("Si el error menciona espeak, instala espeak-ng para Windows (https://github.com/espeak-ng/espeak-ng/releases, "
              "archivo .msi) y vuelve a correr instalar_voz.bat.")
    return ok


if __name__ == "__main__":
    cmd = (sys.argv[1:] or ["prueba"])[0]
    sys.exit(install() if cmd == "instalar" else (0 if test() else 1))
