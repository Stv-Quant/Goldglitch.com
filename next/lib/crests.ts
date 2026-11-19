/** Competition id (as SQPC publishes it) → ESPN league path, for team crests. Unknown leagues fall back to monograms. */
export const ESPN_LEAGUE: Record<string, string> = {
  "football-ucl": "soccer/uefa.champions", "football-uel": "soccer/uefa.europa", "football-uecl": "soccer/uefa.europa.conf",
  "football-lib": "soccer/conmebol.libertadores", "football-sud": "soccer/conmebol.sudamericana",
  "football-e0": "soccer/eng.1", "football-sp1": "soccer/esp.1", "football-i1": "soccer/ita.1", "football-d1": "soccer/ger.1",
  "football-f1": "soccer/fra.1", "football-col": "soccer/col.1", "football-arg": "soccer/arg.1", "football-bra": "soccer/bra.1",
  "football-mex": "soccer/mex.1", "football-usa": "soccer/usa.1", "football-p1": "soccer/por.1", "football-n1": "soccer/ned.1",
  "football-b1": "soccer/bel.1", "football-t1": "soccer/tur.1", "football-sc0": "soccer/sco.1", "football-aut": "soccer/aut.1",
  "football-g1": "soccer/gre.1", "football-dnk": "soccer/den.1", "football-nor": "soccer/nor.1", "football-swe": "soccer/swe.1",
  "football-e1": "soccer/eng.2", "football-sp2": "soccer/esp.2", "football-i2": "soccer/ita.2", "football-d2": "soccer/ger.2",
  "football-f2": "soccer/fra.2", "football-jpn": "soccer/jpn.1",
  "basketball-nba": "basketball/nba", "basketball-ncaab": "basketball/mens-college-basketball",
  "hockey-nhl": "hockey/nhl", "baseball-mlb": "baseball/mlb", "football-nfl": "football/nfl",
};

const NOISE = /\b(fc|cf|sc|ac|afc|cd|ca|club|de|del|la|el|the|sad|ssc|as|us|rc|ud|sd|ec|se|fk|sk|bk|if|calcio|futebol|clube)\b/g;

/** Same key for "Atlético-MG", "Atletico Mineiro" style variants: accents, punctuation and club suffixes dropped. */
export function teamKey(name: string): string {
  return name.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9 ]+/g, " ").replace(NOISE, " ").replace(/\s+/g, " ").trim();
}

/** 96px crop of an ESPN logo via its image combiner (~3 KB instead of a 500px PNG). */
export function espnCrest(href: string | undefined): string | undefined {
  const m = href && /^https:\/\/a\.espncdn\.com(\/i\/teamlogos\/[\w/.-]+\.png)$/.exec(href);
  return m ? `https://a.espncdn.com/combiner/i?img=${m[1]}&w=96&h=96&scale=crop&cquality=80` : undefined;
}

/** Looks a team up: exact key, then the longest key contained in the other (e.g. "vasco" ⊂ "vasco da gama"). */
export function findCrest(map: Record<string, string>, name: string): string | undefined {
  const k = teamKey(name);
  if (!k) return undefined;
  if (map[k]) return map[k];
  let best: string | undefined, len = 0;
  for (const [key, url] of Object.entries(map)) {
    if (key.length < 4) continue;
    if ((k.includes(key) || key.includes(k)) && key.length > len) { best = url; len = key.length; }
  }
  return best;
}
