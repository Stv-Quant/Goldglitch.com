export type Fixture = {
  id: string;
  sport: string;
  league: string;
  home: string;
  away: string;
  kickoffAt: number;
  state: "pre" | "in" | "post";
  outcomes: 2 | 3;
};

const ymdFmt = new Intl.DateTimeFormat("en-CA", { timeZone: "America/Bogota" });

/** True when the kickoff falls on today's date in Colombia. */
export function isTodayBogota(ms: number, now = Date.now()): boolean {
  return ymdFmt.format(ms) === ymdFmt.format(now);
}
