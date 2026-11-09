import Link from "next/link";
import { ViewAs } from "@/components/admin/AdminNav";
import { Badge, DailyBars, Metric, SectionTitle, STATUS_LABEL, STATUS_TONE, ago, dt, pctChange } from "@/components/admin/ui";
import { getOverview } from "@/lib/admin";
import { getViewer } from "@/lib/auth";
import { formatCOP } from "@/lib/plans";

const pct = (v: number | null) => (v === null ? "—" : `${(v * 100).toFixed(1)}%`);
const n = (v: number) => v.toLocaleString("es-CO");

export default async function AdminHome() {
  const [o, viewer] = await Promise.all([getOverview(), getViewer()]);
  const { users: u, subs: s, revenue: r, payments: p, data: d } = o;
  const coverage = d.upcoming7 ? d.upcomingWithPrediction / d.upcoming7 : null;
  const ingestAgeH = d.lastIngest ? (Date.now() - d.lastIngest.received_at) / 3_600_000 : null;
  const skill = d.model?.baseline_brier ? (d.model.baseline_brier - d.model.brier) / d.model.baseline_brier : null;

  return (
    <div className="space-y-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="num text-[11px] tracking-[0.22em] text-gold uppercase">Resumen</p>
          <h1 className="display mt-2 text-[2.4rem] sm:text-[3rem]">Cómo va Goldglitch</h1>
          <p className="mt-1 text-sm text-lo">Datos en vivo de la base de producción · actualizado {dt(o.generatedAt)} (hora Colombia)</p>
        </div>
        <div className="lg:hidden"><ViewAs current={viewer?.viewingAs ?? "elite"} /></div>
      </div>

      {/* Alerts: things that need action today */}
      <Alerts items={[
        s.expiring7 > 0 && { tone: "gold", text: `${s.expiring7} membresía(s) vencen en los próximos 7 días. No hay cobro automático: si no renuevan, pasan a Free.`, href: "/admin/usuarios?seg=expiring" },
        p.pending > 0 && { tone: "gold", text: `${p.pending} pago(s) pendientes de confirmación de Wompi (últimos 30 días).`, href: "/admin/pagos?status=PENDING" },
        ingestAgeH !== null && ingestAgeH > 24 && { tone: "down", text: `SQPC no publica datos hace ${Math.round(ingestAgeH)} h. Los usuarios ven partidos desactualizados.`, href: "/admin/datos" },
        !d.lastIngest && { tone: "down", text: "SQPC aún no ha publicado ningún lote de datos: la app no tiene partidos que mostrar.", href: "/admin/datos" },
        coverage !== null && coverage < 0.8 && { tone: "down", text: `Solo ${pct(coverage)} de los partidos de los próximos 7 días tienen predicción.`, href: "/admin/datos" },
      ]} />

      <section className="space-y-4">
        <SectionTitle title="Ingresos" />
        <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 xl:grid-cols-4">
          <Metric label="MRR (ingreso mensual recurrente)" value={formatCOP(r.mrr)} tone="gold"
            sub={`${s.paying} miembro(s) que pagan`}
            how="Suma, para cada membresía activa pagada, del valor de su último pago llevado a un mes: el plan mensual cuenta completo y el anual dividido entre 12. Las membresías otorgadas a mano no cuentan."
            why="Es el ingreso que el negocio genera cada mes si nadie entra ni sale. La métrica principal para medir crecimiento." />
          <Metric label="Cobrado últimos 30 días" value={formatCOP(r.last30)} sub={`${r.payments30} pago(s) aprobados`}
            delta={pctChange(r.last30, r.prev30) !== null ? { value: pctChange(r.last30, r.prev30)!, good: "up" } : null}
            how="Dinero efectivamente aprobado por Wompi en los últimos 30 días, incluidos planes anuales cobrados de una vez. La flecha compara con los 30 días anteriores."
            why="A diferencia del MRR, refleja caja real: un plan anual dispara este número el mes en que se paga." />
          <Metric label="ARPPU" value={formatCOP(r.arppu)} sub="por miembro que paga, al mes"
            how="MRR dividido entre el número de miembros que pagan (Average Revenue Per Paying User)."
            why="Si sube, la gente elige planes más altos (Elite) o anuales; si baja, predomina Pro mensual." />
          <Metric label="Ingresos históricos" value={formatCOP(r.allTime)} sub={`${r.paymentsAll} pago(s) aprobados en total`}
            how="Suma de todos los pagos aprobados desde el lanzamiento." />
        </div>
        <DailyBars data={o.series.revenue} money title="Cobrado por día" how="Cada barra suma los pagos aprobados ese día (hora Colombia). La barra dorada es el día con más ingresos." />
      </section>

      <section className="space-y-4">
        <SectionTitle title="Usuarios y membresías" />
        <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 xl:grid-cols-4">
          <Metric label="Usuarios registrados" value={n(u.total)} sub={`+${n(u.new7)} esta semana · +${n(u.new30)} en 30 días`}
            delta={pctChange(u.new30, u.newPrev30, 5) !== null ? { value: pctChange(u.new30, u.newPrev30, 5)!, good: "up" } : null}
            how="Cuentas creadas (por enlace o con contraseña). La flecha compara los registros de los últimos 30 días con los 30 anteriores." />
          <Metric label="Activos 7 días" value={n(u.active7)} sub={`${n(u.active30)} activos en 30 días`}
            how="Usuarios que iniciaron sesión al menos una vez en el periodo."
            why={`Activos 7d / registrados = ${pct(u.total ? u.active7 / u.total : null)}. Si es bajo, el producto no está creando hábito.`} />
          <Metric label="Membresías activas" value={n(s.active)} tone="gold" sub={`Pro ${s.pro} · Elite ${s.elite}${s.comps ? ` · ${s.comps} de cortesía` : ""}`}
            how="Cuentas con un plan pagado o otorgado cuya fecha de fin aún no ha pasado." />
          <Metric label="Conversión a pago" value={pct(o.conversion.rate)} sub={`${o.conversion.paidEver} de ${u.total} han pagado alguna vez`}
            how="Usuarios que tienen al menos un pago aprobado, divididos entre todos los registrados."
            why="Referencia de la industria para productos freemium: 2–5%. Por encima de eso, el plan gratis está haciendo bien su trabajo de vitrina." />
          <Metric label="Vencen en 7 días" value={n(s.expiring7)} tone={s.expiring7 ? "gold" : undefined}
            how="Membresías activas cuya fecha de fin cae en los próximos 7 días."
            why="No hay renovación automática: esta es tu lista de seguimiento para recordarles renovar." />
          <Metric label="Vencidas últimos 30 días" value={n(s.expired30)} tone={s.expired30 ? "down" : undefined}
            how="Membresías cuya fecha de fin pasó en los últimos 30 días y no se renovaron (churn)."
            why={`Churn aproximado del mes: ${pct(s.active + s.expired30 ? s.expired30 / (s.active + s.expired30) : null)} de las membresías que existían.`} />
          <Metric label="Tasa de aprobación de pagos" value={pct(p.approvalRate)} sub="últimos 30 días"
            how="Pagos aprobados dividido entre pagos que terminaron (aprobados + rechazados + anulados + error). Los pendientes no cuentan."
            why="Si cae por debajo de ~80%, revisa medios de pago o rechazos del banco en el panel de Wompi." />
          <Metric label="Cuentas suspendidas" value={n(u.suspended)} sub={`${u.admins} administrador(es)`}
            how="Cuentas bloqueadas manualmente desde este panel." />
        </div>
        <DailyBars data={o.series.signups} title="Registros por día" how="Cuentas nuevas creadas cada día (hora Colombia)." />
        <div className="card p-5">
          <SectionTitle title="Pagos de los últimos 30 días por estado" />
          <div className="mt-3 flex flex-wrap gap-2">
            {Object.keys(STATUS_LABEL).map((k) => (
              <Link key={k} href={`/admin/pagos?status=${k}`} className="inline-flex items-center gap-2 rounded-lg border border-line px-3 py-2 hover:border-[var(--border-glass)]">
                <Badge tone={STATUS_TONE[k]}>{STATUS_LABEL[k]}</Badge>
                <span className="num">{p.byStatus[k] ?? 0}</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <SectionTitle title="Datos y modelo"><Link href="/admin/datos" className="text-sm text-gold hover:underline underline-offset-4">Ver detalle →</Link></SectionTitle>
        <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 xl:grid-cols-4">
          <Metric label="Última publicación de SQPC" value={d.lastIngest ? ago(d.lastIngest.received_at) : "Nunca"}
            tone={ingestAgeH === null || ingestAgeH > 24 ? "down" : "up"}
            sub={d.lastIngest ? `${d.lastIngest.records} registros · ${d.lastIngest.source}` : "Sin datos todavía"}
            how="Momento en que el motor SQPC envió su último lote firmado a /api/ingest."
            why="Debería publicar varias veces al día. Más de 24 h sin datos = la app muestra información vieja." />
          <Metric label="Partidos próximos 7 días" value={n(d.upcoming7)} sub={`${n(d.upcomingWithPrediction)} con predicción`}
            how="Partidos programados con inicio en los próximos 7 días, en todas las ligas cubiertas." />
          <Metric label="Cobertura de predicciones" value={pct(coverage)} tone={coverage !== null && coverage < 0.8 ? "down" : coverage !== null ? "up" : undefined}
            how="Porcentaje de los partidos próximos que ya tienen predicción publicada."
            why="Debe acercarse a 100% antes de cada jornada; los partidos sin predicción se ven vacíos para los usuarios." />
          <Metric label="Brier skill del modelo" value={skill === null ? "—" : pct(skill)} tone={skill !== null ? (skill > 0 ? "up" : "down") : undefined}
            sub={d.model ? `Brier ${d.model.brier.toFixed(3)} · ${n(d.model.n)} pronósticos · ${d.model.model_version}` : "Sin métricas publicadas"}
            how="Mejora del Brier score del modelo frente a una referencia ingenua (frecuencias históricas). 0% = igual a la referencia; positivo = mejor."
            why="Es la prueba pública de que el modelo aporta. Si se vuelve negativo, hay que revisar el modelo antes de seguir vendiendo." />
        </div>
      </section>
    </div>
  );
}

function Alerts({ items }: { items: (false | null | { tone: "gold" | "down"; text: string; href: string })[] }) {
  const list = items.filter(Boolean) as { tone: "gold" | "down"; text: string; href: string }[];
  if (!list.length) {
    return <div className="card p-4 text-sm text-mid"><span className="text-up mr-2">●</span>Todo en orden: no hay alertas.</div>;
  }
  return (
    <ul className="space-y-2" aria-label="Alertas">
      {list.map((a) => (
        <li key={a.text}>
          <Link href={a.href} className="card flex items-start gap-3 p-4 text-sm hover:border-[var(--border-glass)]"
            style={{ borderColor: a.tone === "down" ? "rgba(255,90,60,.35)" : "var(--border-glass)" }}>
            <span style={{ color: a.tone === "down" ? "var(--neon-down)" : "var(--gold)" }}>{a.tone === "down" ? "▲" : "●"}</span>
            <span className="flex-1 text-mid">{a.text}</span>
            <span className="text-lo">→</span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
