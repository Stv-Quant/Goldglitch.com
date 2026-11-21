/** Shared helpers for first-party analytics (no third parties, no personal data). */

export const BOT = /bot|crawl|spider|slurp|preview|facebookexternalhit|whatsapp|telegram|headless|lighthouse|pingdom|uptime/i;
export const SESSION_SOURCE_COOKIE = "gg_vs";   // channel of the current 30-min session (for bounce accounting)

export function colombiaDay(ms = Date.now()): string {
  return new Date(ms - 5 * 3600_000).toISOString().slice(0, 10);
}

/** Visitor country from Cloudflare (header or request.cf); "XX" when unknown. */
export function countryOf(request: Request): string {
  const cf = (request as unknown as { cf?: { country?: string } }).cf;
  const c = (request.headers.get("cf-ipcountry") || cf?.country || "XX").toUpperCase();
  return /^[A-Z]{2}$/.test(c) && c !== "T1" ? c : "XX";
}

/** mobile | tablet | desktop, from the viewport width the page reports, else the user agent. */
export function deviceOf(request: Request, width?: unknown): "mobile" | "tablet" | "desktop" {
  const w = Number(width);
  if (Number.isFinite(w) && w > 0) return w < 768 ? "mobile" : w < 1100 ? "tablet" : "desktop";
  const ua = request.headers.get("user-agent") ?? "";
  if (/ipad|tablet/i.test(ua)) return "tablet";
  return /mobi|android|iphone/i.test(ua) ? "mobile" : "desktop";
}

/** /partido/8f3a… → /partido/:id ; keeps paths short and free of identifiers. */
export function normPath(p: unknown): string {
  const path = String(p ?? "/").split(/[?#]/)[0] || "/";
  return path
    .split("/")
    .map((s) => (/^[0-9a-f-]{8,}$/i.test(s) || /\d{3,}/.test(s) ? ":id" : s.replace(/[^\w.-]/g, "").slice(0, 40)))
    .join("/")
    .slice(0, 80) || "/";
}

/** Public pages get heatmaps; private areas (app, admin, sign-in) only get page counts. */
export function heatmapAllowed(path: string): boolean {
  return !/^\/(app|admin|acceso|api|i|m)(\/|$)/.test(path);
}
