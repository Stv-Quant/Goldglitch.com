import { brandColor, teamKey } from "@/lib/crests";

const TTL_S = 30 * 86_400;
/** Our sport ids → TheSportsDB's strSport. */
const TSDB_SPORT: Record<string, string[]> = {
  football: ["Soccer", "American Football"], baseball: ["Baseball"], basketball: ["Basketball"], hockey: ["Ice Hockey"], esports: ["ESports"],
};

type TsdbTeam = { strTeam?: string; strTeamAlternate?: string; strTeamShort?: string; strSport?: string; strBadge?: string; strColour1?: string; strColour2?: string };

/**
 * Fallback crest for a team ESPN's league lists don't cover (smaller leagues, e-sports): TheSportsDB search by name,
 * accepted only when the sport and the name match. { logo, color } or {}; cached 30 days per team at the edge.
 */
export async function GET(request: Request) {
  const u = new URL(request.url);
  const name = (u.searchParams.get("n") ?? "").trim().slice(0, 80);
  const sport = u.searchParams.get("s") ?? "football";
  if (name.length < 2) return Response.json({});

  const cache = (globalThis as unknown as { caches?: { default?: Cache } }).caches?.default;
  const key = new Request(new URL(`/api/crest?n=${encodeURIComponent(teamKey(name))}&s=${sport}&v=2`, request.url).toString());
  if (cache) {
    const hit = await cache.match(key);
    if (hit) return hit;
  }

  let out: { logo?: string; color?: string } = {};
  try {
    const r = await fetch(`https://www.thesportsdb.com/api/v1/json/123/searchteams.php?t=${encodeURIComponent(name)}`);
    const d = (await r.json()) as { teams?: TsdbTeam[] | null };
    const want = teamKey(name), sports = TSDB_SPORT[sport] ?? [];
    const ok = (d.teams ?? []).filter((t) => t.strBadge && (!sports.length || sports.includes(t.strSport ?? "")));
    const hit = ok.find((t) => [t.strTeam, t.strTeamAlternate, t.strTeamShort].some((n) => n && n.split(",").some((x) => teamKey(x) === want)))
      ?? ok.find((t) => { const k = teamKey(t.strTeam ?? ""); return k.length >= 4 && (k.includes(want) || want.includes(k)); });
    if (hit?.strBadge) out = { logo: `${hit.strBadge}/small`, color: brandColor(hit.strColour1?.replace("#", ""), hit.strColour2?.replace("#", "")) };
  } catch { /* monogram */ }

  const res = Response.json(out, { headers: { "cache-control": `public, max-age=86400, s-maxage=${TTL_S}` } });
  if (cache) await cache.put(key, res.clone());
  return res;
}
