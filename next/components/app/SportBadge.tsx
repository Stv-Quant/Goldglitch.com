/**
 * Sport identity for cards: a gold line icon + the sport's name, and an optional large watermark.
 * Icons are drawn here (no emoji) so they stay crisp and on-brand.
 */
const SPORTS: Record<string, { label: string; d: string }> = {
  football: {
    label: "Fútbol",
    d: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm0 4.2 3.3 2.4-1.3 3.9h-4l-1.3-3.9L12 7.2Zm0-4.2v4.2m3.3 2.4 4.6-1.5M14 13.5l2.8 3.8m-6.8-3.8-2.8 3.8m1.5-7.7L4.1 8.1",
  },
  basketball: {
    label: "Baloncesto",
    d: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18ZM3 12h18M12 3v18M5.6 5.6c2.6 2.4 3.4 4.4 3.4 6.4s-.8 4-3.4 6.4M18.4 5.6c-2.6 2.4-3.4 4.4-3.4 6.4s.8 4 3.4 6.4",
  },
  hockey: {
    label: "Hockey",
    d: "M6 3l5.5 13.5c.4 1 1.4 1.5 2.4 1.5H20M14 21h7M4 19.5c0 .8 1.8 1.5 4 1.5s4-.7 4-1.5-1.8-1.5-4-1.5-4 .7-4 1.5Z",
  },
  baseball: {
    label: "Béisbol",
    d: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18ZM6.2 5.2c1.6 1.9 2.4 4.2 2.4 6.8s-.8 4.9-2.4 6.8M17.8 5.2c-1.6 1.9-2.4 4.2-2.4 6.8s.8 4.9 2.4 6.8M7.6 8.5l1.4-.5M8.4 12h1.4M7.6 15.5l1.4.5M16.4 8.5 15 8M15.6 12h-1.4M16.4 15.5 15 16",
  },
  esports: {
    label: "E-sports",
    d: "M7 8h10a4 4 0 0 1 3.9 4.8l-.9 4.3a2 2 0 0 1-3.5.9L14.6 16H9.4l-1.9 2a2 2 0 0 1-3.5-.9l-.9-4.3A4 4 0 0 1 7 8Zm1 3v3m-1.5-1.5h3M15.5 12.2h.01M17.5 14h.01",
  },
  american_football: {
    label: "Fútbol americano",
    d: "M4.5 19.5c-1.5-4.5 0-9 3-12s7.5-4.5 12-3c1.5 4.5 0 9-3 12s-7.5 4.5-12 3ZM9 15l6-6m-4.5 1.5 3 3m-1.5-4.5 3 3m-6 0 3 3",
  },
};

export function sportInfo(sport: string, league?: string) {
  if (sport === "football" && league && /nfl/i.test(league)) return SPORTS.american_football;
  return SPORTS[sport] ?? { label: sport, d: SPORTS.football.d };
}

export function SportIcon({ sport, league, className = "h-3.5 w-3.5" }: { sport: string; league?: string; className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <path d={sportInfo(sport, league).d} />
    </svg>
  );
}

/** Small pill: icon + sport name. */
export function SportBadge({ sport, league }: { sport: string; league?: string }) {
  return (
    <span className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-[rgba(212,175,55,0.28)] bg-[rgba(212,175,55,0.08)] px-2 py-0.5 text-[10px] font-medium uppercase tracking-[0.12em] text-gold">
      <SportIcon sport={sport} league={league} className="h-3 w-3" />
      {sportInfo(sport, league).label}
    </span>
  );
}

/** Large faint icon in a card corner. */
export function SportWatermark({ sport, league }: { sport: string; league?: string }) {
  return (
    <span aria-hidden className="pointer-events-none absolute -right-5 -top-5 text-gold opacity-[0.07]">
      <SportIcon sport={sport} league={league} className="h-28 w-28" />
    </span>
  );
}
