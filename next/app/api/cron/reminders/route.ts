import { audit, requireAdmin, sameOrigin } from "@/lib/auth";
import { safeEqual } from "@/lib/crypto";
import { getDB } from "@/lib/env";
import { runRenewalReminders } from "@/lib/reminders";

/**
 * Runs the daily email job. Called by the Worker's cron trigger (header x-gg-cron = secret kept in D1,
 * created by the scheduled handler) or manually by an admin from /admin/correos.
 */
export async function POST(request: Request) {
  const header = request.headers.get("x-gg-cron");
  let by: string | null = null;
  if (header) {
    const row = await (await getDB()).prepare("SELECT value FROM app_settings WHERE key = 'cron_secret'").first<{ value: string }>();
    if (!row || !safeEqual(row.value, header)) return Response.json({ ok: false }, { status: 401 });
  } else {
    if (!sameOrigin(request)) return Response.json({ ok: false }, { status: 403 });
    const admin = await requireAdmin();
    if (!admin) return Response.json({ ok: false }, { status: 403 });
    by = admin.userId;
  }
  const result = await runRenewalReminders();
  if (by) await audit(by, "reminders_run", null, result);
  return Response.json({ ok: true, ...result });
}
