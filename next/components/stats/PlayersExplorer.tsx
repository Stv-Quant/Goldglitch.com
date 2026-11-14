"use client";

import { useMemo, useState } from "react";
import type { PlayerRow } from "@/lib/contracts";
import { isHot, probColor } from "@/lib/probScale";

type Team = { name: string; short: string };
type Pos = "POR" | "DEF" | "MED" | "DEL";

function pos(role?: string): Pos {
  const r = (role ?? "").toUpperCase();
  if (r.startsWith("G")) return "POR";
  if ((r.startsWith("D") && r !== "DM") || ["CB", "LB", "RB", "WB", "LWB", "RWB"].includes(r)) return "DEF";
  if (r.startsWith("F") || ["ST", "CF", "LW", "RW", "W", "SS"].includes(r)) return "DEL";
  return "MED";
}
const POS_NAME: Record<Pos, string> = { POR: "Portero", DEF: "Defensa", MED: "Mediocampo", DEL: "Delantero" };

const CELL = "w-14 shrink-0 text-right";
const pctTxt = (p: number) => `${Math.round(p * 100)}%`;
const num = (n: number, d = 2) => n.toLocaleString("es-CO", { minimumFractionDigits: d, maximumFractionDigits: d });

/** Values used for sorting and the leader boards; undefined when SQPC did not publish it. */
const METRICS = {
  goal: { label: "Gol", kind: "p", get: (p: PlayerRow) => p.pScore },
  sot: { label: "Remate al arco", kind: "p", get: (p: PlayerRow) => p.probs?.sot1 },
  shots: { label: "Remates esperados", kind: "n", get: (p: PlayerRow) => p.exp?.shots },
  assist: { label: "Asistencia", kind: "p", get: (p: PlayerRow) => p.pAssist },
  card: { label: "Tarjeta", kind: "p", get: (p: PlayerRow) => p.probs?.card },
  fouled: { label: "Faltas recibidas", kind: "n", get: (p: PlayerRow) => p.exp?.fouled },
  fouls: { label: "Faltas cometidas", kind: "n", get: (p: PlayerRow) => p.exp?.fouls },
  saves: { label: "Atajadas", kind: "n", get: (p: PlayerRow) => (pos(p.role) === "POR" ? p.exp?.saves : undefined) },
  minutes: { label: "Minutos", kind: "n", get: (p: PlayerRow) => p.expectedMinutes },
} as const;
type MetricKey = keyof typeof METRICS;
const SORTS: MetricKey[] = ["goal", "sot", "shots", "assist", "card", "fouled", "fouls", "minutes"];
const LEADERS: MetricKey[] = ["goal", "sot", "shots", "card", "fouled", "saves"];

