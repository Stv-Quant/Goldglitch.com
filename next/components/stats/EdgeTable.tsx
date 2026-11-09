import type { Prediction } from "@/lib/contracts";
import { pct } from "@/lib/format";

/**
 * Model vs market. EV sign is carried by text (+/−) and an arrow, not only color.
 * Implied probability uses raw 1/odds (includes the bookmaker margin) — stated in the caption.
 */
export function EdgeTable({ edges }: { edges: Prediction["edges"] }) {
  if (!edges.length) return <p className="text-sm text-lo">Sin cuotas capturadas para este partido.</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-[11px] text-lo">
            <th className="py-2 font-normal">Selección</th>
            <th className="py-2 font-normal text-right">Modelo</th>
            <th className="py-2 font-normal text-right">Cuota</th>
            <th className="py-2 font-normal text-right">Implícita</th>
            <th className="py-2 font-normal text-right">EV</th>
          </tr>
        </thead>
        <tbody>
          {edges.map((e, i) => {
            const positive = e.ev > 0;
            return (
              <tr key={i} className="border-t border-line">
                <td className="py-2.5">
                  <div>{e.selection}</div>
                  <div className="text-[11px] text-lo">{e.market} · {e.bookmaker}</div>
                </td>
                <td className="py-2.5 text-right num">{pct(e.modelP, 1)}</td>
                <td className="py-2.5 text-right num">{e.odds.toFixed(2)}</td>
                <td className="py-2.5 text-right num text-mid">{pct(1 / e.odds, 1)}</td>
                <td className="py-2.5 text-right num font-semibold" style={{ color: positive ? "var(--neon-up)" : "var(--neon-down)" }}>
                  {positive ? "▲ +" : "▼ "}{(e.ev * 100).toFixed(1)}%
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="mt-3 text-[11px] leading-relaxed text-lo">
        EV = probabilidad del modelo × cuota − 1. La probabilidad implícita incluye el margen de la casa.
        Un EV positivo es una discrepancia estadística, no una garantía: el modelo también se equivoca.
      </p>
    </div>
  );
}
