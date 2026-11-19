import { scoreStats } from "@/lib/derived";
import { Prob, ProbMeter } from "./Prob";
import { probColor } from "@/lib/probScale";
import { Bell } from "./Bell";

/** Pro: everything about goals the score matrix implies, most useful first. */
export function GoalsPanel({ xg, matrix, home, away }: {
  xg?: { home: number; away: number };
  matrix?: number[][];
  home: string;
  away: string;
}) {
  const st = matrix ? scoreStats(matrix) : null;
  const maxTotal = st ? Math.max(...st.totalGoals.map((g) => g.p)) : 1;
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {xg && <Kpi label={`xG ${home}`} value={xg.home.toFixed(2)} lead={xg.home >= xg.away} />}
        {xg && <Kpi label={`xG ${away}`} value={xg.away.toFixed(2)} lead={xg.away > xg.home} />}
        {st && <Kpi label="Goles esperados" value={st.expectedTotal.toFixed(2)} />}
        {st && <Kpi label="Ambos marcan" p={st.btts} />}
      </div>

      {st && (
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="card p-4 sm:p-5">
            <h3 className="text-sm text-mid">Marcadores más probables</h3>
            <ol className="mt-3 space-y-2.5">
              {st.top.map((c, i) => (
                <li key={`${c.h}-${c.a}`} className="grid grid-cols-[1.5rem_3.5rem_1fr_3rem] items-center gap-3">
                  <span className="num text-[11px] text-lo">{i + 1}</span>
                  <span className="num text-lg font-semibold text-hi">{c.h}–{c.a}</span>
                  <div className="h-2 overflow-hidden rounded-full bg-[var(--seg-3)]">
                    <div className="h-full rounded-full" style={{ width: `${(c.p / st.top[0].p) * 100}%`, background: i === 0 ? "var(--gold)" : "var(--gold-dim)" }} />
                  </div>
                  <span className="num text-right text-sm text-mid">{(c.p * 100).toFixed(1)}%</span>
                </li>
              ))}
            </ol>
          </div>

          <div className="card p-4 sm:p-5">
            <h3 className="text-sm text-mid">Total de goles en el partido</h3>
            <div className="mt-4">
              <Bell pmf={st.totalGoals.map((g) => g.p)} height={110} tail={0} labels={st.totalGoals.map((g) => (
                <>
                  <span className="block text-[10px] text-lo">{g.label}</span>
                  <span className={`block text-[13px] ${g.p === maxTotal ? "font-semibold text-gold" : "text-mid"}`}>{Math.round(g.p * 100)}%</span>
                </>
              ))} />
            </div>
          </div>

          <div className="card p-4 sm:p-5 lg:col-span-2">
            <h3 className="text-sm text-mid">Defensa</h3>
            <div className="mt-3 grid gap-4 sm:grid-cols-2">
              <Row label={`${home} no recibe gol`} p={st.cleanSheet.home} />
              <Row label={`${away} no recibe gol`} p={st.cleanSheet.away} />
              <Row label={`${home} gana sin recibir`} p={st.winToNil.home} />
              <Row label={`${away} gana sin recibir`} p={st.winToNil.away} />
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

function Kpi({ label, value, p, lead }: { label: string; value?: string; p?: number; lead?: boolean }) {
  return (
    <div className="rounded-[12px] border border-line px-4 py-3">
      <div className="truncate text-[11px] text-lo">{label}</div>
      {p !== undefined ? (
        <Prob p={p} className="text-2xl font-semibold" />
      ) : (
        <div className={`num text-2xl font-semibold ${lead ? "text-gold" : "text-hi"}`}>{value}</div>
      )}
    </div>
  );
}

function Row({ label, p }: { label: string; p: number }) {
  return (
    <div>
      <div className="flex items-baseline justify-between gap-2 text-sm">
        <span className="text-mid">{label}</span>
        <span className="num font-semibold" style={{ color: probColor(p) }}>{Math.round(p * 100)}%</span>
      </div>
      <ProbMeter p={p} className="mt-1.5 h-1.5" />
    </div>
  );
}
