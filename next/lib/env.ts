import "server-only";
import { getCloudflareContext } from "@opennextjs/cloudflare";
import type { D1Database } from "@cloudflare/workers-types";

export type AppEnv = {
  EGG_DB: D1Database;
  APP_URL?: string;
  INGEST_HMAC_SECRET?: string;
  WOMPI_PUBLIC_KEY?: string;
  WOMPI_INTEGRITY_SECRET?: string;
  WOMPI_EVENTS_SECRET?: string;
  RESEND_API_KEY?: string;
  MAIL_FROM?: string;
};

export async function getEnv(): Promise<AppEnv> {
  const { env } = await getCloudflareContext({ async: true });
  return env as unknown as AppEnv;
}

export async function getDB(): Promise<D1Database> {
  const env = await getEnv();
  if (!env.EGG_DB) throw new Error("D1 binding EGG_DB missing");
  return env.EGG_DB;
}

export function requireSecret(value: string | undefined, name: string): string {
  if (!value) throw new Error(`Missing secret: ${name}`);
  return value;
}
