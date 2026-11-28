"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Prob, ProbLegend } from "@/components/stats/Prob";
import { LEAGUE_GROUPS, compareLeagues, leagueInfo } from "@/lib/leagues";
import { probColor } from "@/lib/probScale";
import { Crest, useCrests } from "./Crest";
import { SportIcon } from "./SportBadge";

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
  const crest = useCrests(view ? view.comps.map((c) => c.id) : []);

  return (
    <div className="space-y-7">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="eyebrow">Probabilidades del modelo</p>
          <h1 className="font-display mt-1 text-5xl leading-none tracking-tight"><span className="gold-leaf">Partidos</span></h1>
        </div>
        <ProbLegend />
      </div>

      {/* Summary: one quiet strip instead of three boxes */}
      <dl className="grid grid-cols-3 divide-x divide-[var(--border-soft)] rounded-xl border border-line">
        <Stat label="partidos" value={view ? String(view.upcoming.length) : "·"} />
        <Stat label="picks de 80%+" value={view ? String(view.picks) : "·"} locked={!pro && !!view?.picks} />
        <Stat label="mejor pick" p={pro && view?.best ? view.best : undefined} value={view ? "—" : "·"} locked={!pro && !!view?.picks} />
      </dl>

      <div className="space-y-4">
        <nav className="flex gap-1 rounded-xl border border-line p-1 text-sm sm:inline-flex" aria-label="Día">
          {DAYS.map((d) => (
            <Link key={d.id} href={go({ dia: d.id })} scroll={false} aria-current={day === d.id ? "true" : undefined}
              className={`flex-1 whitespace-nowrap rounded-lg px-4 py-1.5 text-center transition-colors ${day === d.id ? "bg-[var(--gold-faint)] text-hi" : "text-lo hover:text-hi"}`}>
              {d.label}
            </Link>
          ))}
        </nav>

        {view && view.regions.length > 0 && (
          <div>
            <nav className="scroll-x -mx-1 flex gap-5 border-b border-line px-1 text-sm" aria-label="Región">
              <Tab href={go({})} active={!view.reg} count={view.all.length}>Todas</Tab>
              {view.regions.map((g) => (
                <Tab key={g.id} href={go({ region: g.id })} active={view.reg === g.id} count={g.n}>{g.label}</Tab>
              ))}
            </nav>
            {view.regionComps.length > 1 && (
              <nav className="scroll-x -mx-1 mt-3 flex gap-2 px-1 text-sm" aria-label="Liga">
                <Chip href={go({ region: view.reg })} active={!view.selLeague}>Todas las ligas</Chip>
                {view.regionComps.map((c) => (
                  <Chip key={c.id} href={go({ liga: c.id })} active={view.selLeague?.id === c.id} count={view.count(c.id)}>{c.name}</Chip>
                ))}
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
        <section aria-labelledby="h-featured">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h2 id="h-featured" className="flex items-baseline gap-3">
              <span className="font-display text-3xl text-hi">Picks destacados</span>
              <span className="num text-xs text-lo">80% o más según el modelo</span>
            </h2>
            <p className="text-[11px] text-lo">Probabilidad, no certeza: un 80% falla 1 de cada 5 veces.</p>
          </div>
          {pro ? (
            <ul className="scroll-x -mx-4 mt-4 flex snap-x gap-3 px-4 sm:mx-0 sm:grid sm:grid-cols-2 sm:px-0 lg:grid-cols-3">
              {view.featured.map((m) => (
                <li key={m.id} className="w-[80%] shrink-0 snap-start sm:w-auto">
                  <Link href={`/app/partido/${encodeURIComponent(m.id)}`}
                    className="group block h-full rounded-xl border border-line bg-[var(--bg-raise)] p-4 transition-colors hover:border-[var(--border-glass)]">
                    <div className="flex items-center justify-between gap-2 text-[11px] text-lo">
                      <span className="truncate">{m.cn}</span>
                      <span className="num whitespace-nowrap">{dayLabel(m.ko, view.now)} · {time(m.ko)}</span>
                    </div>
                    <div className="mt-3 flex items-center gap-2">
                      <span className="flex -space-x-1.5">
                        <Crest src={crest(m.c, m.h)} sport={m.sport} name={m.h} size={26} className="ring-2 ring-[var(--bg-raise)]" />
                        <Crest src={crest(m.c, m.a)} sport={m.sport} name={m.a} size={26} className="ring-2 ring-[var(--bg-raise)]" />
                      </span>
                      <span className="min-w-0 truncate text-sm text-mid">{m.h} <span className="text-lo">vs</span> {m.a}</span>
                    </div>
                    <div className="mt-4 flex items-end justify-between gap-3">
                      <span className="text-[15px] leading-snug text-hi">{m.k!.l}</span>
                      <Prob p={m.k!.p!} className="text-3xl font-semibold leading-none" />
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-line p-4">
              <p className="text-sm text-mid">Hay <span className="num text-gold">{view.picks}</span> selecciones con 80% o más en estos partidos. Los picks se ven con tu cuenta gratis.</p>
              <Link href="/acceso" className="btn-gold px-4 py-2 text-sm">Crear cuenta gratis</Link>
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
              <section key={k} className="space-y-4">
                <h2 className="flex items-baseline gap-3">
                  <span className="font-display text-3xl text-hi">{dayLabel(ordered[0][1][0].ko, view.now)}</span>
                  <span className="num text-xs text-lo">{n} partido{n === 1 ? "" : "s"} · {ordered.length} liga{ordered.length === 1 ? "" : "s"}</span>
                </h2>
                {ordered.map(([cid, list]) => {
                  const ctry = leagueInfo(cid, list[0].sport).country;
                  const three = list.some((m) => m.o?.d != null);
                  return (
                    <div key={cid} className="overflow-hidden rounded-xl border border-line bg-[rgba(17,15,11,0.6)]">
                      <h3 className="flex items-center gap-2.5 border-b border-line bg-[rgba(237,230,214,0.025)] px-4 py-2.5 text-sm">
                        <SportIcon sport={list[0].sport} league={list[0].cn} className="h-4 w-4 shrink-0 text-gold" />
                        <Link href={go({ liga: cid })} scroll={false} className="truncate font-medium text-hi hover:text-gold">{list[0].cn}</Link>
                        {ctry && !list[0].cn.includes(ctry) && <span className="truncate text-lo">{ctry}</span>}
                        <span className="ml-auto hidden gap-0 sm:flex" aria-hidden>
                          {(three ? ["1", "X", "2"] : ["1", "2"]).map((x) => <span key={x} className="num w-14 text-center text-[11px] text-lo">{x}</span>)}
                        </span>
                      </h3>
                      <ul className="divide-y divide-[var(--border-soft)]">
                        {list.map((m) => <li key={m.id}><Row m={m} pro={pro} three={three} crest={crest} /></li>)}
                      </ul>
                    </div>
                  );
                })}
              </section>
            );
          })}
          {ver !== "todos" && view.matches.length > SHOW && (
            <button type="button" onClick={() => router.replace(go({ region: view.selLeague ? null : view.reg, liga: view.selLeague?.id, ver: "todos" }), { scroll: false })}
              className="block w-full rounded-xl border border-line p-4 text-center text-sm text-gold transition-colors hover:border-[var(--border-glass)]">
              Mostrar los {view.matches.length} partidos ({view.matches.length - SHOW} más)
            </button>
          )}
        </div>
      )}
    </div>
  );
}

/** One match as a scoreboard row: status | crests + teams | 1·X·2. */
function Row({ m, pro, three, crest }: { m: M; pro: boolean; three: boolean; crest: (c: string, t: string) => string | null | undefined }) {
  const finished = m.st === "finished";
  const live = m.st === "live";
  const n = m.k?.n ?? 0;
  const scored = m.hs !== null && m.as !== null;
  const cells = m.o ? (three ? [m.o.h, m.o.d ?? 0, m.o.a] : [m.o.h, m.o.a]) : null;
  const top = cells ? Math.max(...cells) : 0;
  const winH = finished && scored && m.hs! > m.as!, winA = finished && scored && m.as! > m.hs!;
  const cellsNode = cells ? (
        <div className="flex" aria-label={`Probabilidades: local ${Math.round(m.o!.h * 100)}%${three ? `, empate ${Math.round((m.o!.d ?? 0) * 100)}%` : ""}, visitante ${Math.round(m.o!.a * 100)}%`}>
          {cells.map((p, i) => (
            <span key={i} className={`num grid w-9 place-items-center rounded-md py-1.5 text-[13px] sm:w-14 ${p === top ? "font-semibold text-hi" : "text-lo"}`}
              style={p === top ? { background: `color-mix(in srgb, ${probColor(p)} 16%, transparent)`, color: probColor(p) } : undefined}>
              {Math.round(p * 100)}
            </span>
          ))}
        </div>
      ) : (
        <span className="text-[11px] text-lo">—</span>
      );
  return (
    <Link href={`/app/partido/${encodeURIComponent(m.id)}`} className="group grid grid-cols-[2.5rem_1fr_auto] items-center gap-x-2.5 gap-y-1.5 px-3 py-3 transition-colors hover:bg-[rgba(212,175,55,0.04)] sm:grid-cols-[3rem_1fr_auto] sm:gap-x-3 sm:px-4">
      <div className="num text-center text-[12px] leading-tight">
        {live ? <span className="font-semibold" style={{ color: "var(--neon-up)" }}>EN<br />VIVO</span>
          : finished ? <span className="text-lo">Final</span>
          : <span className="text-hi">{time(m.ko)}</span>}
      </div>

      <div className="min-w-0 space-y-1.5">
        {[[m.h, m.hs, winH], [m.a, m.as, winA]].map(([name, score, win], i) => (
          <div key={i} className="flex items-center gap-2.5">
            <Crest src={crest(m.c, name as string)} sport={m.sport} name={name as string} size={22} />
            <span className={`min-w-0 flex-1 truncate text-[15px] ${finished && !win ? "text-mid" : "text-hi"} ${win ? "font-semibold" : ""}`}>{name as string}</span>
            {scored && <span className={`num w-5 text-right text-[15px] ${win || live ? "text-hi" : "text-mid"}`}>{score as number}</span>}
          </div>
        ))}
      </div>
      {cellsNode}
      {!finished && n > 0 && (
          <div className="col-span-2 col-start-2 flex min-w-0 items-center gap-1.5 text-[12px]">
            {pro && m.k?.l && m.k.p ? (
              <>
                <span aria-hidden className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: probColor(m.k.p) }} />
                <span className="min-w-0 truncate text-mid">{m.k.l}</span>
                <Prob p={m.k.p} className="font-semibold" />
                {n > 1 && <span className="text-lo">+{n - 1}</span>}
              </>
            ) : (
              <span className="text-lo">{n} pick{n === 1 ? "" : "s"} de 80%+</span>
            )}
          </div>
        )}
    </Link>
  );
}

