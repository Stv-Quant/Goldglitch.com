import "server-only";
import { randomToken } from "./crypto";
import { getDB, getEnv } from "./env";

const KEY = "ingest_hmac_secret";

export type IngestKeySource = "env" | "panel" | "none";

/**
 * The shared HMAC secret SQPC signs with. A Cloudflare secret (INGEST_HMAC_SECRET) wins if set;
 * otherwise the key generated from the admin panel and stored in D1.
 */
export async function getIngestSecret(): Promise<{ secret: string | null; source: IngestKeySource; updatedAt: number | null }> {
  const env = await getEnv();
  if (env.INGEST_HMAC_SECRET) return { secret: env.INGEST_HMAC_SECRET, source: "env", updatedAt: null };
  try {
    const row = await (await getDB())
      .prepare("SELECT value, updated_at FROM app_settings WHERE key = ?")
      .bind(KEY)
      .first<{ value: string; updated_at: number }>();
    if (row?.value) return { secret: row.value, source: "panel", updatedAt: row.updated_at };
  } catch {
    // table missing before migration 0005: behave as not configured
  }
  return { secret: null, source: "none", updatedAt: null };
}

/** Generates a new key and stores it. The previous key stops working immediately. */
export async function rotateIngestSecret(adminId: string): Promise<string> {
  const secret = `ggsk_${randomToken(32)}`;
  await (await getDB())
    .prepare(
      `INSERT INTO app_settings (key, value, updated_at, updated_by) VALUES (?, ?, ?, ?)
       ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at, updated_by = excluded.updated_by`,
    )
    .bind(KEY, secret, Date.now(), adminId)
    .run();
  return secret;
}
