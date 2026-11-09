export const DEFAULT_TZ = "America/Bogota";

export function pct(p: number, digits = 0): string {
  return `${(p * 100).toFixed(digits)}%`;
}

export function dayKey(ms: number, timeZone = DEFAULT_TZ): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone, year: "numeric", month: "2-digit", day: "2-digit" }).format(ms);
}

export function dayLabel(ms: number, now = Date.now(), timeZone = DEFAULT_TZ): string {
  const k = dayKey(ms, timeZone);
  if (k === dayKey(now, timeZone)) return "Hoy";
  if (k === dayKey(now + 86_400_000, timeZone)) return "Mañana";
  const s = new Intl.DateTimeFormat("es-CO", { timeZone, weekday: "long", day: "numeric", month: "short" }).format(ms);
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export function timeLabel(ms: number, timeZone = DEFAULT_TZ): string {
  return new Intl.DateTimeFormat("es-CO", { timeZone, hour: "2-digit", minute: "2-digit", hour12: false }).format(ms);
}

export function dateLabel(ms: number, timeZone = DEFAULT_TZ): string {
  return new Intl.DateTimeFormat("es-CO", { timeZone, day: "numeric", month: "short", year: "numeric" }).format(ms);
}
