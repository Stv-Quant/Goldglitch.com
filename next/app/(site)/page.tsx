import Link from "next/link";
import { PlanCards } from "@/components/site/PlanCards";
import { ProbabilityBar } from "@/components/stats/ProbabilityBar";

const PRINCIPLES = [
  {
    k: "01",
    title: "Probabilidades, no corazonadas",
    body: "Cada partido llega con la probabilidad que calcula el modelo para cada resultado. Sin «fijas», sin «cuota segura», sin VIP de Telegram.",
  },
  {
    k: "02",
    title: "La incertidumbre a la vista",
    body: "Mostramos el rango en el que puede moverse cada número. Un 55% con poca información no vale lo mismo que un 55% con años de datos.",
  },
  {
    k: "03",
    title: "Historial auditable",
    body: "Publicamos cómo le fue al modelo con partidos que ya se jugaron: calibración, Brier y log-loss, comparado contra una referencia ingenua.",
  },
];

export default function Home() {
  return (
    <>
      <section className="relative overflow-hidden">
        <div aria-hidden className="absolute inset-0 hero-glow" />
        <div aria-hidden className="absolute inset-0 grid-lines opacity-60" />
        <div className="relative mx-auto max-w-6xl px-4 sm:px-6 pt-16 sm:pt-24 pb-16 grid gap-12 lg:grid-cols-[1.15fr_1fr] items-center">
          <div className="rise">
            <p className="eyebrow">Fútbol · MLB · Modelos estadísticos</p>
            <h1 className="mt-4 text-4xl sm:text-6xl font-semibold tracking-tight leading-[1.04]">
              No somos tipsters.
              <br />
              <span className="text-gold">Somos la objetividad</span> de los datos.
            </h1>
            <p className="mt-6 text-lg text-mid max-w-xl leading-relaxed">
              Estadísticas claras de cada partido y lo que dicen los números sobre lo que puede pasar, con su margen
              de error y un historial público para que nos audites.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/acceso" className="btn-gold px-5 py-3">Ver partidos gratis</Link>
              <Link href="/historial" className="btn-ghost px-5 py-3">Cómo medimos el modelo</Link>
            </div>
          </div>

          <div className="glass p-5 sm:p-6 rise" aria-label="Ejemplo de ficha de partido">
            <div className="flex items-center justify-between">
              <span className="eyebrow">Ejemplo de ficha</span>
              <span className="text-[11px] text-lo num">sqpc-dc-1.4</span>
            </div>
            <div className="mt-5 flex items-center justify-between text-sm">
              <span className="font-medium">América de Cali</span>
              <span className="text-lo text-xs">vs</span>
              <span className="font-medium">Deportivo Cali</span>
            </div>
            <div className="mt-4">
              <ProbabilityBar
                home={0.497}
                draw={0.268}
                away={0.235}
                labels={{ home: "América", away: "Cali" }}
                interval={{ home: [0.46, 0.53], draw: [0.24, 0.29], away: [0.2, 0.27] }}
              />
            </div>
            <dl className="mt-6 grid grid-cols-3 gap-3 text-center">
              {[
                ["xG local", "1.52"],
                ["xG visita", "0.89"],
                ["+2.5 goles", "43%"],
              ].map(([k, v]) => (
                <div key={k} className="card py-3">
                  <dt className="text-[11px] text-lo">{k}</dt>
                  <dd className="num text-lg mt-0.5">{v}</dd>
                </div>
              ))}
            </dl>
            <p className="mt-4 text-[11px] text-lo">Datos de ejemplo. Los rangos entre corchetes son el margen de incertidumbre.</p>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 sm:px-6 py-16">
        <p className="eyebrow">Por qué somos distintos</p>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          {PRINCIPLES.map((p) => (
            <article key={p.k} className="card p-6">
              <span className="num text-gold text-sm">{p.k}</span>
              <h2 className="mt-3 text-lg font-semibold">{p.title}</h2>
              <p className="mt-2 text-sm text-mid leading-relaxed">{p.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 sm:px-6 py-16" id="planes">
        <p className="eyebrow">Planes</p>
        <h2 className="mt-3 text-3xl font-semibold tracking-tight">Empieza gratis. Paga solo por profundidad.</h2>
        <div className="mt-8">
          <PlanCards />
        </div>
      </section>
    </>
  );
}