export function PlayersExplorer({ players, home, away }: { players: PlayerRow[]; home: Team; away: Team }) {
  const [side, setSide] = useState<"all" | "home" | "away">("all");
  const [position, setPosition] = useState<Pos | "all">("all");
  const [sort, setSort] = useState<MetricKey>("goal");
  const [open, setOpen] = useState<string | null>(null);
  const [all, setAll] = useState(false);

  const team = (p: PlayerRow) => (p.side === "home" ? home : away);
  const rival = (p: PlayerRow) => (p.side === "home" ? away : home);
  const id = (p: PlayerRow) => `${p.side}-${p.name}`;

  const rows = useMemo(() => {
    const m = METRICS[sort];
    return players
      .filter((p) => (side === "all" || p.side === side) && (position === "all" || pos(p.role) === position))
      .sort((a, b) => (m.get(b) ?? -1) - (m.get(a) ?? -1));
  }, [players, side, position, sort]);

  const shown = all ? rows : rows.slice(0, 14);
  const rich = players.some((p) => p.exp || p.probs);

  return (
    <div className="space-y-6">
      {rich && <Leaders players={players} team={team} />}

      <div className="flex flex-wrap items-center gap-2">
        <Segmented value={side} onChange={setSide}
          options={[["all", "Ambos"], ["home", home.short], ["away", away.short]]} />
        <Segmented value={position} onChange={setPosition}
          options={[["all", "Todos"], ["DEL", "DEL"], ["MED", "MED"], ["DEF", "DEF"], ["POR", "POR"]]} />
        <label className="ml-auto flex items-center gap-2 text-xs text-lo">
          Ordenar por
          <select value={sort} onChange={(e) => setSort(e.target.value as MetricKey)}
            className="rounded-lg border border-line bg-[var(--bg-raise)] px-2.5 py-1.5 text-sm text-hi outline-none">
            {SORTS.map((k) => <option key={k} value={k}>{METRICS[k].label}</option>)}
          </select>
        </label>
      </div>

      <div className="card overflow-hidden p-0">
        <div className="flex items-center gap-1 px-3 py-3 text-[11px] text-lo sm:px-4">
          <span className="min-w-0 flex-1">Jugador</span>
          <span className={`${CELL} hidden md:block`}>Titular</span>
          <span className={`${CELL} hidden sm:block`}>Min.</span>
          <span className={CELL}>Gol</span>
          <span className={CELL}>Al arco</span>
          <span className={`${CELL} hidden sm:block`}>Remates</span>
          <span className={`${CELL} hidden md:block`}>Asist.</span>
          <span className={`${CELL} hidden lg:block`}>Tarjeta</span>
          <span className="w-4 shrink-0" />
        </div>
        <ul>
          {shown.map((p) => {
            const isOpen = open === id(p);
            return (
              <li key={id(p)} className="border-t border-line">
                <button type="button" aria-expanded={isOpen} onClick={() => setOpen(isOpen ? null : id(p))}
                  className={`flex w-full items-center gap-1 px-3 py-2.5 text-left text-sm transition-colors hover:bg-[var(--gold-faint)] sm:px-4 ${isOpen ? "bg-[var(--gold-faint)]" : ""}`}>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-hi">{p.name}</span>
                    <span className="text-[11px] text-lo">{team(p).short} · {pos(p.role)}</span>
                  </span>
                  <span className={`${CELL} hidden md:block`}><P v={p.pStart} /></span>
                  <span className={`${CELL} hidden num text-mid sm:block`}>{p.expectedMinutes !== undefined ? Math.round(p.expectedMinutes) : "—"}</span>
                  <span className={CELL}><P v={p.pScore} bold /></span>
                  <span className={CELL}><P v={p.probs?.sot1} /></span>
                  <span className={`${CELL} hidden num text-mid sm:block`}>{p.exp?.shots !== undefined ? num(p.exp.shots, 1) : "—"}</span>
                  <span className={`${CELL} hidden md:block`}><P v={p.pAssist} /></span>
                  <span className={`${CELL} hidden lg:block`}><P v={p.probs?.card} /></span>
                  <span aria-hidden className={`w-4 shrink-0 text-center text-lo transition-transform ${isOpen ? "rotate-90 text-gold" : ""}`}>›</span>
                </button>
                {isOpen && (
                  <div className="border-t border-line bg-[var(--bg-void)]">
                    <PlayerCard p={p} team={team(p)} rival={rival(p)} />
                  </div>
                )}
              </li>
            );
          })}
        </ul>
        {!rows.length && <p className="p-6 text-sm text-lo">Ningún jugador con ese filtro.</p>}
        {rows.length > shown.length && (
          <button type="button" onClick={() => setAll(true)} className="w-full border-t border-line py-3 text-sm text-gold hover:bg-[var(--gold-faint)]">
            Ver los {rows.length} jugadores
          </button>
        )}
      </div>
      <p className="text-[11px] text-lo">Toca un jugador para ver su ficha completa. Probabilidades para este partido según SQPC; temporada y cara a cara con datos de partidos jugados.</p>
    </div>
  );
}

function P({ v, bold = false }: { v?: number; bold?: boolean }) {
  if (v === undefined) return <span className="num text-lo">—</span>;
  return <span className={`num ${bold ? "font-semibold" : ""} ${isHot(v) ? "p-glow" : ""}`} style={{ color: probColor(v) }}>{pctTxt(v)}</span>;
}

function Segmented<T extends string>({ value, onChange, options }: { value: T; onChange: (v: T) => void; options: [T, string][] }) {
  return (
    <div className="inline-flex rounded-lg border border-line p-0.5 text-xs">
      {options.map(([v, l]) => (
        <button key={v} type="button" aria-pressed={value === v} onClick={() => onChange(v)}
          className={`rounded-md px-2.5 py-1.5 transition-colors ${value === v ? "bg-[var(--gold-faint)] text-hi" : "text-lo hover:text-hi"}`}>
          {l}
        </button>
      ))}
    </div>
  );
}

