import Link from "next/link";

/**
 * Upsell placeholder. Contains no real data — the server never sends locked fields —
 * only an abstract shape so the layout doesn't jump when the user upgrades.
 */
export function LockedPanel({ tier, title, children }: { tier: "Pro" | "Elite"; title: string; children: string }) {
  return (
    <div className="relative overflow-hidden card p-5">
      <div aria-hidden className="absolute inset-0 opacity-40 grid-lines" />
      <div className="relative">
        <div className="flex items-center gap-2">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--gold)" strokeWidth="2" aria-hidden>
            <rect x="4" y="11" width="16" height="10" rx="2" />
            <path d="M8 11V7a4 4 0 0 1 8 0v4" />
          </svg>
          <span className="eyebrow" style={{ color: "var(--gold)" }}>{tier}</span>
        </div>
        <h3 className="mt-2 text-base font-semibold">{title}</h3>
        <p className="mt-1 text-sm text-mid max-w-prose">{children}</p>
        <Link href="/planes" className="btn-ghost mt-4 inline-block px-4 py-2 text-sm">Ver planes</Link>
      </div>
    </div>
  );
}
