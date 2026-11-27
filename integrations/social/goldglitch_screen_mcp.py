"""Servidor MCP "pantalla": le da a Claude Code (Haiku 5.5 con tu plan Pro) ojos y manos sobre el navegador de redes.

Lo arranca Claude Code para una sola tarea (GG_TAREA apunta a un JSON con la página inicial, los archivos, la descripción,
si es ensayo y dónde dejar el resultado). Herramientas: captura, clic, escribir, tecla, desplazar, arrastrar, esperar,
ampliar, abrir_pagina, escribir_texto_preparado y terminar. Las mismas protecciones que el agente por API:
  - el selector de archivos adjunta solo los archivos de la publicación;
  - solo Instagram, Facebook y TikTok;
  - en ensayo, el botón final (Compartir/Publicar) está bloqueado.
"""
from __future__ import annotations

import asyncio
import json
import re
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from mcp.server.fastmcp import FastMCP, Image  # noqa: E402

from goldglitch_social_browser import Browser  # noqa: E402
from goldglitch_social_computer import ALLOWED, H, W, ScreenAgent  # noqa: E402

TASK = json.load(open(os.environ["GG_TAREA"], encoding="utf-8"))
EXEC = ThreadPoolExecutor(max_workers=1)      # Playwright's sync API lives in this one thread
S: dict = {"pg": None, "br": None, "agent": None,
           "state": {"rehearsal": bool(TASK.get("rehearsal")), "files": TASK["files"]}}
if TASK.get("final_regex"):
    S["state"]["final_re"] = re.compile(TASK["final_regex"], re.I)
mcp = FastMCP("pantalla")


def _page():
    if S["pg"] is None:
        br = Browser(net=TASK.get("net"))
        pg = br.page()
        pg.set_viewport_size({"width": W, "height": H})

        def on_chooser(fc) -> None:
            files = S["state"]["files"]
            fc.set_files(files if fc.is_multiple() else files[:1])
            S["state"]["attached"] = True
        pg.on("filechooser", on_chooser)
        pg.on("dialog", lambda d: d.dismiss())
        try:      # sites that open the new File System Access picker skip the chooser we intercept: make them use <input>
            pg.add_init_script("try{Object.defineProperty(window,'showOpenFilePicker',{value:undefined,configurable:true})}catch(e){}")
        except Exception:
            pass
        try:
            pg.goto(TASK["start_url"], wait_until="domcontentloaded", timeout=60_000)
        except Exception:
            pass
        time.sleep(4)
        S.update(br=br, pg=pg, agent=ScreenAgent(br, "", lambda m: None))
    return S["pg"]


def _img(block: dict) -> Image:
    import base64
    return Image(data=base64.b64decode(block["source"]["data"]), format="png")


def _direct_attach(pg) -> str:
    """Put the file straight into the page's <input type=file> (any frame) when clicking the upload button opened no
    chooser we can see (TikTok Studio since 2026-11-25). Only for publications, and only once."""
    files = S["state"].get("files") or []
    if S["state"].get("attached") or not files or TASK.get("kind") == "profile":
        return ""
    for fr in pg.frames:
        try:
            loc = fr.locator("input[type=file]")
            if loc.count() == 0:
                continue
            el = loc.first
            multi = bool(el.get_attribute("multiple") is not None)
            el.set_input_files(files if multi else files[:1], timeout=10_000)
            S["state"]["attached"] = True
            return "Archivo adjuntado directamente en el campo de carga de la página."
        except Exception:
            continue
    return ""


def _act(name: str, a: dict):
    pg = _page()
    out = S["agent"]._do(pg, name, a, S["state"])
    if isinstance(out, str) and "click" in name and not S["state"].get("attached"):
        time.sleep(1.5)                             # a real chooser fires within a second; if not, attach directly
        note = _direct_attach(pg)
        if note:
            out = f"{out} {note}"
    if isinstance(out, list):
        return [_img(out[0])]
    if out.startswith("ENSAYO") or out.startswith("Acción no"):
        return [out]
    time.sleep(0.6)
    return [out, _img(S["agent"]._shot(pg))]


