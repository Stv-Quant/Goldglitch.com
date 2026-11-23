"""Worker de voz natural (Chatterbox Multilingual, Resemble AI, licencia MIT). Corre en su propio entorno (.venv_voz)
para no chocar con las librerías del resto del sistema. Carga el modelo UNA vez y narra todas las frases de un reel.

    .venv_voz\\Scripts\\python.exe goldglitch_voz_worker.py trabajos.json
trabajos.json: {"jobs": [{"text": "...", "path": "salida.wav"}], "ref": "voz_referencia.wav" | null}
Imprime en la última línea un JSON con la duración de cada audio (null si falló).
"""
import json
import os
import sys

import torch
import torchaudio


def main() -> int:
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    device = "cuda" if torch.cuda.is_available() else "cpu"
    try:
        model = ChatterboxMultilingualTTS.from_pretrained(device=device)
    except RuntimeError:            # not enough VRAM: CPU is slower but works
        device = "cpu"
        model = ChatterboxMultilingualTTS.from_pretrained(device=device)
    ref = spec.get("ref") if spec.get("ref") and os.path.exists(spec["ref"]) else None
    out = []
    for j in spec["jobs"]:
        try:
            wav = model.generate(j["text"], language_id="es", audio_prompt_path=ref,
                                 exaggeration=float(spec.get("exaggeration", 0.6)), cfg_weight=float(spec.get("cfg", 0.45)),
                                 temperature=0.8)
            torchaudio.save(j["path"], wav.cpu(), model.sr)
            out.append(wav.shape[-1] / model.sr)
        except Exception as e:
            print(f"voz: {e}", file=sys.stderr)
            out.append(None)
    print(json.dumps({"durations": out, "device": device}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
