"use client";

import { useEffect } from "react";

/** One tiny beacon per browsing session: where the visit came from (no third-party analytics, no personal data). */
export function Attribution() {
  useEffect(() => {
    try {
      if (document.cookie.includes("gg_v=")) return;
      const q = new URLSearchParams(window.location.search);
      const body = JSON.stringify({
        ref: q.get("ref"), utm: q.get("utm_source"), referrer: document.referrer, path: window.location.pathname,
      });
      if (!navigator.sendBeacon?.("/api/t", new Blob([body], { type: "application/json" }))) {
        fetch("/api/t", { method: "POST", body, headers: { "content-type": "application/json" }, keepalive: true }).catch(() => {});
      }
    } catch {
      /* measurement must never break the page */
    }
  }, []);
  return null;
}
