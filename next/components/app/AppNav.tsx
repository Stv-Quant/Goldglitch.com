"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const ITEMS = [
  { href: "/app", label: "Partidos", icon: "M4 6h16M4 12h16M4 18h10" },
  { href: "/historial", label: "Historial", icon: "M4 20V10m6 10V4m6 16v-7m4 7H2" },
  { href: "/app/cuenta", label: "Cuenta", icon: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm-7 9a7 7 0 0 1 14 0" },
];

export function AppNav({ mobile = false }: { mobile?: boolean }) {
  const path = usePathname();
  const active = (href: string) => (href === "/app" ? path === "/app" || path.startsWith("/app/partido") : path.startsWith(href));

  if (mobile) {
    return (
      <nav className="grid grid-cols-3" aria-label="Navegación de la app">
        {ITEMS.map((i) => (
          <Link key={i.href} href={i.href} aria-current={active(i.href) ? "page" : undefined}
            className="flex flex-col items-center gap-1 py-2.5 text-[11px]"
            style={{ color: active(i.href) ? "var(--gold)" : "var(--text-lo)" }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden>
              <path d={i.icon} />
            </svg>
            {i.label}
          </Link>
        ))}
      </nav>
    );
  }

  return (
    <nav className="flex gap-1 text-sm" aria-label="Navegación de la app">
      {ITEMS.map((i) => (
        <Link key={i.href} href={i.href} aria-current={active(i.href) ? "page" : undefined}
          className={`px-3 py-1.5 rounded-lg transition-colors ${active(i.href) ? "text-hi bg-[var(--gold-faint)]" : "text-lo hover:text-hi"}`}>
          {i.label}
        </Link>
      ))}
    </nav>
  );
}
