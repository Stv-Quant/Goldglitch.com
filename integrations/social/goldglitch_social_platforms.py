"""Publicación y comentarios en Instagram, Facebook y TikTok con sus APIs oficiales.

Instagram y Facebook: Graph API con el token de la página (permisos pages_manage_posts, pages_read_engagement,
pages_manage_engagement, instagram_basic, instagram_content_publish, instagram_manage_comments,
instagram_manage_insights). TikTok: Content Posting API (video.publish); hasta que TikTok audite la app, todo lo que
se sube queda privado (SELF_ONLY).
"""
from __future__ import annotations

import json
import os
import time
from typing import Any

import requests

GRAPH = "https://graph.facebook.com/" + os.environ.get("META_GRAPH_VERSION", "v22.0")
TT = "https://open.tiktokapis.com/v2"
HERE = os.path.dirname(os.path.abspath(__file__))
TT_TOKENS = os.path.join(HERE, "redes_tiktok_tokens.json")


class PlatformError(RuntimeError):
    pass


def _check(r: requests.Response) -> dict:
    try:
        j = r.json()
    except ValueError:
        raise PlatformError(f"HTTP {r.status_code}: {r.text[:300]}")
    err = j.get("error") if isinstance(j, dict) else None
    if isinstance(err, dict):
        raise PlatformError(f"{err.get('code')}: {err.get('message')}")
    if r.status_code >= 400:
        raise PlatformError(f"HTTP {r.status_code}: {json.dumps(j)[:300]}")
    return j


