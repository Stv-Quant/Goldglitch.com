import type { Stakes } from "@/lib/contracts";
import { ProbMeter, Prob } from "./Prob";

type Side = NonNullable<Stakes["home"]>;
type Mood = NonNullable<NonNullable<Stakes["mood"]>["home"]>;

const signedPts = (x: number) => `${x > 0 ? "+" : x < 0 ? "−" : ""}${Math.abs(x * 100).toFixed(0)} pts`;

function Form({ s }: { s: string }) {
  const tone: Record<string, string> = { G: "var(--neon-up)", E: "var(--text-lo)", P: "var(--neon-down, #ff5a5a)" };
  return (
    <span className="inline-flex gap-1" aria-label={`Últimos partidos: ${s}`}>
      {[...s].map((c, i) => (
        <span key={i} className="num inline-flex h-5 w-5 items-center justify-center rounded text-[10px] font-semibold"
          style={{ color: tone[c] ?? "var(--text-mid)", border: `1px solid ${tone[c] ?? "var(--border-soft)"}` }}>{c}</span>
      ))}
    </span>
  );
}

function Column({ name, side, mood, f }: { name: string; side?: Side; mood?: Mood; f?: Stakes["format"] }) {
  return (
    <div className="card space-y-3 p-4">
      <div>
        <h3 className="font-semibold text-hi">{name}</h3>
        {side && (
          <p className="num mt-0.5 text-[11px] text-lo">
            {side.pos}º · {side.pts} pts en {side.gp} PJ · DG {side.gd > 0 ? "+" : ""}{side.gd}
          </p>
        )}
      </div>
      {side && <p className="text-sm text-hi">{side.need}</p>}
      {side && f && (
        <div className="space-y-2">
          {([[f.topLabel, side.pTop], [f.zoneLabel, side.pZone], ["Descenso", side.pReleg]] as const).map(([label, p]) => (
            <div key={label}>
              <div className="flex items-baseline justify-between text-xs">
                <span className="text-mid">{label}</span>
                <Prob p={p} />
              </div>
              <ProbMeter p={p} className="mt-1 h-1" />
            </div>
          ))}
          <p className="text-[11px] text-lo">
            Ganar en vez de perder: {f.topLabel.toLowerCase()} {signedPts(side.levTop)} · {f.zoneLabel.toLowerCase()} {signedPts(side.levZone)} · descenso {signedPts(-side.levDown)}
          </p>
        </div>
      )}
      {mood && (
        <div className="flex flex-wrap items-center gap-2 border-t border-line pt-3 text-xs">
          <span className="text-mid">Estado anímico</span>
          <Form s={mood.last} />
          <span className="num" style={{ color: mood.form >= 0 ? "var(--neon-up)" : "var(--text-mid)" }}>
            {mood.form > 0 ? "+" : ""}{mood.form.toFixed(2)} pts/partido
          </span>
          <span className="text-lo">sobre lo esperado{mood.slump ? " · 3 derrotas seguidas" : ""}</span>
        </div>
      )}
    </div>
  );
}

/** "Lo que se juegan": table, end-of-season chances, what this match moves, and recent mood (SQPC stakes model). */
export function StakesPanel({ s, home, away }: { s: Stakes; home: string; away: string }) {
  const f = s.format;
  const e = s.effect;
  const moved = e && e.applied && (Math.abs(e.home - 1) > 5e-4 || Math.abs(e.away - 1) > 5e-4);
  const pctFx = (x: number) => `${x >= 1 ? "+" : "−"}${Math.abs((x - 1) * 100).toFixed(1)}%`;
  return (
    <div className="space-y-4">
      {f && s.progress !== undefined && (
        <p className="text-[11px] text-lo">
          Temporada al {Math.round(s.progress * 100)}% · {f.teams} equipos · {f.games} partidos por equipo · {f.releg} descienden
        </p>
      )}
      <div className="grid gap-4 sm:grid-cols-2">
        <Column name={home} side={s.home} mood={s.mood?.home} f={f} />
        <Column name={away} side={s.away} mood={s.mood?.away} f={f} />
      </div>
      <p className="text-[11px] text-lo">
        {moved
          ? `Goles esperados ajustados por lo que se juegan y su racha: ${home} ${pctFx(e!.home)} · ${away} ${pctFx(e!.away)}. Ya incluido en todas las probabilidades.`
          : "Sin efecto apreciable sobre los goles esperados."}{" "}
        Las probabilidades de fin de temporada salen de simular el resto del campeonato desde la tabla actual, con el formato de cada liga. El efecto sobre los goles se validó fuera de muestra en 27 ligas.
      </p>
    </div>
  );
}
