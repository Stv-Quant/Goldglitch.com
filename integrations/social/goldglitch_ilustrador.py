"""El ilustrador: IA de imágenes que corre GRATIS en tu PC (tarjeta gráfica NVIDIA), sin suscripciones.

Modelos abiertos, elegidos según tu tarjeta (instalar_ilustrador.bat lo decide y lo descarga una vez):
  - FLUX.1 [schnell] (Black Forest Labs, licencia Apache 2.0): la mejor calidad; tarjeta de 16 GB o más.
  - Stable Diffusion XL 1.0 (Stability AI, licencia abierta CreativeML OpenRAIL++-M): tarjetas de 8 a 15 GB.
  - SDXL-Lightning 4 pasos (ByteDance, misma licencia abierta) para tarjetas de 4 a 7 GB (portátiles): la misma
    calidad de SDXL en 4 pasos, cargando el modelo por partes en la tarjeta (más lento, ~1 min por imagen).
Genera ilustraciones de nivel profesional para cada publicación (fondo de la pieza y escenas del reel) y la galería de
personajes del universo EGG (EGG, Mateo, Santiago, Valeria…) con sus expresiones. Se escalan a 4K.
Si no está instalado o falla, las piezas salen con el arte vectorial de siempre.

    python goldglitch_ilustrador.py instalar      # revisa la tarjeta, instala y descarga el modelo (una vez)
    python goldglitch_ilustrador.py personajes    # dibuja la galería de personajes (unos minutos)
    python goldglitch_ilustrador.py prueba        # una ilustración de prueba en redes_salida
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(HERE, "redes_ilustrador.json")
OUT = os.path.join(HERE, "redes_salida", "ilustraciones")
CHARS = os.path.join(HERE, "redes_personajes")
MODELS = os.path.join(HERE, "modelos_ia")

STYLE = ("premium editorial digital illustration by a top concept artist, cinematic lighting, rich detail, painterly "
         "textures, depth of field, dramatic rim light, luxury black and gold color palette, sharp focus, award-winning")
NEGATIVE = ("text, letters, words, watermark, signature, logo, brand, team crest, jersey numbers, real person, celebrity, "
            "blurry, lowres, deformed, extra fingers, bad anatomy, ugly, cartoon for kids, ms paint, pixel art, nsfw")
CHARACTER_DESC = {
    "egg": "a stylish confident young Colombian woman in her twenties, long dark wavy hair with golden highlights, "
           "gold hoop earrings, delicate gold necklace, elegant gold satin top, glamorous makeup, Cali vibe",
    "mateo": "a charismatic young Colombian man, short dark hair, light stubble, green sports cap, green football fan "
             "jersey with white stripes, friendly cheeky grin",
    "santiago": "a sharp ambitious Colombian businessman in his early thirties, groomed black beard, slicked black hair, "
                "tailored navy blue suit, white shirt, burgundy tie, luxury watch",
    "valeria": "a trendy young Latina woman, long fuchsia pink hair, small pearl earrings, oversized amber yellow "
               "streetwear jacket, playful attitude",
}
MOODS = {"smug": "confident smug half-smile, one eyebrow raised", "wink": "playful wink and smile",
         "shock": "shocked surprised face, mouth open, wide eyes", "laugh": "laughing out loud, joyful",
         "neutral": "calm confident expression"}


def cfg() -> dict:
    try:
        return json.load(open(CFG, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def available() -> bool:
    c = cfg()
    return bool(c.get("model")) and os.path.isdir(c.get("path", "")) and os.environ.get("REDES_ILUSTRADOR", "1") != "0"


# ------------------------------------------------------------------ install
def gpu() -> tuple[str, int]:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=20).stdout.strip().splitlines()[0]
        name, mem = [x.strip() for x in out.split(",")]
        return name, int(mem)
    except Exception:
        return "", 0


def ram_gb() -> int:
    try:
        import ctypes

        class M(ctypes.Structure):
            _fields_ = [("l", ctypes.c_ulong), ("load", ctypes.c_ulong), ("total", ctypes.c_ulonglong),
                        ("avail", ctypes.c_ulonglong), ("a", ctypes.c_ulonglong), ("b", ctypes.c_ulonglong),
                        ("c", ctypes.c_ulonglong), ("d", ctypes.c_ulonglong), ("e", ctypes.c_ulonglong)]
        m = M(); m.l = ctypes.sizeof(M)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        return int(m.total / 1024 ** 3)
    except Exception:
        return 16


def _download(model: str) -> str:
    from huggingface_hub import snapshot_download
    path = os.path.join(MODELS, model)
    if model == "flux-schnell":
        snapshot_download("black-forest-labs/FLUX.1-schnell", local_dir=path, ignore_patterns=["flux1-schnell.safetensors", "*.md", "*.png"])
    elif model == "sdxl":
        snapshot_download("stabilityai/stable-diffusion-xl-base-1.0", local_dir=path,
                          allow_patterns=["*.json", "*.txt", "unet/*fp16.safetensors", "text_encoder*/*fp16.safetensors", "tokenizer*/*"])
    else:   # SDXL text encoders/config + the 4-step Lightning UNet (no base UNet: saves 5 GB)
        from huggingface_hub import hf_hub_download
        snapshot_download("stabilityai/stable-diffusion-xl-base-1.0", local_dir=path,
                          allow_patterns=["*.json", "*.txt", "text_encoder*/*fp16.safetensors", "tokenizer*/*"])
        hf_hub_download("ByteDance/SDXL-Lightning", "sdxl_lightning_4step_unet.safetensors", local_dir=path)
    return path


def install() -> int:
    name, vram = gpu()
    ram = ram_gb()
    print(f"Tarjeta gráfica: {name or 'no se encontró una NVIDIA'} · {vram / 1024:.0f} GB · RAM {ram} GB")
    if vram < 3500:
        print("Se necesita una tarjeta NVIDIA de 4 GB o más para dibujar en tu PC. Las piezas seguirán con el arte vectorial.")
        return 1
    model = "flux-schnell" if vram >= 15500 and ram >= 30 else "sdxl" if vram >= 7500 else "sdxl-lightning"
    repo = {"flux-schnell": "black-forest-labs/FLUX.1-schnell", "sdxl": "stabilityai/stable-diffusion-xl-base-1.0",
            "sdxl-lightning": ""}[model]
    repo = repo if model != "sdxl-lightning" else "stabilityai/stable-diffusion-xl-base-1.0 + ByteDance/SDXL-Lightning (4 pasos)"
    size = {"flux-schnell": "unos 34 GB", "sdxl": "unos 7 GB", "sdxl-lightning": "unos 7,5 GB"}[model]
    print(f"Modelo elegido: {repo} (descarga de {size}, una sola vez).")
    pip = [sys.executable, "-m", "pip", "install", "--upgrade"]
    print("Instalando PyTorch con CUDA (unos 2,5 GB)…")
    if subprocess.run(pip + ["torch", "--index-url", "https://download.pytorch.org/whl/cu124"]).returncode:
        print("No se pudo instalar PyTorch."); return 1
    print("Instalando diffusers…")
    if subprocess.run(pip + ["diffusers>=0.31", "transformers>=4.44", "accelerate>=0.33", "safetensors", "sentencepiece",
                             "protobuf", "huggingface_hub>=0.24", "pillow"]).returncode:
        print("No se pudo instalar diffusers."); return 1
    from huggingface_hub import snapshot_download
    print("Descargando el modelo (puede tardar según tu internet)…")
    try:
        path = _download(model)
    except Exception as e:
        if model != "flux-schnell":
            print(f"No se pudo descargar: {e}"); return 1
        print(f"FLUX no se pudo descargar ({str(e)[:160]}); uso Stable Diffusion XL.")
        model, path = "sdxl", _download("sdxl")
    if model.startswith("sdxl"):   # VAE that works in half precision (the original one can give black images in fp16)
        snapshot_download("madebyollin/sdxl-vae-fp16-fix", local_dir=os.path.join(MODELS, "sdxl-vae-fp16-fix"))
    json.dump({"model": model, "path": path, "gpu": name, "vram_mb": vram, "ram_gb": ram, "installed": time.strftime("%Y-%m-%d")},
              open(CFG, "w", encoding="utf-8"), indent=1)
    print("Listo. Probando…")
    return 0 if test() else 1


# ------------------------------------------------------------------ generation
_PIPE = None


def _pipe():
    global _PIPE
    if _PIPE is not None:
        return _PIPE
    import torch
    c = cfg()
    if c["model"] == "flux-schnell":
        from diffusers import FluxPipeline
        p = FluxPipeline.from_pretrained(c["path"], torch_dtype=torch.bfloat16)
        if c.get("vram_mb", 0) >= 23000:
            p.to("cuda")
        else:
            p.enable_model_cpu_offload()
    elif c["model"] == "sdxl-lightning":
        from diffusers import AutoencoderKL, EulerDiscreteScheduler, StableDiffusionXLPipeline, UNet2DConditionModel
        from safetensors.torch import load_file
        unet = UNet2DConditionModel.from_config(os.path.join(c["path"], "unet")).to(torch.float16)
        unet.load_state_dict(load_file(os.path.join(c["path"], "sdxl_lightning_4step_unet.safetensors"), device="cpu"))
        vae = AutoencoderKL.from_pretrained(os.path.join(MODELS, "sdxl-vae-fp16-fix"), torch_dtype=torch.float16)
        p = StableDiffusionXLPipeline.from_pretrained(c["path"], unet=unet, vae=vae, torch_dtype=torch.float16, variant="fp16",
                                                      use_safetensors=True)
        p.scheduler = EulerDiscreteScheduler.from_config(p.scheduler.config, timestep_spacing="trailing")
        p.enable_sequential_cpu_offload()      # 4 GB cards: the model goes to the GPU piece by piece
        p.enable_vae_tiling()
    else:
        from diffusers import AutoencoderKL, DPMSolverMultistepScheduler, StableDiffusionXLPipeline
        vae = AutoencoderKL.from_pretrained(os.path.join(MODELS, "sdxl-vae-fp16-fix"), torch_dtype=torch.float16)
        p = StableDiffusionXLPipeline.from_pretrained(c["path"], vae=vae, torch_dtype=torch.float16, variant="fp16", use_safetensors=True)
        p.scheduler = DPMSolverMultistepScheduler.from_config(p.scheduler.config, use_karras_sigmas=True)
        if c.get("vram_mb", 0) >= 11000:
            p.to("cuda")
        else:
            p.enable_model_cpu_offload()
        p.enable_vae_tiling()
    _PIPE = p
    return p


def generate(prompt: str, w: int = 896, h: int = 1152, seed: int | None = None, name: str = "", upscale_to: tuple[int, int] | None = None) -> str | None:
    """One illustration (PNG path). w×h around 1 megapixel (multiples of 64). upscale_to: final size (e.g. 2160×2700)."""
    if not available():
        return None
    import torch
    from PIL import Image, ImageFilter
    os.makedirs(OUT, exist_ok=True)
    seed = seed if seed is not None else int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)
    path = os.path.join(OUT, f"{name or 'ilus'}_{seed % 100000}.png")
    if os.path.exists(path):
        return path
    p, c = _pipe(), cfg()
    g = torch.Generator("cpu").manual_seed(seed)
    full = f"{prompt}, {STYLE}"
    if c["model"] == "flux-schnell":
        img = p(full, width=w, height=h, num_inference_steps=4, guidance_scale=0.0, max_sequence_length=256, generator=g).images[0]
    elif c["model"] == "sdxl-lightning":
        img = p(full, width=w, height=h, num_inference_steps=4, guidance_scale=0.0, generator=g).images[0]
    else:
        img = p(full, negative_prompt=NEGATIVE, width=w, height=h, num_inference_steps=30, guidance_scale=6.5, generator=g).images[0]
    if upscale_to:
        img = img.resize(upscale_to, Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
    img.save(path)
    return path


def scene(post_type: str, prompt: str, vertical: bool, name: str) -> str | None:
    """Background illustration for a piece: 4:5 for the feed, 9:16 for reels (upscaled to 4K)."""
    w, h = (768, 1344) if vertical else (896, 1152)
    final = (2160, 3840) if vertical else (2160, 2700)
    composition = ("empty dark negative space in the upper and middle area for headline text, subject in the lower third"
                   if not vertical else "vertical composition, empty dark space in the center for big text")
    try:
        return generate(f"{prompt}, {composition}", w, h, name=name, upscale_to=final)
    except Exception as e:
        print(f"Ilustrador: {e}")
        return None


def character_path(who: str, mood: str) -> str | None:
    k = str(who or "").lower()
    p = os.path.join(CHARS, f"{k}_{mood}.png")
    return p if os.path.exists(p) else None


def draw_characters() -> int:
    """The EGG universe gallery: every character × every expression, same seed per character (consistent face)."""
    os.makedirs(CHARS, exist_ok=True)
    n = 0
    for k, desc in CHARACTER_DESC.items():
        seed = int(hashlib.md5(k.encode()).hexdigest()[:8], 16)
        for mood, mdesc in MOODS.items():
            dst = os.path.join(CHARS, f"{k}_{mood}.png")
            if os.path.exists(dst):
                continue
            src = generate(f"head and shoulders portrait of {desc}, {mdesc}, looking at the viewer, dark luxurious "
                           "background with soft golden bokeh, centered", 1024, 1024, seed=seed, name=f"char_{k}_{mood}")
            if src:
                os.replace(src, dst)
                n += 1
                print(f"  {k} · {mood}")
    return n


def test() -> bool:
    p = scene("meme", "a passionate football fan in a stadium at night under golden floodlights, confetti in the air", False, "prueba")
    print(f"Prueba: {p or 'falló'}")
    return bool(p)


if __name__ == "__main__":
    cmd = (sys.argv[1:] or ["prueba"])[0]
    if cmd == "instalar":
        sys.exit(install())
    if cmd == "personajes":
        print(f"{draw_characters()} retratos nuevos en {CHARS}")
        sys.exit(0)
    sys.exit(0 if test() else 1)
