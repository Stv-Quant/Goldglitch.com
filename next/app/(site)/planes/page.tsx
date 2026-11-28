import type { Metadata } from "next";
import { FreeCard } from "@/components/site/FreeCard";

export const metadata: Metadata = {
  title: "Gratis: estadísticas de fútbol sin pagar",
  description: "Goldglitch es gratis: probabilidades, picks de 80%+, goles, córners, tarjetas y jugadores de cada partido. Sin planes de pago ni tarjeta: solo regístrate con tu correo.",
  alternates: { canonical: "/planes" },
};

export default function PlanesPage() {
  return (
    <section className="mx-auto max-w-6xl px-4 sm:px-6 py-16">
      <p className="eyebrow">Gratis</p>
      <h1 className="mt-3 text-3xl sm:text-4xl font-semibold tracking-tight">No hay planes. Todo es gratis.</h1>
      <p className="mt-3 text-mid max-w-2xl">
        No vendemos «picks seguros» ni suscripciones. Te registras con tu correo para recibir alertas y ver las estadísticas
        de cada partido a detalle, y listo: no cobramos nada.
      </p>
      <div className="mt-10">
        <FreeCard />
      </div>
    </section>
  );
}
