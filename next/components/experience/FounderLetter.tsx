import { Mark } from "@/components/brand/Logo";

/** Founder's letter: the "why" in one voice. Pratfall by design — it says what we can't do. */
export function FounderLetter() {
  return (
    <section className="reveal-on-enter relative py-28" aria-labelledby="carta-title">
      <div className="mx-auto max-w-3xl px-5 sm:px-6">
        <p className="num text-[11px] tracking-[0.22em] text-gold uppercase">Carta del fundador</p>
        <h2 id="carta-title" className="display mt-3 text-[2.4rem] sm:text-[3.6rem]">
          El que no mide su error, <em>lo paga</em>.
        </h2>
        <div className="mt-10 space-y-6 text-[17px] sm:text-lg leading-[1.75] text-mid letter">
          <p>
            Vengo de construir sistemas cuantitativos para mercados financieros. Ahí aprendí una regla que el mercado cobra
            caro: un modelo que no mide su propio error no es un modelo, es una opinión con decimales.
          </p>
          <p>
            Cuando miré el mundo de las apuestas deportivas vi lo contrario. Certezas vendidas por WhatsApp. Capturas de las
            ganancias, nunca de las pérdidas. «Fijas» que nadie audita y que desaparecen cuando fallan.
          </p>
          <p className="text-hi">
            Goldglitch existe para ser lo opuesto. No te vamos a decir quién gana. Te vamos a decir qué tan probable es cada
            resultado, cuánto puede equivocarse el modelo y, en público, cuántas veces acertó y cuántas no.
          </p>
          <p>
            Si buscas una certeza, aquí no la vas a encontrar: nadie la tiene. Si quieres entender un partido mejor de lo que
            lo entendías ayer, y decidir tú con los números delante, bienvenido.
          </p>
          <p className="display text-3xl sm:text-4xl text-hi not-italic pt-2">No especulamos. Calculamos.</p>
        </div>
        <div className="mt-10 flex items-center gap-4">
          <Mark size={40} />
          <div>
            <div className="text-hi font-medium">Equipo Goldglitch</div>
            <div className="text-sm text-lo">Hecho en Cali, Colombia</div>
          </div>
        </div>
      </div>
    </section>
  );
}
