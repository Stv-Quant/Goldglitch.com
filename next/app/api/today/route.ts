import { getTodayFixtures } from "@/lib/fixtures";

const TTL_S = 600;

/** Today's fixtures for the landing strip. Edge-cached 10 min so the public feeds are hit at most ~6×/h per colo. */
export async function GET(request: Request) {
  const cache = (globalThis as unknown as { caches?: { default?: Cache } }).caches?.default;
  const key = new Request(new URL("/api/today?v=2", request.url).toString());
  if (cache) {
    const hit = await cache.match(key);
    if (hit) return hit;
  }
  const fixtures = await getTodayFixtures();
  const res = Response.json(
    { fixtures, generatedAt: Date.now() },
    { headers: { "cache-control": `public, max-age=60, s-maxage=${TTL_S}` } },
  );
  if (cache && fixtures.length) await cache.put(key, res.clone());
  return res;
}
