export const SPORTS = ["football", "baseball", "basketball", "hockey", "esports"] as const;
export type Sport = (typeof SPORTS)[number];

export const SPORT_LABEL: Record<Sport, string> = {
  football: "Fútbol",
  baseball: "Béisbol",
  basketball: "Baloncesto",
  hockey: "Hockey",
  esports: "E-sports",
};

/** Short tag for compact UI (banner chips). */
export const SPORT_TAG: Record<Sport, string> = {
  football: "FÚT",
  baseball: "MLB",
  basketball: "BAL",
  hockey: "NHL",
  esports: "ESP",
};

export function isSport(v: string): v is Sport {
  return (SPORTS as readonly string[]).includes(v);
}
