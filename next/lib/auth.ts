import "server-only";
import { cookies } from "next/headers";
import { cache } from "react";
import { getDB } from "./env";
import { randomToken, sha256Hex } from "./crypto";
import type { Tier } from "./plans";

export const SESSION_COOKIE = "gg_session";
/** Admin-only preview: see the product exactly as a Free / Pro / Elite member would. */
export const VIEW_AS_COOKIE = "gg_view_as";
const SESSION_TTL_MS = 30 * 24 * 60 * 60 * 1000;
const LOGIN_TOKEN_TTL_MS = 15 * 60 * 1000;
const LOGIN_TOKENS_PER_WINDOW = 3;

export type Viewer = {
  userId: string;
  email: string;
  isAdmin: boolean;
  /** Effective tier used for gating (for admins: their "view as" choice, default elite). */
  tier: Tier;
  /** The member's own paid tier, ignoring admin preview. */
  ownTier: Tier;
  viewingAs: Tier | null;
  periodEnd: number | null;
  mustChangePassword: boolean;
};

export function normalizeEmail(raw: unknown): string | null {
  const e = String(raw ?? "").trim().toLowerCase();
  if (e.length < 6 || e.length > 254) return null;
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(e) ? e : null;
}

/** Issues a single-use login token. Returns null when rate limited. */
export async function issueLoginToken(email: string): Promise<string | null> {
  const db = await getDB();
  const now = Date.now();
  const recent = await db
    .prepare("SELECT COUNT(*) AS n FROM login_tokens WHERE email = ? AND created_at > ?")
    .bind(email, now - LOGIN_TOKEN_TTL_MS)
    .first<{ n: number }>();
  if ((recent?.n ?? 0) >= LOGIN_TOKENS_PER_WINDOW) return null;

  const token = randomToken(32);
  await db
    .prepare("INSERT INTO login_tokens (token_hash, email, created_at, expires_at) VALUES (?, ?, ?, ?)")
    .bind(await sha256Hex(token), email, now, now + LOGIN_TOKEN_TTL_MS)
    .run();
  return token;
}

/** Consumes a login token atomically and returns the (possibly new) user id. */
export async function consumeLoginToken(token: string): Promise<string | null> {
  const db = await getDB();
  const now = Date.now();
  const hash = await sha256Hex(token);

  // Single UPDATE ... RETURNING makes consumption race-free.
  const row = await db
    .prepare(
      "UPDATE login_tokens SET used_at = ? WHERE token_hash = ? AND used_at IS NULL AND expires_at > ? RETURNING email",
    )
    .bind(now, hash, now)
    .first<{ email: string }>();
  if (!row) return null;

  const userId = crypto.randomUUID();
  const user = await db
    .prepare(
      `INSERT INTO users (id, email, created_at, last_login_at) VALUES (?, ?, ?, ?)
       ON CONFLICT(email) DO UPDATE SET last_login_at = excluded.last_login_at
       RETURNING id`,
    )
    .bind(userId, row.email, now, now)
    .first<{ id: string }>();
  return user?.id ?? null;
}

export async function createSession(userId: string, userAgent: string | null): Promise<void> {
  const db = await getDB();
  const raw = randomToken(32);
  const now = Date.now();
  await db
    .prepare("INSERT INTO sessions (id_hash, user_id, created_at, expires_at, user_agent) VALUES (?, ?, ?, ?, ?)")
    .bind(await sha256Hex(raw), userId, now, now + SESSION_TTL_MS, userAgent?.slice(0, 200) ?? null)
    .run();

  const jar = await cookies();
  jar.set(SESSION_COOKIE, raw, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: SESSION_TTL_MS / 1000,
  });
}

export async function destroySession(): Promise<void> {
  const jar = await cookies();
  const raw = jar.get(SESSION_COOKIE)?.value;
  if (raw) {
    const db = await getDB();
    await db.prepare("DELETE FROM sessions WHERE id_hash = ?").bind(await sha256Hex(raw)).run();
  }
  jar.delete(SESSION_COOKIE);
}

/** Resolves the current viewer once per request. */
export const getViewer = cache(async (): Promise<Viewer | null> => {
  const jar = await cookies();
  const raw = jar.get(SESSION_COOKIE)?.value;
  if (!raw) return null;

  const db = await getDB();
  const now = Date.now();
  const row = await db
    .prepare(
      `SELECT u.id, u.email, u.is_admin, u.status, u.must_change_password, s2.plan, s2.current_period_end
         FROM sessions s
         JOIN users u ON u.id = s.user_id
         LEFT JOIN subscriptions s2 ON s2.user_id = u.id
        WHERE s.id_hash = ? AND s.expires_at > ?`,
    )
    .bind(await sha256Hex(raw), now)
    .first<{
      id: string; email: string; is_admin: number; status: string; must_change_password: number;
      plan: "pro" | "elite" | null; current_period_end: number | null;
    }>();
  if (!row || row.status === "suspended") return null;

  const active = row.plan !== null && row.current_period_end !== null && row.current_period_end > now;
  const ownTier: Tier = active ? row.plan! : "free";
  const isAdmin = row.is_admin === 1;
  let viewingAs: Tier | null = null;
  if (isAdmin) {
    const v = jar.get(VIEW_AS_COOKIE)?.value;
    viewingAs = v === "free" || v === "pro" || v === "elite" ? v : "elite";
  }
  return {
    userId: row.id,
    email: row.email,
    isAdmin,
    tier: viewingAs ?? ownTier,
    ownTier,
    viewingAs,
    periodEnd: row.current_period_end,
    mustChangePassword: row.must_change_password === 1,
  };
});

export async function getTier(): Promise<Tier> {
  return (await getViewer())?.tier ?? "free";
}

/** Throws a redirect-friendly null for non-admins; use in admin pages and API routes. */
export async function requireAdmin(): Promise<Viewer | null> {
  const v = await getViewer();
  return v && v.isAdmin && !v.mustChangePassword ? v : null;
}

const ATTEMPT_WINDOW_MS = 15 * 60 * 1000;
const MAX_FAILS = 8;

export async function tooManyAttempts(key: string): Promise<boolean> {
  const db = await getDB();
  const r = await db
    .prepare("SELECT COUNT(*) AS n FROM auth_attempts WHERE key = ? AND at > ? AND ok = 0")
    .bind(key, Date.now() - ATTEMPT_WINDOW_MS)
    .first<{ n: number }>();
  return (r?.n ?? 0) >= MAX_FAILS;
}

export async function recordAttempt(key: string, ok: boolean): Promise<void> {
  const db = await getDB();
  await db.prepare("INSERT INTO auth_attempts (key, at, ok) VALUES (?, ?, ?)").bind(key, Date.now(), ok ? 1 : 0).run();
}

export async function audit(adminId: string, action: string, targetUserId: string | null, detail?: unknown): Promise<void> {
  const db = await getDB();
  await db
    .prepare("INSERT INTO admin_audit (id, admin_id, action, target_user_id, detail, created_at) VALUES (?, ?, ?, ?, ?, ?)")
    .bind(crypto.randomUUID(), adminId, action, targetUserId, detail === undefined ? null : JSON.stringify(detail), Date.now())
    .run();
}

/** Rejects cross-site POSTs to state-changing endpoints (cookies are SameSite=Lax; this is defense in depth). */
export function sameOrigin(request: Request): boolean {
  const origin = request.headers.get("origin");
  if (!origin) return true; // same-origin form posts from older browsers omit it
  return origin === new URL(request.url).origin;
}
