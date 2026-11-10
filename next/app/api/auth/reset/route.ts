import { createSession, sameOrigin } from "@/lib/auth";
import { sha256Hex } from "@/lib/crypto";
import { getDB } from "@/lib/env";
import { later, sendPasswordChanged } from "@/lib/mail";
import { hashPassword, passwordProblem } from "@/lib/password";

/** Sets a new password from a recovery link, signs out every session and signs this browser in. */
export async function POST(request: Request) {
  if (!sameOrigin(request)) return Response.json({ ok: false }, { status: 403 });
  const body = await request.json().catch(() => null);
  const token = String(body?.token ?? "");
  const password = String(body?.password ?? "");
  if (token.length < 20) return Response.json({ ok: false, error: "El enlace no es válido." }, { status: 400 });

  const db = await getDB();
  const now = Date.now();
  const hash = await sha256Hex(token);
  const row = await db
    .prepare(
      `SELECT r.user_id, u.email, u.status, u.is_admin FROM password_resets r JOIN users u ON u.id = r.user_id
        WHERE r.token_hash = ? AND r.used_at IS NULL AND r.expires_at > ?`,
    )
    .bind(hash, now)
    .first<{ user_id: string; email: string; status: string; is_admin: number }>();
  if (!row || row.status === "suspended") {
    return Response.json({ ok: false, error: "El enlace venció o ya se usó. Pide uno nuevo." }, { status: 400 });
  }
  // Validate before burning the token, so a weak password doesn't cost the user their link.
  const problem = passwordProblem(password, row.email);
  if (problem) return Response.json({ ok: false, error: problem }, { status: 400 });

  const claimed = await db
    .prepare("UPDATE password_resets SET used_at = ? WHERE token_hash = ? AND used_at IS NULL AND expires_at > ? RETURNING user_id")
    .bind(now, hash, now)
    .first();
  if (!claimed) return Response.json({ ok: false, error: "El enlace venció o ya se usó. Pide uno nuevo." }, { status: 400 });

  await db.batch([
    db.prepare("UPDATE users SET password_hash = ?, must_change_password = 0, last_login_at = ? WHERE id = ?").bind(await hashPassword(password), now, row.user_id),
    db.prepare("DELETE FROM sessions WHERE user_id = ?").bind(row.user_id),
    db.prepare("UPDATE password_resets SET used_at = ? WHERE user_id = ? AND used_at IS NULL").bind(now, row.user_id),
  ]);
  await createSession(row.user_id, request.headers.get("user-agent"));
  await later(sendPasswordChanged({ id: row.user_id, email: row.email }));
  return Response.json({ ok: true, next: row.is_admin ? "/admin" : "/app" });
}
