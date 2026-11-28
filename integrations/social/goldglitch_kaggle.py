"""Clips de video con IA generados gratis en Kaggle, para los videos de redes.

  python goldglitch_kaggle.py generar [n]   arma n prompts (estilos y temas variados), sube el cuaderno y lo lanza
  python goldglitch_kaggle.py estado        en qué va el cuaderno
  python goldglitch_kaggle.py traer         espera a que termine y descarga los clips a redes_clips\\ (biblioteca)
  python goldglitch_kaggle.py todo [n]      generar + traer (lo que hace generar_clips_ia.bat)

Credenciales: KAGGLE_API_TOKEN en .env (token nuevo de Kaggle → Settings → API Tokens). Usuario: KAGGLE_USERNAME
(por defecto easygoldglitch). La GPU de Kaggle exige el teléfono verificado en la cuenta.
Los prompts nunca piden escudos, marcas, textos ni personas reales (y el negativo los excluye).
"""
from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "redes_clips")
WORK = os.path.join(HERE, "redes_salida", "kaggle")
SLUG = "egg-clips-ia"

STYLES = {   # every clip gets one look, so videos never share the same style
    "cine": "cinematic photorealistic, anamorphic lens, shallow depth of field, dramatic night stadium lighting, film grain",
    "pixar": "3D animated film style, soft global illumination, expressive, vibrant colors, family movie render",
    "anime": "anime style, dynamic speed lines, bold cel shading, dramatic sky, high energy",
    "maqueta": "miniature tilt-shift diorama, toy-like, clay and felt textures, macro photography",
    "noir": "black and white noir, high contrast, rain, volumetric light beams, moody",
    "dron": "aerial drone shot, golden hour, sweeping camera move, ultra wide, epic scale",
}
SCENES = [   # football curiosities, no clubs, no real people, no text
    ("estadio", "a giant empty football stadium at night, floodlights turning on one by one, camera flying low over the pitch"),
    ("gol", "a football ball hitting the back of the net in extreme slow motion, net rippling, sparks of light"),
    ("portero", "a goalkeeper silhouette diving in slow motion under heavy rain, water droplets frozen in the air"),
    ("reloj", "a giant clock floating over a football pitch, its hands spinning faster and faster, players as tiny silhouettes"),
    ("balon_gigante", "a football the size of a building rolling slowly through an empty city street at dawn"),
    ("hinchada", "a sea of fans in the stands lifting their arms, flares glowing gold, smoke drifting, no flags or logos"),
    ("tactica", "glowing lines drawing passes across a dark football pitch seen from above, like a living tactics board"),
    ("corner", "a corner flag waving in strong wind, the ball placed beside it, crowd blurred behind, tension"),
    ("tarjeta", "a referee's hand raising a yellow card in slow motion against a stormy sky, dramatic backlight"),
    ("lluvia", "heavy rain on a football pitch at night, puddles reflecting floodlights, a ball splashing through water"),
    ("tunel", "players walking out of a dark stadium tunnel toward blinding light, camera following from behind"),
    ("numeros", "golden numbers and statistics floating in the air over a football pitch at night, data particles"),
    ("penal", "a penalty spot with the ball on it, camera slowly pushing in, heartbeat tension, stadium lights flickering"),
    ("barrio", "kids playing football on a dusty street at sunset in a latin american neighborhood, warm light, joy"),
    ("tormenta", "lightning striking behind a floodlit football stadium, dark clouds rolling, epic"),
    ("trofeo", "a shining golden trophy rotating slowly on a pedestal in a dark room, light beams, dust particles"),
]


def load_env() -> None:
    path = os.path.join(HERE, ".env")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    os.environ.setdefault("KAGGLE_USERNAME", "easygoldglitch")


def log(msg: str) -> None:
    line = f"[{datetime.now():%Y-%m-%d %H:%M}] {msg}"
    print(line, flush=True)
    try:
        with open(os.path.join(HERE, "redes.log"), "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def kaggle(*args: str, check: bool = True) -> str:
    exe = shutil.which("kaggle") or os.path.join(os.path.dirname(sys.executable), "kaggle")
    cmd = [exe, *args] if os.path.exists(exe) or shutil.which("kaggle") else [sys.executable, "-m", "kaggle", *args]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    out = (p.stdout or "") + (p.stderr or "")
    if "No module named 'six'" in out and not os.environ.get("_EGG_SIX"):   # kaggle 2.2.x ships without its 'six' dependency
        os.environ["_EGG_SIX"] = "1"
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "six"], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return kaggle(*args, check=check)
    if "Authentication required" in out:
        raise RuntimeError("Kaggle no aceptó el token: revisa que .env tenga KAGGLE_API_TOKEN=... (sin comillas ni espacios)")
    if check and p.returncode != 0:
        raise RuntimeError(out.strip()[-600:] or f"kaggle {' '.join(args)} falló")
    return out


