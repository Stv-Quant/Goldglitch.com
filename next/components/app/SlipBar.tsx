"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { scoreSlip } from "@/lib/slip";
import { probColor } from "@/lib/probScale";
import { useSlipDraft } from "./slipDraft";

/** Floating summary of the combinada being built; hidden on the Combinadas page itself. */
export function SlipBar() {
  const { legs } = useSlipDraft();
  const path = usePathname();
  if (!legs.length || path.startsWith("/app/combinadas")) return null;
  const s = scoreSlip(legs);
  return (
    <Link href="/app/combinadas"
      className="fixed inset-x-4 bottom-20 z-40 mx-auto flex max-w-md items-center justify-between gap-3 rounded-2xl border border-[var(--border-glass)] bg-[rgba(14,13,11,0.96)] px-4 py-3 shadow-2xl backdrop-blur sm:bottom-6">
      <span className="text-sm">
        <span className="text-hi">Combinada</span>
        <span className="text-lo"> · {legs.length} selección{legs.length === 1 ? "" : "es"}</span>
      </span>
      <span className="flex items-center gap-3">
        {legs.length > 1 && <span className="num text-lg font-semibold" style={{ color: probColor(s.p) }}>{(s.p * 100).toFixed(1)}%</span>}
        <span className="text-sm text-gold">Ver →</span>
      </span>
    </Link>
  );
}
