import { cookies } from "next/headers";
import { requireAdmin, sameOrigin, VIEW_AS_COOKIE } from "@/lib/auth";

export async function POST(request: Request) {
  if (!sameOrigin(request)) return Response.json({ ok: false }, { status: 403 });
  if (!(await requireAdmin())) return Response.json({ ok: false }, { status: 403 });
  const body = await request.json().catch(() => null);
  const tier = body?.tier;
  if (!["free", "pro", "elite"].includes(tier)) return Response.json({ ok: false }, { status: 400 });
  (await cookies()).set(VIEW_AS_COOKIE, tier, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 30 * 24 * 60 * 60,
  });
  return Response.json({ ok: true });
}