def library() -> list[dict]:
    p = os.path.join(LIB, "indice.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []


def prompts(n: int, seed: int | None = None) -> list[dict]:
    """n prompts with varied scenes × styles, preferring combinations the library does not have yet."""
    rng = random.Random(seed if seed is not None else int(time.time()))
    have = {(c.get("tema"), c.get("estilo")) for c in library()}
    combos = [(t, d, s) for t, d in SCENES for s in STYLES]
    rng.shuffle(combos)
    combos.sort(key=lambda c: (c[0], c[2]) in have)
    out, stamp = [], datetime.now().strftime("%m%d%H%M")
    for k, (tema, desc, est) in enumerate(combos[:n]):
        out.append({"id": f"{stamp}_{k:02d}", "tema": tema, "estilo": est,
                    "prompt": f"{desc}. {STYLES[est]}. Vertical 9:16 composition, dynamic camera movement, highly detailed."})
    return out


def generar(n: int = 12) -> str:
    if not os.environ.get("KAGGLE_API_TOKEN") and not os.path.exists(os.path.expanduser("~/.kaggle/kaggle.json")):
        raise RuntimeError("falta KAGGLE_API_TOKEN en .env")
    user = os.environ["KAGGLE_USERNAME"]
    items = prompts(n)
    d = os.path.join(WORK, "kernel")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d, exist_ok=True)
    src = open(os.path.join(HERE, "kaggle_clips_kernel.py"), encoding="utf-8").read()
    open(os.path.join(d, "egg_clips.py"), "w", encoding="utf-8").write(src.replace("__PROMPTS__", json.dumps(items, ensure_ascii=False)))
    meta = {"id": f"{user}/{SLUG}", "title": SLUG, "code_file": "egg_clips.py", "language": "python", "kernel_type": "script",
            "is_private": "true", "enable_gpu": "true", "enable_internet": "true", "dataset_sources": [],
            "competition_sources": [], "kernel_sources": []}
    if os.environ.get("KAGGLE_GPU"):                 # Kaggle's default GPU is T4 x2 (the P100 was retired)
        meta["machine_shape"] = os.environ["KAGGLE_GPU"]
    json.dump(meta, open(os.path.join(d, "kernel-metadata.json"), "w", encoding="utf-8"), indent=1)
    json.dump(items, open(os.path.join(WORK, "pedido.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    out = kaggle("kernels", "push", "-p", d)
    log(f"Kaggle: {len(items)} clips pedidos ({', '.join(sorted({i['estilo'] for i in items}))}). {out.strip()[-160:]}")
    return out


def estado() -> str:
    user = os.environ["KAGGLE_USERNAME"]
    return kaggle("kernels", "status", f"{user}/{SLUG}").strip()


def traer(wait_min: int = 300) -> int:
    """Wait for the run to finish, download the clips, upscale them to 1080×1920 and add them to the library."""
    user = os.environ["KAGGLE_USERNAME"]
    t_end = time.time() + wait_min * 60
    st = ""
    while time.time() < t_end:
        st = estado().lower()
        if any(w in st for w in ("complete", "error", "cancel")):
            break
        if "queued" in st and time.time() > t_end - (wait_min - 45) * 60:
            log("Kaggle: lleva 45 min en cola; si sigue así, prueba más tarde o cambia la GPU en .env (KAGGLE_GPU)")
        print(f"  {datetime.now():%H:%M} {st[-80:]}", flush=True)
        time.sleep(60)
    dl = os.path.join(WORK, "salida")
    shutil.rmtree(dl, ignore_errors=True)
    os.makedirs(dl, exist_ok=True)
    kaggle("kernels", "output", f"{user}/{SLUG}", "-p", dl, check=False)
    if os.path.exists(os.path.join(dl, "log.txt")):
        shutil.copy(os.path.join(dl, "log.txt"), os.path.join(WORK, "ultimo_log.txt"))
    idx_p = os.path.join(dl, "index.json")
    if not os.path.exists(idx_p):
        log(f"Kaggle: sin clips ({st[-120:]}). Revisa redes_salida\\kaggle\\ultimo_log.txt")
        return 0
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    os.makedirs(LIB, exist_ok=True)
    lib, added = library(), 0
    for c in json.load(open(idx_p, encoding="utf-8")):
        src = os.path.join(dl, c["file"])
        if not os.path.exists(src):
            continue
        dst = os.path.join(LIB, f"{c['tema']}_{c['estilo']}_{c['id']}.mp4")
        subprocess.run([ff, "-y", "-loglevel", "error", "-i", src, "-vf",
                        "scale=1080:1920:flags=lanczos,fps=30,eq=contrast=1.04:saturation=1.08,unsharp=5:5:0.6",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-an", dst],
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if os.path.exists(dst):
            lib.append({k: c.get(k) for k in ("id", "tema", "estilo", "prompt", "modelo")} |
                       {"file": os.path.basename(dst), "fecha": datetime.now().strftime("%Y-%m-%d"), "usos": 0})
            added += 1
    json.dump(lib, open(os.path.join(LIB, "indice.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log(f"Kaggle: {added} clips nuevos en la biblioteca (total {len(lib)}).")
    return added


def main() -> None:
    load_env()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "todo"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    try:
        if cmd == "generar":
            generar(n)
        elif cmd == "estado":
            print(estado())
        elif cmd == "traer":
            traer()
        else:
            generar(n)
            print("Generando en Kaggle (puede tardar 1-2 horas). No cierres esta ventana.")
            time.sleep(120)
            traer()
    except Exception as e:
        log(f"Kaggle: ERROR {str(e)[:500]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
