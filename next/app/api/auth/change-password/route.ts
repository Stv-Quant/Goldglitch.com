import { cookies } from "next/headers";
import { getViewer, sameOrigin, SESSION_COOKIE } from "@/lib/auth";
import { sha256Hex } from "@/lib/crypto";
import { getDB } from "@/lib/env";
import { hashPassword, passwordProblem, verifyPassword } from "@/lib/password";

export async function POST(request: Request) {
  if (!sameOrigin(request)) return Response.json({ ok: false, error: "forbidden" }, { status: 403 });
  const viewer = await getViewer();
  if (!viewer) return Response.json({ ok: false, error: "unauthenticated" }, { status: 401 });

  const body = await request.json().catch(() => null);
  const current = String(body?.current ?? "");
  const next = String(body?.next ?? "");

  const db = await getDB();
  const row = await db.prepare("SELECT password_hash FROM users WHERE id = ?").bind(viewer.userId).first<{ password_hash: string | null }>();
  // Users who already have a password must prove it (also when it's a temporary one).
  if (row?.password_hash && !(await verifyPassword(current, row.password_hash))) {
    return Response.json({ ok: false, error: "Tu contraseña actual no coincide." }, { status: 400 });
  }
  if (current && current === next) return Response.json({ ok: false, error: "La nueva contraseña debe ser distinta." }, { status: 400 });
  const problem = passwordProblem(next, viewer.email);
  if (problem) return Response.json({ ok: false, error: problem }, { status: 400 });

  await db
    .prepare("UPDATE users SET password_hash = ?, must_change_password = 0 WHERE id = ?")
    .bind(await hashPassword(next), viewer.userId)
    .run();

  // Sign out every other session: whoever knew the old (temporary) password is out.
  const raw = (await cookies()).get(SESSION_COOKIE)?.value ?? "";
  await db.prepare("DELETE FROM sessions WHERE user_id = ? AND id_hash != ?").bind(viewer.userId, await sha256Hex(raw)).run();

  return Response.json({ ok: true, next: viewer.isAdmin ? "/admin" : "/app" });
}
