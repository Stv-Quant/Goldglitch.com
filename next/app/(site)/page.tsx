import { FounderLetter } from "@/components/experience/FounderLetter";
import { RevealObserver } from "@/components/experience/RevealObserver";
import { SignalStory } from "@/components/experience/SignalStory";
import { PlanCards } from "@/components/site/PlanCards";

const JSON_LD = {
  "@context": "https://schema.org",
  "@graph": [
    { "@type": "Organization", "@id": "https://easygoldglitch.com/#org", name: "Goldglitch", url: "https://easygoldglitch.com",
      logo: "https://easygoldglitch.com/icons/icon-512.png", areaServed: "CO" },
    { "@type": "WebSite", name: "Goldglitch", url: "https://easygoldglitch.com", inLanguage: "es-CO", publisher: { "@id": "https://easygoldglitch.com/#org" } },
    { "@type": "WebApplication", name: "Goldglitch", url: "https://easygoldglitch.com", applicationCategory: "SportsApplication",
      operatingSystem: "Web", inLanguage: "es-CO",
      description: "Probabilidades de cada partido de fútbol y béisbol calculadas por un modelo estadístico, con historial público de aciertos y fallos.",
      offers: { "@type": "Offer", price: "0", priceCurrency: "COP" } },
  ],
};

export default function Home() {
  return (
    <div className="grain -mt-[calc(4rem+36px)]">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(JSON_LD) }} />
      <SignalStory />
      <FounderLetter />
      <section className="reveal-on-enter relative mx-auto max-w-6xl px-5 sm:px-6 pt-24 pb-10" id="planes">
        <div>
          <p className="num text-[11px] tracking-[0.22em] text-lo uppercase">Planes</p>
          <h2 className="display mt-4 text-[2.6rem] sm:text-[4rem]">
            Empieza gratis. <em>Paga solo</em> si quieres más.
          </h2>
        </div>
        <div className="mt-10">
          <PlanCards />
        </div>
      </section>
      <RevealObserver />
    </div>
  );
}
