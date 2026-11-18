import { getTodayFixtures } from "@/lib/fixtures";
import { landingRecord, landingSample } from "@/lib/landing";

const TTL_S = 600;

/**
 * Today's fixtures (with crests) for the banner and the landing, plus one open 1X2 sample and the public record headline.
 * Edge-cached 10 min so the public feeds and D1 are hit at most ~6×/h per colo.
 */
export async function GET(request: Request) {
  const cache = (globalThis as unknown as { caches?: { default?: Cache } }).caches?.default;
  const key = new Request(new URL("/api/today?v=3", request.url).toString());
  if (cache) {
    const hit = await cache.match(key);
    if (hit) return hit;
  }
  const fixtures = await getTodayFixtures();
  const [sample, record] = await Promise.all([landingSample(fixtures), landingRecord()]);
  const res = Response.json(
    { fixtures, sample, record, generatedAt: Date.now() },
    { headers: { "cache-control": `public, max-age=60, s-maxage=${TTL_S}` } },
  );
  if (cache && fixtures.length) await cache.put(key, res.clone());
  return res;
}
