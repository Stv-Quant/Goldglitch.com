"use client";

import { useState } from "react";

export type Tab = { id: string; label: string; badge?: string; content: React.ReactNode };

/** Simple tab set: server-rendered panels, only one visible at a time. Keeps long match pages short. */
export function Tabs({ tabs, label }: { tabs: Tab[]; label: string }) {
  const [active, setActive] = useState(tabs[0]?.id);
  if (!tabs.length) return null;
  return (
    <div>
      <div role="tablist" aria-label={label} className="scroll-x -mx-4 flex gap-1 border-b border-line px-4 sm:mx-0 sm:px-0">
        {tabs.map((t) => {
          const on = t.id === active;
          return (
            <button key={t.id} type="button" role="tab" id={`tab-${t.id}`} aria-selected={on} aria-controls={`panel-${t.id}`}
              onClick={() => setActive(t.id)}
              className={`relative whitespace-nowrap px-3.5 py-3 text-sm transition-colors ${on ? "text-hi" : "text-lo hover:text-mid"}`}>
              {t.label}
              {t.badge && <span className="num ml-1.5 text-[10px] text-gold">{t.badge}</span>}
              {on && <span aria-hidden className="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-[var(--gold)]" />}
            </button>
          );
        })}
      </div>
      {tabs.map((t) => (
        <div key={t.id} role="tabpanel" id={`panel-${t.id}`} aria-labelledby={`tab-${t.id}`} hidden={t.id !== active} className="pt-5">
          {t.content}
        </div>
      ))}
    </div>
  );
}
