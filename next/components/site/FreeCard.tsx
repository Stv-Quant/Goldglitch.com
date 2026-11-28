import Link from "next/link";

/** Goldglitch is free: the only thing an account asks for is an email. What it unlocks, in one card. */
export const FREE_FEATURES = [
  "Probabilidades de cada partido: ganador, goles, córners, tarjetas, remates y jugadores",
  "Picks del modelo con 80% o más, partido por partido",
  "xG, marcadores más probables y portería a cero",
  "Fútbol, béisbol, baloncesto, hockey y NFL",
  "Alertas de los partidos que te interesan",
  "Combinadas: arma y guarda las tuyas",
  "Historial público de aciertos y fallos",
];

export function FreeCard({ cta = true }: { cta?: boolean }) {
  return (
    <div className="glass p-6 sm:p-8 max-w-3xl">
      <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
        <span className="num text-4xl font-semibold text-gold">$0</span>
        <span className="text-mid">para siempre · sin tarjeta · sin planes de pago</span>
      </div>
      <p className="mt-3 text-hi">Solo necesitas tu correo. Con la cuenta gratis ves todo:</p>
      <ul className="mt-4 grid gap-2 sm:grid-cols-2 text-sm text-mid">
        {FREE_FEATURES.map((f) => (
          <li key={f} className="flex gap-2">
            <span aria-hidden className="text-gold">✓</span>
            <span>{f}</span>
          </li>
        ))}
      </ul>
      {cta && (
        <Link href="/acceso" className="btn-gold mt-6 inline-block px-6 py-3 text-[15px]">Crear cuenta gratis</Link>
      )}
    </div>
  );
}
