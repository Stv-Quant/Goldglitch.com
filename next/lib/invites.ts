import "server-only";
import { randomToken } from "./crypto";
import { getDB } from "./env";

export const INVITE_COOKIE = "gg_invite";
const DAY = 86_400_000;

export type Invite = {
  id: string; code: string; label: string; max_uses: number; uses: number; expires_at: number;
  gift_plan: "pro" | "elite" | null; gift_days: number | null; created_at: number; revoked_at: number | null;
};

export type InviteState = "active" | "full" | "expired" | "revoked";

export function inviteState(i: Invite, now = Date.now()): InviteState {
  if (i.revoked_at) return "revoked";
  if (i.expires_at <= now) return "expired";
  if (i.uses >= i.max_uses) return "full";
  return "active";
}

export function normalizeCode(v: unknown): string | null {
  const s = String(v ?? "").trim();
  return /^[A-Za-z0-9_-]{6,40}$/.test(s) ? s : null;
}

export async function getInviteByCode(code: string): Promise<Invite | null> {
  return (await getDB()).prepare("SELECT * FROM invites WHERE code = ?").bind(code).first<Invite>();
}

export async function createInvite(o: {
  label: string; maxUses: number; expiresAt: number; giftPlan: "pro" | "elite" | null; giftDays: number | null; adminId: string;
}): Promise<Invite> {
  const db = await getDB();
  const id = crypto.randomUUID();
  const code = randomToken(9).replace(/[^A-Za-z0-9]/g, "").slice(0, 10) || randomToken(12).slice(0, 10);
  const now = Date.now();
  await db
    .prepare(
      `INSERT INTO invites (id, code, label, max_uses, uses, expires_at, gift_plan, gift_days, created_by, created_at)
       VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?, ?)`,
    )
    .bind(id, code, o.label, o.maxUses, o.expiresAt, o.giftPlan, o.giftPlan ? o.giftDays : null, o.adminId, now)
    .run();
  return (await getInviteByCode(code))!;
}

/**
 * Called once, when a brand-new account is created from a magic link that carried an invite.
 * The seat is claimed atomically (cap and deadline checked in the same UPDATE), then the gift plan, if any, is applied.
 */
export async function redeemInvite(code: string, userId: string): Promise<boolean> {
  const db = await getDB();
  const now = Date.now();
  const inv = await db
    .prepare(
      `UPDATE invites SET uses = uses + 1
        WHERE code = ? AND revoked_at IS NULL AND expires_at > ? AND uses < max_uses
        RETURNING id, gift_plan, gift_days`,
    )
    .bind(code, now)
    .first<{ id: string; gift_plan: "pro" | "elite" | null; gift_days: number | null }>();
  if (!inv) return false;
  const stmts = [
    db.prepare("INSERT OR IGNORE INTO invite_redemptions (invite_id, user_id, redeemed_at) VALUES (?, ?, ?)").bind(inv.id, userId, now),
  ];
  if (inv.gift_plan && inv.gift_days) {
    stmts.push(
      db
        .prepare(
          `INSERT INTO subscriptions (user_id, plan, current_period_end, provider, updated_at) VALUES (?, ?, ?, 'admin', ?)
           ON CONFLICT(user_id) DO NOTHING`,
        )
        .bind(userId, inv.gift_plan, now + inv.gift_days * DAY, now),
    );
  }
  await db.batch(stmts);
  return true;
}
