import { Mark } from "@/components/brand/Logo";

/** Founder's letter: the "why" in one voice. Pratfall by design — it says what we can't do. */
export function FounderLetter() {
  return (
    <section className="reveal-on-enter relative py-28" aria-labelledby="carta-title">
      <div className="mx-auto max-w-3xl px-5 sm:px-6">
        <p className="num text-[11px] tracking-[0.22em] text-gold uppercase">Carta del fundador</p>
        <h2 id="carta-title" className="display mt-3 text-[2.4rem] sm:text-[3.6rem]">
          Por qué existe <em>Goldglitch</em>.
        </h2>
        <div className="mt-10 space-y-6 text-[17px] sm:text-lg leading-[1.75] text-mid letter">
          <p>
            Vengo de construir modelos para mercados financieros. Ahí aprendí algo simple: si no mides tus errores, no
            tienes un modelo. Tienes una opinión.
          </p>
          <p>
            En el fútbol vi lo contrario. Fijas por WhatsApp. Capturas de lo que ganaron, nunca de lo que perdieron. Nadie
            muestra su historial completo.
          </p>
          <p className="text-hi">
            Goldglitch hace lo opuesto. No te decimos quién va a ganar. Te decimos qué tan probable es cada resultado, y
            publicamos cuántas veces acertamos y cuántas no.
          </p>
          <p>Si buscas una fija, aquí no la vas a encontrar. Nadie la tiene. Si quieres decidir con números, bienvenido.</p>
          <p className="display text-3xl sm:text-4xl text-hi not-italic pt-2">No adivinamos. Calculamos.</p>
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
