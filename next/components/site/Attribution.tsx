"use client";

import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";

/**
 * First-party measurement (no third-party analytics, no personal data):
 * - one visit beacon per 30-min session (source, country, device);
 * - page views, time actually visible on each page and max scroll depth;
 * - clicks on public pages for the heatmap (position + label of the button/link, never typed text).
 * Disabled inside the admin heatmap viewer (iframe) and with ?gg_nt=1.
 */
const off = () => {
  try {
    return window.top !== window.self || new URLSearchParams(location.search).has("gg_nt");
  } catch {
    return true;
  }
};
const width = () => window.innerWidth || document.documentElement.clientWidth || 0;
let queue: unknown[] = [];

function flush(useBeacon = false) {
  if (!queue.length) return;
  const body = JSON.stringify({ w: width(), ev: queue.splice(0, 40) });
  try {
    if (useBeacon && navigator.sendBeacon?.("/api/t/e", new Blob([body], { type: "application/json" }))) return;
    fetch("/api/t/e", { method: "POST", body, headers: { "content-type": "application/json" }, keepalive: true }).catch(() => {});
  } catch {
    /* never break the page */
  }
}

function label(el: Element | null): string {
  const t = el?.closest("[data-track],a,button,[role=button],summary,input[type=submit]");
  if (!t) return "";
  const dt = t.getAttribute("data-track");
  if (dt) return dt;
  const tag = t.tagName.toLowerCase();
  const text = (t.getAttribute("aria-label") || (tag === "input" ? (t as HTMLInputElement).value : t.textContent) || "").trim();
  const href = tag === "a" ? (t.getAttribute("href") || "").split("?")[0].slice(0, 40) : "";
  return `${tag === "a" ? "link" : "boton"}: ${text.slice(0, 40)}${href ? ` → ${href}` : ""}`;
}

export function Attribution() {
  const path = usePathname();
  const page = useRef({ path: "", shown: 0, visibleSince: 0, maxScroll: 0, reported: false });

  // visit beacon (once per session)
  useEffect(() => {
    if (off()) return;
    try {
      if (document.cookie.includes("gg_v=")) return;
      const q = new URLSearchParams(window.location.search);
      const body = JSON.stringify({ ref: q.get("ref"), utm: q.get("utm_source"), referrer: document.referrer, path: location.pathname, w: width() });
      sessionStorage.setItem("gg_pages", "0");
      if (!navigator.sendBeacon?.("/api/t", new Blob([body], { type: "application/json" }))) {
        fetch("/api/t", { method: "POST", body, headers: { "content-type": "application/json" }, keepalive: true }).catch(() => {});
      }
    } catch {
      /* measurement must never break the page */
    }
  }, []);

  // page views + engagement per route
  useEffect(() => {
    if (off() || !path) return;
    const st = page.current;
    const leave = () => {
      if (!st.path) return;
      const ms = st.shown + (st.visibleSince ? Date.now() - st.visibleSince : 0);
      // the first report of a view carries the exit and scroll; later ones (tab hidden again) only add time
      queue.push({ k: "leave", p: st.path, ms, sc: st.reported ? -1 : st.maxScroll });
      st.path = "";
      st.reported = true;
    };
    leave();
    flush();
    Object.assign(st, { path, shown: 0, visibleSince: document.visibilityState === "visible" ? Date.now() : 0, maxScroll: 0, reported: false });
    queue.push({ k: "pv", p: path });
    try {
      const n = Number(sessionStorage.getItem("gg_pages") || "0") + 1;
      sessionStorage.setItem("gg_pages", String(n));
      if (n === 2) queue.push({ k: "deep" });
    } catch {
      /* ignore */
    }
    const onScroll = () => {
      const h = document.documentElement.scrollHeight - window.innerHeight;
      const pct = h > 0 ? Math.round(((window.scrollY + 0) / h) * 100) : 100;
      if (pct > st.maxScroll) st.maxScroll = Math.min(100, pct);
    };
    onScroll();
    const onVis = () => {
      if (document.visibilityState === "hidden") {
        if (st.visibleSince) st.shown += Date.now() - st.visibleSince;
        st.visibleSince = 0;
        const keep = { ...st };
        leave();
        flush(true);
        Object.assign(st, { path: keep.path, shown: 0, maxScroll: keep.maxScroll });   // resume counting if they come back
      } else if (!st.visibleSince) {
        st.visibleSince = Date.now();
      }
    };
    const onClick = (e: MouseEvent) => {
      const docW = document.documentElement.scrollWidth || width();
      queue.push({ k: "click", p: path, x: e.pageX / Math.max(docW, 1), y: e.pageY, t: label(e.target as Element) });
      if (queue.length >= 20) flush();
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    document.addEventListener("visibilitychange", onVis);
    document.addEventListener("click", onClick, { capture: true, passive: true });
    const timer = setInterval(() => flush(), 15_000);
    return () => {
      window.removeEventListener("scroll", onScroll);
      document.removeEventListener("visibilitychange", onVis);
      document.removeEventListener("click", onClick, { capture: true });
      clearInterval(timer);
      if (st.visibleSince) st.shown += Date.now() - st.visibleSince;
      st.visibleSince = 0;
    };
  }, [path]);

  return null;
}
