import { audit, requireAdmin, sameOrigin } from "@/lib/auth";
import { getDB } from "@/lib/env";

/** { action: "revoke" } stops new sign-ups through the link. People already registered keep their account. */
export async function POST(request: Request, { params }: { params: Promise<{ id: string }> }) {
  if (!sameOrigin(request)) return Response.json({ ok: false }, { status: 403 });
  const admin = await requireAdmin();
  if (!admin) return Response.json({ ok: false }, { status: 403 });
  const { id } = await params;
  const b = await request.json().catch(() => ({}));
  if (b.action !== "revoke") return Response.json({ ok: false, error: "Acción no válida." }, { status: 400 });
  const r = await (await getDB()).prepare("UPDATE invites SET revoked_at = ? WHERE id = ? AND revoked_at IS NULL").bind(Date.now(), id).run();
  if (!r.meta.changes) return Response.json({ ok: false, error: "La invitación no existe o ya estaba desactivada." }, { status: 404 });
  await audit(admin.userId, "invite_revoke", null, { id });
  return Response.json({ ok: true });
}
