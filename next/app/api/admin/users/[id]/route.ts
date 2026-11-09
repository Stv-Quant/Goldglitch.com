import { audit, requireAdmin, sameOrigin } from "@/lib/auth";
import { getDB } from "@/lib/env";

const DAY = 24 * 60 * 60 * 1000;

type Body =
  | { action: "grant"; plan: "pro" | "elite"; days: number }
  | { action: "revoke" }
  | { action: "note"; body: string }
  | { action: "tags"; tags: string }
  | { action: "suspend" | "activate" | "make_admin" | "remove_admin" | "logout" | "force_password_change" };

export async function POST(request: Request, { params }: { params: Promise<{ id: string }> }) {
  if (!sameOrigin(request)) return Response.json({ ok: false, error: "forbidden" }, { status: 403 });
  const admin = await requireAdmin();
  if (!admin) return Response.json({ ok: false, error: "forbidden" }, { status: 403 });

  const { id } = await params;
  const b = (await request.json().catch(() => null)) as Body | null;
  if (!b?.action) return Response.json({ ok: false, error: "invalid" }, { status: 400 });

  const db = await getDB();
  const target = await db.prepare("SELECT id, email, password_hash FROM users WHERE id = ?").bind(id).first<{ id: string; email: string; password_hash: string | null }>();
  if (!target) return Response.json({ ok: false, error: "not_found" }, { status: 404 });
  const self = target.id === admin.userId;
  const now = Date.now();

  switch (b.action) {
    case "grant": {
      const days = Math.round(Number(b.days));
      if (!["pro", "elite"].includes(b.plan) || !(days >= 1 && days <= 3650)) return Response.json({ ok: false, error: "Plan o días inválidos." }, { status: 400 });
      const ext = days * DAY;
      await db
        .prepare(
          `INSERT INTO subscriptions (user_id, plan, current_period_end, provider, updated_at) VALUES (?1, ?2, ?3 + ?4, 'admin', ?3)
           ON CONFLICT(user_id) DO UPDATE SET
             current_period_end = CASE WHEN subscriptions.plan = excluded.plan AND subscriptions.current_period_end > ?3
                                       THEN subscriptions.current_period_end + ?4 ELSE ?3 + ?4 END,
             plan = excluded.plan, provider = 'admin', updated_at = ?3`,
        )
        .bind(id, b.plan, now, ext)
        .run();
      await audit(admin.userId, "grant_plan", id, { plan: b.plan, days });
      break;
    }
    case "revoke":
      await db.prepare("UPDATE subscriptions SET current_period_end = ?, updated_at = ? WHERE user_id = ?").bind(now, now, id).run();
      await audit(admin.userId, "revoke_plan", id);
      break;
    case "note": {
      const body = String(b.body ?? "").trim().slice(0, 4000);
      if (!body) return Response.json({ ok: false, error: "La nota está vacía." }, { status: 400 });
      await db.prepare("INSERT INTO crm_notes (id, user_id, author_id, body, created_at) VALUES (?, ?, ?, ?, ?)").bind(crypto.randomUUID(), id, admin.userId, body, now).run();
      await audit(admin.userId, "add_note", id);
      break;
    }
    case "tags": {
      const tags = String(b.tags ?? "").split(",").map((t) => t.trim().toLowerCase()).filter(Boolean).slice(0, 12).join(",");
      await db.prepare("UPDATE users SET tags = ? WHERE id = ?").bind(tags || null, id).run();
      await audit(admin.userId, "set_tags", id, { tags });
      break;
    }
    case "suspend":
      if (self) return Response.json({ ok: false, error: "No puedes suspender tu propia cuenta." }, { status: 400 });
      await db.batch([
        db.prepare("UPDATE users SET status = 'suspended' WHERE id = ?").bind(id),
        db.prepare("DELETE FROM sessions WHERE user_id = ?").bind(id),
      ]);
      await audit(admin.userId, "suspend", id);
      break;
    case "activate":
      await db.prepare("UPDATE users SET status = 'active' WHERE id = ?").bind(id).run();
      await audit(admin.userId, "activate", id);
      break;
    case "make_admin":
      await db.prepare("UPDATE users SET is_admin = 1 WHERE id = ?").bind(id).run();
      await audit(admin.userId, "make_admin", id);
      break;
    case "remove_admin":
      if (self) return Response.json({ ok: false, error: "No puedes quitarte el rol de administrador a ti mismo." }, { status: 400 });
      await db.prepare("UPDATE users SET is_admin = 0 WHERE id = ?").bind(id).run();
      await audit(admin.userId, "remove_admin", id);
      break;
    case "logout":
      if (self) return Response.json({ ok: false, error: "Usa «Cerrar sesión» para tu propia cuenta." }, { status: 400 });
      await db.prepare("DELETE FROM sessions WHERE user_id = ?").bind(id).run();
      await audit(admin.userId, "logout_all", id);
      break;
    case "force_password_change":
      if (!target.password_hash) return Response.json({ ok: false, error: "Este usuario entra solo con enlace; no tiene contraseña." }, { status: 400 });
      await db.prepare("UPDATE users SET must_change_password = 1 WHERE id = ?").bind(id).run();
      await audit(admin.userId, "force_password_change", id);
      break;
    default:
      return Response.json({ ok: false, error: "invalid" }, { status: 400 });
  }
  return Response.json({ ok: true });
}
