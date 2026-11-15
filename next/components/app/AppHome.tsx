"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Prob, ProbLegend } from "@/components/stats/Prob";
import { ProbabilityBar } from "@/components/stats/ProbabilityBar";
import { LEAGUE_GROUPS, compareLeagues, leagueInfo } from "@/lib/leagues";
import { probColor } from "@/lib/probScale";

/** One match as /api/app/matches sends it (built by D1, see lib/appList.ts). */
type M = {
  id: string; sport: string; ko: number; st: string; hs: number | null; as: number | null;
  c: string; cn: string; h: string; hn: string; a: string; an: string;
  o: { h: number; d: number | null; a: number } | null;
  k: { n: number; l?: string; p?: number } | null;
};
type Data = { day: string; now: number; tier: string; matches: M[] };

const DAYS = [
  { id: "hoy", label: "Hoy" },
  { id: "manana", label: "Mañana" },
  { id: "semana", label: "7 días" },
  { id: "todo", label: "Todo" },
] as const;
const SHOW = 40;
const FEATURED = 0.8;
const TZ = "America/Bogota";

const fmtKey = new Intl.DateTimeFormat("en-CA", { timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit" });
const fmtTime = new Intl.DateTimeFormat("es-CO", { timeZone: TZ, hour: "2-digit", minute: "2-digit", hour12: false });
const fmtDay = new Intl.DateTimeFormat("es-CO", { timeZone: TZ, weekday: "long", day: "numeric", month: "short" });
const dayKey = (ms: number) => fmtKey.format(ms);
const time = (ms: number) => fmtTime.format(ms);
function dayLabel(ms: number, now: number) {
  const k = dayKey(ms);
  if (k === dayKey(now)) return "Hoy";
  if (k === dayKey(now + 86_400_000)) return "Mañana";
  const s = fmtDay.format(ms);
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export function AppHome() {
  const params = useSearchParams();
  const router = useRouter();
  const path = usePathname();
  const dia = params.get("dia") ?? "";
  const region = params.get("region");
  const liga = params.get("liga");
  const ver = params.get("ver");
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let alive = true;
    fetch(`/api/app/matches${dia ? `?dia=${dia}` : ""}`, { cache: "no-store" })
      .then((r) => (r.status === 401 ? (location.href = "/acceso", null) : r.ok ? r.json() : Promise.reject(r.status)))
      .then((d: Data | null) => { if (alive && d) { setData(d); setError(false); } })
      .catch(() => alive && setError(true));
    return () => { alive = false; };
  }, [dia]);

  const go = (q: { dia?: string; region?: string | null; liga?: string | null; ver?: string | null }) => {
    const sp = new URLSearchParams();
    const d = q.dia ?? (data?.day && dia ? data.day : dia);
    if (d) sp.set("dia", d);
    if (q.region) sp.set("region", q.region);
    if (q.liga) sp.set("liga", q.liga);
    if (q.ver) sp.set("ver", q.ver);
    const s = sp.toString();
    return s ? `${path}?${s}` : path;
  };

  const view = useMemo(() => {
    if (!data) return null;
    const { now, matches: all } = data;
    const comps = Array.from(new Map(all.map((m) => [m.c, { id: m.c, name: m.cn, sport: m.sport }])).values())
      .sort((x, y) => compareLeagues(x, y, x.sport, y.sport));
    const groupOf = (m: M) => leagueInfo(m.c, m.sport).group;
    const regions = LEAGUE_GROUPS.map((g) => ({ ...g, n: all.filter((m) => groupOf(m) === g.id).length })).filter((g) => g.n > 0);
    const selLeague = comps.find((c) => c.id === liga);
    const reg = selLeague ? leagueInfo(selLeague.id, selLeague.sport).group : regions.some((g) => g.id === region) ? region : null;
    const regionComps = reg ? comps.filter((c) => leagueInfo(c.id, c.sport).group === reg) : [];
    const matches = all.filter((m) => (selLeague ? m.c === selLeague.id : reg ? groupOf(m) === reg : true));
    const upcoming = matches.filter((m) => m.st !== "finished" && m.ko > now - 3 * 3_600_000);
    const picks = upcoming.reduce((n, m) => n + (m.k?.n ?? 0), 0);
    const best = upcoming.reduce((b, m) => Math.max(b, m.k?.p ?? 0), 0);
    const featured = upcoming
      .filter((m) => m.st === "scheduled" && m.ko > now && (m.k?.p ?? 0) >= FEATURED)
      .sort((x, y) => (y.k!.p! - x.k!.p!) || x.ko - y.ko)
      .slice(0, 6);
    const shown = ver === "todos" ? matches : matches.slice(0, SHOW);
    const days = new Map<string, Map<string, M[]>>();
    for (const m of shown) {
      const d = days.get(dayKey(m.ko)) ?? new Map<string, M[]>();
      d.set(m.c, [...(d.get(m.c) ?? []), m]);
      days.set(dayKey(m.ko), d);
    }
    return { now, all, comps, regions, selLeague, reg, regionComps, matches, upcoming, picks, best, featured, days, count: (c: string) => all.filter((m) => m.c === c).length };
  }, [data, liga, region, ver]);

  const day = data?.day ?? (dia || "hoy");
  const pro = data ? data.tier !== "free" : true;

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
        <Stat label="Partidos" value={view ? String(view.upcoming.length) : "·"} />
        <Stat label="Picks 75%+" value={view ? String(view.picks) : "·"} locked={!pro && !!view?.picks} />
        <Stat label="Mejor pick" p={pro && view?.best ? view.best : undefined} value={view ? "—" : "·"} locked={!pro && !!view?.picks} />
      </div>

      <div className="space-y-3">
        <nav className="flex gap-1 rounded-xl border border-line p-1 text-sm sm:inline-flex" aria-label="Día">
          {DAYS.map((d) => (
            <Link key={d.id} href={go({ dia: d.id })} scroll={false} aria-current={day === d.id ? "true" : undefined}
              className={`flex-1 whitespace-nowrap rounded-lg px-4 py-1.5 text-center transition-colors ${day === d.id ? "bg-[var(--gold-faint)] text-hi" : "text-lo hover:text-hi"}`}>
              {d.label}
            </Link>
          ))}
        </nav>

        {view && view.regions.length > 0 && (
          <div className="card p-3 sm:p-4">
            <nav className="scroll-x -mx-1 flex gap-2 px-1 text-sm sm:flex-wrap" aria-label="Región">
              <Chip href={go({})} active={!view.reg} count={view.all.length}>Todas</Chip>
              {view.regions.map((g) => (
                <Chip key={g.id} href={go({ region: g.id })} active={view.reg === g.id} count={g.n}>{g.label}</Chip>
              ))}
            </nav>
            {view.regionComps.length > 0 && (
              <nav className="mt-3 flex flex-wrap gap-2 border-t border-line pt-3 text-sm" aria-label="Liga">
                <Chip href={go({ region: view.reg })} active={!view.selLeague} small>Todas las ligas</Chip>
                {view.regionComps.map((c) => {
                  const ctry = leagueInfo(c.id, c.sport).country;
                  return (
                    <Chip key={c.id} href={go({ liga: c.id })} active={view.selLeague?.id === c.id} small count={view.count(c.id)}>
                      {c.name}{ctry && !c.name.includes(ctry) ? <span className="ml-1 text-lo">· {ctry}</span> : null}
                    </Chip>
                  );
                })}
              </nav>
            )}
          </div>
        )}
      </div>

      {error && (
        <div className="card p-6 text-sm text-mid">
          No pudimos cargar los partidos. <button type="button" className="text-gold underline" onClick={() => location.reload()}>Reintentar</button>
        </div>
      )}

      {!view && !error && <Skeleton />}

      {view && (pro ? view.featured.length > 0 : view.picks > 0) && (
        <section aria-labelledby="h-featured" className="rounded-[16px] border border-[var(--border-glass)] p-4 sm:p-6"
          style={{ background: "linear-gradient(135deg, rgba(212,175,55,0.10), rgba(46,242,160,0.03) 60%, transparent)" }}>
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <div>
              <p className="eyebrow text-gold">Picks destacados</p>
              <h2 id="h-featured" className="mt-1 text-xl font-semibold">80% o más según el modelo</h2>
            </div>
            <p className="max-w-sm text-[11px] text-lo">Probabilidad, no certeza: un 80% falla 1 de cada 5 veces.</p>
          </div>
          {pro ? (
            <ul className="scroll-x -mx-4 mt-4 flex snap-x gap-3 px-4 sm:mx-0 sm:grid sm:grid-cols-2 sm:px-0 lg:grid-cols-3">
              {view.featured.map((m) => (
                <li key={m.id} className="w-[78%] shrink-0 snap-start sm:w-auto">
                  <Link href={`/app/partido/${encodeURIComponent(m.id)}`}
                    className="relative block h-full overflow-hidden rounded-[12px] border border-line bg-[var(--bg-raise)] p-4 transition-colors hover:border-[var(--gold)]">
                    <span aria-hidden className="absolute inset-y-0 left-0 w-1" style={{ background: probColor(m.k!.p!) }} />
                    <div className="flex items-center justify-between gap-2 text-[11px] text-lo">
                      <span className="truncate">{m.cn}</span>
                      <span className="num whitespace-nowrap">{dayLabel(m.ko, view.now)} · {time(m.ko)}</span>
                    </div>
                    <div className="mt-1 truncate text-sm text-mid">{m.h} vs {m.a}</div>
                    <div className="mt-3 text-hi">{m.k!.l}</div>
                    <Prob p={m.k!.p!} className="mt-1 block text-3xl font-semibold" />
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-[12px] border border-line p-4">
              <p className="text-sm text-mid">Hay <span className="num text-gold">{view.picks}</span> selecciones con 75% o más en estos partidos. Los picks son parte de Pro.</p>
              <Link href="/planes" className="btn-gold px-4 py-2 text-sm">Ver planes</Link>
            </div>
          )}
        </section>
      )}

      {view && view.matches.length === 0 && (
        <div className="card p-8 text-mid">
          {day === "hoy" || day === "manana" ? `No hay partidos publicados para ${day === "hoy" ? "hoy" : "mañana"}. Prueba con 7 días.` : "No hay partidos publicados para esta ventana. El modelo publica nuevas fichas varias veces al día."}
        </div>
      )}

      {view && view.matches.length > 0 && (
        <div className="space-y-10">
          {Array.from(view.days.entries()).map(([k, leagues]) => {
            const ordered = [...leagues.entries()].sort(([, x], [, y]) => compareLeagues({ id: x[0].c, name: x[0].cn }, { id: y[0].c, name: y[0].cn }, x[0].sport, y[0].sport));
            const n = ordered.reduce((s, [, l]) => s + l.length, 0);
            return (
              <section key={k} className="space-y-5">
                <h2 className="flex items-baseline gap-2 border-b border-line pb-2">
                  <span className="text-xl font-semibold">{dayLabel(ordered[0][1][0].ko, view.now)}</span>
                  <span className="num text-xs text-lo">{n} partido{n === 1 ? "" : "s"} · {ordered.length} liga{ordered.length === 1 ? "" : "s"}</span>
                </h2>
                {ordered.map(([cid, list]) => {
                  const ctry = leagueInfo(cid, list[0].sport).country;
                  return (
                    <div key={cid}>
                      <h3 className="mb-2 flex items-center gap-2 text-sm">
                        <span aria-hidden className="h-3 w-0.5 rounded-full bg-[var(--gold)]" />
                        <Link href={go({ liga: cid })} scroll={false} className="font-medium text-hi hover:text-gold">{list[0].cn}</Link>
                        {ctry && !list[0].cn.includes(ctry) && <span className="text-lo">{ctry}</span>}
                        <span className="num text-[11px] text-lo">· {list.length}</span>
                      </h3>
                      <ul className="grid gap-3 md:grid-cols-2">
                        {list.map((m) => <li key={m.id}><Card m={m} pro={pro} /></li>)}
                      </ul>
                    </div>
                  );
                })}
              </section>
            );
          })}
          {ver !== "todos" && view.matches.length > SHOW && (
            <button type="button" onClick={() => router.replace(go({ region: view.selLeague ? null : view.reg, liga: view.selLeague?.id, ver: "todos" }), { scroll: false })}
              className="block w-full card p-4 text-center text-sm text-gold transition-colors hover:border-[var(--border-glass)]">
              Mostrar los {view.matches.length} partidos ({view.matches.length - SHOW} más)
            </button>
          )}
        </div>
      )}
    </div>
  );
}

function Card({ m, pro }: { m: M; pro: boolean }) {
  const finished = m.st === "finished";
  const n = m.k?.n ?? 0;
  return (
    <Link href={`/app/partido/${encodeURIComponent(m.id)}`} className="block card p-4 transition-colors hover:border-[var(--border-glass)] sm:p-5">
      <div className="flex items-center justify-between gap-2 text-[11px] text-lo">
        <span className="truncate">{m.cn}</span>
        <span className="num whitespace-nowrap">
          {m.st === "live" ? <span style={{ color: "var(--neon-up)" }}>● EN VIVO</span> : finished ? "Final" : time(m.ko)}
        </span>
      </div>
      <div className="mt-3 grid grid-cols-[1fr_auto_1fr] items-center gap-3">
        <span className="truncate font-medium">{m.h}</span>
        <span className="num text-sm text-lo">{m.hs !== null && m.as !== null ? `${m.hs} – ${m.as}` : "vs"}</span>
        <span className="truncate text-right font-medium">{m.a}</span>
      </div>
      <div className="mt-4">
        {m.o ? (
          <ProbabilityBar size="sm" home={m.o.h} draw={m.o.d} away={m.o.a} labels={{ home: m.hn, away: m.an }} />
        ) : (
          <p className="text-xs text-lo">Modelo pendiente para este partido.</p>
        )}
      </div>
      {!finished && n > 0 && (
        <div className="mt-3 flex items-center justify-between gap-3 border-t border-line pt-3 text-xs">
          {pro && m.k?.l && m.k.p ? (
            <>
              <span className="min-w-0 truncate text-mid">
                <span aria-hidden className="mr-1.5 inline-block h-2 w-2 rounded-full align-middle" style={{ background: probColor(m.k.p) }} />
                {m.k.l}
              </span>
              <span className="whitespace-nowrap">
                <Prob p={m.k.p} className="font-semibold" />
                {n > 1 && <span className="ml-1.5 text-lo">+{n - 1}</span>}
              </span>
            </>
          ) : (
            <>
              <span className="text-mid">{n} pick{n === 1 ? "" : "s"} de 75% o más</span>
              <span className="text-[10px] uppercase tracking-[0.14em] text-gold">Pro</span>
            </>
          )}
        </div>
      )}
    </Link>
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
    <Link href={href} scroll={false} aria-current={active ? "true" : undefined}
      className={`whitespace-nowrap rounded-full border transition-colors ${small ? "px-2.5 py-0.5 text-[13px]" : "px-3 py-1"} ${active ? "border-[var(--border-glass)] bg-[var(--gold-faint)] text-hi" : "border-line text-lo hover:text-hi"}`}>
      {children}
      {count !== undefined && <span className={`num ml-1.5 text-[11px] ${active ? "text-gold" : "text-lo"}`}>{count}</span>}
    </Link>
  );
}

function Skeleton() {
  return (
    <div className="grid gap-3 md:grid-cols-2" aria-hidden>
      {Array.from({ length: 6 }, (_, i) => (
        <div key={i} className="card h-[150px] animate-pulse p-5">
          <div className="h-3 w-1/3 rounded bg-[var(--seg-3)]" />
          <div className="mt-5 h-4 w-3/4 rounded bg-[var(--seg-3)]" />
          <div className="mt-6 h-2 w-full rounded bg-[var(--seg-3)]" />
        </div>
      ))}
    </div>
  );
}
