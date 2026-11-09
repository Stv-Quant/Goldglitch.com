import { Badge, ago, dt } from "@/components/admin/ui";
import { getDataHealth } from "@/lib/admin";

const STATUS: Record<string, string> = { scheduled: "Programados", live: "En vivo", finished: "Finalizados", postponed: "Aplazados", canceled: "Cancelados" };

export default async function DataPage() {
  const d = await getDataHealth();
  const last = d.batches[0];
  return (
    <div className="space-y-8">
      <div>
        <p className="num text-[11px] tracking-[0.22em] text-gold uppercase">SQPC → Goldglitch</p>
        <h1 className="display mt-2 text-[2.4rem]">Datos y modelo</h1>
        <p className="mt-2 max-w-2xl text-sm text-mid">
          Aquí ves lo que el motor SQPC ha publicado. Si algo falla, los usuarios lo notan primero en esta capa: partidos sin
          predicción o datos viejos.
        </p>
      </div>

      <div className="grid gap-3 grid-cols-2 xl:grid-cols-4">
        <Stat label="Última publicación" value={last ? ago(last.received_at) : "Nunca"} sub={last ? dt(last.received_at) : "SQPC aún no ha enviado datos"} bad={!last || Date.now() - last.received_at > 86_400_000} />
        <Stat label="Predicciones guardadas" value={(d.predictions.n ?? 0).toLocaleString("es-CO")} sub={d.predictions.last ? `última ${ago(d.predictions.last)}` : "—"} />
        <Stat label="Próximos sin predicción" value={String(d.missing.length)} sub="partidos en los próximos 7 días" bad={d.missing.length > 0} />
        <Stat label="Competiciones" value={String(d.competitions.length)} sub={d.matchStatus.map((m) => `${STATUS[m.status] ?? m.status} ${m.n}`).join(" · ") || "—"} />
      </div>

      <section>
        <h2 className="text-lg font-semibold">Próximos partidos sin predicción</h2>
        <p className="mt-1 text-xs text-lo">Las predicciones solo se aceptan antes del inicio (sello). Si un partido empieza sin predicción, se queda sin ella.</p>
        <ul className="card mt-3 divide-y divide-[var(--border-soft)] text-sm">
          {d.missing.map((m) => (
            <li key={m.id} className="flex flex-wrap justify-between gap-2 px-4 py-2.5">
              <span>{m.home} — {m.away} <span className="text-lo">· {m.comp}</span></span>
              <span className="num text-xs text-gold">{dt(m.kickoff_at)}</span>
            </li>
          ))}
          {!d.missing.length && <li className="px-4 py-4 text-mid"><span className="text-up mr-2">●</span>Todos los partidos próximos tienen predicción.</li>}
        </ul>
      </section>

      <section>
        <h2 className="text-lg font-semibold">Rendimiento publicado del modelo</h2>
        <p className="mt-1 text-xs text-lo">
          Brier: error cuadrático medio de las probabilidades (0 = perfecto, menor es mejor). Skill: mejora frente a la referencia
          ingenua. Log-loss: castiga la sobreconfianza. Es lo mismo que ve el público en /historial.
        </p>
        <div className="card mt-3 overflow-x-auto">
          <table className="w-full text-sm min-w-[720px]">
            <thead><tr className="text-left text-[11px] text-lo border-b border-line">
              <th className="px-4 py-2.5 font-normal">Modelo</th><th className="px-4 py-2.5 font-normal">Deporte</th><th className="px-4 py-2.5 font-normal text-right">N</th>
              <th className="px-4 py-2.5 font-normal text-right">Brier</th><th className="px-4 py-2.5 font-normal text-right">Referencia</th>
              <th className="px-4 py-2.5 font-normal text-right">Skill</th><th className="px-4 py-2.5 font-normal text-right">Log-loss</th><th className="px-4 py-2.5 font-normal">Publicado</th>
            </tr></thead>
            <tbody>
              {d.metrics.map((m) => {
                const skill = m.baseline_brier ? (m.baseline_brier - m.brier) / m.baseline_brier : null;
                return (
                  <tr key={m.id} className="border-t border-line num">
                    <td className="px-4 py-2.5">{m.model_version}</td>
                    <td className="px-4 py-2.5">{m.sport === "football" ? "Fútbol" : "MLB"}</td>
                    <td className="px-4 py-2.5 text-right">{m.n.toLocaleString("es-CO")}</td>
                    <td className="px-4 py-2.5 text-right">{m.brier.toFixed(3)}</td>
                    <td className="px-4 py-2.5 text-right text-lo">{m.baseline_brier?.toFixed(3) ?? "—"}</td>
                    <td className="px-4 py-2.5 text-right" style={{ color: skill === null ? undefined : skill > 0 ? "var(--neon-up)" : "var(--neon-down)" }}>{skill === null ? "—" : `${(skill * 100).toFixed(1)}%`}</td>
                    <td className="px-4 py-2.5 text-right">{m.log_loss.toFixed(3)}</td>
                    <td className="px-4 py-2.5 text-xs text-lo">{dt(m.generated_at)}</td>
                  </tr>
                );
              })}
              {!d.metrics.length && <tr><td colSpan={8} className="px-4 py-6 text-center text-lo">SQPC aún no ha publicado métricas.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>

      <div className="grid gap-8 xl:grid-cols-2">
        <section>
          <h2 className="text-lg font-semibold">Competiciones</h2>
          <ul className="card mt-3 divide-y divide-[var(--border-soft)] text-sm">
            {d.competitions.map((c) => (
              <li key={c.name} className="flex justify-between gap-2 px-4 py-2.5">
                <span>{c.name} <Badge>{c.sport === "football" ? "fútbol" : "MLB"}</Badge></span>
                <span className="num text-xs text-lo">{c.n} partidos · {c.upcoming} próximos</span>
              </li>
            ))}
            {!d.competitions.length && <li className="px-4 py-4 text-lo">Sin competiciones.</li>}
          </ul>
        </section>
        <section>
          <h2 className="text-lg font-semibold">Últimas publicaciones (lotes)</h2>
          <ul className="card mt-3 divide-y divide-[var(--border-soft)] text-sm">
            {d.batches.map((b) => (
              <li key={b.id} className="flex flex-wrap justify-between gap-2 px-4 py-2.5">
                <span className="num text-xs">{dt(b.received_at)} <span className="text-lo">· {b.source}</span></span>
                <span className="num text-xs text-lo">{b.records} registros</span>
              </li>
            ))}
            {!d.batches.length && <li className="px-4 py-4 text-lo">Sin lotes recibidos.</li>}
          </ul>
        </section>
      </div>
    </div>
  );
}

function Stat({ label, value, sub, bad }: { label: string; value: string; sub: string; bad?: boolean }) {
  return (
    <div className="card p-4 sm:p-5">
      <div className="text-xs text-lo">{label}</div>
      <div className="num mt-1 text-2xl font-semibold" style={{ color: bad ? "var(--neon-down)" : undefined }}>{value}</div>
      <div className="mt-0.5 text-[12px] text-mid">{sub}</div>
    </div>
  );
}
