import { cookies } from "next/headers";
import { createSession, normalizeEmail, normalizeUsername, recordAttempt, sameOrigin, tooManyAttempts } from "@/lib/auth";
import { getDB } from "@/lib/env";
import { INVITE_COOKIE, normalizeCode, redeemInvite } from "@/lib/invites";
import { later, sendWelcome } from "@/lib/mail";
import { hashPassword, passwordProblem } from "@/lib/password";

/** Sign-up with username, email and password. Logs the user in and sends the welcome email. */
export async function POST(request: Request) {
  if (!sameOrigin(request)) return Response.json({ ok: false, error: "forbidden" }, { status: 403 });
  const body = await request.json().catch(() => null);
  const username = normalizeUsername(body?.username);
  const email = normalizeEmail(body?.email);
  const password = String(body?.password ?? "");
  if (!username) return Response.json({ ok: false, error: "invalid_username" }, { status: 400 });
  if (!email) return Response.json({ ok: false, error: "invalid_email" }, { status: 400 });
  if (body?.adult !== true) return Response.json({ ok: false, error: "adult" }, { status: 400 });
  const weak = passwordProblem(password, email, username);
  if (weak) return Response.json({ ok: false, error: "weak_password", message: weak }, { status: 400 });

  const ip = request.headers.get("cf-connecting-ip") ?? "unknown";
  if (await tooManyAttempts(`signup:${ip}`, 6)) return Response.json({ ok: false, error: "rate_limited" }, { status: 429 });

  const db = await getDB();
  const [byEmail, byName] = await Promise.all([
    db.prepare("SELECT 1 AS x FROM users WHERE email = ?").bind(email).first(),
    db.prepare("SELECT 1 AS x FROM users WHERE lower(display_name) = lower(?)").bind(username).first(),
  ]);
  if (byEmail) { await recordAttempt(`signup:${ip}`, false); return Response.json({ ok: false, error: "email_taken" }, { status: 409 }); }
  if (byName) return Response.json({ ok: false, error: "username_taken" }, { status: 409 });

  const id = crypto.randomUUID();
  const now = Date.now();
  const inserted = await db
    .prepare(
      `INSERT INTO users (id, email, display_name, password_hash, created_at, last_login_at) VALUES (?, ?, ?, ?, ?, ?)
       ON CONFLICT(email) DO NOTHING RETURNING id`,
    )
    .bind(id, email, username, await hashPassword(password), now, now)
    .first<{ id: string }>();
  if (!inserted) return Response.json({ ok: false, error: "email_taken" }, { status: 409 });
  await recordAttempt(`signup:${ip}`, true);

  const jar = await cookies();
  const invite = normalizeCode(jar.get(INVITE_COOKIE)?.value);
  if (invite) { await redeemInvite(invite, id).catch(() => false); jar.delete(INVITE_COOKIE); }

  await createSession(id, request.headers.get("user-agent"));
  await later(sendWelcome({ id, email, name: username }));
  return Response.json({ ok: true, next: "/app" });
}
