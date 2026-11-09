import { formatCOP } from "@/lib/plans";
import type { DailyPoint } from "@/lib/admin";

/**
 * A KPI with its definition one click away. `how` answers "how is this computed",
 * `why` answers "what should I do with it" — every number in the panel carries both.
 */
export function Metric({
  label, value, sub, how, why, tone, delta,
}: {
  label: string; value: string; sub?: string; how: string; why?: string;
  tone?: "gold" | "up" | "down"; delta?: { value: number; good: "up" | "down" } | null;
}) {
  const color = tone === "gold" ? "var(--gold)" : tone === "up" ? "var(--neon-up)" : tone === "down" ? "var(--neon-down)" : "var(--text-hi)";
  return (
    <div className="card p-4 sm:p-5 flex flex-col">
      <div className="text-xs text-lo">{label}</div>
      <div className="mt-1 flex items-baseline gap-2">
        <span className="num text-2xl sm:text-[1.75rem] font-semibold break-all" style={{ color }}>{value}</span>
        {delta && Number.isFinite(delta.value) && <Delta {...delta} />}
      </div>
      {sub && <div className="mt-0.5 text-[12px] text-mid">{sub}</div>}
      <details className="metric-help mt-auto pt-3 text-[12px] text-lo">
        <summary className="cursor-pointer select-none hover:text-hi">¿Qué mide?</summary>
        <p className="mt-2 leading-relaxed">{how}</p>
        {why && <p className="mt-1.5 leading-relaxed text-mid">{why}</p>}
      </details>
    </div>
  );
}

function Delta({ value, good }: { value: number; good: "up" | "down" }) {
  const up = value >= 0;
  const positive = good === "up" ? up : !up;
  return (
    <span className="num text-[11px]" style={{ color: positive ? "var(--neon-up)" : "var(--neon-down)" }}
      title="Variación frente a los 30 días anteriores">
      {up ? "▲" : "▼"} {Math.abs(value * 100).toFixed(0)}%
    </span>
  );
}

/** Change vs the previous period; null when the base is too small for a % to mean anything. */
export function pctChange(cur: number, prev: number, minBase = 1): number | null {
  if (prev < minBase) return null;
  return (cur - prev) / prev;
}

/** 30-day daily bars. SVG (30 marks), direct labels for total, peak and last day. */
export function DailyBars({ data, money, title, how }: { data: DailyPoint[]; money?: boolean; title: string; how: string }) {
  const W = 600, H = 150, pad = 4;
  const max = Math.max(1, ...data.map((d) => d.value));
  const bw = (W - pad * 2) / data.length;
  const total = data.reduce((a, d) => a + d.value, 0);
  const fmt = (v: number) => (money ? formatCOP(v) : v.toLocaleString("es-CO"));
  const peak = data.reduce((a, d) => (d.value > a.value ? d : a), data[0]);
  return (
    <figure className="card p-5">
      <figcaption className="flex flex-wrap items-baseline justify-between gap-2">
        <span className="text-sm text-mid">{title}</span>
        <span className="num text-sm"><span className="text-lo">30 días:</span> <span className="text-hi">{fmt(total)}</span></span>
      </figcaption>
      <svg viewBox={`0 0 ${W} ${H + 18}`} className="mt-4 w-full h-auto" role="img"
        aria-label={`${title}. Total 30 días ${fmt(total)}. Máximo ${fmt(peak.value)} el ${peak.day}.`}>
        <line x1={0} x2={W} y1={H} y2={H} stroke="var(--border-soft)" />
        {data.map((d, i) => {
          const h = (d.value / max) * (H - 8);
          return (
            <rect key={d.day} x={pad + i * bw + bw * 0.15} y={H - h} width={bw * 0.7} height={Math.max(h, d.value ? 2 : 0)} rx={2}
              fill={d === peak && d.value ? "var(--gold)" : "rgba(212,175,55,0.45)"}>
              <title>{`${d.day}: ${fmt(d.value)}`}</title>
            </rect>
          );
        })}
        <text x={0} y={H + 14} fontSize="10" fill="var(--text-lo)" className="num">{data[0]?.day.slice(5)}</text>
        <text x={W} y={H + 14} fontSize="10" fill="var(--text-lo)" textAnchor="end" className="num">{data[data.length - 1]?.day.slice(5)}</text>
      </svg>
      <details className="metric-help mt-2 text-[12px] text-lo">
        <summary className="cursor-pointer select-none hover:text-hi">¿Cómo se calcula?</summary>
        <p className="mt-2 leading-relaxed">{how}</p>
      </details>
    </figure>
  );
}

export function Badge({ children, tone = "line" }: { children: React.ReactNode; tone?: "gold" | "up" | "down" | "line" | "flare" }) {
  const styles: Record<string, string> = {
    gold: "border-[var(--border-glass)] text-gold",
    up: "border-[rgba(46,242,160,.35)] text-up",
    down: "border-[rgba(255,90,60,.4)] text-down",
    flare: "border-[var(--flare)] text-flare",
    line: "border-line text-lo",
  };
  return <span className={`inline-flex items-center rounded-full border px-2 py-0.5 num text-[10px] tracking-[0.12em] uppercase ${styles[tone]}`}>{children}</span>;
}

export function SectionTitle({ title, children }: { title: string; children?: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3">
      <h2 className="text-lg font-semibold">{title}</h2>
      {children}
    </div>
  );
}

const TZ = "America/Bogota";
export function dt(ms: number | null | undefined): string {
  if (!ms) return "—";
  return new Intl.DateTimeFormat("es-CO", { timeZone: TZ, day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", hour12: false }).format(ms);
}
export function ago(ms: number | null | undefined): string {
  if (!ms) return "nunca";
  const s = Math.round((Date.now() - ms) / 1000);
  if (s < 60) return "hace segundos";
  const m = Math.round(s / 60);
  if (m < 60) return `hace ${m} min`;
  const h = Math.round(m / 60);
  if (h < 48) return `hace ${h} h`;
  return `hace ${Math.round(h / 24)} d`;
}

export const STATUS_TONE: Record<string, "up" | "gold" | "down" | "line"> = { APPROVED: "up", PENDING: "gold", DECLINED: "down", VOIDED: "down", ERROR: "down" };
export const STATUS_LABEL: Record<string, string> = { APPROVED: "Aprobado", PENDING: "Pendiente", DECLINED: "Rechazado", VOIDED: "Anulado", ERROR: "Error" };
