import { createSession, normalizeEmail, recordAttempt, sameOrigin, tooManyAttempts } from "@/lib/auth";
import { getDB } from "@/lib/env";
import { verifyPassword } from "@/lib/password";

// Constant work for unknown accounts so response time doesn't reveal which emails exist.
const DUMMY = "pbkdf2$100000$AAAAAAAAAAAAAAAAAAAAAA==$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";

export async function POST(request: Request) {
  if (!sameOrigin(request)) return Response.json({ ok: false, error: "forbidden" }, { status: 403 });
  const body = await request.json().catch(() => null);
  const email = normalizeEmail(body?.email);
  const password = String(body?.password ?? "");
  if (!email || !password) return Response.json({ ok: false, error: "invalid" }, { status: 400 });

  const ip = request.headers.get("cf-connecting-ip") ?? "unknown";
  if ((await tooManyAttempts(`email:${email}`)) || (await tooManyAttempts(`ip:${ip}`))) {
    return Response.json({ ok: false, error: "rate_limited" }, { status: 429 });
  }

  const db = await getDB();
  const user = await db
    .prepare("SELECT id, password_hash, status, must_change_password FROM users WHERE email = ?")
    .bind(email)
    .first<{ id: string; password_hash: string | null; status: string; must_change_password: number }>();

  const ok = await verifyPassword(password, user?.password_hash ?? DUMMY);
  if (!user || !ok || !user.password_hash) {
    await recordAttempt(`email:${email}`, false);
    await recordAttempt(`ip:${ip}`, false);
    return Response.json({ ok: false, error: "bad_credentials" }, { status: 401 });
  }
  if (user.status === "suspended") return Response.json({ ok: false, error: "suspended" }, { status: 403 });

  await recordAttempt(`email:${email}`, true);
  await db.prepare("UPDATE users SET last_login_at = ? WHERE id = ?").bind(Date.now(), user.id).run();
  await createSession(user.id, request.headers.get("user-agent"));
  return Response.json({ ok: true, next: user.must_change_password ? "/acceso/nueva-clave" : "/app" });
}
