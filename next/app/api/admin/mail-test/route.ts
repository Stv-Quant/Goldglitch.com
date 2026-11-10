import { audit, requireAdmin, sameOrigin } from "@/lib/auth";
import { sendTestEmail } from "@/lib/mail";

/** Sends a test email to the signed-in admin. */
export async function POST(request: Request) {
  if (!sameOrigin(request)) return Response.json({ ok: false }, { status: 403 });
  const admin = await requireAdmin();
  if (!admin) return Response.json({ ok: false }, { status: 403 });
  const ok = await sendTestEmail(admin.email, admin.userId);
  await audit(admin.userId, "mail_test", null, { ok });
  return Response.json({ ok });
}
