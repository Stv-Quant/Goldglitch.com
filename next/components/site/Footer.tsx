import Link from "next/link";
import { Mark } from "@/components/brand/Logo";
import { COMPANY, LEGAL_LINKS } from "@/components/site/LegalPage";

const COLUMNS = [
  {
    title: "Producto",
    links: [
      { href: "/app", label: "Partidos" },
      { href: "/historial", label: "Historial del modelo" },
      { href: "/historial", label: "Metodología" },
      { href: "/planes", label: "Planes" },
    ],
  },
  {
    title: "Deportes",
    links: [
      { href: "/app", label: "Fútbol" },
      { href: "/app", label: "Béisbol · Baloncesto · Hockey" },
      { href: "/planes", label: "NBA · pronto" },
      { href: "/planes", label: "Tenis · pronto" },
    ],
  },
  { title: "Legal", links: LEGAL_LINKS },
];

export function Footer() {
  return (
    <footer className="relative mt-24 border-t border-line">
      <div className="mx-auto max-w-6xl px-5 sm:px-6 pt-16 pb-10">
        <div className="grid gap-12 md:grid-cols-[1.3fr_repeat(3,1fr)]">
          <div>
            <div className="flex items-center gap-3">
              <Mark size={30} />
              <span className="font-semibold tracking-tight">Goldglitch<span className="text-lo font-normal"> · Stats</span></span>
            </div>
            <p className="display mt-6 text-3xl leading-tight">No especulamos.<br /><em>Calculamos.</em></p>
            <p className="mt-4 text-sm text-lo max-w-xs">Estadísticas y probabilidades deportivas con incertidumbre visible e historial auditable.</p>
          </div>
          {COLUMNS.map((c) => (
            <nav key={c.title} aria-label={c.title}>
              <h2 className="num text-[11px] tracking-[0.22em] uppercase text-hi">{c.title}</h2>
              <ul className="mt-4 space-y-2.5 text-sm">
                {c.links.map((l) => (
                  <li key={l.label}><Link href={l.href} className="text-mid hover:text-hi transition-colors">{l.label}</Link></li>
                ))}
              </ul>
            </nav>
          ))}
        </div>

        <div className="mt-14 grid gap-4 border-t border-line pt-8 md:grid-cols-[auto_1fr] md:items-start">
          <span className="inline-flex h-9 min-w-9 items-center justify-center rounded-full border border-[var(--flare)] px-2 num text-xs text-flare" aria-label="Solo mayores de 18 años">18+</span>
          <p className="text-[13px] leading-relaxed text-lo">
            {COMPANY.brand} provee herramientas estadísticas e información educativa. No es una casa de apuestas, no recibe
            apuestas, no es asesor financiero ni de inversión y no garantiza resultados ni ganancias. Las probabilidades
            describen la incertidumbre: los resultados poco probables ocurren. Apostar implica riesgo de pérdida; si lo haces,
            usa operadores autorizados por Coljuegos y solo dinero que puedas perder.{" "}
            <Link href="/legal/juego-responsable" className="text-mid underline underline-offset-4 hover:text-hi">Juego responsable</Link>.
          </p>
        </div>

        <div className="mt-8 flex flex-col gap-2 text-xs text-lo sm:flex-row sm:items-center sm:justify-between">
          <p>© {new Date().getFullYear()} {COMPANY.brand}. Todos los derechos reservados.</p>
          <p>Hecho en Cali, Colombia.</p>
        </div>
      </div>
    </footer>
  );
}
