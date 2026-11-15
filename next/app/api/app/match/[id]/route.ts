import { getViewer } from "@/lib/auth";
import { getMatch } from "@/lib/data";

export const dynamic = "force-dynamic";

/** One match sheet, redacted for the viewer's plan. The page draws it in the browser. */
export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  const viewer = await getViewer().catch(() => null);
  if (!viewer) return Response.json({ error: "auth" }, { status: 401 });
  const { id } = await params;
  const m = await getMatch(decodeURIComponent(id), viewer.tier);
  if (!m) return Response.json({ error: "not_found" }, { status: 404 });
  return Response.json(m, { headers: { "cache-control": "private, no-store" } });
}
