import Link from "next/link";

export const LEGAL_LINKS = [
  { href: "/legal/terminos", label: "Términos y condiciones" },
  { href: "/legal/privacidad", label: "Política de privacidad" },
  { href: "/legal/riesgo", label: "Descargo de responsabilidad" },
  { href: "/legal/juego-responsable", label: "Juego responsable" },
  { href: "/legal/cookies", label: "Cookies" },
];

/** Company identity used across legal texts. Fill the bracketed values before relying on these documents. */
export const COMPANY = {
  brand: "Goldglitch",
  legalName: "[RAZÓN SOCIAL]",
  taxId: "[NIT]",
  address: "[DIRECCIÓN], Cali, Valle del Cauca, Colombia",
  email: "[CORREO DE CONTACTO]",
  site: "easygoldglitch.com",
};

export const LEGAL_UPDATED = "8 de noviembre de 2026";

export function LegalPage({ title, intro, children }: { title: string; intro: string; children: React.ReactNode }) {
  return (
    <div className="mx-auto max-w-6xl px-5 sm:px-6 py-16 grid gap-12 lg:grid-cols-[220px_1fr]">
      <nav aria-label="Documentos legales" className="lg:sticky lg:top-24 self-start">
        <p className="num text-[11px] tracking-[0.22em] text-lo uppercase">Legal</p>
        <ul className="mt-4 space-y-2 text-sm">
          {LEGAL_LINKS.map((l) => (
            <li key={l.href}><Link href={l.href} className="text-mid hover:text-hi">{l.label}</Link></li>
          ))}
        </ul>
      </nav>
      <article className="legal max-w-3xl">
        <h1 className="display text-[2.6rem] sm:text-[3.4rem]">{title}</h1>
        <p className="mt-3 num text-[11px] tracking-[0.18em] uppercase text-lo">Última actualización: {LEGAL_UPDATED}</p>
        <p className="mt-8 text-lg text-mid leading-relaxed">{intro}</p>
        <div className="mt-10 space-y-10">{children}</div>
      </article>
    </div>
  );
}

export function Clause({ n, title, children }: { n: string; title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="text-lg font-semibold text-hi"><span className="num text-gold mr-3">{n}</span>{title}</h2>
      <div className="mt-3 space-y-3 text-[15px] leading-relaxed text-mid">{children}</div>
    </section>
  );
}
