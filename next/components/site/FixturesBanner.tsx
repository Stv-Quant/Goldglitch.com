"use client";

import Link from "next/link";
import { isTodayBogota, type Fixture } from "@/components/experience/fixture";
import { useFixtures } from "@/components/experience/useFixtures";

const timeFmt = new Intl.DateTimeFormat("es-CO", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "America/Bogota" });

function Item({ f }: { f: Fixture }) {
  const marks = f.outcomes === 3 ? ["1", "X", "2"] : ["1", "2"];
  return (
    <Link href="/acceso" className="banner-item" tabIndex={-1}>
      <span className="banner-chip">{f.sport}</span>
      <span className={f.state === "in" ? "text-up" : "text-lo"}>
        {f.state === "in" ? "EN VIVO" : `${isTodayBogota(f.kickoffAt) ? "HOY" : "MAÑ"} ${timeFmt.format(f.kickoffAt)}`}
      </span>
      <span className="text-hi">{f.home}</span>
      <span className="text-lo">vs</span>
      <span className="text-hi">{f.away}</span>
      {marks.map((m) => (
        <span key={m} className="whitespace-nowrap">
          <span className="text-lo">{m}</span> <span className="banner-q">???</span>
        </span>
      ))}
    </Link>
  );
}

/**
 * Stock-ticker style strip on top of the site: upcoming matches with every probability hidden as "???".
 * Fixed height so it never shifts the layout, even while loading or when nothing is scheduled.
 */
export function FixturesBanner() {
  const fixtures = useFixtures();
  const list = fixtures ?? [];
  // Repeat short match days so the loop never shows a gap.
  const filled = list.length ? Array.from({ length: Math.max(1, Math.ceil(8 / list.length)) }, () => list).flat() : [];

  return (
    <div className="fixtures-banner" role="region" aria-label="Próximos partidos">
      <Link href="/acceso" className="banner-label">
        <span className="live-dot" aria-hidden /> Próximos
      </Link>
      <div className="banner-viewport">
        {fixtures === null || !fixtures.length ? (
          <span className="banner-loading">{fixtures === null ? "Cargando partidos…" : "Hoy y mañana no hay partidos en las ligas que seguimos."}</span>
        ) : (
          <div className="banner-track" style={{ ["--banner-dur" as string]: `${Math.max(35, filled.length * 5)}s` }}>
            {[0, 1].map((copy) => (
              <div key={copy} className="banner-run" aria-hidden={copy === 1 || undefined}>
                {filled.map((f, i) => <Item key={`${f.id}-${i}`} f={f} />)}
              </div>
            ))}
          </div>
        )}
      </div>
      <Link href="/acceso" className="banner-cta">Ver probabilidades →</Link>
    </div>
  );
}
