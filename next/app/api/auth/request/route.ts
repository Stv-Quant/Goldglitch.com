import { issueLoginToken, normalizeEmail } from "@/lib/auth";
import { getEnv } from "@/lib/env";
import { sendMagicLink } from "@/lib/mail";

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const email = normalizeEmail(body?.email);
  if (!email) return Response.json({ ok: false, error: "invalid_email" }, { status: 400 });

  const token = await issueLoginToken(email);
  if (!token) return Response.json({ ok: false, error: "rate_limited" }, { status: 429 });

  const env = await getEnv();
  const origin = env.APP_URL ?? new URL(request.url).origin;
  const link = `${origin}/auth/verify?token=${encodeURIComponent(token)}`;

  const sent = await sendMagicLink(email, link);
  if (!sent) return Response.json({ ok: false, error: "mail_failed" }, { status: 502 });

  return Response.json({ ok: true });
}