# ------------------------------------------------------------------ Meta (Facebook page + Instagram)
class Meta:
    def __init__(self, page_id: str, page_token: str, ig_user_id: str | None):
        self.page, self.token, self.ig = page_id, page_token, ig_user_id

    def _get(self, path: str, **params) -> dict:
        return _check(requests.get(f"{GRAPH}/{path}", params={**params, "access_token": self.token}, timeout=60))

    def _post(self, path: str, data: dict | None = None, files: dict | None = None) -> dict:
        return _check(requests.post(f"{GRAPH}/{path}", data={**(data or {}), "access_token": self.token}, files=files, timeout=300))

    # --- Instagram
    def ig_wait(self, container: str, tries: int = 60) -> None:
        for _ in range(tries):
            st = self._get(container, fields="status_code,status").get("status_code")
            if st == "FINISHED":
                return
            if st in ("ERROR", "EXPIRED"):
                raise PlatformError(f"Instagram no procesó el contenido ({st}).")
            time.sleep(5)
        raise PlatformError("Instagram tardó demasiado procesando el contenido.")

    def ig_publish(self, container: str) -> str:
        self.ig_wait(container)
        return self._post(f"{self.ig}/media_publish", {"creation_id": container})["id"]

    def ig_image(self, url: str, caption: str) -> str:
        c = self._post(f"{self.ig}/media", {"image_url": url, "caption": caption})["id"]
        return self.ig_publish(c)

    def ig_carousel(self, urls: list[str], caption: str) -> str:
        kids = [self._post(f"{self.ig}/media", {"image_url": u, "is_carousel_item": "true"})["id"] for u in urls[:20]]
        for k in kids:
            self.ig_wait(k)
        c = self._post(f"{self.ig}/media", {"media_type": "CAROUSEL", "children": ",".join(kids), "caption": caption})["id"]
        return self.ig_publish(c)

    def ig_story(self, url: str) -> str:
        c = self._post(f"{self.ig}/media", {"media_type": "STORIES", "image_url": url})["id"]
        return self.ig_publish(c)

    def ig_reel(self, path: str, caption: str) -> str:
        """Reel by resumable upload (the file goes straight to Meta, no public URL needed)."""
        c = self._post(f"{self.ig}/media", {"media_type": "REELS", "upload_type": "resumable", "caption": caption,
                                            "share_to_feed": "true"})
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            r = requests.post(c["uri"], data=f, timeout=600, headers={
                "Authorization": f"OAuth {self.token}", "offset": "0", "file_size": str(size)})
        _check(r)
        return self.ig_publish(c["id"])

    # --- Facebook page
    def fb_photos(self, paths: list[str], caption: str) -> str:
        if len(paths) == 1:
            with open(paths[0], "rb") as f:
                return self._post(f"{self.page}/photos", {"message": caption}, files={"source": f})["post_id"]
        ids = []
        for p in paths[:10]:
            with open(p, "rb") as f:
                ids.append(self._post(f"{self.page}/photos", {"published": "false"}, files={"source": f})["id"])
        data = {"message": caption}
        for i, pid in enumerate(ids):
            data[f"attached_media[{i}]"] = json.dumps({"media_fbid": pid})
        return self._post(f"{self.page}/feed", data)["id"]

    def fb_video(self, path: str, caption: str, title: str) -> str:
        with open(path, "rb") as f:
            return self._post(f"{self.page}/videos", {"description": caption, "title": title[:100]}, files={"source": f})["id"]

    # --- comments
    def ig_recent_comments(self, media_limit: int = 12) -> list[dict]:
        if not self.ig:
            return []
        me = self._get(self.ig, fields="username").get("username")
        out = []
        for m in self._get(f"{self.ig}/media", fields="id,caption,comments_count", limit=media_limit).get("data", []):
            if not m.get("comments_count"):
                continue
            for c in self._get(f"{m['id']}/comments", fields="id,text,username,timestamp,replies{username}", limit=50).get("data", []):
                if c.get("username") == me or any(r.get("username") == me for r in (c.get("replies") or {}).get("data", [])):
                    continue
                out.append({"net": "instagram", "id": c["id"], "text": c.get("text", ""), "user": c.get("username"),
                            "post": (m.get("caption") or "")[:200]})
        return out

    def fb_recent_comments(self, post_limit: int = 12) -> list[dict]:
        out = []
        for p in self._get(f"{self.page}/posts", fields="id,message", limit=post_limit).get("data", []):
            for c in self._get(f"{p['id']}/comments", fields="id,message,from,comments{from}", limit=50, filter="toplevel").get("data", []):
                frm = (c.get("from") or {}).get("id")
                if frm == self.page or any((r.get("from") or {}).get("id") == self.page for r in (c.get("comments") or {}).get("data", [])):
                    continue
                out.append({"net": "facebook", "id": c["id"], "text": c.get("message", ""), "user": (c.get("from") or {}).get("name"),
                            "post": (p.get("message") or "")[:200]})
        return out

    def reply(self, c: dict, text: str) -> None:
        if c["net"] == "instagram":
            self._post(f"{c['id']}/replies", {"message": text})
        else:
            self._post(f"{c['id']}/comments", {"message": text})

    def hide(self, c: dict) -> None:
        if c["net"] == "instagram":
            self._post(c["id"], {"hide": "true"})
        else:
            self._post(c["id"], {"is_hidden": "true"})

    # --- metrics
    def ig_insights(self, days: int = 7) -> list[dict]:
        if not self.ig:
            return []
        since = time.time() - days * 86400
        out = []
        for m in self._get(f"{self.ig}/media", fields="id,caption,media_type,timestamp,like_count,comments_count", limit=40).get("data", []):
            ts = time.mktime(time.strptime(m["timestamp"][:19], "%Y-%m-%dT%H:%M:%S"))
            if ts < since:
                continue
            row = {"net": "instagram", "type": m.get("media_type"), "caption": (m.get("caption") or "")[:120],
                   "likes": m.get("like_count"), "comments": m.get("comments_count")}
            try:
                ins = self._get(f"{m['id']}/insights", metric="reach,saved,shares").get("data", [])
                row.update({x["name"]: (x.get("values") or [{}])[0].get("value", x.get("total_value", {}).get("value")) for x in ins})
            except PlatformError:
                pass
            out.append(row)
        return out


