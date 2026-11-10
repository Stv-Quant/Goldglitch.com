import Link from "next/link";
import { notFound } from "next/navigation";
import { EdgeTable } from "@/components/stats/EdgeTable";
import { FeatureCompare } from "@/components/stats/FeatureCompare";
import { LockedPanel } from "@/components/stats/LockedPanel";
import { ProbabilityBar } from "@/components/stats/ProbabilityBar";
import { ScoreMatrix } from "@/components/stats/ScoreMatrix";
import { getTier } from "@/lib/auth";
import { getMatch } from "@/lib/data";
import { dayLabel, pct, timeLabel } from "@/lib/format";
import { SPORT_LABEL } from "@/lib/sports";

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
            <section className="card p-5 sm:p-6" aria-labelledby="h-mk">
              <h2 id="h-mk" className="text-sm text-mid mb-4">Mercados</h2>
              <ul className="space-y-4">
                {p.markets!.map((mk) => (
                  <li key={mk.key}>
                    <div className="flex items-baseline justify-between text-sm">
                      <span>{mk.label}</span>
                      <span className="num">
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
