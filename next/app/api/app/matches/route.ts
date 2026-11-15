import { getViewer } from "@/lib/auth";
import { compactList, openCount } from "@/lib/appList";
import { bogotaDay } from "@/lib/fixtures";

export const dynamic = "force-dynamic";

const WINDOW_MS = 21 * 86_400_000;
const DAYS = ["hoy", "manana", "semana", "todo"] as const;
type Day = (typeof DAYS)[number];

/**
 * Match list for the app home. The JSON comes straight from D1 (see compactList): the Worker only concatenates
 * strings, so the request stays far below the free plan's CPU limit however many matches are published.
 */
export async function GET(req: Request) {
  const viewer = await getViewer().catch(() => null);
  if (!viewer) return Response.json({ error: "auth" }, { status: 401 });
  const tier = viewer.tier;
  const q = new URL(req.url).searchParams.get("dia");
  const now = Date.now();
  const t0 = bogotaDay(now), t1 = bogotaDay(now + 86_400_000);
  const range: Record<Day, [number, number]> = {
    hoy: [t0.start, t0.end],
    manana: [t1.start, t1.end],
    semana: [now - 3 * 3_600_000, now + 7 * 86_400_000],
    todo: [now - 3 * 3_600_000, now + WINDOW_MS],
  };
  let day: Day = DAYS.includes(q as Day) ? (q as Day) : "hoy";
  // Default: today while something is still to be played; otherwise the next 7 days.
  if (!q && (await openCount(tier, ...range.hoy)) === 0) day = "semana";
  const list = await compactList(tier, ...range[day]);
  return new Response(`{"day":"${day}","now":${now},"tier":"${tier}","matches":${list}}`, {
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "private, no-store" },
  });
}
