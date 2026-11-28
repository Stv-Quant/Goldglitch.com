import { FounderLetter } from "@/components/experience/FounderLetter";
import { RevealObserver } from "@/components/experience/RevealObserver";
import { SignalStory } from "@/components/experience/SignalStory";
import { FreeCard } from "@/components/site/FreeCard";

const JSON_LD = {
  "@context": "https://schema.org",
  "@graph": [
    { "@type": "Organization", "@id": "https://easygoldglitch.com/#org", name: "Goldglitch", url: "https://easygoldglitch.com",
      logo: "https://easygoldglitch.com/icons/icon-512.png", areaServed: "CO" },
    { "@type": "WebSite", name: "Goldglitch", url: "https://easygoldglitch.com", inLanguage: "es-CO", publisher: { "@id": "https://easygoldglitch.com/#org" } },
    { "@type": "WebApplication", name: "Goldglitch", url: "https://easygoldglitch.com", applicationCategory: "SportsApplication",
      operatingSystem: "Web", inLanguage: "es-CO",
      description: "Estadísticas y probabilidades de cada partido de fútbol y béisbol, gratis: calculadas por un modelo estadístico, con historial público de aciertos y fallos. Solo pide registrarse.",
      isAccessibleForFree: true,
      offers: { "@type": "Offer", price: "0", priceCurrency: "COP", description: "Gratis: solo requiere registrarse con el correo." } },
    { "@type": "FAQPage", mainEntity: [
      { "@type": "Question", name: "¿Goldglitch es gratis?",
        acceptedAnswer: { "@type": "Answer", text: "Sí. Goldglitch es 100% gratis: no hay planes de pago ni se pide tarjeta. Solo te registras con tu correo para ver todas las estadísticas y recibir alertas." } },
      { "@type": "Question", name: "¿Para qué tengo que registrarme?",
        acceptedAnswer: { "@type": "Answer", text: "La cuenta gratis sirve para ver las estadísticas de cada partido a detalle (goles, córners, tarjetas, jugadores y picks de 80% o más) y recibir alertas de los partidos que te interesan." } },
      { "@type": "Question", name: "¿Goldglitch vende pronósticos o fijas?",
        acceptedAnswer: { "@type": "Answer", text: "No. Publicamos probabilidades calculadas por un modelo estadístico y el historial público de aciertos y fallos. No vendemos nada." } },
      { "@type": "Question", name: "¿Qué deportes cubre?",
        acceptedAnswer: { "@type": "Answer", text: "Fútbol (Champions, Premier League, LaLiga, liga colombiana y más), béisbol, baloncesto, hockey y NFL." } },
    ] },
  ],
};

export default function Home() {
  return (
    <div className="grain -mt-[calc(4rem+36px)]">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(JSON_LD) }} />
      <SignalStory />
      <FounderLetter />
      <section className="reveal-on-enter relative mx-auto max-w-6xl px-5 sm:px-6 pt-24 pb-10" id="gratis">
        <div>
          <p className="num text-[11px] tracking-[0.22em] text-lo uppercase">Gratis</p>
          <h2 className="display mt-4 text-[2.6rem] sm:text-[4rem]">
            Todo es gratis. <em>Solo regístrate.</em>
          </h2>
          <p className="mt-4 text-mid max-w-2xl">No cobramos nada. La cuenta sirve para recibir alertas y ver las estadísticas de cada partido a detalle.</p>
        </div>
        <div className="mt-10">
          <FreeCard />
        </div>
      </section>
      <RevealObserver />
    </div>
  );
}
