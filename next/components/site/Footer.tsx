import Link from "next/link";

export function Footer() {
  return (
    <footer className="mt-24 border-t border-line">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-10 grid gap-6 sm:grid-cols-[1fr_auto] text-sm">
        <div className="space-y-2 max-w-xl">
          <p className="text-mid">
            Goldglitch publica estadísticas y probabilidades derivadas de modelos. No es una casa de apuestas,
            no recibe apuestas y no garantiza resultados.
          </p>
          <p className="text-lo text-xs">
            Contenido para mayores de 18 años. Si decides apostar, hazlo con dinero que puedas perder y fija límites.
          </p>
        </div>
        <nav className="flex gap-5 text-lo" aria-label="Pie de página">
          <Link href="/historial" className="hover:text-hi">Historial</Link>
          <Link href="/planes" className="hover:text-hi">Planes</Link>
          <Link href="/acceso" className="hover:text-hi">Entrar</Link>
        </nav>
      </div>
    </footer>
  );
}
