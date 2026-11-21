import { Metric } from "@/components/admin/ui";
import { Heatmap } from "@/components/admin/Heatmap";
import { analyticsReport, heatmapPaths } from "@/lib/analyticsReport";

export const dynamic = "force-dynamic";

const flag = (cc: string) => (/^[A-Z]{2}$/.test(cc) && cc !== "XX" ? String.fromCodePoint(...[...cc].map((c) => 0x1f1a5 + c.charCodeAt(0))) : "🌐");
const NAMES = new Intl.DisplayNames(["es"], { type: "region" });
const country = (cc: string) => { try { return cc === "XX" ? "Desconocido" : NAMES.of(cc) ?? cc; } catch { return cc; } };
const n = (v: number | null | undefined) => (v == null ? "—" : v.toLocaleString("es-CO"));
const DEV = { mobile: "Celular", tablet: "Tablet", desktop: "Computador" } as Record<string, string>;

export default async function AnalyticsPage({ searchParams }: { searchParams: Promise<{ dias?: string }> }) {
  const days = Math.max(1, Math.min(Number((await searchParams).dias) || 30, 90));
  const [r, paths] = await Promise.all([analyticsReport(days), heatmapPaths(days)]);
  const visits = r.countries.reduce((a, c) => a + c.visits, 0);
  const bounce = visits ? Math.round((r.countries.reduce((a, c) => a + (c.bouncePct ?? 0) * c.visits, 0) / visits) * 10) / 10 : null;
  const views = r.pages.reduce((a, p) => a + p.views, 0);
  const engaged = views ? Math.round(r.pages.reduce((a, p) => a + (p.avgEngagedSec ?? 0) * p.views, 0) / views) : null;
  const signups = r.countries.reduce((a, c) => a + c.signups, 0) + r.signupCountriesWithoutVisits.reduce((a, s) => a + Number(s.n), 0);
  const maxV = Math.max(1, ...r.countries.map((c) => c.visits));
  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="num text-[11px] tracking-[0.22em] text-gold uppercase">Analítica propia</p>
          <h1 className="display mt-2 text-[2.4rem]">Países, páginas y mapas de calor</h1>
          <p className="mt-2 max-w-2xl text-sm text-mid">{r.notes}</p>
        </div>
        <div className="flex gap-2 text-sm">
          {[1, 7, 30, 90].map((d) => (
            <a key={d} href={`?dias=${d}`} className={`rounded-lg px-3 py-2 border ${d === days ? "border-[var(--gold)] text-hi" : "border-line text-lo"}`}>{d === 1 ? "Hoy" : `${d} d`}</a>
          ))}
        </div>
      </div>

      <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 xl:grid-cols-4">
        <Metric label="Sesiones" value={n(visits)} sub={`${r.countries.length} países`} how="Una sesión = una visita de hasta 30 minutos de actividad." />
        <Metric label="Rebote" value={bounce == null ? "—" : `${bounce}%`} how="Sesiones que vieron una sola página." why="Si es alto en un canal o país, el mensaje de entrada no coincide con lo que encuentran." tone={bounce != null && bounce > 70 ? "down" : undefined} />
        <Metric label="Tiempo por página" value={engaged == null ? "—" : `${engaged} s`} sub={`${n(views)} páginas vistas`} how="Tiempo con la página visible (pestaña al frente), promedio por vista." />
        <Metric label="Cuentas creadas" value={n(signups)} sub={visits ? `${Math.round((signups / visits) * 1000) / 10}% de las sesiones` : undefined} how="Cuentas nuevas en el periodo; el país es el del registro." tone="gold" />
      </div>

      <section className="card p-4 sm:p-5 overflow-x-auto">
        <h2 className="text-lg font-semibold">Por país</h2>
        <table className="mt-3 w-full text-sm">
          <thead className="text-xs text-lo text-left"><tr><th className="py-1">País</th><th>Sesiones</th><th className="w-[30%]"></th><th>Rebote</th><th>Cuentas</th><th>Visita→cuenta</th><th>Compradores</th><th>Ingresos</th></tr></thead>
          <tbody>
            {r.countries.map((c) => (
              <tr key={String(c.country)} className="border-t border-line">
                <td className="py-1.5 whitespace-nowrap">{flag(String(c.country))} {country(String(c.country))}</td>
                <td className="num">{n(c.visits)}</td>
                <td><div className="h-2 rounded bg-[var(--gold)]" style={{ width: `${(c.visits / maxV) * 100}%` }} /></td>
                <td className="num">{c.bouncePct ?? "—"}%</td><td className="num">{n(c.signups)}</td>
                <td className="num">{c.visitToSignupPct ?? "—"}%</td><td className="num">{n(c.buyers)}</td><td className="num">${n(c.revenueCOP)}</td>
              </tr>
            ))}
            {!r.countries.length && <tr><td colSpan={8} className="py-3 text-lo">Aún no hay sesiones medidas con país (empieza desde hoy).</td></tr>}
          </tbody>
        </table>
      </section>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="card p-4 sm:p-5">
          <h2 className="text-lg font-semibold">Dispositivos</h2>
          <ul className="mt-3 space-y-2 text-sm">
            {r.devices.map((d) => (
              <li key={String(d.device)} className="flex justify-between"><span>{DEV[String(d.device)] ?? d.device}</span>
                <span className="num text-mid">{n(d.visits)} sesiones · rebote {d.bouncePct ?? "—"}% · {n(d.signups)} cuentas</span></li>
            ))}
          </ul>
        </section>
        <section className="card p-4 sm:p-5 overflow-x-auto">
          <h2 className="text-lg font-semibold">Canal × país</h2>
          <table className="mt-3 w-full text-sm"><tbody>
            {r.sourceByCountry.slice(0, 15).map((x, i) => (
              <tr key={i} className="border-t border-line"><td className="py-1">{String(x.source)}</td><td>{flag(String(x.country))} {String(x.country)}</td>
                <td className="num text-right">{n(x.visits)}</td><td className="num text-right text-lo">rebote {x.bouncePct ?? "—"}%</td></tr>
            ))}
          </tbody></table>
        </section>
      </div>

      <section className="card p-4 sm:p-5 overflow-x-auto">
        <h2 className="text-lg font-semibold">Páginas</h2>
        <table className="mt-3 w-full text-sm">
          <thead className="text-xs text-lo text-left"><tr><th className="py-1">Página</th><th>Vistas</th><th>Tiempo prom.</th><th>Scroll prom.</th><th>Llega al 50%</th><th>Llega al 90%</th></tr></thead>
          <tbody>{r.pages.map((p) => (
            <tr key={String(p.path)} className="border-t border-line"><td className="py-1.5 num">{String(p.path)}</td><td className="num">{n(p.views)}</td>
              <td className="num">{p.avgEngagedSec ?? "—"} s</td><td className="num">{p.avgScrollPct ?? "—"}%</td>
              <td className="num">{p.reach50Pct ?? "—"}%</td><td className="num">{p.reach90Pct ?? "—"}%</td></tr>
          ))}</tbody>
        </table>
      </section>

      <section className="card p-4 sm:p-5">
        <h2 className="text-lg font-semibold">Botones y enlaces más clicados</h2>
        <ol className="mt-3 grid gap-1 sm:grid-cols-2 text-sm">
          {r.ctas.slice(0, 20).map((c, i) => (
            <li key={i} className="flex justify-between gap-3 border-t border-line py-1"><span className="truncate"><span className="num text-lo">{String(c.path)}</span> · {String(c.target)}</span><span className="num">{n(c.clicks)}</span></li>
          ))}
          {!r.ctas.length && <li className="text-lo">Todavía no hay clics medidos.</li>}
        </ol>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-3">Mapa de calor</h2>
        <Heatmap paths={paths} />
      </section>
    </div>
  );
}
