"""Publicación en Instagram, Facebook y TikTok usando un navegador real (sin APIs, sin Meta Developers, sin suscripciones).

Los agentes manejan un Chrome/Chromium con un perfil propio (carpeta redes_perfil) donde tú iniciaste sesión una vez con
`goldglitch_social.py conectar`. Nunca se guardan ni se escriben contraseñas: la sesión vive en ese perfil, como en tu
navegador de siempre.

Cada red tiene el mismo "contrato" que las clases de la API (goldglitch_social_platforms), así el resto del sistema no
cambia. Si algo falla se guarda una captura en redes_salida/errores para corregir el paso exacto.

Modo ensayo (REDES_ENSAYO=1 o `tick --ensayo`): hace todo, menos el clic final de "Compartir/Publicar", con la ventana a
la vista. Sirve para comprobar cada paso antes de dejarlo en automático.
"""
from __future__ import annotations

import json
import os
import random
import re
import time
from typing import Any

from goldglitch_social_platforms import PlatformError

HERE = os.path.dirname(os.path.abspath(__file__))
PROFILE = os.path.join(HERE, "redes_perfil")
CONFIG = os.path.join(HERE, "redes_navegador.json")
ERRDIR = os.path.join(HERE, "redes_salida", "errores")

IG = "https://www.instagram.com/"
FB = "https://www.facebook.com/"
TT_UPLOAD = "https://www.tiktok.com/tiktokstudio/upload?from=webapp"

# Cookies that only exist with a signed-in session.
SESSION_COOKIES = {"instagram": ("instagram.com", "sessionid"), "facebook": ("facebook.com", "c_user"),
                   "tiktok": ("tiktok.com", "sessionid"), "youtube": ("youtube.com", "LOGIN_INFO")}


def rx(*words: str) -> re.Pattern:
    """Case-insensitive regex for the Spanish and English UI texts."""
    return re.compile("|".join(re.escape(w) for w in words), re.I)


def brave_sessions(cfg: dict) -> dict:
    """Networks that run in Brave: read their session straight from the agents' Brave profile, so a sign-in done there
    (or copied from your Brave) counts without reconnecting."""
    out = dict(cfg.get("sessions") or {})
    for net in cfg.get("brave_redes") or []:
        if net in SESSION_COOKIES and not out.get(net):
            dom, name = SESSION_COOKIES[net]
            n = _has_session(os.path.join(BRAVE_PROFILE, "Default"), dom, name)
            if n > 0 or (n < 0 and _brave_up()):          # locked = the agents' Brave is open with that profile
                out[net] = True
    return out


def load_config() -> dict:
    try:
        with open(CONFIG, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_config(cfg: dict) -> None:
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=1)


BRAVE_PROFILE = os.path.join(HERE, "redes_perfil_brave")
BRAVE_PORT = int(os.environ.get("REDES_BRAVE_PUERTO", "9333"))


def brave_exe() -> str | None:
    for base in (os.environ.get("PROGRAMFILES", r"C:\Program Files"), os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
                 os.environ.get("LOCALAPPDATA", "")):
        p = os.path.join(base or "", "BraveSoftware", "Brave-Browser", "Application", "brave.exe")
        if base and os.path.exists(p):
            return p
    return None


def uses_brave(net: str | None) -> bool:
    """Networks that run in Brave (a normal Brave window driven over its debugging port: TikTok refuses the
    Playwright-launched Chrome but works in Brave)."""
    if os.environ.get("REDES_NAVEGADOR", "").lower() == "brave":
        return True
    return bool(net) and net in (load_config().get("brave_redes") or [])


def _brave_up() -> bool:
    import urllib.request
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{BRAVE_PORT}/json/version", timeout=2).read()
        return True
    except Exception:
        return False


def profile_ready() -> bool:
    return os.path.isdir(PROFILE) and bool(load_config().get("connected"))