/** Top three per headline stat, both teams together. */
function Leaders({ players, team }: { players: PlayerRow[]; team: (p: PlayerRow) => Team }) {
  const boards = LEADERS.map((k) => {
    const m = METRICS[k];
    const top = players
      .map((p) => ({ p, v: m.get(p) }))
      .filter((x): x is { p: PlayerRow; v: number } => x.v !== undefined && x.v > 0)
      .sort((a, b) => b.v - a.v)
      .slice(0, 3);
    return { k, m, top };
  }).filter((b) => b.top.length);
  if (!boards.length) return null;
  return (
    <section aria-labelledby="h-leaders">
      <h3 id="h-leaders" className="mb-3 text-sm text-mid">Líderes del partido</h3>
      <div className="scroll-x -mx-4 flex snap-x gap-3 px-4 sm:mx-0 sm:grid sm:grid-cols-2 sm:px-0 lg:grid-cols-3">
        {boards.map(({ k, m, top }) => (
          <div key={k} className="card w-[72%] shrink-0 snap-start p-4 sm:w-auto">
            <div className="text-[10px] uppercase tracking-[0.16em] text-lo">
              {m.kind === "p" ? `Prob. de ${m.label.toLowerCase()}` : m.label}
            </div>
            <ol className="mt-3 space-y-2.5">
              {top.map(({ p, v }, i) => (
                <li key={`${p.side}-${p.name}`} className="flex items-baseline justify-between gap-3">
                  <span className="min-w-0 truncate text-sm">
                    <span className="num mr-2 text-[11px] text-lo">{i + 1}</span>
                    <span className={i === 0 ? "text-hi" : "text-mid"}>{p.name}</span>
                    <span className="ml-1.5 text-[10px] text-lo">{team(p).short}</span>
                  </span>
                  {m.kind === "p"
                    ? <P v={v} bold={i === 0} />
                    : <span className={`num ${i === 0 ? "font-semibold text-gold" : "text-mid"}`}>{num(v, 1)}</span>}
                </li>
              ))}
            </ol>
          </div>
        ))}
      </div>
    </section>
  );
}

const MATCH_PROBS: { label: string; get: (p: PlayerRow) => number | undefined; gk?: boolean }[] = [
  { label: "Marca gol", get: (p) => p.pScore },
  { label: "2+ goles", get: (p) => p.probs?.goal2 },
  { label: "Asistencia", get: (p) => p.pAssist },
  { label: "1+ remate", get: (p) => p.probs?.shots1 },
  { label: "2+ remates", get: (p) => p.probs?.shots2 },
  { label: "3+ remates", get: (p) => p.probs?.shots3 },
  { label: "1+ al arco", get: (p) => p.probs?.sot1 },
  { label: "2+ al arco", get: (p) => p.probs?.sot2 },
  { label: "Comete falta", get: (p) => p.probs?.fouls1 },
  { label: "2+ faltas", get: (p) => p.probs?.fouls2 },
  { label: "Recibe falta", get: (p) => p.probs?.fouled1 },
  { label: "Tarjeta", get: (p) => p.probs?.card },
  { label: "Fuera de juego", get: (p) => p.probs?.offside1 },
  { label: "2+ atajadas", get: (p) => p.probs?.saves2, gk: true },
  { label: "3+ atajadas", get: (p) => p.probs?.saves3, gk: true },
  { label: "4+ atajadas", get: (p) => p.probs?.saves4, gk: true },
];

const EXP: { key: string; label: string }[] = [
  { key: "goals", label: "Goles" }, { key: "assists", label: "Asist." }, { key: "shots", label: "Remates" },
  { key: "sot", label: "Al arco" }, { key: "fouls", label: "Faltas" }, { key: "fouled", label: "Recibidas" },
  { key: "yellow", label: "Amarillas" }, { key: "offsides", label: "Offside" }, { key: "saves", label: "Atajadas" },
];

