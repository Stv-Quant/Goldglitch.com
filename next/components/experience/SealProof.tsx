/**
 * The seal: a prediction receipt with a stamp that lands when the section enters.
 * Values are an illustrative example of the real seal shown on every match page.
 */
export function SealProof() {
  return (
    <section className="reveal-on-enter relative mx-auto max-w-6xl px-5 sm:px-6 py-28 grid gap-12 lg:grid-cols-[1.05fr_1fr] items-center" aria-labelledby="sello-title">
      <div>
        <p className="num text-[11px] tracking-[0.22em] text-gold uppercase">El sello</p>
        <h2 id="sello-title" className="display mt-3 text-[2.6rem] sm:text-[4rem]">
          Antes del pitazo, <em>sellado</em>. Después, intocable.
        </h2>
        <p className="mt-5 max-w-lg text-mid leading-relaxed">
          Un tipster puede borrar el pick que falló. Nosotros no podemos. Cada pronóstico queda registrado con su hora y su
          huella digital antes de que empiece el partido, y el servidor rechaza cualquier cambio posterior. Lo que ves en el
          historial es exactamente lo que publicamos.
        </p>
        <ul className="mt-8 grid gap-3 text-sm">
          {[
            ["Hora exacta", "registrada antes del inicio del partido"],
            ["Huella SHA-256", "cualquier alteración cambia el código"],
            ["Aciertos y fallos", "se publican juntos, sin selección"],
          ].map(([k, v]) => (
            <li key={k} className="flex gap-3">
              <span className="text-gold num">—</span>
              <span><span className="text-hi">{k}</span> <span className="text-lo">{v}</span></span>
            </li>
          ))}
        </ul>
      </div>

      <div className="seal-scene relative mx-auto w-full max-w-md">
        <div className="seal-receipt card relative p-6 sm:p-7 num text-[12px] leading-6 text-mid">
          <div className="flex justify-between text-[10px] tracking-[0.2em] uppercase text-lo">
            <span>Pronóstico</span>
            <span>Ejemplo</span>
          </div>
          <div className="mt-4 border-y border-dashed border-line py-4 space-y-1">
            <Row k="Partido" v="ARS — LIV" />
            <Row k="Modelo" v="sqpc 1.4" />
            <Row k="Local / X / Visita" v={<><span className="text-gold">49%</span> · 27% · 24%</>} />
            <Row k="Rango (80%)" v="45–52 · 24–29 · 21–28" />
          </div>
          <div className="mt-4 space-y-1">
            <Row k="Sellado" v="14:38:07" />
            <Row k="Inicio" v="16:30:00" />
            <Row k="Margen" v="1 h 51 min antes" />
            <Row k="SHA-256" v={<span className="text-hi">9f3a6c1e02b7d4…</span>} />
          </div>
          <div className="seal-stamp absolute -right-3 -bottom-5 sm:-right-6 grid place-items-center rounded-full border-2 border-[var(--gold)] text-gold h-28 w-28 rotate-[-14deg]" aria-hidden>
            <div className="text-center leading-tight">
              <div className="text-[9px] tracking-[0.25em]">GOLDGLITCH</div>
              <div className="display text-2xl">Sellado</div>
              <div className="text-[9px] tracking-[0.25em]">PRE-PITAZO</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Row({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-lo">{k}</span>
      <span className="text-right">{v}</span>
    </div>
  );
}
