type Item = { sport: string; home: string; away: string; p: number[] };

// Illustrative values only (labelled on screen). Real fixtures come from SQPC via /api/ingest.
const ROW_A: Item[] = [
  { sport: "FÚT", home: "AME", away: "CAL", p: [0.5, 0.27, 0.23] },
  { sport: "MLB", home: "NYY", away: "BOS", p: [0.58, 0.42] },
  { sport: "FÚT", home: "ARS", away: "LIV", p: [0.49, 0.27, 0.24] },
  { sport: "MLB", home: "LAD", away: "SFG", p: [0.61, 0.39] },
  { sport: "FÚT", home: "NAL", away: "MIL", p: [0.52, 0.29, 0.19] },
  { sport: "MLB", home: "HOU", away: "SEA", p: [0.54, 0.46] },
];
const ROW_B: Item[] = [
  { sport: "NBA", home: "BOS", away: "LAL", p: [0.62, 0.38] },
  { sport: "TEN", home: "J. A", away: "J. B", p: [0.57, 0.43] },
  { sport: "FÚT", home: "MCI", away: "CHE", p: [0.57, 0.24, 0.19] },
  { sport: "NBA", home: "DEN", away: "PHX", p: [0.55, 0.45] },
  { sport: "TEN", home: "J. C", away: "J. D", p: [0.71, 0.29] },
  { sport: "FÚT", home: "JUN", away: "TOL", p: [0.43, 0.32, 0.25] },
];

function Row({ items, reverse, dur }: { items: Item[]; reverse?: boolean; dur: string }) {
  const doubled = [...items, ...items];
  return (
    <div className="ticker overflow-hidden py-3">
      <ul className="ticker-track" data-reverse={reverse ? "" : undefined} style={{ ["--ticker-dur" as string]: dur }}>
        {doubled.map((m, i) => {
          const max = Math.max(...m.p);
          return (
            <li key={i} className="flex items-center gap-4 num text-sm whitespace-nowrap" aria-hidden={i >= items.length}>
              <span className="text-[10px] tracking-[0.2em] text-lo border border-line rounded px-1.5 py-0.5">{m.sport}</span>
              <span className="text-hi">{m.home}</span>
              <span className="flex gap-2">
                {m.p.map((v, j) => (
                  <span key={j} style={{ color: v === max ? "var(--gold)" : "var(--text-lo)" }}>{Math.round(v * 100)}</span>
                ))}
              </span>
              <span className="text-hi">{m.away}</span>
              <span className="text-line">/</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export function ProbabilityTicker() {
  return (
    <section aria-label="Ejemplos de probabilidades" className="relative border-y border-line bg-[var(--bg-raise)]/60 py-2 my-10">
      <Row items={ROW_A} dur="55s" />
      <Row items={ROW_B} dur="70s" reverse />
      <p className="px-5 sm:px-6 pb-2 text-[10px] num tracking-[0.18em] uppercase text-lo">
        Ejemplos ilustrativos · el número dorado es el resultado más probable, no una garantía
      </p>
    </section>
  );
}
