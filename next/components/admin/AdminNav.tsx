"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";

const ITEMS = [
  { href: "/admin", label: "Resumen" },
  { href: "/admin/usuarios", label: "Usuarios" },
  { href: "/admin/pagos", label: "Pagos" },
  { href: "/admin/datos", label: "Datos y modelo" },
  { href: "/admin/auditoria", label: "Auditoría" },
];

export function AdminNav() {
  const path = usePathname();
  const active = (h: string) => (h === "/admin" ? path === "/admin" : path.startsWith(h));
  return (
    <nav aria-label="Administración" className="flex lg:flex-col gap-1 overflow-x-auto -mx-1 px-1 text-sm">
      {ITEMS.map((i) => (
        <Link key={i.href} href={i.href} aria-current={active(i.href) ? "page" : undefined}
          className={`whitespace-nowrap rounded-lg px-3 py-2 transition-colors ${active(i.href) ? "bg-[var(--gold-faint)] text-hi" : "text-lo hover:text-hi"}`}>
          {i.label}
        </Link>
      ))}
    </nav>
  );
}

/** Admin preview switch: browse the product as a Free / Pro / Elite member would. */
export function ViewAs({ current }: { current: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  async function set(tier: string) {
    setBusy(true);
    await fetch("/api/admin/view-as", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ tier }) });
    setBusy(false);
    router.refresh();
  }
  return (
    <div>
      <div className="num text-[10px] tracking-[0.18em] uppercase text-lo">Ver la app como</div>
      <div role="radiogroup" aria-label="Ver la app como" className="mt-2 inline-flex rounded-lg border border-line p-0.5 text-xs">
        {[["free", "Free"], ["pro", "Pro"], ["elite", "Elite"]].map(([k, l]) => (
          <button key={k} role="radio" aria-checked={current === k} disabled={busy} onClick={() => set(k)}
            className={`px-3 py-1.5 rounded-md ${current === k ? "bg-[var(--gold-faint)] text-hi" : "text-lo hover:text-hi"}`}>
            {l}
          </button>
        ))}
      </div>
      <Link href="/app" className="mt-2 block text-xs text-gold hover:underline underline-offset-4">Abrir la app →</Link>
    </div>
  );
}
