import { espnCrest, teamKey } from "@/lib/crests";

const TTL_S = 30 * 86_400;
/** Our sport ids → ESPN search `sport` values. */
const ESPN_SPORT: Record<string, string[]> = {
  football: ["soccer", "football"], baseball: ["baseball"], basketball: ["basketball"], hockey: ["hockey"],
};

type Hit = { displayName?: string; image?: { default?: string } | string; sport?: string };

/**
 * Fallback crest for a team ESPN's league lists don't cover: ESPN's team search by name, accepted only when the
 * sport and the name match. { logo } or {}. Hits cached 30 days at the edge, misses 1 hour. (E-sports and anything
 * still missing are tried from the browser against TheSportsDB, which rate-limits Cloudflare's shared IPs.)
 */
export async function GET(request: Request) {
  const u = new URL(request.url);
  const name = (u.searchParams.get("n") ?? "").trim().slice(0, 80);
  const sport = u.searchParams.get("s") ?? "football";
  const sports = ESPN_SPORT[sport];
  if (name.length < 2 || !sports) return Response.json({}, { headers: { "cache-control": "public, max-age=86400" } });

  const cache = (globalThis as unknown as { caches?: { default?: Cache } }).caches?.default;
  const key = new Request(new URL(`/api/crest?n=${encodeURIComponent(teamKey(name))}&s=${sport}&v=5`, request.url).toString());
  if (cache) {
    const hit = await cache.match(key);
    if (hit) return hit;
  }

  let out: { logo?: string } = {};
  try {
    const r = await fetch(`https://site.web.api.espn.com/apis/search/v2?query=${encodeURIComponent(name)}&limit=8&type=team`, {
      headers: { accept: "application/json", "user-agent": "Mozilla/5.0 (compatible; Goldglitch/1.0)" },
    });
    if (!r.ok) throw new Error(String(r.status));
    const d = (await r.json()) as { results?: { type?: string; contents?: Hit[] }[] };
    const teams = (d.results ?? []).filter((x) => x.type === "team").flatMap((x) => x.contents ?? [])
      .filter((t) => sports.includes(t.sport ?? ""));
    const want = teamKey(name);
    const img = (t: Hit) => (typeof t.image === "string" ? t.image : t.image?.default);
    const best = teams.find((t) => teamKey(t.displayName ?? "") === want)
      ?? teams.find((t) => { const k = teamKey(t.displayName ?? ""); return k.length >= 4 && (k.includes(want) || want.includes(k)); });
    const logo = best ? espnCrest(img(best)) : undefined;
    if (logo) out = { logo };
  } catch { /* the browser tries TheSportsDB */ }

  const ttl = out.logo ? TTL_S : 3600;
  const res = Response.json(out, { headers: { "cache-control": `public, max-age=${Math.min(ttl, 86400)}, s-maxage=${ttl}` } });
  if (cache) await cache.put(key, res.clone());
  return res;
}
