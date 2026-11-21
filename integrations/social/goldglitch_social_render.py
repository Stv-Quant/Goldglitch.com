"""Piezas gráficas de Goldglitch para redes: imágenes (JPEG) y videos verticales (MP4) con la marca.

Se dibujan como HTML con Chromium (Playwright) y los videos se arman con ffmpeg (imageio-ffmpeg trae el binario).
Todos los números vienen de los datos de la web; aquí solo se maquetan.
"""
from __future__ import annotations

import html
import os
import subprocess
import tempfile
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "redes_salida")

# Escala de color de la app (rubí → brasa → ámbar → oro → lima → esmeralda).
STEPS = [(0.85, "#00f0a0"), (0.75, "#a6ff3c"), (0.65, "#ffe14d"), (0.55, "#ffb020"), (0.40, "#ff7a2f"), (0.0, "#ff4d6d")]


def color(p: float) -> str:
    return next(c for t, c in STEPS if p >= t)


def esc(s) -> str:
    return html.escape(str(s or ""))


BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@500;700&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
body{width:%(w)dpx;height:%(h)dpx;background:#050505;color:#ede6d6;font-family:Inter,system-ui,sans-serif;overflow:hidden;position:relative}
.bg{position:absolute;inset:0;background:radial-gradient(900px 700px at 85%% -10%%,rgba(212,175,55,.22),transparent 60%%),radial-gradient(700px 600px at -10%% 110%%,rgba(46,242,160,.10),transparent 60%%)}
.grid{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);background-size:54px 54px}
.wrap{position:relative;height:100%%;display:flex;flex-direction:column;padding:%(pad)dpx}
.brand{display:flex;align-items:center;gap:16px;font-weight:600;font-size:30px;letter-spacing:.01em}
.logo{width:52px;height:52px;border-radius:50%%;border:3px solid #d4af37;display:grid;place-items:center}
.logo i{display:block;width:6px;background:#d4af37;margin:0 2px;border-radius:2px}
.eyebrow{font-family:'JetBrains Mono',monospace;letter-spacing:.28em;text-transform:uppercase;color:#d4af37;font-size:24px}
.mono{font-family:'JetBrains Mono',monospace}
.muted{color:#9a9384}
.foot{margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;color:#7d776b;font-size:22px}
.card{border:1.5px solid rgba(255,255,255,.09);border-radius:28px;background:rgba(18,17,14,.78);padding:40px}
.bar{height:16px;border-radius:99px;background:#2a2823;overflow:hidden}
.bar>span{display:block;height:100%%;border-radius:99px}
"""

LOGO = '<div class="logo"><div style="display:flex;align-items:flex-end;height:24px"><i style="height:10px"></i><i style="height:17px"></i><i style="height:24px"></i></div></div>'


def page(body: str, w: int, h: int, pad: int = 80) -> str:
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE_CSS % {'w': w, 'h': h, 'pad': pad}}</style></head>"
            f"<body><div class='bg'></div><div class='grid'></div><div class='wrap'>{body}</div></body></html>")


def brand_row(right: str = "") -> str:
    return f"<div style='display:flex;justify-content:space-between;align-items:center'><div class='brand'>{LOGO}Goldglitch <span class='muted' style='font-weight:400'>· Stats</span></div><div class='eyebrow' style='font-size:20px'>{esc(right)}</div></div>"


FOOT = ("<div class='foot'><span>easygoldglitch.com</span>"
        "<span style='text-align:right'>Probabilidad, no certeza · Solo +18</span></div>")


# ------------------------------------------------------------------ slides
def cover(title: str, subtitle: str, eyebrow: str, w: int, h: int) -> str:
    return page(f"""{brand_row(eyebrow)}
      <div style='margin:auto 0'>
        <div class='eyebrow'>{esc(eyebrow)}</div>
        <div style='font-size:{int(w * 0.088)}px;font-weight:800;line-height:1.02;margin-top:28px;letter-spacing:-.02em'>{esc(title)}</div>
        <div class='muted' style='font-size:{int(w * 0.034)}px;margin-top:34px;line-height:1.35'>{esc(subtitle)}</div>
      </div>{FOOT}""", w, h)


def pick_slide(pk: dict, idx: int, total: int, when: str, w: int, h: int) -> str:
    p = float(pk["p"])
    c = color(p)
    return page(f"""{brand_row(f"{idx}/{total}")}
      <div style='margin:auto 0'>
        <div class='eyebrow' style='color:#9a9384'>{esc(pk.get('league'))} · {esc(when)}</div>
        <div style='font-size:{int(w * 0.052)}px;font-weight:600;margin-top:22px;line-height:1.15'>{esc(pk['home'])} <span class='muted'>vs</span> {esc(pk['away'])}</div>
        <div class='card' style='margin-top:50px;border-color:{c}55'>
          <div class='muted' style='font-size:26px;text-transform:uppercase;letter-spacing:.18em'>{esc(pk.get('group') or 'Pick del modelo')}</div>
          <div style='font-size:{int(w * 0.044)}px;font-weight:600;margin-top:18px;line-height:1.2'>{esc(pk['label'])}</div>
          <div class='mono' style='font-size:{int(w * 0.16)}px;font-weight:700;color:{c};margin-top:20px;line-height:1;text-shadow:0 0 40px {c}66'>{round(p * 100)}%</div>
          <div class='bar' style='margin-top:26px'><span style='width:{p * 100:.1f}%;background:{c}'></span></div>
        </div>
      </div>{FOOT}""", w, h)


def results_slide(rows: list[dict], won: int, n: int, title: str, w: int, h: int) -> str:
    items = "".join(
        f"<div style='display:flex;gap:22px;align-items:flex-start;padding:18px 0;border-top:1px solid rgba(255,255,255,.07)'>"
        f"<div class='mono' style='font-size:34px;width:44px;color:{'#2ef2a0' if r['status'] == 'won' else '#ff4d6d'}'>{'✓' if r['status'] == 'won' else '✗'}</div>"
        f"<div style='flex:1'><div style='font-size:27px;line-height:1.25'>{esc(r['label'])}</div>"
        f"<div class='muted' style='font-size:21px;margin-top:6px'>{esc(r['home'])} vs {esc(r['away'])}</div></div>"
        f"<div class='mono muted' style='font-size:26px'>{round(float(r['p']) * 100)}%</div></div>"
        for r in rows)
    rate = round(won / n * 100) if n else 0
    return page(f"""{brand_row("Resultados")}
      <div style='margin-top:60px'>
        <div class='eyebrow'>{esc(title)}</div>
        <div style='display:flex;align-items:baseline;gap:24px;margin-top:20px'>
          <div class='mono' style='font-size:{int(w * 0.13)}px;font-weight:700;color:#d4af37'>{won}/{n}</div>
          <div class='muted' style='font-size:34px'>acertados · {rate}%</div>
        </div>
      </div>
      <div style='margin-top:30px'>{items}</div>{FOOT}""", w, h)


def text_slide(title: str, body: str, eyebrow: str, w: int, h: int) -> str:
    paras = "".join(f"<p style='margin-top:26px'>{esc(x)}</p>" for x in body.split("\n") if x.strip())
    return page(f"""{brand_row(eyebrow)}
      <div style='margin:auto 0'>
        <div class='eyebrow'>{esc(eyebrow)}</div>
        <div style='font-size:{int(w * 0.07)}px;font-weight:800;line-height:1.05;margin-top:24px;letter-spacing:-.02em'>{esc(title)}</div>
        <div class='muted' style='font-size:{int(w * 0.033)}px;line-height:1.45;margin-top:12px'>{paras}</div>
      </div>{FOOT}""", w, h)


def cta_slide(w: int, h: int) -> str:
    return page(f"""{brand_row()}
      <div style='margin:auto 0'>
        <div style='font-size:{int(w * 0.075)}px;font-weight:800;line-height:1.05'>Todas las estadísticas,<br><span style='color:#d4af37'>partido a partido.</span></div>
        <div class='muted' style='font-size:{int(w * 0.034)}px;margin-top:30px;line-height:1.4'>Probabilidades del modelo, líneas de goles, córners, tarjetas y jugadores, y el historial público de aciertos.</div>
        <div class='card mono' style='margin-top:46px;font-size:{int(w * 0.04)}px;color:#d4af37;display:inline-block'>easygoldglitch.com</div>
      </div>{FOOT}""", w, h)


# ------------------------------------------------------------------ rendering
def render(html_pages: list[str], w: int, h: int, name: str) -> list[str]:
    """HTML → JPEG files (quality 92). Returns their paths."""
    from playwright.sync_api import sync_playwright
    Path(OUT).mkdir(exist_ok=True)
    paths = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
        for i, doc in enumerate(html_pages):
            pg.set_content(doc, wait_until="networkidle")
            pg.wait_for_timeout(250)
            path = os.path.join(OUT, f"{name}_{i + 1}.jpg")
            pg.screenshot(path=path, type="jpeg", quality=92)
            paths.append(path)
        b.close()
    return paths


def video(frames: list[str], name: str, seconds: float = 3.2) -> str:
    """Vertical MP4 (H.264, 30 fps) from 1080×1920 frames with a soft zoom and crossfades. Silent."""
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    Path(OUT).mkdir(exist_ok=True)
    out = os.path.join(OUT, f"{name}.mp4")
    fade = 0.45
    n = int(seconds * 30)
    inputs, parts = [], []
    for i, f in enumerate(frames):
        # One still per input; zoompan turns it into an n-frame clip with a slow push-in.
        inputs += ["-i", f]
        parts.append(f"[{i}:v]scale=1080:1920,zoompan=z='min(zoom+0.0006,1.05)':d={n}:s=1080x1920:fps=30,"
                     f"format=yuv420p,setsar=1[v{i}]")
    chain, last, t = [], "v0", seconds - fade
    for i in range(1, len(frames)):
        chain.append(f"[{last}][v{i}]xfade=transition=fade:duration={fade}:offset={t:.2f}[x{i}]")
        last, t = f"x{i}", t + seconds - fade
    graph = ";".join(parts + chain)
    cmd = [ff, "-y", *inputs, "-filter_complex", graph, "-map", f"[{last}]", "-r", "30", "-c:v", "libx264",
           "-preset", "veryfast", "-crf", "23", "-maxrate", "6M", "-bufsize", "12M", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True, capture_output=True)
    return out


def tmpdir() -> str:
    return tempfile.mkdtemp(prefix="gg_redes_")


# ------------------------------------------------------------------ profile assets (logo + cover)
MARK = ('<svg viewBox="0 0 32 32" width="{s}" height="{s}"><circle cx="16" cy="16" r="14" fill="none" stroke="#d4af37" stroke-width="1.6"/>'
        '<circle cx="16" cy="16" r="10.5" fill="none" stroke="#d4af37" stroke-opacity=".25" stroke-width="1"/>'
        '<rect x="10" y="17" width="3" height="6" rx="1" fill="#d4af37" fill-opacity=".45"/>'
        '<rect x="14.5" y="13" width="3" height="10" rx="1" fill="#d4af37" fill-opacity=".7"/>'
        '<rect x="19" y="9" width="3" height="14" rx="1" fill="#d4af37"/></svg>')
SERIF = "@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif&display=swap');"


def avatar_page(size: int = 1080) -> str:
    """Profile picture: the mark alone, centred inside the circle crop every network applies."""
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>*{{margin:0}}body{{width:{size}px;height:{size}px;"
            "background:radial-gradient(circle at 50% 42%,#1d1708 0%,#070604 58%,#020202 100%);display:grid;place-items:center}"
            f"</style></head><body>{MARK.format(s=int(size * 0.62))}</body></html>")


def cover_page(w: int = 1640, h: int = 624) -> str:
    """Facebook cover: content kept in the centre band (mobile crops the sides)."""
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>{SERIF}
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=JetBrains+Mono:wght@500&display=swap');
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{w}px;height:{h}px;overflow:hidden;color:#ede6d6;font-family:Inter,sans-serif;
 background:radial-gradient(700px 420px at 50% 0%,rgba(212,175,55,.20),transparent 70%),linear-gradient(180deg,#0b0906,#020202);position:relative}}
.grid{{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.03) 1px,transparent 1px);background-size:48px 48px}}
.wrap{{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);display:flex;align-items:center;gap:38px}}
.name{{font-family:'Instrument Serif',serif;font-size:96px;line-height:1;letter-spacing:-.01em;
 background:linear-gradient(180deg,#f6e6a8,#d4af37 55%,#9c7a1f);-webkit-background-clip:text;color:transparent}}
.tag{{margin-top:14px;font-size:30px;color:#cfc6b2;white-space:nowrap}}
.url{{margin-top:18px;font-family:'JetBrains Mono',monospace;font-size:22px;letter-spacing:.2em;color:#d4af37;text-transform:uppercase}}
.rule{{position:absolute;left:0;right:0;bottom:0;height:3px;background:linear-gradient(90deg,transparent,#d4af37,transparent)}}
{'.wrap{zoom:1.45}' if w >= 2000 else ''}
</style></head><body><div class='grid'></div><div class='wrap'>{MARK.format(s=190)}
<div><div class='name'>Goldglitch Stats</div><div class='tag'>Probabilidades de cada partido. Datos, no fijas.</div>
<div class='url'>easygoldglitch.com</div></div></div><div class='rule'></div></body></html>"""


def profile_assets() -> dict:
    """Renders the logo (1080×1080) and the Facebook cover (1640×624). Returns their paths."""
    logo = render([avatar_page()], 1080, 1080, "perfil_logo")[0]
    cover = render([cover_page()], 1640, 624, "perfil_portada")[0]
    banner = render([cover_page(2560, 1440)], 2560, 1440, "perfil_banner_youtube")[0]   # content stays in the safe area
    return {"logo": logo, "portada": cover, "banner": banner}
