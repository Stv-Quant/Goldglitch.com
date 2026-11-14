import type { KindSummary, TrackedRow } from "@/lib/tracked";
import { dateLabel, pct } from "@/lib/format";
import { SPORT_LABEL } from "@/lib/sports";

const STATUS: Record<TrackedRow["status"], { mark: string; cls: string; text: string }> = {
  won: { mark: "✓", cls: "text-up", text: "Acertado" },
  lost: { mark: "✗", cls: "text-down", text: "Fallado" },
  void: { mark: "–", cls: "text-lo", text: "Nulo" },
  pending: { mark: "·", cls: "text-lo", text: "En juego" },
};

function Card({ label, value, hint, tone }: { label: string; value: string; hint?: string; tone?: "gold" | "up" | "down" }) {
  const cls = tone === "gold" ? "text-gold" : tone === "up" ? "text-up" : tone === "down" ? "text-down" : "";
  return (
    <div className="card p-5">
      <div className="text-xs text-lo">{label}</div>
      <div className={`num mt-1 text-2xl font-semibold ${cls}`}>{value}</div>
      {hint && <div className="text-[11px] text-lo mt-1">{hint}</div>}
    </div>
  );
}

/** Cumulative (hits − expected hits): flat around zero = the model hits as often as it says. */
function Drift({ curve }: { curve: KindSummary["curve"] }) {
  if (curve.length < 5) return null;
  const W = 640, H = 120, pad = 6;
  const lim = Math.max(3, ...curve.map((c) => Math.abs(c.diff)));
  const x = (i: number) => pad + (i / (curve.length - 1)) * (W - 2 * pad);
  const y = (v: number) => H / 2 - (v / lim) * (H / 2 - pad);
  const d = curve.map((c, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(c.diff).toFixed(1)}`).join(" ");
  const last = curve[curve.length - 1].diff;
  return (
    <div className="card p-5">
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="text-sm text-mid">Aciertos reales − aciertos esperados por el modelo (acumulado)</h3>
        <span className={`num text-sm ${last >= 0 ? "text-up" : "text-down"}`}>{last >= 0 ? "+" : ""}{last.toFixed(1)}</span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="mt-3 w-full block" role="img"
        aria-label="Diferencia acumulada entre aciertos reales y aciertos que esperaba el modelo">
        <line x1={pad} x2={W - pad} y1={H / 2} y2={H / 2} stroke="var(--text-lo)" strokeDasharray="4 4" />
        <path d={d} fill="none" stroke="var(--gold)" strokeWidth={1.6} />
      </svg>
      <p className="mt-2 text-[11px] text-lo">
        Sube cuando los aciertos superan lo que estimaba el modelo y baja cuando quedan por debajo. Si el modelo está bien calibrado, la línea oscila cerca de cero.
      </p>
    </div>
  );
}

function BucketTable({ title, rows, labelOf }: { title: string; rows: KindSummary["byBand"]; labelOf?: (k: string) => string }) {
  if (!rows.length) return null;
  return (
    <div className="card p-5">
      <h3 className="text-sm text-mid">{title}</h3>
      <table className="mt-3 w-full text-sm">
        <thead>
          <tr className="text-[11px] text-lo text-left">
            <th className="font-normal py-1"></th>
            <th className="font-normal py-1 text-right">Picks</th>
            <th className="font-normal py-1 text-right">Estimado</th>
            <th className="font-normal py-1 text-right">Real</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((b) => (
            <tr key={b.key} className="border-t border-line">
              <td className="py-1.5">{labelOf ? labelOf(b.key) : b.key}</td>
              <td className="py-1.5 text-right num">{b.won}/{b.n}</td>
              <td className="py-1.5 text-right num text-mid">{pct(b.expected, 1)}</td>
              <td className={`py-1.5 text-right num ${b.hitRate >= b.expected ? "text-up" : "text-down"}`}>{pct(b.hitRate, 1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function TrackRecord({ featured, value, rows }: { featured: KindSummary; value: KindSummary; rows: TrackedRow[] }) {
  const recent = rows.filter((r) => r.status !== "pending").slice(0, 40);
  if (!featured.settled && !value.settled) {
    return (
      <div className="card mt-8 p-8 text-mid">
        Todavía no hay picks liquidados. Cada pick de 75% o más se guarda antes del partido y aparece aquí, acertado o fallado, cuando termina.
      </div>
    );
  }
  const diff = featured.hitRate !== null && featured.expected !== null ? featured.hitRate - featured.expected : null;
  return (
    <div className="mt-8 space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card label="Picks acertados" value={featured.settled ? `${featured.won}/${featured.settled}` : "—"}
          hint={featured.void ? `${featured.void} nulos (aplazados o empujes) no cuentan` : "Picks de 75% o más ya liquidados"} tone="gold" />
        <Card label="Tasa de acierto" value={featured.hitRate !== null ? pct(featured.hitRate, 1) : "—"} hint="Lo que pasó" />
        <Card label="Probabilidad estimada (promedio)" value={featured.expected !== null ? pct(featured.expected, 1) : "—"}
          hint={diff !== null ? `${diff >= 0 ? "+" : ""}${(diff * 100).toFixed(1)} pts de acierto real frente a lo estimado` : "Lo que estimó el modelo"}
          tone={diff === null ? undefined : diff >= 0 ? "up" : "down"} />
        <Card label="Error de calibración" value={featured.brier !== null ? featured.brier.toFixed(3) : "—"} hint="Brier: más bajo es mejor (0 = perfecto)" />
      </div>

      <Drift curve={featured.curve} />

      <div className="grid gap-6 lg:grid-cols-3">
        <BucketTable title="Por rango de probabilidad" rows={featured.byBand} />
        <BucketTable title="Por deporte" rows={featured.bySport} labelOf={(k) => SPORT_LABEL[k as keyof typeof SPORT_LABEL] ?? k} />
        <BucketTable title="Por tipo de pick" rows={featured.byGroup.slice(0, 8)} />
      </div>

      {value.settled > 0 && (
        <div className="card p-5">
          <h3 className="text-sm text-mid">Apuestas de valor validadas (1X2, a la cuota publicada, stake 1)</h3>
          <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
            <div><div className="text-[11px] text-lo">Liquidadas</div><div className="num text-lg">{value.won}/{value.settled}</div></div>
            <div><div className="text-[11px] text-lo">Acierto real vs estimado</div>
              <div className="num text-lg">{value.hitRate !== null ? `${pct(value.hitRate, 1)} / ${pct(value.expected ?? 0, 1)}` : "—"}</div></div>
            <div><div className="text-[11px] text-lo">Ganancia</div>
              <div className={`num text-lg ${(value.profit ?? 0) >= 0 ? "text-up" : "text-down"}`}>
                {value.profit !== null ? `${value.profit >= 0 ? "+" : ""}${value.profit.toFixed(2)} u` : "—"}</div></div>
            <div><div className="text-[11px] text-lo">Rendimiento por apuesta</div>
              <div className={`num text-lg ${(value.roi ?? 0) >= 0 ? "text-up" : "text-down"}`}>
                {value.roi !== null ? `${value.roi >= 0 ? "+" : ""}${(value.roi * 100).toFixed(1)}%` : "—"}</div></div>
          </div>
          <p className="mt-3 text-[11px] text-lo">Con pocas apuestas el resultado es casi todo azar: cuenta después de varios cientos.</p>
        </div>
      )}

      {recent.length > 0 && (
        <div className="card p-5">
          <h3 className="text-sm text-mid">Últimos picks liquidados</h3>
          <ul className="mt-3 divide-y divide-[var(--border-soft)]">
            {recent.map((r) => {
              const s = STATUS[r.status];
              return (
                <li key={r.id} className="py-2.5 flex items-start gap-3">
                  <span className={`num w-5 text-center text-base leading-6 ${s.cls}`} aria-label={s.text}>{s.mark}</span>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm text-hi">
                      {r.label}
                      {r.kind === "value" && <span className="ml-2 text-[11px] text-gold">valor{r.price ? ` @ ${r.price.toFixed(2)}` : ""}</span>}
                    </div>
                    <div className="text-[11px] text-lo truncate">
                      {dateLabel(r.kickoffAt)} · {r.competition} · {r.home} vs {r.away}{r.result ? ` · ${r.result}` : ""}
                    </div>
                  </div>
                  <span className="num text-sm text-mid whitespace-nowrap">{pct(r.p, 0)}</span>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