# ------------------------------------------------------------------ TikTok
class TikTok:
    def __init__(self, client_key: str, client_secret: str, privacy: str = "SELF_ONLY"):
        self.key, self.secret, self.privacy = client_key, client_secret, privacy

    @staticmethod
    def auth_url(client_key: str, redirect: str, state: str) -> str:
        from urllib.parse import urlencode
        return "https://www.tiktok.com/v2/auth/authorize/?" + urlencode({
            "client_key": client_key, "scope": "user.info.basic,video.publish,video.upload", "response_type": "code",
            "redirect_uri": redirect, "state": state})

    def exchange(self, code: str, redirect: str) -> dict:
        r = requests.post(f"{TT}/oauth/token/", timeout=30, data={
            "client_key": self.key, "client_secret": self.secret, "code": code, "grant_type": "authorization_code",
            "redirect_uri": redirect})
        j = r.json()
        if "access_token" not in j:
            raise PlatformError(f"TikTok no entregó el token: {j}")
        self._save(j)
        return j

    def _save(self, j: dict) -> None:
        j = {**j, "obtained_at": int(time.time())}
        with open(TT_TOKENS, "w", encoding="utf-8") as f:
            json.dump(j, f)

    def token(self) -> str:
        try:
            with open(TT_TOKENS, encoding="utf-8") as f:
                t = json.load(f)
        except (OSError, ValueError):
            raise PlatformError("TikTok no está conectado: ejecuta  goldglitch_social.py tiktok-login")
        if time.time() > t["obtained_at"] + int(t.get("expires_in", 86400)) - 600:
            r = requests.post(f"{TT}/oauth/token/", timeout=30, data={
                "client_key": self.key, "client_secret": self.secret, "grant_type": "refresh_token",
                "refresh_token": t["refresh_token"]})
            j = r.json()
            if "access_token" not in j:
                raise PlatformError(f"TikTok no renovó el token (vuelve a conectar con tiktok-login): {j}")
            self._save(j)
            return j["access_token"]
        return t["access_token"]

    def _api(self, path: str, body: dict) -> dict:
        r = requests.post(f"{TT}{path}", json=body, timeout=60, headers={
            "Authorization": f"Bearer {self.token()}", "Content-Type": "application/json; charset=UTF-8"})
        j = r.json()
        err = j.get("error") or {}
        if err.get("code") not in (None, "ok"):
            raise PlatformError(f"TikTok {err.get('code')}: {err.get('message')}")
        return j.get("data") or {}

    def video(self, path: str, title: str) -> str:
        info = self._api("/post/publish/creator_info/query/", {})
        allowed = info.get("privacy_level_options") or ["SELF_ONLY"]
        privacy = self.privacy if self.privacy in allowed else ("SELF_ONLY" if "SELF_ONLY" in allowed else allowed[0])
        size = os.path.getsize(path)
        chunk = size if size <= 64 * 1024 * 1024 else 10 * 1024 * 1024
        n = max(1, size // chunk)
        init = self._api("/post/publish/video/init/", {
            "post_info": {"title": title[:2200], "privacy_level": privacy, "disable_comment": False,
                          "disable_duet": False, "disable_stitch": False, "is_aigc": False},
            "source_info": {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": chunk, "total_chunk_count": n}})
        with open(path, "rb") as f:
            for i in range(n):
                start = i * chunk
                end = size - 1 if i == n - 1 else start + chunk - 1
                f.seek(start)
                data = f.read(end - start + 1)
                r = requests.put(init["upload_url"], data=data, timeout=600, headers={
                    "Content-Type": "video/mp4", "Content-Length": str(len(data)), "Content-Range": f"bytes {start}-{end}/{size}"})
                if r.status_code >= 400:
                    raise PlatformError(f"TikTok rechazó la subida: HTTP {r.status_code} {r.text[:200]}")
        pid = init["publish_id"]
        for _ in range(60):
            st = self._api("/post/publish/status/fetch/", {"publish_id": pid}).get("status")
            if st in ("PUBLISH_COMPLETE", "SEND_TO_USER_INBOX"):
                return pid
            if st == "FAILED":
                raise PlatformError("TikTok no pudo publicar el video.")
            time.sleep(5)
        return pid
