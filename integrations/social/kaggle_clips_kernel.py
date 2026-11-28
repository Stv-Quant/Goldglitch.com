"""EGG · clips de video con IA en las GPU gratis de Kaggle (2 × T4 de 16 GB).

goldglitch_kaggle.py escribe este archivo con la lista de PROMPTS del día y lo sube como cuaderno de Kaggle.
Cada GPU genera la mitad de los clips con Wan (modelo abierto de Alibaba, Apache 2.0) y los deja en /kaggle/working:
clip_XX.mp4 + index.json. Tu PC los descarga después con `kaggle kernels output`.

Modelo: Wan 2.1 T2V 1.3B (corre en fp16 en una T4, ~8 GB). Si WAN_MODEL apunta al 5B y falla, vuelve al 1.3B.
Formato vertical 480×832, 81 cuadros a 16 fps (5 s). El PC lo escala a 1080×1920.
"""
import json
import os
import subprocess
import sys
import time

PROMPTS = __PROMPTS__          # [{"id": "...", "prompt": "...", "estilo": "...", "tema": "..."}]
MODEL = os.environ.get("WAN_MODEL", "Wan-AI/Wan2.1-T2V-1.3B-Diffusers")
FALLBACK = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
OUT = "/kaggle/working"
NEG = ("logo, text, letters, words, subtitles, watermark, team crest, club badge, brand, sponsor, jersey number, "
       "real person, celebrity, deformed, blurry, low quality, static, still image, worst quality, jpeg artifacts, "
       "extra fingers, extra limbs, ugly, overexposed")


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(os.path.join(OUT, "log.txt"), "a", encoding="utf-8") as f:
        f.write(line + "\n")


def worker(gpu: int, items: list):
    """One process per GPU."""
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu)
    import torch
    from diffusers import AutoencoderKLWan, WanPipeline
    from diffusers.utils import export_to_video

    def load(mid):
        vae = AutoencoderKLWan.from_pretrained(mid, subfolder="vae", torch_dtype=torch.float32)
        pipe = WanPipeline.from_pretrained(mid, vae=vae, torch_dtype=torch.float16)
        if "1.3B" in mid:
            pipe.to("cuda")
        else:
            pipe.enable_model_cpu_offload()
        return pipe

    try:
        pipe = load(MODEL)
        mid = MODEL
    except Exception as e:
        log(f"gpu{gpu}: {MODEL} no cargó ({str(e)[:200]}); uso {FALLBACK}")
        pipe, mid = load(FALLBACK), FALLBACK
    done = []
    for it in items:
        t0 = time.time()
        try:
            frames = pipe(prompt=it["prompt"], negative_prompt=NEG, height=832, width=480, num_frames=81,
                          guidance_scale=5.0, num_inference_steps=int(os.environ.get("WAN_STEPS", "30"))).frames[0]
            path = os.path.join(OUT, f"clip_{it['id']}.mp4")
            export_to_video(frames, path, fps=16)
            done.append(it | {"file": os.path.basename(path), "modelo": mid, "segundos": round(time.time() - t0)})
            log(f"gpu{gpu}: listo {it['id']} en {round(time.time() - t0)} s")
        except Exception as e:
            log(f"gpu{gpu}: falló {it['id']}: {str(e)[:300]}")
        with open(os.path.join(OUT, f"index_gpu{gpu}.json"), "w", encoding="utf-8") as f:
            json.dump(done, f, ensure_ascii=False, indent=1)


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--worker":
        gpu = int(sys.argv[2])
        worker(gpu, PROMPTS[gpu::2])
        return
    log(f"{len(PROMPTS)} clips · modelo {MODEL}")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "diffusers>=0.33", "transformers", "accelerate",
                    "ftfy", "imageio", "imageio-ffmpeg", "sentencepiece"], check=False)
    try:
        import torch
        n = torch.cuda.device_count()
    except Exception:
        n = 0
    log(f"GPU disponibles: {n}")
    if n == 0:
        log("sin GPU: activa el acelerador del cuaderno (requiere teléfono verificado en Kaggle)")
        return
    procs = [subprocess.Popen([sys.executable, __file__, "--worker", str(g)]) for g in range(min(n, 2))]
    for p in procs:
        p.wait()
    allc = []
    for g in range(2):
        p = os.path.join(OUT, f"index_gpu{g}.json")
        if os.path.exists(p):
            allc += json.load(open(p, encoding="utf-8"))
    with open(os.path.join(OUT, "index.json"), "w", encoding="utf-8") as f:
        json.dump(allc, f, ensure_ascii=False, indent=1)
    log(f"terminado: {len(allc)} de {len(PROMPTS)} clips")


if __name__ == "__main__":
    main()
