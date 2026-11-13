import { audit, requireAdmin, sameOrigin } from "@/lib/auth";
import { createInvite } from "@/lib/invites";

const DAY = 86_400_000;

/** Creates an invitation link. Body: { label, maxUses, expiresOn: "YYYY-MM-DD" (Colombia), giftPlan?, giftDays? } */
export async function POST(request: Request) {
  if (!sameOrigin(request)) return Response.json({ ok: false }, { status: 403 });
  const admin = await requireAdmin();
  if (!admin) return Response.json({ ok: false }, { status: 403 });
  const b = await request.json().catch(() => ({}));

  const label = String(b.label ?? "").trim().slice(0, 80);
  const maxUses = Math.round(Number(b.maxUses));
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(b.expiresOn ?? ""));
  // End of that day in Colombia (UTC-5): 23:59:59.999 local = next day 04:59:59.999 UTC.
  const expiresAt = m ? Date.UTC(+m[1], +m[2] - 1, +m[3] + 1, 5) - 1 : NaN;
  const giftPlan = b.giftPlan === "pro" || b.giftPlan === "elite" ? b.giftPlan : null;
  const giftDays = giftPlan ? Math.round(Number(b.giftDays)) : null;

  if (!label) return Response.json({ ok: false, error: "Ponle un nombre a la invitación." }, { status: 400 });
  if (!(maxUses >= 1 && maxUses <= 100_000)) return Response.json({ ok: false, error: "El máximo de personas debe estar entre 1 y 100.000." }, { status: 400 });
  if (!Number.isFinite(expiresAt) || expiresAt <= Date.now()) return Response.json({ ok: false, error: "La fecha límite debe ser hoy o una fecha futura." }, { status: 400 });
  if (expiresAt > Date.now() + 730 * DAY) return Response.json({ ok: false, error: "La fecha límite no puede pasar de 2 años." }, { status: 400 });
  if (giftPlan && !(giftDays! >= 1 && giftDays! <= 365)) return Response.json({ ok: false, error: "Los días de regalo deben estar entre 1 y 365." }, { status: 400 });

  const invite = await createInvite({ label, maxUses, expiresAt, giftPlan, giftDays, adminId: admin.userId });
  await audit(admin.userId, "invite_create", null, { id: invite.id, label, maxUses, expiresAt, giftPlan, giftDays });
  return Response.json({ ok: true, invite });
}
