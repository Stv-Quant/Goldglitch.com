import { issueLoginToken, normalizeEmail } from "@/lib/auth";
import { INVITE_COOKIE, normalizeCode } from "@/lib/invites";
import { appUrl, sendMagicLink } from "@/lib/mail";
import { cookies } from "next/headers";

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const email = normalizeEmail(body?.email);
  if (!email) return Response.json({ ok: false, error: "invalid_email" }, { status: 400 });

  // An invite opened earlier in this browser (/i/<code>) rides along with the magic link.
  const invite = normalizeCode(body?.invite) ?? normalizeCode((await cookies()).get(INVITE_COOKIE)?.value);
  const token = await issueLoginToken(email, invite);
  if (!token) return Response.json({ ok: false, error: "rate_limited" }, { status: 429 });

  const origin = await appUrl();
  const link = `${origin}/auth/verify?token=${encodeURIComponent(token)}`;

  const sent = await sendMagicLink(email, link);
  if (!sent) return Response.json({ ok: false, error: "mail_failed" }, { status: 502 });

  return Response.json({ ok: true });
}
