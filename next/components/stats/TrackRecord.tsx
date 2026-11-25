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
            <th className="font-normal py-1 text-right">Real</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((b) => (
            <tr key={b.key} className="border-t border-line">
              <td className="py-1.5">{labelOf ? labelOf(b.key) : b.key}</td>
              <td className="py-1.5 text-right num">{b.won}/{b.n}</td>
              <td className="py-1.5 text-right num text-hi">{pct(b.hitRate, 1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function TrackRecord({ featured, value, rows }: { featured: KindSummary; value: KindSummary; rows: TrackedRow[] }) {
  const recent = rows.filter((r) => r.status !== "pending" && r.kind === "featured").slice(0, 40);
  if (!featured.settled) {
    return (
      <div className="card mt-8 p-8 text-mid">
        Todavía no hay picks liquidados. Cada pick de 80% o más se guarda antes del partido y aparece aquí, acertado o fallado, cuando termina.
      </div>
    );
  }
  return (
    <div className="mt-8 space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <Card label="Picks acertados" value={featured.settled ? `${featured.won}/${featured.settled}` : "—"}
          hint={featured.void ? `${featured.void} nulos (aplazados o empujes) no cuentan` : "Picks de 80% o más ya liquidados"} tone="gold" />
        <Card label="Tasa de acierto" value={featured.hitRate !== null ? pct(featured.hitRate, 1) : "—"} hint="Lo que pasó" />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <BucketTable title="Por rango de probabilidad" rows={featured.byBand} />
        <BucketTable title="Por deporte" rows={featured.bySport} labelOf={(k) => SPORT_LABEL[k as keyof typeof SPORT_LABEL] ?? k} />
        <BucketTable title="Por tipo de pick" rows={featured.byGroup.slice(0, 8)} />
      </div>

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
