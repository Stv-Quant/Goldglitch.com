import { ESPN_LEAGUE, espnCrest, teamKey } from "@/lib/crests";

const TTL_S = 7 * 86_400;

type EspnTeam = { team?: { color?: string; alternateColor?: string; displayName?: string; shortDisplayName?: string; name?: string; location?: string; nickname?: string; logos?: { href: string; rel?: string[] }[] } };

/**
 * Team crests for one competition: { teams: { <teamKey>: <crest url> } }. One league per request keeps each
 * Worker invocation small; responses live a week in the edge cache.
 */
export async function GET(request: Request) {
  const comp = new URL(request.url).searchParams.get("c") ?? "";
  const path = ESPN_LEAGUE[comp];
  if (!path) return Response.json({ teams: {}, colors: {} }, { headers: { "cache-control": `public, max-age=86400` } });

  const cache = (globalThis as unknown as { caches?: { default?: Cache } }).caches?.default;
  const key = new Request(new URL(`/api/crests?c=${encodeURIComponent(comp)}&v=2`, request.url).toString());
  if (cache) {
    const hit = await cache.match(key);
    if (hit) return hit;
  }

  const teams: Record<string, string> = {};
  const colors: Record<string, string> = {};
  try {
    const r = await fetch(`https://site.api.espn.com/apis/site/v2/sports/${path}/teams?limit=500`, { headers: { accept: "application/json" } });
    const d = (await r.json()) as { sports?: { leagues?: { teams?: EspnTeam[] }[] }[] };
    for (const { team: t } of d.sports?.[0]?.leagues?.[0]?.teams ?? []) {
      if (!t) continue;
      const logo = espnCrest((t.logos?.find((l) => l.rel?.includes("dark")) ?? t.logos?.[0])?.href);
      if (!logo) continue;
      const color = brandColor(t.color, t.alternateColor);
      for (const n of [t.displayName, t.shortDisplayName, t.name, t.location, t.nickname]) {
        const k = n ? teamKey(n) : "";
        if (k && !teams[k]) { teams[k] = logo; if (color) colors[k] = color; }
      }
    }
  } catch { /* monograms on the client */ }

  const res = Response.json({ teams, colors }, { headers: { "cache-control": `public, max-age=86400, s-maxage=${TTL_S}` } });
  if (cache && Object.keys(teams).length) await cache.put(key, res.clone());
  return res;
}

/** Team colour usable on a near-black page: the primary unless it is too dark or too grey, then the alternate. */
function brandColor(primary?: string, alt?: string): string | undefined {
  const ok = (h?: string) => {
    if (!h || !/^[0-9a-f]{6}$/i.test(h)) return false;
    const [r, g, b] = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
    const lum = 0.2126 * r + 0.7152 * g + 0.0722 * b, sat = Math.max(r, g, b) - Math.min(r, g, b);
    return lum > 45 && (sat > 40 || lum > 200);
  };
  const c = ok(primary) ? primary : ok(alt) ? alt : undefined;
  return c ? `#${c.toLowerCase()}` : undefined;
}
