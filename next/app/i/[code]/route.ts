import { NextResponse } from "next/server";
import { INVITE_COOKIE, getInviteByCode, inviteState, normalizeCode } from "@/lib/invites";

/** easygoldglitch.com/i/<code>: remembers the invite in this browser and sends the visitor to sign up. */
export async function GET(request: Request, { params }: { params: Promise<{ code: string }> }) {
  const origin = new URL(request.url).origin;
  const code = normalizeCode((await params).code);
  const invite = code ? await getInviteByCode(code) : null;
  const state = invite ? inviteState(invite) : "invalid";
  if (state !== "active") {
    return NextResponse.redirect(new URL(`/acceso?invitacion=${state}`, origin), { status: 303 });
  }
  const res = NextResponse.redirect(new URL("/acceso?invitacion=ok", origin), { status: 303 });
  res.cookies.set(INVITE_COOKIE, code!, {
    httpOnly: true, secure: true, sameSite: "lax", path: "/",
    maxAge: Math.max(60, Math.min(30 * 86400, Math.floor((invite!.expires_at - Date.now()) / 1000))),
  });
  return res;
}
