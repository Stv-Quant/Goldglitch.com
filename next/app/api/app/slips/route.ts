import { getViewer, sameOrigin } from "@/lib/auth";
import { hasTier } from "@/lib/plans";
import { listSlips, resolveLegs, saveSlip } from "@/lib/slips";

export const dynamic = "force-dynamic";

async function proViewer() {
  const v = await getViewer().catch(() => null);
  if (!v) return { error: Response.json({ error: "auth" }, { status: 401 }) };
  if (!hasTier(v.tier, "pro")) return { error: Response.json({ error: "Las combinadas se usan con tu cuenta gratis." }, { status: 403 }) };
  return { v };
}

export async function GET() {
  const { v, error } = await proViewer();
  if (error) return error;
  return Response.json({ slips: await listSlips(v.userId) }, { headers: { "cache-control": "private, no-store" } });
}

export async function POST(req: Request) {
  if (!sameOrigin(req)) return Response.json({ error: "origin" }, { status: 403 });
  const { v, error } = await proViewer();
  if (error) return error;
  const body = (await req.json().catch(() => null)) as { name?: unknown; legs?: unknown } | null;
  const raw = Array.isArray(body?.legs) ? body!.legs : [];
  const wanted = raw
    .filter((l): l is { matchId: string; label: string } =>
      !!l && typeof (l as { matchId?: unknown }).matchId === "string" && typeof (l as { label?: unknown }).label === "string")
    .map((l) => ({ matchId: l.matchId.slice(0, 128), label: l.label.slice(0, 200) }));
  if (wanted.length !== raw.length) return Response.json({ error: "Selección inválida." }, { status: 400 });
  const legs = await resolveLegs(wanted);
  if (typeof legs === "string") return Response.json({ error: legs }, { status: 400 });
  const name = typeof body?.name === "string" && body.name.trim() ? body.name.trim().slice(0, 60) : null;
  const id = await saveSlip(v.userId, name, legs);
  if (!id) return Response.json({ error: "Llegaste al máximo de combinadas guardadas: borra alguna." }, { status: 400 });
  return Response.json({ ok: true, id });
}