const SEASON: { key: keyof NonNullable<PlayerRow["season"]>; label: string; per90?: boolean }[] = [
  { key: "goals", label: "Goles", per90: true }, { key: "assists", label: "Asistencias", per90: true },
  { key: "shots", label: "Remates", per90: true }, { key: "sot", label: "Remates al arco", per90: true },
  { key: "fouls", label: "Faltas cometidas", per90: true }, { key: "fouled", label: "Faltas recibidas", per90: true },
  { key: "yellow", label: "Amarillas", per90: true }, { key: "offsides", label: "Fueras de juego", per90: true },
  { key: "saves", label: "Atajadas", per90: true },
];

/** Full player sheet: this match, season and head-to-head. */
function PlayerCard({ p, team, rival }: { p: PlayerRow; team: Team; rival: Team }) {
  const gk = pos(p.role) === "POR";
  const s = p.season;
  const probs = MATCH_PROBS.filter((x) => (!x.gk || gk) && x.get(p) !== undefined);
  const exps = EXP.filter((e) => p.exp?.[e.key] !== undefined && (e.key !== "saves" || gk));
  const seasonRows = SEASON.filter((r) => s?.[r.key] !== undefined && (r.key !== "saves" || gk));
  const mins = s?.minutes;
  const vs = p.vsOpp;

  return (
    <div className="min-w-0 space-y-6 p-4 sm:p-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="text-[11px] uppercase tracking-[0.16em] text-lo">{team.name} · {POS_NAME[pos(p.role)]}{p.role ? ` (${p.role})` : ""}</div>
          <div className="mt-1 text-xl font-semibold text-hi">{p.name}</div>
        </div>
        <div className="flex gap-5 sm:text-right">
          {p.pStart !== undefined && <Big label="Titular" v={<P v={p.pStart} bold />} />}
          {p.expectedMinutes !== undefined && <Big label="Minutos esperados" v={<span className="num text-hi">{Math.round(p.expectedMinutes)}</span>} />}
          {s?.apps !== undefined && <Big label="Partidos" v={<span className="num text-hi">{s.apps}{s.starts !== undefined ? <span className="text-xs text-lo"> ({s.starts} tit.)</span> : null}</span>} />}
        </div>
      </div>

      {probs.length > 0 && (
        <section>
          <h4 className="mb-2 text-[11px] uppercase tracking-[0.16em] text-lo">En este partido</h4>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-6">
            {probs.map((x) => {
              const v = x.get(p)!;
              return (
                <div key={x.label} className="rounded-[10px] border border-line px-3 py-2.5">
                  <div className="truncate text-[11px] text-lo">{x.label}</div>
                  <div className="mt-0.5 text-lg"><P v={v} bold /></div>
                  <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-[var(--seg-3)]">
                    <div className="h-full rounded-full" style={{ width: `${Math.max(2, v * 100)}%`, background: probColor(v) }} />
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {exps.length > 0 && (
        <section>
          <h4 className="mb-2 text-[11px] uppercase tracking-[0.16em] text-lo">Promedio esperado hoy</h4>
          <div className="scroll-x flex gap-2">
            {exps.map((e) => (
              <div key={e.key} className="min-w-[84px] flex-1 rounded-[10px] border border-line px-3 py-2">
                <div className="text-[11px] text-lo">{e.label}</div>
                <div className="num text-base text-hi">{num(p.exp![e.key], 2)}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {seasonRows.length > 0 && (
          <section>
            <h4 className="mb-2 text-[11px] uppercase tracking-[0.16em] text-lo">
              Temporada{mins ? <span className="normal-case tracking-normal"> · {mins.toLocaleString("es-CO")} min</span> : null}
            </h4>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-[11px] text-lo">
                  <th className="py-1.5 text-left font-normal">Estadística</th>
                  <th className="py-1.5 text-right font-normal">Total</th>
                  <th className="py-1.5 text-right font-normal">Por 90</th>
                  <th className="hidden py-1.5 text-right font-normal sm:table-cell">Por partido</th>
                </tr>
              </thead>
              <tbody>
                {seasonRows.map((r) => {
                  const v = s![r.key]!;
                  return (
                    <tr key={r.key} className="border-t border-line">
                      <td className="py-1.5 text-mid">{r.label}</td>
                      <td className="py-1.5 text-right num text-hi">{v}</td>
                      <td className="py-1.5 text-right num text-mid">{mins ? num((v / mins) * 90) : "—"}</td>
                      <td className="hidden py-1.5 text-right num text-mid sm:table-cell">{s?.apps ? num(v / s.apps) : "—"}</td>
                    </tr>
                  );
                })}
                {s?.shots ? (
                  <tr className="border-t border-line">
                    <td className="py-1.5 text-mid">Precisión de remate</td>
                    <td className="py-1.5 text-right num text-hi" colSpan={3}>{s.sot !== undefined ? `${Math.round((s.sot / s.shots) * 100)}% al arco` : "—"}{s.goals !== undefined ? ` · ${Math.round((s.goals / s.shots) * 100)}% gol` : ""}</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </section>
        )}

        <section>
          <h4 className="mb-2 text-[11px] uppercase tracking-[0.16em] text-lo">Contra {rival.name}</h4>
          {vs && vs.games > 0 ? (
            <>
              <div className="flex flex-wrap gap-x-5 gap-y-1 text-sm">
                <span className="text-mid"><span className="num text-hi">{vs.games}</span> partido{vs.games === 1 ? "" : "s"}</span>
                {vs.minutes !== undefined && <span className="text-mid"><span className="num text-hi">{vs.minutes}</span> min</span>}
                {vs.totals?.goals !== undefined && <span className="text-mid"><span className="num text-hi">{vs.totals.goals}</span> goles</span>}
                {vs.totals?.assists !== undefined && <span className="text-mid"><span className="num text-hi">{vs.totals.assists}</span> asist.</span>}
                {vs.totals?.shots !== undefined && <span className="text-mid"><span className="num text-hi">{vs.totals.shots}</span> remates</span>}
                {vs.totals?.sot !== undefined && <span className="text-mid"><span className="num text-hi">{vs.totals.sot}</span> al arco</span>}
              </div>
              {(vs.recent?.length ?? 0) > 0 && (
                <div className="mt-3 overflow-x-auto"><table className="w-full min-w-[360px] text-sm">
                  <thead>
                    <tr className="text-[11px] text-lo">
                      <th className="py-1.5 text-left font-normal">Fecha</th>
                      <th className="py-1.5 text-right font-normal">Min</th>
                      <th className="py-1.5 text-right font-normal">G</th>
                      <th className="py-1.5 text-right font-normal">A</th>
                      <th className="py-1.5 text-right font-normal">Rem.</th>
                      <th className="py-1.5 text-right font-normal">Arco</th>
                      <th className="py-1.5 text-right font-normal">Faltas</th>
                      <th className="py-1.5 text-right font-normal">TA</th>
                    </tr>
                  </thead>
                  <tbody>
                    {vs.recent!.map((g, i) => (
                      <tr key={`${g.date}-${i}`} className="border-t border-line num">
                        <td className="py-1.5 text-left text-mid">
                          {new Date(`${g.date}T12:00:00Z`).toLocaleDateString("es-CO", { day: "numeric", month: "short", year: "2-digit" })}
                          {g.starter === false && <span className="ml-1 text-[10px] text-lo">supl.</span>}
                        </td>
                        <td className="py-1.5 text-right text-mid">{g.minutes ?? "—"}</td>
                        <td className={`py-1.5 text-right ${g.goals ? "text-gold" : "text-mid"}`}>{g.goals ?? "—"}</td>
                        <td className="py-1.5 text-right text-mid">{g.assists ?? "—"}</td>
                        <td className="py-1.5 text-right text-mid">{g.shots ?? "—"}</td>
                        <td className="py-1.5 text-right text-mid">{g.sot ?? "—"}</td>
                        <td className="py-1.5 text-right text-mid">{g.fouls ?? "—"}</td>
                        <td className="py-1.5 text-right" style={g.yellow ? { color: "var(--p4)" } : undefined}>{g.yellow ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table></div>
              )}
            </>
          ) : (
            <p className="text-sm text-lo">Sin partidos registrados contra este rival.</p>
          )}
        </section>
      </div>
    </div>
  );
}

function Big({ label, v }: { label: string; v: React.ReactNode }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-[0.14em] text-lo">{label}</div>
      <div className="text-xl font-semibold">{v}</div>
    </div>
  );
}