async def _run(fn, *args):
    return await asyncio.get_running_loop().run_in_executor(EXEC, fn, *args)


def _ask_person(motivo: str) -> list:
    """Bring the window to the screen, beep, and give the person up to 2 minutes (they solve captchas, not the agent)."""
    pg = _page()
    try:
        cdp = pg.context.new_cdp_session(pg)
        win = cdp.send("Browser.getWindowForTarget")["windowId"]
        cdp.send("Browser.setWindowBounds", {"windowId": win, "bounds": {"windowState": "normal"}})
        cdp.send("Browser.setWindowBounds", {"windowId": win, "bounds": {"left": 60, "top": 40, "width": 1320, "height": 960}})
        pg.bring_to_front()
    except Exception:
        pass
    try:
        import ctypes
        for _ in range(3):
            ctypes.windll.user32.MessageBeep(0x30)
            time.sleep(0.4)
        ctypes.windll.user32.FlashWindow(ctypes.windll.user32.GetForegroundWindow(), True)
    except Exception:
        pass
    S["state"]["persona"] = S["state"].get("persona", 0) + 1
    first = S["agent"]._shot(pg)
    for _ in range(24):                     # up to 2 minutes, returns early when the screen changes a lot
        time.sleep(5)
        now = S["agent"]._shot(pg)
        if now["source"]["data"][-4000:] != first["source"]["data"][-4000:]:
            time.sleep(3)
            break
    return [_img(S["agent"]._shot(pg)), f"Se esperó a la persona por: {motivo}. Revisa la captura: si el captcha ya no está, sigue."]


@mcp.tool()
async def esperar_persona(motivo: str = "captcha") -> list:
    """Cuando aparezca un captcha, rompecabezas o verificación: NO lo resuelvas. Esta herramienta pone la ventana a la
    vista, avisa con un sonido y espera hasta 2 minutos a que la persona lo resuelva. Puedes usarla hasta 3 veces."""
    if S["state"].get("persona", 0) >= 3:
        return ["Ya se esperó 3 veces: termina con estado bloqueado."]
    return await _run(_ask_person, motivo)


@mcp.tool()
async def captura() -> list:
    """Captura de la pantalla actual (1280×800). Las coordenadas de las demás herramientas usan esta imagen."""
    return await _run(lambda: [_img(S["agent"]._shot(_page())) if _page() else "sin página"])


@mcp.tool()
async def clic(x: int, y: int, boton: str = "left", veces: int = 1) -> list:
    """Clic en (x, y). boton: left | right | middle. veces: 1, 2 (doble) o 3 (triple). Devuelve la pantalla nueva."""
    name = {"right": "right_click", "middle": "middle_click"}.get(boton) or {2: "double_click", 3: "triple_click"}.get(veces, "left_click")
    return await _run(_act, name, {"coordinate": [x, y]})


@mcp.tool()
async def escribir(texto: str) -> list:
    """Escribe texto donde está el cursor (no la uses para la descripción: usa escribir_texto_preparado)."""
    return await _run(_act, "type", {"text": texto})


@mcp.tool()
async def tecla(combinacion: str, repetir: int = 1) -> list:
    """Pulsa una tecla o combinación: Return, Escape, Tab, BackSpace, Delete, ctrl+a, Page_Down…"""
    return await _run(_act, "key", {"text": combinacion, "repeat": repetir})


@mcp.tool()
async def desplazar(x: int, y: int, direccion: str = "down", cantidad: int = 3) -> list:
    """Desplaza la página en (x, y). direccion: up | down | left | right."""
    return await _run(_act, "scroll", {"coordinate": [x, y], "scroll_direction": direccion, "scroll_amount": cantidad})


