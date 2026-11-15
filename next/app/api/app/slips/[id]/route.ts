import { getViewer, sameOrigin } from "@/lib/auth";
import { deleteSlip } from "@/lib/slips";

export async function DELETE(req: Request, { params }: { params: Promise<{ id: string }> }) {
  if (!sameOrigin(req)) return Response.json({ error: "origin" }, { status: 403 });
  const v = await getViewer().catch(() => null);
  if (!v) return Response.json({ error: "auth" }, { status: 401 });
  const { id } = await params;
  return Response.json({ ok: await deleteSlip(v.userId, id) });
}
