import Link from "next/link";
import { ProbabilityBar } from "@/components/stats/ProbabilityBar";
import { getTier } from "@/lib/auth";
import { listMatches, type MatchView } from "@/lib/data";
import { dayKey, dayLabel, timeLabel } from "@/lib/format";
import { PICK_FEATURED } from "@/lib/picks";

export const dynamic = "force-dynamic";

const WINDOW_MS = 21 * 24 * 60 * 60 * 1000;

export default async function MatchesPage({ searchParams }: { searchParams: Promise<{ liga?: string }> }) {
  const { liga } = await searchParams;
  const tier = await getTier();
  const now = Date.now();
  const all = await listMatches(tier, now - 3 * 60 * 60 * 1000, now + WINDOW_MS);

  const competitions = Array.from(new Map(all.map((m) => [m.competition.id, m.competition])).values());
  const matches = liga ? all.filter((m) => m.competition.id === liga) : all;

  const days = new Map<string, MatchView[]>();
  for (const m of matches) {
    const k = dayKey(m.kickoffAt);
    days.set(k, [...(days.get(k) ?? []), m]);
  }

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Próximas 3 semanas</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">Partidos</h1>
        </div>
        {competitions.length > 1 && (
          <nav className="flex flex-wrap gap-2 text-sm" aria-label="Filtrar por liga">
            <Chip href="/app" active={!liga}>Todas</Chip>
            {competitions.map((c) => (
              <Chip key={c.id} href={`/app?liga=${encodeURIComponent(c.id)}`} active={liga === c.id}>{c.name}</Chip>
            ))}
          </nav>
        )}
      </div>

      <FeaturedPicks matches={matches} now={now} />

      {matches.length === 0 ? (
        <div className="card mt-8 p-8 text-mid">
          No hay partidos publicados para esta ventana. El modelo publica nuevas fichas varias veces al día.
        </div>
      ) : (
        <div className="mt-8 space-y-10">
          {Array.from(days.entries()).map(([k, list]) => (
            <section key={k} aria-labelledby={`d-${k}`}>
              <h2 id={`d-${k}`} className="eyebrow mb-3">{dayLabel(list[0].kickoffAt, now)}</h2>
              <ul className="grid gap-3 md:grid-cols-2">
                {list.map((m) => (
                  <li key={m.id}><MatchCard m={m} /></li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}

function Chip({ href, active, children }: { href: string; active: boolean; children: React.ReactNode }) {
  return (
    <Link href={href} aria-current={active ? "true" : undefined}
      className={`px-3 py-1 rounded-full border transition-colors ${active ? "border-[var(--border-glass)] text-hi bg-[var(--gold-faint)]" : "border-line text-lo hover:text-hi"}`}>
      {children}
    </Link>
  );
}

function MatchCard({ m }: { m: MatchView }) {
  const p = m.prediction;
  const finished = m.status === "finished";
  return (
    <Link href={`/app/partido/${encodeURIComponent(m.id)}`}
      className="block card p-4 sm:p-5 transition-colors hover:border-[var(--border-glass)]">
      <div className="flex items-center justify-between text-[11px] text-lo">
        <span className="truncate">{m.competition.name}</span>
        <span className="num">
          {m.status === "live" ? <span style={{ color: "var(--neon-up)" }}>● EN VIVO</span> : finished ? "Final" : timeLabel(m.kickoffAt)}
        </span>
      </div>
      <div className="mt-3 grid grid-cols-[1fr_auto_1fr] items-center gap-3">
        <span className="font-medium truncate">{m.home.name}</span>
        <span className="num text-lo text-sm">
          {m.homeScore !== null && m.awayScore !== null ? `${m.homeScore} – ${m.awayScore}` : "vs"}
        </span>
        <span className="font-medium truncate text-right">{m.away.name}</span>
      </div>
      <div className="mt-4">
        {p ? (
          <ProbabilityBar size="sm" home={p.outcome.home} draw={p.outcome.draw} away={p.outcome.away}
            labels={{ home: m.home.short, away: m.away.short }} />
        ) : (
          <p className="text-xs text-lo">Modelo pendiente para este partido.</p>
        )}
      </div>
    </Link>
  );
}

/** Every selection at ≥80% across the upcoming matches, best first. Free accounts see how many there are. */
function FeaturedPicks({ matches, now }: { matches: MatchView[]; now: number }) {
  const upcoming = matches.filter((m) => m.status === "scheduled" && m.kickoffAt > now);
  const picks = upcoming
    // One per match (its strongest) so the section spans many games instead of three picks of the same one.
    .flatMap((m) => m.picks.filter((k) => k.p >= PICK_FEATURED).slice(0, 1).map((k) => ({ m, k })))
    .sort((a, b) => b.k.p - a.k.p || a.m.kickoffAt - b.m.kickoffAt);
  const locked = upcoming.reduce((n, m) => n + m.picksLocked, 0);
  if (!picks.length && !locked) return null;

  return (
    <section aria-labelledby="h-featured" className="mt-8 rounded-[16px] border border-[var(--border-glass)] p-5 sm:p-6"
      style={{ background: "linear-gradient(135deg, rgba(212,175,55,0.10), rgba(212,175,55,0.02) 55%, transparent)" }}>
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <p className="eyebrow text-gold">Picks destacados</p>
          <h2 id="h-featured" className="mt-1 text-xl font-semibold">80% o más según el modelo</h2>
        </div>
        <p className="text-[11px] text-lo max-w-sm">Probabilidad, no certeza: un 80% falla 1 de cada 5 veces. Revisa el partido antes de decidir.</p>
      </div>
      {picks.length ? (
        <ul className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {picks.slice(0, 12).map(({ m, k }) => (
            <li key={`${m.id}-${k.key}`}>
              <Link href={`/app/partido/${encodeURIComponent(m.id)}`}
                className="block h-full rounded-[12px] border border-line bg-[var(--bg-raise)]/60 p-4 transition-colors hover:border-[var(--gold)]">
                <div className="flex items-center justify-between gap-2 text-[11px] text-lo">
                  <span className="truncate">{m.competition.name}</span>
                  <span className="num whitespace-nowrap">{dayLabel(m.kickoffAt, now)} · {timeLabel(m.kickoffAt)}</span>
                </div>
                <div className="mt-1 truncate text-sm text-mid">{m.home.name} vs {m.away.name}</div>
                <div className="mt-3 text-hi">{k.label}</div>
                <div className="mt-1 flex items-baseline justify-between">
                  <span className="num text-2xl font-semibold text-gold">{Math.round(k.p * 100)}%</span>
                  <span className="num text-[11px] text-lo">cuota justa {(1 / k.p).toFixed(2)}</span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      ) : (
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-[12px] border border-line p-4">
          <p className="text-sm text-mid">Hay <span className="text-gold num">{locked}</span> selecciones con 75% o más en los próximos partidos. Los picks son parte de Pro y Elite.</p>
          <Link href="/planes" className="btn-gold px-4 py-2 text-sm">Ver planes</Link>
        </div>
      )}
    </section>
  );
}
