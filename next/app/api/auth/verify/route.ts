import { NextResponse } from "next/server";
import { consumeLoginToken, createSession } from "@/lib/auth";
import { later, sendWelcome } from "@/lib/mail";

// POST-only on purpose: mail scanners prefetch GET links and would burn single-use tokens.
export async function POST(request: Request) {
  const origin = new URL(request.url).origin;
  const form = await request.formData().catch(() => null);
  const token = String(form?.get("token") ?? "");

  const user = token.length >= 20 ? await consumeLoginToken(token) : null;
  if (!user) return NextResponse.redirect(new URL("/acceso?error=link", origin), { status: 303 });

  await createSession(user.id, request.headers.get("user-agent"));
  if (user.isNew) await later(sendWelcome(user));
  return NextResponse.redirect(new URL("/app", origin), { status: 303 });
}