class Browser:
    """One persistent browser for the whole tick (opened on first use, closed at the end)."""

    def __init__(self, visible: bool = False, rehearsal: bool = False, net: str | None = None):
        self.visible, self.rehearsal = visible or rehearsal, rehearsal
        self.net = net
        self._pw = self._ctx = self._cdp = None
        self._mine: list = []

    def _brave(self):
        """Start (or reuse) a real Brave window with its own profile and attach to it. No automation flags at all."""
        import subprocess
        exe = brave_exe()
        if not exe:
            raise PlatformError("No encontré Brave instalado (BraveSoftware\\Brave-Browser\\Application\\brave.exe)")
        if not _brave_up():
            args = [exe, f"--user-data-dir={BRAVE_PROFILE}", f"--remote-debugging-port={BRAVE_PORT}", "--no-first-run",
                    "--no-default-browser-check", "--window-size=1320,960"]
            if not self.visible:
                args.append("--window-position=-2400,0")
            subprocess.Popen(args, creationflags=getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
            for _ in range(40):
                if _brave_up():
                    break
                time.sleep(0.5)
            else:
                raise PlatformError("Brave no abrió su puerto de control (¿hay otro Brave con este perfil abierto?)")
        self._cdp = self._pw.chromium.connect_over_cdp(f"http://127.0.0.1:{BRAVE_PORT}")
        return self._cdp.contexts[0] if self._cdp.contexts else self._cdp.new_context()

    # --- lifecycle
    def context(self):
        if self._ctx:
            return self._ctx
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        if uses_brave(self.net):
            try:
                self._ctx = self._brave()
            except Exception as e:
                self.close()
                raise e if isinstance(e, PlatformError) else PlatformError(f"No se pudo conectar con Brave: {e}")
            self._ctx.set_default_timeout(30_000)
            return self._ctx
        args = ["--disable-blink-features=AutomationControlled", "--no-first-run", "--no-default-browser-check"]
        if not self.visible:
            args.append("--window-position=-2400,0")      # real window (sites treat headless as a bot), just off-screen
        args.append("--window-size=1320,960")
        # No "--enable-automation" (it sets navigator.webdriver and shows the "controlled by software" bar): TikTok
        # refuses to load its pages in a browser that announces automation.
        opts: dict[str, Any] = dict(user_data_dir=PROFILE, headless=False, args=args, locale="es-CO", no_viewport=True,
                                    ignore_default_args=["--enable-automation"], timezone_id="America/Bogota")
        try:
            self._ctx = self._pw.chromium.launch_persistent_context(channel="chrome", **opts)   # installed Google Chrome
        except Exception:
            try:
                self._ctx = self._pw.chromium.launch_persistent_context(**opts)              # Playwright's Chromium
            except Exception as e:
                self.close()
                raise PlatformError(f"No se pudo abrir el navegador de redes (¿quedó otro abierto?): {e}")
        self._ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
        self._ctx.set_default_timeout(30_000)
        return self._ctx

    def page(self):
        ctx = self.context()
        pg = ctx.new_page()
        self._mine.append(pg)
        return pg

    def close(self) -> None:
        try:
            if self._cdp:                       # Brave stays open (signed in); only our tabs close
                for pg in self._mine:
                    try:
                        pg.close()
                    except Exception:
                        pass
                self._cdp.close()
            elif self._ctx:
                self._ctx.close()
        finally:
            if self._pw:
                self._pw.stop()
            self._ctx = self._pw = self._cdp = None
            self._mine = []

    def signed_in(self) -> dict[str, bool]:
        cookies = self.context().cookies()
        return {net: any(c["name"] == name and dom in c["domain"] for c in cookies)
                for net, (dom, name) in SESSION_COOKIES.items()}

    # --- helpers
    @staticmethod
    def pause(a: float = 0.8, b: float = 1.8) -> None:
        time.sleep(random.uniform(a, b))

    def fail(self, pg, net: str, step: str, e: Exception | None = None) -> PlatformError:
        os.makedirs(ERRDIR, exist_ok=True)
        shot = os.path.join(ERRDIR, f"{net}_{time.strftime('%Y%m%d_%H%M%S')}.png")
        try:
            pg.screenshot(path=shot, full_page=False)
        except Exception:
            shot = "(sin captura)"
        try:   # what the page offers (buttons, links, labels, file inputs) so the step can be fixed from here
            items = pg.evaluate("""() => {
              const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
              const out = [];
              document.querySelectorAll('a,button,[role=button],[role=link],[role=menuitem],[aria-label],input[type=file]').forEach(e => {
                if (e.tagName !== 'INPUT' && !vis(e)) return;
                const t = (e.getAttribute('aria-label') || e.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 80);
                const extra = e.tagName === 'INPUT' ? ` accept=${e.accept} multiple=${e.multiple} inDialog=${!!e.closest('[role=dialog]')}` : '';
                if (t || extra) out.push(`${e.tagName.toLowerCase()}[${e.getAttribute('role') || ''}] ${t} ${e.getAttribute('href') || ''}${extra}`);
              });
              return [...new Set(out)].slice(0, 400);
            }""")
            with open(shot[:-4] + ".txt", "w", encoding="utf-8") as f:
                f.write(pg.url + "\n" + "\n".join(items))
        except Exception:
            pass
        return PlatformError(f"{net}: falló el paso «{step}» ({type(e).__name__ + ': ' + str(e)[:160] if e else 'no encontrado'}). Captura: {shot}")

    @staticmethod
    def first_visible(*locators, timeout: float = 8.0):
        """The first locator that becomes visible, or None."""
        end = time.time() + timeout
        while time.time() < end:
            for loc in locators:
                try:
                    if loc.count() and loc.first.is_visible():
                        return loc.first
                except Exception:
                    pass
            time.sleep(0.4)
        return None

    def dismiss(self, pg) -> None:
        """Close the usual pop-ups (notifications, cookies, 'save login')."""
        for _ in range(3):
            b = self.first_visible(pg.get_by_role("button", name=rx("Ahora no", "Not now", "Rechazar cookies opcionales",
                                                                   "Decline optional cookies", "Permitir solo las cookies necesarias",
                                                                   "Only allow essential cookies")), timeout=1.5)
            if not b:
                return
            b.click()
            self.pause(0.5, 1.0)

    def type_text(self, pg, box, text: str) -> None:
        box.click()
        self.pause(0.3, 0.7)
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if line:
                pg.keyboard.insert_text(line)
            if i < len(lines) - 1:
                pg.keyboard.press("Shift+Enter")
        self.pause()

    def finish(self, pg, button, net: str) -> bool:
        """Final click — skipped in rehearsal mode. Returns True if it really published."""
        if self.rehearsal:
            print(f"[ensayo] {net}: todo listo; NO se hace clic en «Publicar». Revisa la ventana (20 s).")
            time.sleep(20)
            return False
        button.click()
        return True


# ------------------------------------------------------------------ Instagram + Facebook (same contract as Meta)
class BrowserMeta:
    local = True            # receives file paths, not public URLs

    def __init__(self, br: Browser, fb_page: str | None, instagram: bool = True):
        self.br, self.fb_page = br, fb_page
        self.ig = "navegador" if instagram else None
        self.fb = bool(fb_page)

    # --- Instagram
    def _ig_post(self, paths: list[str], caption: str) -> str:
        br = self.br
        pg = br.page()
        step = "abrir Instagram"
        try:
            pg.goto(IG, wait_until="domcontentloaded")
            br.pause(2, 3.5)
            br.dismiss(pg)
            step = "botón Crear"
            file_in = pg.locator('div[role="dialog"] input[type="file"]')   # only the "new post" dialog, never a page input
            label = re.compile(r"^(Crear|Create|Nueva publicación|New post)$", re.I)

            def open_create() -> bool:
                c = br.first_visible(pg.get_by_role("link", name=label), pg.get_by_role("button", name=label),
                                     pg.get_by_label(label), timeout=4)
                if not c:
                    return False
                c.click()
                br.pause()
                sub = br.first_visible(pg.get_by_role("link", name=re.compile(r"^(Publicación|Post)$", re.I)),
                                       pg.get_by_role("button", name=re.compile(r"^(Publicación|Post)$", re.I)),
                                       pg.get_by_text(re.compile(r"^(Publicación|Post)$")), timeout=3)
                if sub:
                    sub.click()
                    br.pause()
                return br.first_visible(pg.locator('div[role="dialog"]'), timeout=8) is not None

            opened = open_create()
            if not opened:                       # icon-only sidebar: "Crear" may live in the ☰ menu
                more = br.first_visible(pg.get_by_role("link", name=rx("Más", "More")), pg.get_by_role("button", name=rx("Más", "More")),
                                        pg.get_by_label(re.compile(r"^(Más|More|Configuración|Settings)$", re.I)), timeout=3)
                if more:
                    more.click()
                    br.pause()
                    opened = open_create()
            if not opened:
                raise br.fail(pg, "instagram", step)
            step = "subir archivos"
            if file_in.count():
                multi = file_in.first.evaluate("e => e.multiple")
                file_in.first.set_input_files(paths if multi or len(paths) == 1 else paths[:1])
            else:
                pick = br.first_visible(pg.get_by_role("button", name=rx("Seleccionar del ordenador", "Seleccionar de la computadora",
                                                                         "Select from computer", "Seleccionar")), timeout=8)
                if not pick:
                    raise br.fail(pg, "instagram", step)
                with pg.expect_file_chooser() as fc:
                    pick.click()
                ch = fc.value
                ch.set_files(paths if ch.is_multiple() or len(paths) == 1 else paths[:1])
            br.pause(2.5, 4)
            ok = br.first_visible(pg.get_by_role("button", name=rx("Aceptar", "OK")), timeout=3)   # "videos now share as reels"
            if ok:
                ok.click()
                br.pause()
            for n in (1, 2):
                step = f"Siguiente ({n})"
                nxt = br.first_visible(pg.get_by_role("button", name=re.compile(r"^(Siguiente|Next)$", re.I)),
                                       pg.locator('div[role="dialog"] div[role="button"]', has_text=re.compile(r"^(Siguiente|Next)$")),
                                       timeout=20)
                if not nxt:
                    raise br.fail(pg, "instagram", step)
                nxt.click()
                br.pause(1.5, 2.5)
            step = "escribir descripción"
            box = br.first_visible(pg.locator('div[role="dialog"] div[contenteditable="true"]'), timeout=15)
            if not box:
                raise br.fail(pg, "instagram", step)
            br.type_text(pg, box, caption[:2200])
            step = "Compartir"
            share = br.first_visible(pg.get_by_role("button", name=re.compile(r"^(Compartir|Share)$", re.I)),
                                     pg.locator('div[role="dialog"] div[role="button"]', has_text=re.compile(r"^(Compartir|Share)$")),
                                     timeout=10)
            if not share:
                raise br.fail(pg, "instagram", step)
            if not br.finish(pg, share, "instagram"):
                return "ensayo"
            step = "confirmación"
            done = br.first_visible(pg.get_by_text(rx("Se compartió tu publicación", "Se ha compartido tu publicación",
                                                      "Your post has been shared", "Se compartió tu reel", "Your reel has been shared")),
                                    timeout=240)
            if not done:
                raise br.fail(pg, "instagram", step)
            br.pause()
            return "publicado"
        except PlatformError:
            raise
        except Exception as e:
            raise br.fail(pg, "instagram", step, e)
        finally:
            pg.close()

    def ig_image(self, path: str, caption: str) -> str:
        return self._ig_post([path], caption)

    def ig_carousel(self, paths: list[str], caption: str) -> str:
        return self._ig_post(paths[:10], caption)

    def ig_reel(self, path: str, caption: str) -> str:
        return self._ig_post([path], caption)

    def ig_story(self, path: str) -> str:
        raise PlatformError("instagram: las historias no se pueden subir desde la web de escritorio (se omite)")

    # --- Facebook page (the profile must be switched into the page once, during `conectar`)
    def fb_photos(self, paths: list[str], caption: str) -> str:
        br = self.br
        pg = br.page()
        step = "abrir la página"
        try:
            pg.goto(self.fb_page or FB, wait_until="domcontentloaded")
            br.pause(2.5, 4)
            br.dismiss(pg)
            # If the session is still the personal profile, Facebook shows "Cambiar ahora" on a page you manage:
            # switch so the post goes out as the page, never as the personal profile.
            sw = br.first_visible(pg.get_by_role("button", name=rx("Cambiar ahora", "Switch now", "Cambiar a la página",
                                                                  "Switch into page")), timeout=3)
            if sw:
                step = "cambiar a la página"
                sw.click()
                br.pause(3, 5)
                confirm = br.first_visible(pg.get_by_role("button", name=re.compile(r"^(Cambiar|Switch)$", re.I)), timeout=4)
                if confirm:
                    confirm.click()
                    br.pause(4, 6)
                pg.goto(self.fb_page or FB, wait_until="domcontentloaded")
                br.pause(3, 4)
                br.dismiss(pg)
            step = "abrir el cuadro de publicación"
            opener = br.first_visible(
                pg.get_by_role("button", name=rx("¿Qué estás pensando", "What's on your mind", "Crear publicación", "Create post")),
                pg.get_by_text(rx("¿Qué estás pensando", "What's on your mind")), timeout=15)
            if not opener:
                raise br.fail(pg, "facebook", step)
            opener.click()
            br.pause(1.5, 2.5)
            dlg = pg.get_by_role("dialog").filter(has_text=rx("Crear publicación", "Create post")).last
            step = "adjuntar fotos"
            dialogs = pg.locator('div[role="dialog"]')
            inp = dialogs.locator('input[type="file"]')
            if not inp.count():
                btn = br.first_visible(dialogs.get_by_label(rx("Foto/video", "Photo/video")),
                                       dialogs.get_by_role("button", name=rx("Foto/video", "Photo/video")), timeout=8)
                if not btn:
                    raise br.fail(pg, "facebook", step)
                try:
                    with pg.expect_file_chooser(timeout=5000) as fc:
                        btn.click()
                    fc.value.set_files(paths[:10] if fc.value.is_multiple() else paths[:1])
                    inp = None
                except Exception:
                    br.pause()
                    inp = dialogs.locator('input[type="file"]')
                    if not inp.count():
                        add = br.first_visible(dialogs.get_by_text(rx("Agregar fotos/videos", "Add photos/videos")), timeout=6)
                        if not add:
                            raise br.fail(pg, "facebook", step)
                        with pg.expect_file_chooser(timeout=8000) as fc:
                            add.click()
                        fc.value.set_files(paths[:10] if fc.value.is_multiple() else paths[:1])
                        inp = None
            if inp is not None:
                multi = inp.first.evaluate("e => e.multiple")
                inp.first.set_input_files(paths[:10] if multi else paths[:1])
            br.pause(3, 5)
            dlg = dialogs.filter(has_text=rx("Crear publicación", "Create post")).last
            step = "escribir texto"
            box = br.first_visible(dlg.get_by_role("textbox"), dlg.locator('div[contenteditable="true"]'), timeout=10)
            if not box:
                raise br.fail(pg, "facebook", step)
            br.type_text(pg, box, caption)
            nxt = br.first_visible(dlg.get_by_role("button", name=re.compile(r"^(Siguiente|Next)$", re.I)), timeout=3)
            if nxt:
                nxt.click()
                br.pause(1.5, 2.5)
            step = "Publicar"
            post = br.first_visible(pg.get_by_role("button", name=re.compile(r"^(Publicar|Post)$", re.I)),
                                    pg.locator('div[aria-label="Publicar"], div[aria-label="Post"]'), timeout=10)
            if not post:
                raise br.fail(pg, "facebook", step)
            if not br.finish(pg, post, "facebook"):
                return "ensayo"
            step = "confirmación"
            end = time.time() + 180
            while time.time() < end and dlg.count() and dlg.is_visible():
                time.sleep(1)
            if dlg.count() and dlg.is_visible():
                raise br.fail(pg, "facebook", step)
            br.pause(2, 3)
            return "publicado"
        except PlatformError:
            raise
        except Exception as e:
            raise br.fail(pg, "facebook", step, e)
        finally:
            pg.close()

    def fb_video(self, path: str, caption: str, title: str = "") -> str:
        return self.fb_photos([path], caption)

    # --- comments and metrics: not yet in browser mode (they come in the next step, once publishing is confirmed)
    def ig_recent_comments(self, media_limit: int = 12) -> list[dict]:
        return []

    def fb_recent_comments(self, post_limit: int = 12) -> list[dict]:
        return []

    def reply(self, c: dict, text: str) -> None:
        raise PlatformError("respuestas por navegador aún no activadas")

    def hide(self, c: dict) -> None:
        raise PlatformError("ocultar por navegador aún no activado")

    def ig_insights(self, days: int = 7) -> list[dict]:
        return []


# ------------------------------------------------------------------ TikTok (same contract as TikTok.video)
class BrowserTikTok:
    local = True

    def __init__(self, br: Browser):
        self.br = br

    def video(self, path: str, title: str) -> str:
        br = self.br
        pg = br.page()
        step = "abrir TikTok Studio"
        try:
            pg.goto(TT_UPLOAD, wait_until="domcontentloaded")
            br.pause(3, 5)
            br.dismiss(pg)
            step = "subir video"
            pg.locator('input[type="file"]').first.set_input_files(path)
            step = "esperar la subida"
            post = pg.locator('button[data-e2e="post_video_button"]')
            if not br.first_visible(post, pg.get_by_role("button", name=re.compile(r"^(Publicar|Post)$", re.I)), timeout=120):
                raise br.fail(pg, "tiktok", step)
            end = time.time() + 300
            while time.time() < end:
                done = br.first_visible(pg.get_by_text(rx("Subido", "Uploaded", "Cargado")), timeout=2)
                b = post.first if post.count() else pg.get_by_role("button", name=re.compile(r"^(Publicar|Post)$", re.I)).first
                if done or (b.is_enabled() and b.get_attribute("aria-disabled") != "true" and b.get_attribute("data-disabled") != "true"):
                    break
                time.sleep(2)
            step = "escribir descripción"
            box = br.first_visible(pg.locator('div[contenteditable="true"]'), timeout=15)
            if not box:
                raise br.fail(pg, "tiktok", step)
            box.click()
            pg.keyboard.press("Control+A")
            pg.keyboard.press("Delete")
            br.type_text(pg, box, title[:2200])
            pg.keyboard.press("Escape")               # close a hashtag suggestion list if one opened
            br.pause()
            step = "Publicar"
            b = post.first if post.count() else pg.get_by_role("button", name=re.compile(r"^(Publicar|Post)$", re.I)).first
            b.scroll_into_view_if_needed()
            if not br.finish(pg, b, "tiktok"):
                return "ensayo"
            now = br.first_visible(pg.get_by_role("button", name=rx("Publicar ahora", "Post now")), timeout=5)
            if now:
                now.click()
            step = "confirmación"
            end = time.time() + 240
            while time.time() < end:
                if "/tiktokstudio/content" in pg.url or br.first_visible(
                        pg.get_by_text(rx("Tu video se ha publicado", "se publicó", "Your video has been posted", "Video published")), timeout=2):
                    br.pause()
                    return "publicado"
            raise br.fail(pg, "tiktok", step)
        except PlatformError:
            raise
        except Exception as e:
            raise br.fail(pg, "tiktok", step, e)
        finally:
            pg.close()


# ------------------------------------------------------------------ one-time sign-in
def _brave_user_data() -> str:
    return os.path.join(os.environ.get("LOCALAPPDATA", ""), "BraveSoftware", "Brave-Browser", "User Data")


def _brave_running() -> bool:
    import subprocess
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq brave.exe"], capture_output=True, text=True).stdout
        return "brave.exe" in out.lower()
    except Exception:
        return False


def _has_session(profile_dir: str, dom: str, name: str) -> int:
    """How many session cookies of `dom` this Brave profile has (host and name are not encrypted)."""
    import shutil
    import sqlite3
    import tempfile
    for rel in (os.path.join("Network", "Cookies"), "Cookies"):
        src = os.path.join(profile_dir, rel)
        if os.path.exists(src):
            tmp = os.path.join(tempfile.mkdtemp(), "c.db")
            try:
                shutil.copy2(src, tmp)
                with sqlite3.connect(tmp) as db:
                    return db.execute("SELECT count(*) FROM cookies WHERE host_key LIKE ? AND name = ?",
                                      (f"%{dom}", name)).fetchone()[0]
            except Exception:
                return -1           # locked by a running Brave: cannot tell
    return 0


SKIP = {"Cache", "Code Cache", "GPUCache", "DawnCache", "DawnGraphiteCache", "DawnWebGPUCache", "GrShaderCache",
        "ShaderCache", "CacheStorage", "ScriptCache", "Login Data", "Login Data-journal", "Login Data For Account",
        "Login Data For Account-journal", "Web Data", "Web Data-journal", "History", "History-journal", "Top Sites",
        "Visited Links", "Favicons", "Favicons-journal", "Shortcuts", "Media History", "BrowserMetrics", "Crashpad"}


def adopt_brave(nets: list[str]) -> bool:
    """Copy the session of your installed Brave (where you are already signed in) into the agents' Brave profile.
    Passwords, history and autofill are NOT copied. Brave must be closed while copying (its files are locked)."""
    import shutil
    src_root = _brave_user_data()
    if not os.path.isdir(src_root):
        print("No encontré tu perfil de Brave.")
        return False
    dom, name = SESSION_COOKIES[nets[0]]
    cands = [d for d in os.listdir(src_root) if d == "Default" or d.startswith("Profile ")]
    scored = sorted(((_has_session(os.path.join(src_root, d), dom, name), d) for d in cands), reverse=True)
    if not scored or scored[0][0] == 0:
        print(f"En tu Brave no encontré una sesión de {nets[0]} iniciada.")
        return False
    prof = scored[0][1]
    print(f"Tu Brave tiene la sesión de {nets[0]} en el perfil '{prof}'. La copio al Brave de los agentes "
          "(sin contraseñas, historial ni autocompletar).")
    for _ in range(3):
        if not _brave_running():
            break
        ans = input("Brave está abierto y sus archivos están bloqueados. Ciérralo por completo (también desde la bandeja) "
                    "y presiona Enter, o escribe C para que lo cierre yo: ").strip().lower()
        if ans == "c":
            import subprocess
            subprocess.run(["taskkill", "/IM", "brave.exe", "/F"], capture_output=True)
            time.sleep(2)
    if _brave_running():
        print("Brave sigue abierto: no se pudo copiar la sesión.")
        return False
    if os.path.isdir(BRAVE_PROFILE):
        shutil.rmtree(BRAVE_PROFILE, ignore_errors=True)
    os.makedirs(BRAVE_PROFILE, exist_ok=True)
    shutil.copy2(os.path.join(src_root, "Local State"), os.path.join(BRAVE_PROFILE, "Local State"))
    shutil.copytree(os.path.join(src_root, prof), os.path.join(BRAVE_PROFILE, "Default"),
                    ignore=lambda d, names: [n for n in names if n in SKIP], dirs_exist_ok=True)
    cfg = load_config()
    cfg["brave_redes"] = sorted(set(cfg.get("brave_redes") or []) | set(nets))
    save_config(cfg)
    return True


def connect_brave(nets: list[str]) -> None:
    """Sign in to these networks in Brave (its own profile); from then on the agents use Brave for them."""
    nets = [n for n in nets if n in SESSION_COOKIES] or ["tiktok"]
    if not brave_exe():
        print("No encontré Brave instalado en este PC.")
        return
    urls = {"tiktok": "https://www.tiktok.com/", "instagram": IG, "facebook": FB, "youtube": "https://studio.youtube.com/"}
    adopted = adopt_brave(nets)
    br = Browser(visible=True, net=nets[0])
    cfg = load_config()
    cfg["brave_redes"] = sorted(set(cfg.get("brave_redes") or []) | set(nets))
    save_config(cfg)
    ctx = br.context()
    for n in nets:
        try:
            br.page().goto(urls[n], wait_until="domcontentloaded", timeout=60_000)
        except Exception:
            pass
    br._mine = []                                # leave the tabs open for you
    print(f"""
Se abrió Brave (un perfil aparte, solo para los agentes) con: {", ".join(nets)}.
  Inicia sesión con la cuenta de Goldglitch (marca "recordar" si aparece). Tus contraseñas no pasan por este programa.
  No cierres esa ventana de Brave mientras los agentes trabajan; si la cierras, se vuelve a abrir sola.
""")
    if adopted:
        time.sleep(6)
        print("Revisa en esa ventana que TikTok aparezca con la cuenta de Goldglitch iniciada.")
    input("Cuando veas la sesión iniciada (si no, inicia sesión ahí), presiona Enter aquí... ")
    status = {net: any(c["name"] == name and dom in c["domain"] for c in ctx.cookies())
              for net, (dom, name) in SESSION_COOKIES.items() if net in nets}
    br.close()
    cfg = load_config()
    cfg.update({"connected": True, "sessions": {**(cfg.get("sessions") or {}), **status}})
    save_config(cfg)
    for net, ok in status.items():
        print(f"  {net:10s} {'conectado en Brave' if ok else 'SIN sesión (vuelve a intentarlo)'}")


def connect() -> None:
    """Visible browser with the three sites; you sign in yourself (passwords never pass through this program)."""
    br = Browser(visible=True)
    ctx = br.context()
    for url in (IG, FB, "https://www.tiktok.com/", "https://studio.youtube.com/"):
        try:
            ctx.new_page().goto(url, wait_until="domcontentloaded", timeout=60_000)
        except Exception:
            pass        # a slow site keeps loading in its tab; you can also reload it or type the address yourself
    for p in list(ctx.pages):
        if p.url in ("about:blank", "chrome://newtab/"):
            p.close()
    print("""
Se abrió un navegador con cuatro pestañas: Instagram, Facebook, TikTok y YouTube Studio.

  1) Inicia sesión en cada una con las cuentas de Goldglitch (marca "recordar" si aparece).
     Si alguna pestaña se queda en blanco, recárgala (F5) o escribe la dirección (tiktok.com) en esa pestaña.
     En TikTok usa "Iniciar sesión" arriba a la derecha. En YouTube inicia sesión con la cuenta de Google del canal
     de EGG y elige ese canal si te pregunta. Las sesiones que ya iniciaste se conservan.
  2) En Facebook, cambia a la PÁGINA de Goldglitch: foto de perfil (arriba a la derecha) > "Cambiar a ..." /
     "Ver todos los perfiles" > la página. Así las publicaciones salen como la página, no como tu perfil.
  3) Abre la página de Goldglitch en esa pestaña y copia su dirección (ej. https://www.facebook.com/goldglitch).
""")
    page_url = input("Pega aquí la dirección de la página de Facebook (o Enter si no usarás Facebook): ").strip()
    input("Cuando hayas iniciado sesión en las cuatro, presiona Enter aquí... ")
    status = br.signed_in()
    br.close()
    cfg = load_config()
    cfg.update({"connected": True, "facebook_page": page_url or None, "sessions": status, "at": time.strftime("%Y-%m-%d %H:%M")})
    save_config(cfg)
    for net, ok in status.items():
        print(f"  {net:10s} {'conectado' if ok else 'SIN sesión (vuelve a correr conectar_redes.bat)'}")
    print("\nListo. Prueba sin publicar con:  python goldglitch_social.py tick --ensayo")
