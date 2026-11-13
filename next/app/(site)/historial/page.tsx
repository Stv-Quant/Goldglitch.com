import type { Metadata } from "next";
import { CalibrationChart } from "@/components/stats/CalibrationChart";
import { TrackRecord } from "@/components/stats/TrackRecord";
import { latestMetrics } from "@/lib/data";
import { getDB } from "@/lib/env";
import { summarize, trackedPicks } from "@/lib/tracked";
import { dateLabel } from "@/lib/format";
import { SPORT_LABEL } from "@/lib/sports";

export const metadata: Metadata = {
  title: "Historial del modelo",
  description: "Cada pick del sistema, acertado o fallado, y la calibración del modelo sobre partidos ya jugados. Auditable y público.",
};
export const dynamic = "force-dynamic";

export default async function HistorialPage() {
  const metrics = await latestMetrics().catch(() => []);
  const m = metrics[0];
  const rows = await getDB()
    .then((db) => trackedPicks(db, 365))
    .catch(() => []);
  const featured = summarize(rows, "featured");
  const value = summarize(rows, "value");

  return (
    <section className="mx-auto max-w-6xl px-4 sm:px-6 py-16">
      <p className="eyebrow">Historial público</p>
      <h1 className="mt-3 text-3xl sm:text-4xl font-semibold tracking-tight">¿Cuando decimos 60%, pasa el 60% de las veces?</h1>
      <p className="mt-3 text-mid max-w-2xl leading-relaxed">
        Esa es la única pregunta que importa. Aquí medimos al modelo contra partidos que ya se jugaron y que nunca vio
        al entrenar. Si se equivoca, se ve.
      </p>

      <div className="mt-12">
        <p className="eyebrow">Seguimiento de picks</p>
        <h2 className="mt-2 text-2xl font-semibold tracking-tight">Cada pick que el sistema escoge, acertado o fallado</h2>
        <p className="mt-2 text-mid max-w-3xl text-sm leading-relaxed">
          El pick destacado de cada partido (la selección más probable del modelo, 80% o más) queda guardado antes de que
          empiece y se liquida con el resultado real. No se borra ni se edita nada después del inicio. Un pick de 85% debe
          fallar más o menos 15 de cada 100 veces: lo que importa es que la tasa real se parezca a la prometida.
        </p>
        <TrackRecord featured={featured} value={value} rows={rows} />
      </div>

      <h2 className="mt-16 text-2xl font-semibold tracking-tight">Calibración del modelo (1X2)</h2>
      {!m ? (
        <div className="card mt-10 p-8 text-mid">El primer reporte de rendimiento se publica cuando el modelo acumule suficientes partidos evaluados.</div>
      ) : (
        <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_1.1fr]">
          <div className="card p-6">
            <h2 className="text-sm text-mid">Calibración · {SPORT_LABEL[m.sport]}</h2>
            <div className="mt-4">
              <CalibrationChart bins={m.calibration} />
            </div>
            <p className="mt-3 text-xs text-lo">
              Cada punto agrupa pronósticos similares. Sobre la diagonal punteada = calibración perfecta. El tamaño indica cuántos casos hay.
            </p>
          </div>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Stat label="Brier score" value={m.brier.toFixed(3)} hint="Menor es mejor" accent />
              <Stat
                label="Referencia ingenua"
                value={m.baselineBrier !== undefined ? m.baselineBrier.toFixed(3) : "—"}
                hint="Frecuencias históricas"
              />
              <Stat label="Log-loss" value={m.logLoss.toFixed(3)} hint="Castiga la sobreconfianza" />
              <Stat label="Pronósticos evaluados" value={m.n.toLocaleString("es-CO")} hint={`${dateLabel(m.windowStart)} – ${dateLabel(m.windowEnd)}`} />
            </div>
            {m.baselineBrier !== undefined && (
              <div className="card p-5">
                <p className="text-sm text-mid leading-relaxed">
                  El modelo mejora a la referencia ingenua en{" "}
                  <span className="num text-gold font-semibold">
                    {(((m.baselineBrier - m.brier) / m.baselineBrier) * 100).toFixed(1)}%
                  </span>{" "}
                  (Brier skill score). Una referencia ingenua predice siempre las frecuencias históricas de local, empate y visita.
                </p>
              </div>
            )}
            <div className="card p-5 text-sm text-mid leading-relaxed">
              <h3 className="text-hi font-medium">Qué significa</h3>
              <p className="mt-2">
                El Brier score mide la distancia entre la probabilidad pronosticada y lo que ocurrió (0 = perfecto). El log-loss
                penaliza fuerte cuando el modelo se muestra muy seguro y falla. Ningún modelo acierta siempre; uno honesto
                acierta en la proporción que dice.
              </p>
              <p className="mt-3 text-xs text-lo num">Modelo {m.modelVersion}</p>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

function Stat({ label, value, hint, accent }: { label: string; value: string; hint: string; accent?: boolean }) {
  return (
    <div className="card p-5">
      <div className="text-xs text-lo">{label}</div>
      <div className={`num mt-1 text-2xl font-semibold ${accent ? "text-gold" : ""}`}>{value}</div>
      <div className="text-[11px] text-lo mt-1">{hint}</div>
    </div>
  );
}
