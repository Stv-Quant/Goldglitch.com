/**
 * How leagues are grouped and ordered in the app: by region, most followed first.
 * Unknown competitions fall into "Otras ligas" (football) or "Otros deportes" (anything else), sorted by name.
 */
export type LeagueGroup = { id: string; label: string };

export const LEAGUE_GROUPS: LeagueGroup[] = [
  { id: "intl", label: "Copas internacionales" },
  { id: "top5", label: "Las 5 grandes de Europa" },
  { id: "sa", label: "Sudamérica" },
  { id: "na", label: "Norte y Centroamérica" },
  { id: "eu", label: "Resto de Europa" },
  { id: "second", label: "Segundas divisiones" },
  { id: "asia", label: "Asia" },
  { id: "other", label: "Otras ligas" },
  { id: "us", label: "Otros deportes" },
];

/** [group, order inside the group, country] by competition id. */
const LEAGUES: Record<string, [string, number, string]> = {
  "football-ucl": ["intl", 1, "Europa"],
  "football-uel": ["intl", 2, "Europa"],
  "football-uecl": ["intl", 3, "Europa"],
  "football-lib": ["intl", 4, "Sudamérica"],
  "football-sud": ["intl", 5, "Sudamérica"],
  "football-e0": ["top5", 1, "Inglaterra"],
  "football-sp1": ["top5", 2, "España"],
  "football-i1": ["top5", 3, "Italia"],
  "football-d1": ["top5", 4, "Alemania"],
  "football-f1": ["top5", 5, "Francia"],
  "football-col": ["sa", 1, "Colombia"],
  "football-arg": ["sa", 2, "Argentina"],
  "football-bra": ["sa", 3, "Brasil"],
  "football-mex": ["na", 1, "México"],
  "football-usa": ["na", 2, "Estados Unidos"],
  "football-p1": ["eu", 1, "Portugal"],
  "football-n1": ["eu", 2, "Países Bajos"],
  "football-b1": ["eu", 3, "Bélgica"],
  "football-t1": ["eu", 4, "Turquía"],
  "football-sc0": ["eu", 5, "Escocia"],
  "football-aut": ["eu", 6, "Austria"],
  "football-g1": ["eu", 7, "Grecia"],
  "football-dnk": ["eu", 8, "Dinamarca"],
  "football-nor": ["eu", 9, "Noruega"],
  "football-swe": ["eu", 10, "Suecia"],
  "football-e1": ["second", 1, "Inglaterra"],
  "football-sp2": ["second", 2, "España"],
  "football-i2": ["second", 3, "Italia"],
  "football-d2": ["second", 4, "Alemania"],
  "football-f2": ["second", 5, "Francia"],
  "football-jpn": ["asia", 1, "Japón"],
  "basketball-nba": ["us", 1, "Baloncesto"],
  "basketball-ncaab": ["us", 2, "Baloncesto"],
  "hockey-nhl": ["us", 3, "Hockey"],
  "baseball-mlb": ["us", 4, "Béisbol"],
  "football-nfl": ["us", 5, "Fútbol americano"],
};

export function leagueInfo(id: string, sport?: string): { group: string; order: number; country: string | null } {
  const l = LEAGUES[id];
  if (l) return { group: l[0], order: l[1], country: l[2] };
  return { group: sport && sport !== "football" ? "us" : "other", order: 99, country: null };
}

const GROUP_RANK = new Map(LEAGUE_GROUPS.map((g, i) => [g.id, i]));

/** Sort key: region first, then the league's place in it, then name. */
export function leagueRank(c: { id: string; name: string }, sport?: string): [number, number, string] {
  const i = leagueInfo(c.id, sport);
  return [GROUP_RANK.get(i.group) ?? 99, i.order, c.name];
}

export function compareLeagues(a: { id: string; name: string }, b: { id: string; name: string }, sa?: string, sb?: string): number {
  const x = leagueRank(a, sa), y = leagueRank(b, sb);
  return x[0] - y[0] || x[1] - y[1] || x[2].localeCompare(y[2], "es");
}
