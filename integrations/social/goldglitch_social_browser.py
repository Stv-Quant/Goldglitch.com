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


def load_config() -> dict:
    try:
        with open(CONFIG, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_config(cfg: dict) -> None:
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=1)


def profile_ready() -> bool:
    return os.path.isdir(PROFILE) and bool(load_config().get("connected"))


class Browser:
    """One persistent browser for the whole tick (opened on first use, closed at the end)."""

    def __init__(self, visible: bool = False, rehearsal: bool = False):
        self.visible, self.rehearsal = visible or rehearsal, rehearsal
        self._pw = self._ctx = None

    # --- lifecycle
    def context(self):
        if self._ctx:
            return self._ctx
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
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
        return pg

    def close(self) -> None:
        try:
            if self._ctx:
                self._ctx.close()
        finally:
            if self._pw:
                self._pw.stop()
            self._ctx = self._pw = None

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
