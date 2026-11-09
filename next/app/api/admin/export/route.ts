import { audit, requireAdmin } from "@/lib/auth";
import { listPayments, listUsers, type Segment } from "@/lib/admin";

function csv(rows: (string | number | null)[][]): string {
  const esc = (v: string | number | null) => {
    const s = v === null || v === undefined ? "" : String(v);
    // Neutralize spreadsheet formula injection, then quote.
    const safe = /^[=+\-@\t\r]/.test(s) ? `'${s}` : s;
    return `"${safe.replace(/"/g, '""')}"`;
  };
  return "﻿" + rows.map((r) => r.map(esc).join(",")).join("\r\n");
}

const iso = (ms: number | null) => (ms ? new Date(ms).toISOString() : "");

export async function GET(request: Request) {
  const admin = await requireAdmin();
  if (!admin) return new Response("forbidden", { status: 403 });
  const url = new URL(request.url);
  const what = url.searchParams.get("what");

  let body: string;
  let name: string;
  if (what === "payments") {
    const rows = await listPayments(url.searchParams.get("status") ?? "", url.searchParams.get("q") ?? "");
    body = csv([
      ["referencia", "correo", "plan", "periodo", "monto_cop", "estado", "wompi_tx", "creado", "actualizado"],
      ...rows.map((p) => [p.id, p.email ?? "", p.plan, p.period, p.amount_in_cents / 100, p.status, p.provider_tx_id, iso(p.created_at), iso(p.updated_at)]),
    ]);
    name = "pagos";
  } else {
    const all: Awaited<ReturnType<typeof listUsers>>["rows"] = [];
    for (let page = 0; page < 200; page++) {
      const r = await listUsers(url.searchParams.get("q") ?? "", (url.searchParams.get("seg") ?? "all") as Segment, page, 500);
      all.push(...r.rows);
      if (r.rows.length < 500) break;
    }
    const now = Date.now();
    body = csv([
      ["id", "correo", "plan", "estado_plan", "vence", "origen_plan", "total_pagado_cop", "pagos", "registro", "ultimo_ingreso", "estado_cuenta", "admin", "etiquetas"],
      ...all.map((u) => [
        u.id, u.email, u.plan ?? "free",
        u.current_period_end && u.current_period_end > now ? "activo" : u.plan ? "vencido" : "free",
        iso(u.current_period_end), u.provider, u.paid_cents / 100, u.payments_n, iso(u.created_at), iso(u.last_login_at),
        u.status, u.is_admin ? "si" : "no", u.tags,
      ]),
    ]);
    name = "usuarios";
  }
  await audit(admin.userId, `export_${name}`, null);
  const stamp = new Date().toISOString().slice(0, 10);
  return new Response(body, {
    headers: {
      "content-type": "text/csv; charset=utf-8",
      "content-disposition": `attachment; filename="goldglitch-${name}-${stamp}.csv"`,
      "cache-control": "no-store",
    },
  });
}
