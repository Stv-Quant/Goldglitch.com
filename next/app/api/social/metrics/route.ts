import { getDB } from "@/lib/env";
import { readSigned } from "@/lib/signed";
import { analyticsReport } from "@/lib/analyticsReport";

export const dynamic = "force-dynamic";

const DAY = 86_400_000;
const REAL = "status = 'APPROVED' AND COALESCE(note, '') NOT LIKE 'Prueba%'";   // test payments never count

/**
 * Organic growth funnel for the growth committee (signed, PC only):
 * visits by source → accounts by first-touch source → paying accounts and revenue, for 1/7/30 days,
 * a 14-day daily series and the performance of each tagged link (?ref=).
 */
export async function POST(req: Request) {
  const raw = await readSigned(req, 10_000);
  if (raw instanceof Response) return raw;
  const db = await getDB();
  const now = Date.now();
  const co = (ms: number) => new Date(ms - 5 * 3600_000).toISOString().slice(0, 10);   // Colombia day
  const win = { d1: 1, d7: 7, d30: 30 } as const;

  const funnel = async (days: number) => {
    const since = now - days * DAY;
    const [visits, signups, paid] = await db.batch([
      db.prepare(
        `SELECT CASE WHEN source LIKE 'ref:%' THEN
                  CASE substr(source, 5, 2) WHEN 'ig' THEN 'instagram' WHEN 'fb' THEN 'facebook' WHEN 'tt' THEN 'tiktok' ELSE 'campana' END
                ELSE source END AS source, SUM(visits) AS n
           FROM traffic_daily WHERE day >= ? GROUP BY 1 ORDER BY n DESC`,
      ).bind(co(since)),
      db.prepare(
        "SELECT COALESCE(signup_source, 'antes_de_medir') AS source, COUNT(*) AS n FROM users WHERE created_at >= ? GROUP BY 1 ORDER BY n DESC",
      ).bind(since),
      db.prepare(
        `SELECT COALESCE(u.signup_source, 'antes_de_medir') AS source, COUNT(DISTINCT p.user_id) AS buyers,
                SUM(p.amount_in_cents) AS cents, COUNT(*) AS payments
           FROM payments p JOIN users u ON u.id = p.user_id
          WHERE p.status = 'APPROVED' AND COALESCE(p.note, '') NOT LIKE 'Prueba%' AND p.updated_at >= ? GROUP BY 1 ORDER BY cents DESC`,
      ).bind(since),
    ]);
    const v = visits.results as { source: string; n: number }[];
    const s = signups.results as { source: string; n: number }[];
    const p = paid.results as { source: string; buyers: number; cents: number; payments: number }[];
    const tv = v.reduce((a, r) => a + r.n, 0), ts = s.reduce((a, r) => a + r.n, 0), tb = p.reduce((a, r) => a + r.buyers, 0);
    const pct = (a: number, b: number) => (b ? Math.round((a / b) * 1000) / 10 : null);
    const sources = [...new Set([...v, ...s, ...p].map((r) => r.source))].map((src) => {
      const vi = v.find((r) => r.source === src)?.n ?? 0, si = s.find((r) => r.source === src)?.n ?? 0;
      const pi = p.find((r) => r.source === src);
      return { source: src, visits: vi, signups: si, buyers: pi?.buyers ?? 0, revenueCOP: Math.round((pi?.cents ?? 0) / 100),
               visitToSignupPct: pct(si, vi), signupToPaidPct: pct(pi?.buyers ?? 0, si) };
    });
    return {
      visits: tv, signups: ts, buyers: tb, revenueCOP: Math.round(p.reduce((a, r) => a + r.cents, 0) / 100),
      visitToSignupPct: pct(ts, tv), signupToPaidPct: pct(tb, ts), visitToPaidPct: pct(tb, tv), sources,
    };
  };

  const since14 = now - 14 * DAY;
  const [series, refs, subs, users, landings] = await db.batch([
    db.prepare(
      `WITH d AS (SELECT day, SUM(visits) v FROM traffic_daily WHERE day >= ?1 GROUP BY day),
            s AS (SELECT date((created_at - 18000000) / 1000, 'unixepoch') day, COUNT(*) n FROM users WHERE created_at >= ?2 GROUP BY 1),
            p AS (SELECT date((updated_at - 18000000) / 1000, 'unixepoch') day, COUNT(*) n, SUM(amount_in_cents) c FROM payments WHERE ${REAL} AND updated_at >= ?2 GROUP BY 1)
       SELECT d.day, d.v AS visits, COALESCE(s.n, 0) AS signups, COALESCE(p.n, 0) AS payments, COALESCE(p.c, 0) / 100 AS revenueCOP
         FROM d LEFT JOIN s ON s.day = d.day LEFT JOIN p ON p.day = d.day ORDER BY d.day`,
    ).bind(co(since14), since14),
    db.prepare(
      `SELECT substr(t.source, 5) AS ref, SUM(t.visits) AS visits,
              (SELECT COUNT(*) FROM users u WHERE u.signup_ref = substr(t.source, 5)) AS signups,
              (SELECT COUNT(DISTINCT p.user_id) FROM payments p JOIN users u ON u.id = p.user_id
                WHERE u.signup_ref = substr(t.source, 5) AND p.status = 'APPROVED' AND COALESCE(p.note, '') NOT LIKE 'Prueba%') AS buyers
         FROM traffic_daily t WHERE t.source LIKE 'ref:%' AND t.day >= ? GROUP BY t.source ORDER BY visits DESC LIMIT 30`,
    ).bind(co(now - 30 * DAY)),
    db.prepare("SELECT plan, COUNT(*) AS n FROM subscriptions WHERE current_period_end > ? GROUP BY plan").bind(now),
    db.prepare("SELECT COUNT(*) AS n FROM users"),
    db.prepare("SELECT landing, SUM(visits) AS visits FROM traffic_daily WHERE day >= ? GROUP BY landing ORDER BY visits DESC LIMIT 12").bind(co(now - 7 * DAY)),
  ]);

  return Response.json({
    generatedAt: now,
    measuringSince: (await db.prepare("SELECT MIN(day) AS d FROM traffic_daily").first<{ d: string | null }>())?.d ?? null,
    totals: { accounts: (users.results[0] as { n: number }).n, activeSubscriptions: subs.results },
    funnel: { d1: await funnel(win.d1), d7: await funnel(win.d7), d30: await funnel(win.d30) },
    daily14: series.results,
    refs30: refs.results,
    landings7: landings.results,
    analytics30: await analyticsReport(30).catch(() => null),
    notes: "Visitas = sesiones de navegación (una cada 30 min). Origen = primer contacto. Pagos de prueba excluidos.",
  });
}
