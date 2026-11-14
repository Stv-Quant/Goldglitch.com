import Link from "next/link";
import { Prob, ProbLegend } from "@/components/stats/Prob";
import { ProbabilityBar } from "@/components/stats/ProbabilityBar";
import { getTier } from "@/lib/auth";
import { listMatches, type MatchView } from "@/lib/data";
import { dayKey, dayLabel, timeLabel } from "@/lib/format";
import { bogotaDay } from "@/lib/fixtures";
import { LEAGUE_GROUPS, compareLeagues, leagueInfo } from "@/lib/leagues";
import { PICK_FEATURED } from "@/lib/picks";
import { probColor } from "@/lib/probScale";

export const dynamic = "force-dynamic";

const WINDOW_MS = 21 * 24 * 60 * 60 * 1000;
const DAYS = [
  { id: "hoy", label: "Hoy" },
  { id: "manana", label: "Mañana" },
  { id: "semana", label: "7 días" },
  { id: "todo", label: "Todo" },
] as const;

export default async function MatchesPage({ searchParams }: { searchParams: Promise<{ liga?: string; dia?: string; region?: string; ver?: string }> }) {
  const { liga, dia, region, ver } = await searchParams;
  const tier = await getTier();
  const now = Date.now();
  const today = dayKey(now);
  const tomorrow = dayKey(now + 86_400_000);
  const t0 = bogotaDay(now), t1 = bogotaDay(now + 86_400_000);
  // Only the chosen window is read from the database (the whole 3 weeks used to exceed the Worker's CPU limit).
  const RANGE: Record<string, [number, number]> = {
    hoy: [t0.start, t0.end],
    manana: [t1.start, t1.end],
    semana: [now - 3 * 3_600_000, now + 7 * 86_400_000],
    todo: [now - 3 * 3_600_000, now + WINDOW_MS],
  };
  const open = (m: MatchView) => m.status !== "finished";
  let day = DAYS.some((d) => d.id === dia) ? dia! : "hoy";
  let all = await listMatches(tier, ...RANGE[day]);
  // Default: today when something is still to be played; otherwise the next 7 days.
  if (!dia && !all.some(open)) {
    day = "semana";
    all = await listMatches(tier, ...RANGE.semana);
  }
  const inDay = (m: MatchView) =>
    day === "todo" ? true
    : day === "semana" ? m.kickoffAt < now + 7 * 86_400_000
    : dayKey(m.kickoffAt) === (day === "hoy" ? today : tomorrow);

  const dayMatches = all.filter(inDay);
  // Regions and leagues present in the chosen day, in the app's order.
  const comps = Array.from(new Map(dayMatches.map((m) => [m.competition.id, { ...m.competition, sport: m.sport }])).values())
    .sort((x, y) => compareLeagues(x, y, x.sport, y.sport));
  const count = (f: (m: MatchView) => boolean) => dayMatches.filter(f).length;
  const regions = LEAGUE_GROUPS.map((g) => ({ ...g, n: count((m) => leagueInfo(m.competition.id, m.sport).group === g.id) })).filter((g) => g.n > 0);
  const selLeague = comps.find((c) => c.id === liga);
  const reg = selLeague ? leagueInfo(selLeague.id, selLeague.sport).group : regions.some((g) => g.id === region) ? region! : null;
  const regionComps = reg ? comps.filter((c) => leagueInfo(c.id, c.sport).group === reg) : [];

  const matches = dayMatches.filter((m) =>
    selLeague ? m.competition.id === selLeague.id : reg ? leagueInfo(m.competition.id, m.sport).group === reg : true);
  const upcoming = matches.filter((m) => open(m) && m.kickoffAt > now - 3 * 3_600_000);

  const picks = upcoming.flatMap((m) => m.picks).length;
  const lockedPicks = upcoming.reduce((n, m) => n + m.picksLocked, 0);
  const best = upcoming.flatMap((m) => m.picks).reduce((b, k) => Math.max(b, k.p), 0);

  // Day → league (in league order) → matches by time. At most SHOW cards unless asked for all (keeps the page light).
  const SHOW = 40;
  const showAll = ver === "todos";
  const shown = showAll ? matches : matches.slice(0, SHOW);
  const days = new Map<string, Map<string, MatchView[]>>();
  for (const m of shown) {
    const d = days.get(dayKey(m.kickoffAt)) ?? new Map<string, MatchView[]>();
    d.set(m.competition.id, [...(d.get(m.competition.id) ?? []), m]);
    days.set(dayKey(m.kickoffAt), d);
  }
  const href = (q: { liga?: string; dia?: string; region?: string; ver?: string }) => {
    const sp = new URLSearchParams();
    if (q.ver) sp.set("ver", q.ver);
    if (q.dia) sp.set("dia", q.dia);
    if (q.region) sp.set("region", q.region);
    if (q.liga) sp.set("liga", q.liga);
    const s = sp.toString();
    return s ? `/app?${s}` : "/app";
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="eyebrow">Probabilidades del modelo</p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight">Partidos</h1>
        </div>
        <ProbLegend />
      </div>

      <div className="grid grid-cols-3 gap-2 sm:gap-3">
        <Stat label="Partidos" value={String(upcoming.length)} />
        <Stat label="Picks 75%+" value={String(picks || lockedPicks)} locked={!picks && lockedPicks > 0} />
        <Stat label="Mejor pick" p={best || undefined} value={best ? undefined : "—"} locked={!best && lockedPicks > 0} />
      </div>

      <div className="space-y-3">
        <nav className="flex gap-1 rounded-xl border border-line p-1 text-sm sm:inline-flex" aria-label="Día">
          {DAYS.map((d) => (
            <Link key={d.id} href={href({ dia: d.id })} aria-current={day === d.id ? "true" : undefined}
              className={`flex-1 whitespace-nowrap rounded-lg px-4 py-1.5 text-center transition-colors ${day === d.id ? "bg-[var(--gold-faint)] text-hi" : "text-lo hover:text-hi"}`}>
              {d.label}
            </Link>
          ))}
        </nav>

        {regions.length > 0 && (
          <div className="card p-3 sm:p-4">
            <nav className="scroll-x -mx-1 flex gap-2 px-1 text-sm sm:flex-wrap" aria-label="Región">
              <Chip href={href({ dia: day })} active={!reg} count={dayMatches.length}>Todas</Chip>
              {regions.map((g) => (
                <Chip key={g.id} href={href({ dia: day, region: g.id })} active={reg === g.id} count={g.n}>{g.label}</Chip>
              ))}
            </nav>
            {regionComps.length > 0 && (
              <nav className="mt-3 flex flex-wrap gap-2 border-t border-line pt-3 text-sm" aria-label="Liga">
                <Chip href={href({ dia: day, region: reg! })} active={!selLeague} small>Todas las ligas</Chip>
                {regionComps.map((c) => {
                  const ctry = leagueInfo(c.id, c.sport).country;
                  return (
                    <Chip key={c.id} href={href({ dia: day, liga: c.id })} active={selLeague?.id === c.id} small
                      count={count((m) => m.competition.id === c.id)}>
                      {c.name}{ctry && !c.name.includes(ctry) ? <span className="ml-1 text-lo">· {ctry}</span> : null}
                    </Chip>
                  );
                })}
              </nav>
            )}
          </div>
        )}
      </div>

      <FeaturedPicks matches={upcoming} now={now} />

      {matches.length === 0 ? (
        <div className="card p-8 text-mid">
          {day === "hoy" || day === "manana" ? `No hay partidos publicados para ${day === "hoy" ? "hoy" : "mañana"}. Prueba con 7 días.` : "No hay partidos publicados para esta ventana. El modelo publica nuevas fichas varias veces al día."}
        </div>
      ) : (
        <div className="space-y-10">
          {Array.from(days.entries()).map(([k, leagues]) => {
            const ordered = [...leagues.entries()].sort(([, a], [, b]) => compareLeagues(a[0].competition, b[0].competition, a[0].sport, b[0].sport));
            const n = ordered.reduce((s, [, l]) => s + l.length, 0);
            return (
              <section key={k} aria-labelledby={`d-${k}`} className="space-y-5">
                <h2 id={`d-${k}`} className="flex items-baseline gap-2 border-b border-line pb-2">
                  <span className="text-xl font-semibold">{dayLabel(ordered[0][1][0].kickoffAt, now)}</span>
                  <span className="num text-xs text-lo">{n} partido{n === 1 ? "" : "s"} · {ordered.length} liga{ordered.length === 1 ? "" : "s"}</span>
                </h2>
                {ordered.map(([cid, list]) => {
                  const ctry = leagueInfo(cid, list[0].sport).country;
                  return (
                    <div key={cid}>
                      <h3 className="mb-2 flex items-center gap-2 text-sm">
                        <span aria-hidden className="h-3 w-0.5 rounded-full bg-[var(--gold)]" />
                        <Link href={href({ dia: day, liga: cid })} className="font-medium text-hi hover:text-gold">{list[0].competition.name}</Link>
                        {ctry && !list[0].competition.name.includes(ctry) && <span className="text-lo">{ctry}</span>}
                        <span className="num text-[11px] text-lo">· {list.length}</span>
                      </h3>
                      <ul className="grid gap-3 md:grid-cols-2">
                        {list.map((m) => <li key={m.id}><MatchCard m={m} /></li>)}
                      </ul>
                    </div>
                  );
                })}
              </section>
            );
          })}
          {!showAll && matches.length > SHOW && (
            <Link href={href({ dia: day, region: selLeague ? undefined : reg ?? undefined, liga: selLeague?.id, ver: "todos" })}
              className="block card p-4 text-center text-sm text-gold transition-colors hover:border-[var(--border-glass)]">
              Mostrar los {matches.length} partidos ({matches.length - SHOW} más)
            </Link>
          )}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, p, locked }: { label: string; value?: string; p?: number; locked?: boolean }) {
  return (
    <div className="card px-3 py-3 sm:px-4">
      <div className="truncate text-[11px] text-lo">{label}</div>
      <div className="mt-0.5 flex items-baseline gap-1.5">
        {p !== undefined ? <Prob p={p} className="text-2xl font-semibold" /> : <span className="num text-2xl font-semibold text-hi">{value}</span>}
        {locked && <span className="text-[10px] uppercase tracking-[0.14em] text-gold">Pro</span>}
      </div>
    </div>
  );
}

function Chip({ href, active, children, count, small = false }: {
  href: string; active: boolean; children: React.ReactNode; count?: number; small?: boolean;
}) {
  return (
    <Link href={href} aria-current={active ? "true" : undefined}
      className={`whitespace-nowrap rounded-full border transition-colors ${small ? "px-2.5 py-0.5 text-[13px]" : "px-3 py-1"} ${active ? "border-[var(--border-glass)] bg-[var(--gold-faint)] text-hi" : "border-line text-lo hover:text-hi"}`}>
      {children}
      {count !== undefined && <span className={`num ml-1.5 text-[11px] ${active ? "text-gold" : "text-lo"}`}>{count}</span>}
    </Link>
  );
}

function MatchCard({ m }: { m: MatchView }) {
  const p = m.prediction;
  const finished = m.status === "finished";
  const top = m.picks[0];
  return (
    <Link href={`/app/partido/${encodeURIComponent(m.id)}`}
      className="block card p-4 transition-colors hover:border-[var(--border-glass)] sm:p-5">
      <div className="flex items-center justify-between gap-2 text-[11px] text-lo">
        <span className="truncate">{m.competition.name}</span>
        <span className="num whitespace-nowrap">
          {m.status === "live" ? <span style={{ color: "var(--neon-up)" }}>● EN VIVO</span> : finished ? "Final" : timeLabel(m.kickoffAt)}
        </span>
      </div>
      <div className="mt-3 grid grid-cols-[1fr_auto_1fr] items-center gap-3">
        <span className="truncate font-medium">{m.home.name}</span>
        <span className="num text-sm text-lo">
          {m.homeScore !== null && m.awayScore !== null ? `${m.homeScore} – ${m.awayScore}` : "vs"}
        </span>
        <span className="truncate text-right font-medium">{m.away.name}</span>
      </div>
      <div className="mt-4">
        {p ? (
          <ProbabilityBar size="sm" home={p.outcome.home} draw={p.outcome.draw} away={p.outcome.away}
            labels={{ home: m.home.short, away: m.away.short }} />
        ) : (
          <p className="text-xs text-lo">Modelo pendiente para este partido.</p>
        )}
      </div>
      {!finished && (top || m.picksLocked > 0) && (
        <div className="mt-3 flex items-center justify-between gap-3 border-t border-line pt-3 text-xs">
          {top ? (
            <>
              <span className="min-w-0 truncate text-mid">
                <span aria-hidden className="mr-1.5 inline-block h-2 w-2 rounded-full align-middle" style={{ background: probColor(top.p) }} />
                {top.label}
              </span>
              <span className="whitespace-nowrap">
                <Prob p={top.p} className="font-semibold" />
                {m.picks.length > 1 && <span className="ml-1.5 text-lo">+{m.picks.length - 1}</span>}
              </span>
            </>
          ) : (
            <>
              <span className="text-mid">{m.picksLocked} pick{m.picksLocked === 1 ? "" : "s"} de 75% o más</span>
              <span className="text-[10px] uppercase tracking-[0.14em] text-gold">Pro</span>
            </>
          )}
        </div>
      )}
    </Link>
  );
}

/** Every selection at ≥80% across the upcoming matches, best first. Free accounts see how many there are. */
function FeaturedPicks({ matches, now }: { matches: MatchView[]; now: number }) {
  const list = matches.filter((m) => m.status === "scheduled" && m.kickoffAt > now);
  const picks = list
    // One per match (its strongest) so the section spans many games instead of three picks of the same one.
    .flatMap((m) => m.picks.filter((k) => k.p >= PICK_FEATURED).slice(0, 1).map((k) => ({ m, k })))
    .sort((a, b) => b.k.p - a.k.p || a.m.kickoffAt - b.m.kickoffAt);
  const locked = list.reduce((n, m) => n + m.picksLocked, 0);
  if (!picks.length && !locked) return null;

  return (
    <section aria-labelledby="h-featured" className="rounded-[16px] border border-[var(--border-glass)] p-4 sm:p-6"
      style={{ background: "linear-gradient(135deg, rgba(212,175,55,0.10), rgba(46,242,160,0.03) 60%, transparent)" }}>
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <p className="eyebrow text-gold">Picks destacados</p>
          <h2 id="h-featured" className="mt-1 text-xl font-semibold">80% o más según el modelo</h2>
        </div>
        <p className="max-w-sm text-[11px] text-lo">Probabilidad, no certeza: un 80% falla 1 de cada 5 veces.</p>
      </div>
      {picks.length ? (
        <ul className="scroll-x -mx-4 mt-4 flex snap-x gap-3 px-4 sm:mx-0 sm:grid sm:grid-cols-2 sm:px-0 lg:grid-cols-3">
          {picks.slice(0, 6).map(({ m, k }) => (
            <li key={`${m.id}-${k.key}`} className="w-[78%] shrink-0 snap-start sm:w-auto">
              <Link href={`/app/partido/${encodeURIComponent(m.id)}`}
                className="relative block h-full overflow-hidden rounded-[12px] border border-line bg-[var(--bg-raise)] p-4 transition-colors hover:border-[var(--gold)]">
                <span aria-hidden className="absolute inset-y-0 left-0 w-1" style={{ background: probColor(k.p) }} />
                <div className="flex items-center justify-between gap-2 text-[11px] text-lo">
                  <span className="truncate">{m.competition.name}</span>
                  <span className="num whitespace-nowrap">{dayLabel(m.kickoffAt, now)} · {timeLabel(m.kickoffAt)}</span>
                </div>
                <div className="mt-1 truncate text-sm text-mid">{m.home.name} vs {m.away.name}</div>
                <div className="mt-3 text-hi">{k.label}</div>
                <div className="mt-1 flex items-baseline justify-between">
                  <Prob p={k.p} className="text-3xl font-semibold" />
                  <span className="num text-[11px] text-lo">cuota justa {(1 / k.p).toFixed(2)}</span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      ) : (
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-[12px] border border-line p-4">
          <p className="text-sm text-mid">Hay <span className="num text-gold">{locked}</span> selecciones con 75% o más en los próximos partidos. Los picks son parte de Pro.</p>
          <Link href="/planes" className="btn-gold px-4 py-2 text-sm">Ver planes</Link>
        </div>
      )}
    </section>
  );
}
