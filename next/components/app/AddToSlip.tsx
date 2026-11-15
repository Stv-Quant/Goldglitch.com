"use client";

import type { Leg } from "@/lib/slip";
import { useSlipDraft } from "./slipDraft";

/** "+ Combinada" toggle on a pick card. */
export function AddToSlip({ leg }: { leg: Leg }) {
  const d = useSlipDraft();
  const on = d.has(leg);
  return (
    <button type="button" aria-pressed={on} disabled={!on && d.full}
      onClick={(e) => { e.preventDefault(); e.stopPropagation(); d.toggle(leg); }}
      className={`rounded-lg border px-2.5 py-1 text-[11px] transition-colors disabled:opacity-40 ${on ? "border-[var(--gold)] bg-[var(--gold-faint)] text-gold" : "border-line text-lo hover:text-hi"}`}>
      {on ? "✓ En la combinada" : "+ Combinada"}
    </button>
  );
}
