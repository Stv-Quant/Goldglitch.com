import { BOT, SESSION_SOURCE_COOKIE, colombiaDay, countryOf, deviceOf, heatmapAllowed, normPath } from "@/lib/analytics";
import { getDB } from "@/lib/env";

type Ev =
  | { k: "pv"; p: string }
  | { k: "deep" }
  | { k: "leave"; p: string; ms: number; sc: number }
  | { k: "click"; p: string; x: number; y: number; t?: string };

/**
 * Engagement events from <Attribution/> in small batches: page views, second page of a session (not a bounce),
 * time on page + scroll depth when leaving, and clicks for the heatmap. Aggregated on write; nothing personal stored.
 */
export async function POST(request: Request) {
  const ok = new Response(null, { status: 204 });
  if (BOT.test(request.headers.get("user-agent") ?? "")) return ok;
  const body = (await request.json().catch(() => null)) as { w?: number; ev?: Ev[] } | null;
  const evs = Array.isArray(body?.ev) ? body!.ev.slice(0, 40) : [];
  if (!evs.length) return ok;
  const day = colombiaDay(), country = countryOf(request), device = deviceOf(request, body?.w);
  const db = await getDB();
  const stmts = [];
  for (const e of evs) {
    if (e.k === "pv") {
      stmts.push(db.prepare(
        `INSERT INTO pageviews_daily (day, path, country, device, views) VALUES (?1, ?2, ?3, ?4, 1)
         ON CONFLICT(day, path, country, device) DO UPDATE SET views = views + 1`).bind(day, normPath(e.p), country, device));
    } else if (e.k === "deep") {
      const jar = request.headers.get("cookie") ?? "";
      const m = jar.match(new RegExp(`${SESSION_SOURCE_COOKIE}=([^;]+)`));
      const [d, src, dev] = decodeURIComponent(m?.[1] ?? "").split("|");
      if (d && src && dev) stmts.push(db.prepare(
        `UPDATE visits_geo_daily SET single_page = MAX(single_page - 1, 0)
          WHERE day = ?1 AND country = ?2 AND source = ?3 AND device = ?4`).bind(d, country, src, dev));
    } else if (e.k === "leave") {
      const ms = Math.max(0, Math.min(Number(e.ms) || 0, 30 * 60_000));
      const path = normPath(e.p);
      if (Number(e.sc) < 0) {        // same view reported again: only the extra visible time
        stmts.push(db.prepare(`UPDATE pageviews_daily SET engaged_ms = engaged_ms + ?5 WHERE day = ?1 AND path = ?2 AND country = ?3 AND device = ?4`)
          .bind(day, path, country, device, ms));
        continue;
      }
      const sc = Math.max(0, Math.min(Math.round(Number(e.sc) || 0), 100));
      stmts.push(db.prepare(
        `INSERT INTO pageviews_daily (day, path, country, device, exits, engaged_ms, scroll_sum) VALUES (?1, ?2, ?3, ?4, 1, ?5, ?6)
         ON CONFLICT(day, path, country, device) DO UPDATE SET exits = exits + 1, engaged_ms = engaged_ms + ?5, scroll_sum = scroll_sum + ?6`)
        .bind(day, path, country, device, ms, sc));
      if (heatmapAllowed(path)) stmts.push(db.prepare(
        `INSERT INTO heat_scroll (day, path, device, depth, n) VALUES (?1, ?2, ?3, ?4, 1)
         ON CONFLICT(day, path, device, depth) DO UPDATE SET n = n + 1`).bind(day, path, device, Math.floor(sc / 10)));
    } else if (e.k === "click") {
      const path = normPath(e.p);
      if (!heatmapAllowed(path)) continue;
      const gx = Math.max(0, Math.min(Math.floor(Number(e.x) * 50), 49)), gy = Math.max(0, Math.min(Math.floor(Number(e.y) / 40), 500));
      if (!Number.isFinite(gx) || !Number.isFinite(gy)) continue;
      stmts.push(db.prepare(
        `INSERT INTO heat_clicks (day, path, device, gx, gy, n) VALUES (?1, ?2, ?3, ?4, ?5, 1)
         ON CONFLICT(day, path, device, gx, gy) DO UPDATE SET n = n + 1`).bind(day, path, device, gx, gy));
      const t = String(e.t ?? "").replace(/\s+/g, " ").trim().slice(0, 60);
      if (t) stmts.push(db.prepare(
        `INSERT INTO heat_targets (day, path, target, n) VALUES (?1, ?2, ?3, 1)
         ON CONFLICT(day, path, target) DO UPDATE SET n = n + 1`).bind(day, path, t));
    }
  }
  if (stmts.length) await db.batch(stmts);
  return ok;
}