function Stat({ label, value, p, locked }: { label: string; value?: string; p?: number; locked?: boolean }) {
  return (
    <div className="flex flex-col gap-0.5 px-3 py-3 sm:flex-row sm:items-baseline sm:gap-2 sm:px-5">
      <dd className="order-1">
        {p !== undefined ? <Prob p={p} className="text-2xl font-semibold" /> : <span className="num text-2xl font-semibold text-hi">{value}</span>}
      </dd>
      <dt className="order-2 truncate text-[12px] text-lo">
        {label}{locked && <span className="ml-1.5 text-[10px] uppercase tracking-[0.14em] text-gold">con cuenta</span>}
      </dt>
    </div>
  );
}

function Tab({ href, active, children, count }: { href: string; active: boolean; children: React.ReactNode; count?: number }) {
  return (
    <Link href={href} scroll={false} aria-current={active ? "true" : undefined}
      className={`-mb-px whitespace-nowrap border-b-2 pb-2.5 transition-colors ${active ? "border-[var(--gold)] text-hi" : "border-transparent text-lo hover:text-hi"}`}>
      {children}
      {count !== undefined && <span className={`num ml-1.5 text-[11px] ${active ? "text-gold" : "text-lo"}`}>{count}</span>}
    </Link>
  );
}

function Chip({ href, active, children, count }: { href: string; active: boolean; children: React.ReactNode; count?: number }) {
  return (
    <Link href={href} scroll={false} aria-current={active ? "true" : undefined}
      className={`whitespace-nowrap rounded-full border px-3 py-1 text-[13px] transition-colors ${active ? "border-[var(--border-glass)] bg-[var(--gold-faint)] text-hi" : "border-line text-lo hover:text-hi"}`}>
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
