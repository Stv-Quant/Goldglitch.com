import type { D1Database } from "@cloudflare/workers-types";

declare module "@opennextjs/cloudflare" {
  interface CloudflareEnv {
    EGG_DB: D1Database;
    APP_URL?: string;
    MAIL_FROM?: string;
    INGEST_HMAC_SECRET?: string;
    WOMPI_PUBLIC_KEY?: string;
    WOMPI_INTEGRITY_SECRET?: string;
    WOMPI_EVENTS_SECRET?: string;
    RESEND_API_KEY?: string;
  }
}

export {};