@mcp.tool()
async def arrastrar(x1: int, y1: int, x2: int, y2: int) -> list:
    """Arrastra con el botón izquierdo de (x1, y1) a (x2, y2)."""
    return await _run(_act, "left_click_drag", {"start_coordinate": [x1, y1], "coordinate": [x2, y2]})


@mcp.tool()
async def esperar(segundos: float = 3) -> list:
    """Espera (máx. 30 s), por ejemplo mientras sube un video, y devuelve la pantalla."""
    return await _run(_act, "wait", {"duration": segundos})


@mcp.tool()
async def ampliar(x0: int, y0: int, x1: int, y1: int) -> list:
    """Imagen ampliada de una zona de la pantalla para leer texto pequeño."""
    return await _run(_act, "zoom", {"region": [x0, y0, x1, y1]})


@mcp.tool()
async def abrir_pagina(url: str) -> list:
    """Abre una dirección de Instagram, Facebook o TikTok."""
    def go():
        host = urlsplit(url).hostname or ""
        if not any(host == d or host.endswith("." + d) for d in ALLOWED):
            return ["Solo se permiten direcciones de Instagram, Facebook o TikTok."]
        pg = _page()
        pg.goto(url, wait_until="domcontentloaded", timeout=60_000)
        time.sleep(3)
        return [_img(S["agent"]._shot(pg))]
    return await _run(go)


@mcp.tool()
async def escribir_texto_preparado() -> list:
    """Escribe la descripción exacta de la publicación donde está el cursor (haz clic antes en el cuadro de texto)."""
    return await _run(_act, "type", {"text": TASK["caption"]})


async def escribir_texto_guardado(cual: str) -> list:
    """Escribe, donde está el cursor, uno de los textos preparados de la tarea (por ejemplo: bio, descripcion, sitio_web)."""
    textos = TASK.get("textos") or {}
    if cual not in textos:
        return [f"No existe '{cual}'. Disponibles: {', '.join(textos) or 'ninguno'}"]
    return await _run(_act, "type", {"text": textos[cual]})


async def preparar_archivo(cual: str) -> str:
    """Elige qué archivo adjuntar la próxima vez que abras un selector de archivos (por ejemplo: logo, portada)."""
    archivos = TASK.get("archivos") or {}
    if cual not in archivos:
        return f"No existe '{cual}'. Disponibles: {', '.join(archivos) or 'ninguno'}"
    S["state"]["files"] = [archivos[cual]]
    return f"Listo: el próximo selector de archivos adjuntará '{cual}'."


# Only profile tasks have several named files/texts; in a publication the files attach by themselves, so these
# tools are not offered there (an agent once tried preparar_archivo('1') and stopped).
if TASK.get("textos"):
    mcp.tool()(escribir_texto_guardado)
if TASK.get("archivos"):
    mcp.tool()(preparar_archivo)


@mcp.tool()
async def terminar(estado: str, detalle: str) -> str:
    """Termina la tarea. estado: publicado | listo_para_publicar | bloqueado | fallo. detalle: qué pasó."""
    def done():
        shot = None
        if estado not in ("publicado", "listo_para_publicar") and S["pg"] is not None:
            try:
                os.makedirs(os.path.dirname(TASK["evidence"]), exist_ok=True)
                S["pg"].screenshot(path=TASK["evidence"])
                shot = TASK["evidence"]
            except Exception:
                pass
        with open(TASK["result"], "w", encoding="utf-8") as f:
            json.dump({"estado": estado, "detalle": detalle[:3000], "final_bloqueado": bool(S["state"].get("blocked_final")),
                       "adjuntado": bool(S["state"].get("attached")), "captura": shot}, f, ensure_ascii=False)
        if S["br"] is not None:
            S["br"].close()
            S.update(br=None, pg=None)
        return "Tarea terminada. No hagas nada más."
    return await _run(done)


if __name__ == "__main__":
    mcp.run()
