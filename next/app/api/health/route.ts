import { getDB } from "@/lib/env";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const db = await getDB();
    const r = await db.prepare("SELECT 1 AS ok").first<{ ok: number }>();
    return Response.json({ ok: true, db: r?.ok === 1, ts: Date.now() }, { headers: { "cache-control": "no-store" } });
  } catch (e) {
    return Response.json({ ok: false, error: String(e).slice(0, 200) }, { status: 500 });
  }
}
