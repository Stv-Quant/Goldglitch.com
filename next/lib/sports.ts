export const SPORTS = ["football", "baseball", "basketball", "hockey"] as const;
export type Sport = (typeof SPORTS)[number];

export const SPORT_LABEL: Record<Sport, string> = {
  football: "Fútbol",
  baseball: "Béisbol",
  basketball: "Baloncesto",
  hockey: "Hockey",
};

/** Short tag for compact UI (banner chips). */
export const SPORT_TAG: Record<Sport, string> = {
  football: "FÚT",
  baseball: "MLB",
  basketball: "BAL",
  hockey: "NHL",
};

export function isSport(v: string): v is Sport {
  return (SPORTS as readonly string[]).includes(v);
}
