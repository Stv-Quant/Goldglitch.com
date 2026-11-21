import { colombiaDay } from "./analytics";
import { getDB } from "./env";

const DAY = 86_400_000;

export type Row = Record<string, string | number | null>;

/**
 * Everything the growth team and the admin panel need, from first-party tables:
 * country, device and source × country, bounce, pages (views, engaged time, scroll), CTAs clicked,
 * signups/buyers by country and device, and daily series by country.
 */
export async function analyticsReport(days = 30) {
  const db = await getDB();
  const since = colombiaDay(Date.now() - days * DAY), sinceMs = Date.now() - days * DAY;
  const q = (sql: string, ...b: unknown[]) => db.prepare(sql).bind(...b);
  const [countries, devices, srcCountry, pages, ctas, signupsC, buyersC, signupsD, daily, scroll] = await db.batch([
    q(`SELECT country, SUM(visits) visits, SUM(single_page) single FROM visits_geo_daily WHERE day >= ? GROUP BY country ORDER BY visits DESC LIMIT 40`, since),
    q(`SELECT device, SUM(visits) visits, SUM(single_page) single FROM visits_geo_daily WHERE day >= ? GROUP BY device ORDER BY visits DESC`, since),
    q(`SELECT source, country, SUM(visits) visits, SUM(single_page) single FROM visits_geo_daily WHERE day >= ? GROUP BY source, country ORDER BY visits DESC LIMIT 60`, since),
    q(`SELECT path, SUM(views) views, SUM(exits) exits, SUM(engaged_ms) ms, SUM(scroll_sum) sc FROM pageviews_daily WHERE day >= ? GROUP BY path ORDER BY views DESC LIMIT 30`, since),
    q(`SELECT path, target, SUM(n) n FROM heat_targets WHERE day >= ? GROUP BY path, target ORDER BY n DESC LIMIT 40`, since),
    q(`SELECT COALESCE(signup_country, 'XX') country, COUNT(*) n FROM users WHERE created_at >= ? GROUP BY 1 ORDER BY n DESC`, sinceMs),
    q(`SELECT COALESCE(u.signup_country, 'XX') country, COUNT(DISTINCT p.user_id) buyers, SUM(p.amount_in_cents) / 100 revenueCOP
         FROM payments p JOIN users u ON u.id = p.user_id WHERE p.status = 'APPROVED' AND COALESCE(p.note, '') NOT LIKE 'Prueba%' AND p.updated_at >= ? GROUP BY 1`, sinceMs),
    q(`SELECT COALESCE(signup_device, 'desconocido') device, COUNT(*) n FROM users WHERE created_at >= ? GROUP BY 1`, sinceMs),
    q(`SELECT day, country, SUM(visits) visits FROM visits_geo_daily WHERE day >= ? GROUP BY day, country ORDER BY day`, colombiaDay(Date.now() - 14 * DAY)),
    q(`SELECT path, depth, SUM(n) n FROM heat_scroll WHERE day >= ? GROUP BY path, depth`, since),
  ]);
  const r = (x: { results: unknown[] }) => x.results as Row[];
  const pct = (a: number, b: number) => (b ? Math.round((a / b) * 1000) / 10 : null);
  const sC = new Map(r(signupsC).map((x) => [x.country, Number(x.n)]));
  const bC = new Map(r(buyersC).map((x) => [x.country, x]));
  const reach: Record<string, number[]> = {};
  for (const s of r(scroll)) (reach[String(s.path)] ??= Array(11).fill(0))[Number(s.depth)] += Number(s.n);
  return {
    days,
    countries: r(countries).map((c) => {
      const v = Number(c.visits), s = sC.get(c.country) ?? 0, b = bC.get(c.country);
      return { country: c.country, visits: v, bouncePct: pct(Number(c.single), v), signups: s, visitToSignupPct: pct(s, v),
               buyers: Number(b?.buyers ?? 0), revenueCOP: Number(b?.revenueCOP ?? 0) };
    }),
    signupCountriesWithoutVisits: r(signupsC).filter((s) => !r(countries).some((c) => c.country === s.country)),
    devices: r(devices).map((d) => ({ device: d.device, visits: Number(d.visits), bouncePct: pct(Number(d.single), Number(d.visits)),
                                     signups: Number(r(signupsD).find((s) => s.device === d.device)?.n ?? 0) })),
    sourceByCountry: r(srcCountry).map((x) => ({ source: x.source, country: x.country, visits: Number(x.visits), bouncePct: pct(Number(x.single), Number(x.visits)) })),
    pages: r(pages).map((p) => {
      const views = Number(p.views), exits = Number(p.exits);
      const rr = reach[String(p.path)];
      const total = rr ? rr.reduce((a, b) => a + b, 0) : 0;
      const reached = (band: number) => (rr && total ? Math.round((rr.slice(band).reduce((a, b) => a + b, 0) / total) * 100) : null);
      return { path: p.path, views, avgEngagedSec: views ? Math.round(Number(p.ms) / views / 100) / 10 : null,
               avgScrollPct: exits ? Math.round(Number(p.sc) / exits) : null, reach50Pct: reached(5), reach90Pct: reached(9) };
    }),
    ctas: r(ctas).map((c) => ({ path: c.path, target: c.target, clicks: Number(c.n) })),
    dailyByCountry: r(daily),
    notes: "Datos propios: país por Cloudflare, dispositivo por ancho de pantalla, rebote = sesión de una sola página, "
         + "tiempo = tiempo con la página visible. Sin datos personales.",
  };
}

export async function heatmap(path: string, device: string, days: number) {
  const db = await getDB();
  const since = colombiaDay(Date.now() - days * DAY);
  const [cells, scroll, targets] = await db.batch([
    db.prepare(`SELECT gx, gy, SUM(n) n FROM heat_clicks WHERE path = ? AND device = ? AND day >= ? GROUP BY gx, gy`).bind(path, device, since),
    db.prepare(`SELECT depth, SUM(n) n FROM heat_scroll WHERE path = ? AND device = ? AND day >= ? GROUP BY depth ORDER BY depth`).bind(path, device, since),
    db.prepare(`SELECT target, SUM(n) n FROM heat_targets WHERE path = ? AND day >= ? GROUP BY target ORDER BY n DESC LIMIT 15`).bind(path, since),
  ]);
  return { cells: cells.results as Row[], scroll: scroll.results as Row[], targets: targets.results as Row[] };
}

export async function heatmapPaths(days: number): Promise<string[]> {
  const db = await getDB();
  const rows = await db.prepare(`SELECT path, SUM(n) n FROM heat_clicks WHERE day >= ? GROUP BY path ORDER BY n DESC LIMIT 30`)
    .bind(colombiaDay(Date.now() - days * DAY)).all();
  return (rows.results as Row[]).map((x) => String(x.path));
}
