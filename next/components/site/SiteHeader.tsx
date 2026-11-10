import Link from "next/link";
import { Logo } from "@/components/brand/Logo";
import { FixturesBanner } from "@/components/site/FixturesBanner";
import { getViewer } from "@/lib/auth";

export async function SiteHeader() {
  const viewer = await getViewer().catch(() => null);
  return (
    <header className="sticky top-0 z-40 bg-gradient-to-b from-[rgba(10,9,7,0.92)] via-[rgba(10,9,7,0.6)] to-transparent">
      <FixturesBanner />
      <div className="mx-auto max-w-6xl px-4 sm:px-6 h-16 flex items-center justify-between">
        <Logo />
        <nav className="flex items-center gap-1 sm:gap-4 text-sm" aria-label="Principal">
          <Link href="/historial" className="hidden sm:inline px-2 py-1 text-mid hover:text-hi">Historial</Link>
          <Link href="/planes" className="hidden sm:inline px-2 py-1 text-mid hover:text-hi">Planes</Link>
          {viewer ? (
            <Link href="/app" className="btn-gold px-4 py-1.5">Abrir app</Link>
          ) : (
            <Link href="/acceso" className="btn-gold px-4 py-1.5">Entrar</Link>
          )}
        </nav>
      </div>
    </header>
  );
}
