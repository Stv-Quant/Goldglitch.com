import Link from "next/link";
import { notFound } from "next/navigation";
import { EdgeTable } from "@/components/stats/EdgeTable";
import { FeatureCompare } from "@/components/stats/FeatureCompare";
import { LockedPanel } from "@/components/stats/LockedPanel";
import { ProbabilityBar } from "@/components/stats/ProbabilityBar";
import { ScoreMatrix } from "@/components/stats/ScoreMatrix";
import { StatLines } from "@/components/stats/StatLines";
import { getTier } from "@/lib/auth";
import { getMatch } from "@/lib/data";
import { dayLabel, pct, timeLabel } from "@/lib/format";
import { SPORT_LABEL } from "@/lib/sports";
import { PICK_FEATURED, PICK_MIN } from "@/lib/picks";

export const dynamic = "force-dynamic";

export default async function MatchPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const tier = await getTier();
  const m = await getMatch(decodeURIComponent(id), tier);
  if (!m) notFound();
  if ("locked" in m) {
    return (
      <div className="max-w-xl">
        <LockedPanel tier="Elite" title={`${SPORT_LABEL[m.sport]} es parte de Elite`}>
          {`El modelo completo de ${SPORT_LABEL[m.sport].toLowerCase()} (probabilidades, marcadores esperados y valor frente al mercado) está disponible en el plan Elite.`}
        </LockedPanel>
      </div>
    );
  }

  const p = m.prediction;

  return (
    <article className="space-y-6">
      <Link href="/app" className="text-sm text-lo hover:text-hi">← Partidos</Link>

      {/* Header: the first fixation is the favorite's probability inside the bar */}
      <header className="glass p-5 sm:p-7">
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-lo">
          <span>{m.competition.name}{m.venue ? ` · ${m.venue}` : ""}</span>
          <span className="num">{dayLabel(m.kickoffAt)} · {timeLabel(m.kickoffAt)}</span>
        </div>
        <div className="mt-5 grid grid-cols-[1fr_auto_1fr] items-center gap-4">
          <h1 className="text-xl sm:text-2xl font-semibold truncate">{m.home.name}</h1>
          <span className="num text-lo">
            {m.homeScore !== null && m.awayScore !== null ? `${m.homeScore} – ${m.awayScore}` : "vs"}
          </span>
          <p className="text-xl sm:text-2xl font-semibold truncate text-right">{m.away.name}</p>
        </div>
        {p ? (
          <div className="mt-6">
            <ProbabilityBar home={p.outcome.home} draw={p.outcome.draw} away={p.outcome.away}
              labels={{ home: m.home.short, away: m.away.short }} interval={p.interval} />
            <p className="mt-4 text-[11px] text-lo num">
              Modelo {p.modelVersion} · actualizado {timeLabel(p.generatedAt)}
              {p.locked.pro && " · el rango de incertidumbre es parte de Pro"}
            </p>
          </div>
        ) : (
          <p className="mt-6 text-sm text-lo">El modelo aún no publica este partido.</p>
        )}
      </header>

      {p && m.status !== "finished" && (m.picks.length > 0 || m.picksLocked > 0) && (
        <section className="card p-5 sm:p-6 border-[var(--border-glass)]" aria-labelledby="h-picks"
          style={{ background: "linear-gradient(180deg, rgba(212,175,55,0.07), transparent 60%)" }}>
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h2 id="h-picks" className="text-sm text-gold">Picks del modelo · {Math.round(PICK_MIN * 100)}% o más</h2>
            <p className="text-[11px] text-lo">Probabilidad, no certeza: un 80% falla 1 de cada 5 veces.</p>
          </div>
          {m.picks.length > 0 ? (
            <ul className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {m.picks.map((k) => (
                <li key={k.key} className="rounded-[12px] border p-4"
                  style={{ borderColor: k.p >= PICK_FEATURED ? "var(--gold)" : "var(--border-glass)" }}>
                  <div className="flex items-center justify-between gap-2 text-[10px] uppercase tracking-[0.16em] text-lo">
                    <span>{k.source}</span>
                    {k.p >= PICK_FEATURED && <span className="text-gold">Destacado</span>}
                  </div>
                  <div className="mt-2 text-hi">{k.label}</div>
                  <div className="mt-1 flex items-baseline justify-between">
                    <span className="num text-2xl font-semibold text-gold">{Math.round(k.p * 100)}%</span>
                    <span className="num text-[11px] text-lo">cuota justa {(1 / k.p).toFixed(2)}</span>
                  </div>
                  {(k.lo != null && k.hi != null) || k.price ? (
                    <div className="mt-1 flex justify-between gap-2 num text-[11px] text-lo">
                      <span>{k.lo != null && k.hi != null ? `rango ${Math.round(k.lo * 100)}–${Math.round(k.hi * 100)}%` : ""}</span>
                      <span>{k.price ? `${k.book ?? "casa"} ${k.price.toFixed(2)}` : ""}</span>
                    </div>
                  ) : null}
                </li>
              ))}
            </ul>
          ) : (
            <div className="mt-4">
              <LockedPanel tier="Pro" title={`${m.picksLocked} pick${m.picksLocked === 1 ? "" : "s"} del modelo en este partido`}>
                {"Las selecciones con 75% o más de probabilidad según el modelo, con su cuota justa."}
              </LockedPanel>
            </div>
          )}
        </section>
      )}

      {p && (p.lines.length > 0 || p.linesLocked > 0) && (
        <section className="card p-5 sm:p-6" aria-labelledby="h-lines">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h2 id="h-lines" className="text-sm text-mid">Estadísticas del partido</h2>
            <p className="text-[11px] text-lo">Mueve la línea de 0.5 en 0.5. Por defecto: la línea con el lado más probable (≥65%).</p>
          </div>
          {p.lines.length > 0 && <div className="mt-4"><StatLines lines={p.lines} /></div>}
          {p.linesLocked > 0 && (
            <div className="mt-4">
              <LockedPanel tier="Pro" title={`${p.linesLocked} estadísticas más con Pro`}>
                {"Goles por equipo, remates, remates al arco, faltas, tarjetas, fueras de juego y jugadores, cada una con su línea ajustable."}
              </LockedPanel>
            </div>
          )}
        </section>
      )}

      {p && (
        <div className="grid gap-6 lg:grid-cols-2">
          <section className="card p-5 sm:p-6" aria-labelledby="h-form">
            <h2 id="h-form" className="text-sm text-mid mb-4">Comparativa estadística</h2>
            {p.features.length ? (
              <FeatureCompare rows={p.features} homeShort={m.home.short} awayShort={m.away.short} />
            ) : (
              <p className="text-sm text-lo">Sin estadísticas descriptivas para este partido.</p>
            )}
          </section>

          {p.locked.pro ? (
            <LockedPanel tier="Pro" title={m.sport === "football" ? "Goles esperados y marcadores" : "Mercados y rangos"}>
              {m.sport === "football"
                ? "xG de cada equipo, la probabilidad de cada marcador exacto, mercados de goles y el desglose por jugador."
                : "Rango de incertidumbre, hándicap, totales y el resto de mercados que calcula el modelo."}
            </LockedPanel>
          ) : !p.xg && !p.scoreMatrix ? null : (
            <section className="card p-5 sm:p-6" aria-labelledby="h-goals">
              <h2 id="h-goals" className="text-sm text-mid">Goles esperados</h2>
              {p.xg && (
                <div className="mt-3 grid grid-cols-2 gap-3">
                  <XG label={m.home.short} v={p.xg.home} lead={p.xg.home >= p.xg.away} />
                  <XG label={m.away.short} v={p.xg.away} lead={p.xg.away > p.xg.home} />
                </div>
              )}
              {p.scoreMatrix && (
                <div className="mt-6">
                  <ScoreMatrix matrix={p.scoreMatrix} homeLabel={m.home.short} awayLabel={m.away.short} />
                </div>
              )}
            </section>
          )}

          {!p.locked.pro && (p.markets?.length ?? 0) > 0 && (
            <section className="card p-5 sm:p-6 lg:col-span-2" aria-labelledby="h-mk">
              <h2 id="h-mk" className="text-sm text-mid mb-4">Mercados</h2>
              <div className="grid gap-x-8 gap-y-6 md:grid-cols-2 xl:grid-cols-3">
                {Array.from(Map.groupBy(p.markets!, (mk) => mk.group ?? "Otros")).map(([g, rows]) => (
                  <div key={g}>
                    <h3 className="mb-2 text-[11px] uppercase tracking-[0.16em] text-lo">{g}</h3>
                    <ul className="space-y-3">
                      {rows.map((mk) => (
                        <li key={mk.key} className={mk.p >= PICK_MIN ? "-mx-2 rounded-lg border border-[var(--border-glass)] bg-[var(--gold-faint)] px-2 py-1.5" : undefined}>
                          <div className="flex items-baseline justify-between gap-2 text-sm">
                            <span className="min-w-0">{mk.label}{mk.p >= PICK_MIN && <span className="ml-2 rounded border border-[var(--gold)] px-1.5 py-px text-[10px] uppercase tracking-[0.14em] text-gold">Pick</span>}</span>
                            <span className="num whitespace-nowrap">
                              {pct(mk.p)}
                              {mk.interval && <span className="text-lo text-xs ml-1">[{pct(mk.interval[0])}–{pct(mk.interval[1])}]</span>}
                            </span>
                          </div>
                          <div className="relative mt-1.5 h-1.5 rounded-full bg-[var(--seg-3)]">
                            {mk.interval && (
                              <div className="absolute inset-y-0 rounded-full bg-[var(--seg-2)]"
                                style={{ left: `${mk.interval[0] * 100}%`, width: `${(mk.interval[1] - mk.interval[0]) * 100}%` }} />
                            )}
                            <div className="absolute -top-0.5 h-2.5 w-0.5 rounded bg-[var(--text-hi)]" style={{ left: `calc(${mk.p * 100}% - 1px)` }} />
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </section>
          )}

          {!p.locked.pro && (p.players?.length ?? 0) > 0 && (
            <section className="card p-5 sm:p-6" aria-labelledby="h-pl">
              <h2 id="h-pl" className="text-sm text-mid mb-3">Jugadores</h2>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-[11px] text-lo">
                    <th className="py-2 font-normal">Jugador</th>
                    <th className="py-2 font-normal text-right">Min. esp.</th>
                    <th className="py-2 font-normal text-right">P(gol)</th>
                    <th className="py-2 font-normal text-right">P(asist.)</th>
                    <th className="py-2 font-normal text-right hidden sm:table-cell">PJ</th>
                    <th className="py-2 font-normal text-right hidden sm:table-cell">Goles</th>
                    <th className="py-2 font-normal text-right hidden sm:table-cell">Asist.</th>
                    <th className="py-2 font-normal text-right hidden md:table-cell">Remates</th>
                  </tr>
                </thead>
                <tbody>
                  {p.players!.map((pl) => (
                    <tr key={`${pl.side}-${pl.name}`} className="border-t border-line">
                      <td className="py-2.5">
                        {pl.name}
                        <span className="text-[11px] text-lo ml-1.5">{pl.side === "home" ? m.home.short : m.away.short}{pl.role ? ` · ${pl.role}` : ""}</span>
                      </td>
                      <td className="py-2.5 text-right num text-mid">{pl.expectedMinutes ?? "—"}</td>
                      <td className="py-2.5 text-right num">{pl.pScore !== undefined ? pct(pl.pScore) : "—"}</td>
                      <td className="py-2.5 text-right num text-mid">{pl.pAssist !== undefined ? pct(pl.pAssist) : "—"}</td>
                      <td className="py-2.5 text-right num text-lo hidden sm:table-cell">{pl.season?.apps ?? "—"}</td>
                      <td className="py-2.5 text-right num hidden sm:table-cell">{pl.season?.goals ?? "—"}</td>
                      <td className="py-2.5 text-right num text-mid hidden sm:table-cell">{pl.season?.assists ?? "—"}</td>
                      <td className="py-2.5 text-right num text-mid hidden md:table-cell">{pl.season?.shots ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}

          <div className="lg:col-span-2">
            {p.locked.elite ? (
              <LockedPanel tier="Elite" title="Modelo contra mercado">
                Compara la probabilidad del modelo con las cuotas de las casas y ve dónde difieren, con el valor esperado calculado.
              </LockedPanel>
            ) : (
              <section className="card p-5 sm:p-6" aria-labelledby="h-ev">
                <h2 id="h-ev" className="text-sm text-mid mb-3">Modelo contra mercado</h2>
                <EdgeTable edges={p.edges ?? []} />
              </section>
            )}
          </div>
        </div>
      )}
    </article>
  );
}

function XG({ label, v, lead }: { label: string; v: number; lead: boolean }) {
  return (
    <div className="rounded-[10px] border border-line px-4 py-3">
      <div className="text-[11px] text-lo">xG {label}</div>
      <div className={`num text-2xl font-semibold ${lead ? "text-gold" : ""}`}>{v.toFixed(2)}</div>
    </div>
  );
}
