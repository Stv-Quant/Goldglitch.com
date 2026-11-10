import { normalizeEmail, recordAttempt, sameOrigin, tooManyAttempts } from "@/lib/auth";
import { randomToken, sha256Hex } from "@/lib/crypto";
import { getDB } from "@/lib/env";
import { appUrl, later, sendPasswordReset } from "@/lib/mail";

const TTL_MS = 30 * 60 * 1000;

/**
 * Starts a password recovery. Always answers ok so the form never reveals which emails have an account.
 * Limits: 3 requests per email and 8 per IP per 15 min (shared auth_attempts table).
 */
export async function POST(request: Request) {
  if (!sameOrigin(request)) return Response.json({ ok: false }, { status: 403 });
  const body = await request.json().catch(() => null);
  const email = normalizeEmail(body?.email);
  if (!email) return Response.json({ ok: false, error: "Escribe un correo válido." }, { status: 400 });

  const ip = request.headers.get("cf-connecting-ip") ?? "unknown";
  if ((await tooManyAttempts(`reset:${email}`, 3)) || (await tooManyAttempts(`reset-ip:${ip}`))) {
    return Response.json({ ok: false, error: "Demasiados intentos. Espera 15 minutos." }, { status: 429 });
  }
  await recordAttempt(`reset:${email}`, false);
  await recordAttempt(`reset-ip:${ip}`, false);

  const db = await getDB();
  const user = await db.prepare("SELECT id, email, status FROM users WHERE email = ?").bind(email).first<{ id: string; email: string; status: string }>();
  if (user && user.status !== "suspended") {
    const token = randomToken(32);
    const now = Date.now();
    await db
      .prepare("INSERT INTO password_resets (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)")
      .bind(await sha256Hex(token), user.id, now, now + TTL_MS)
      .run();
    const link = `${await appUrl()}/acceso/restablecer?token=${encodeURIComponent(token)}`;
    await later(sendPasswordReset(user, link));
  }
  return Response.json({ ok: true });
}
