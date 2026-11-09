import { audit, requireAdmin, sameOrigin } from "@/lib/auth";
import { getIngestSecret, rotateIngestSecret } from "@/lib/ingestKey";

/** Generates (or replaces) the SQPC publishing key. The key is returned once and never shown again. */
export async function POST(request: Request) {
  if (!sameOrigin(request)) return Response.json({ ok: false }, { status: 403 });
  const admin = await requireAdmin();
  if (!admin) return Response.json({ ok: false }, { status: 403 });
  const current = await getIngestSecret();
  if (current.source === "env") {
    return Response.json({ ok: false, error: "managed_in_cloudflare" }, { status: 409 });
  }
  const secret = await rotateIngestSecret(admin.userId);
  await audit(admin.userId, current.source === "none" ? "ingest_key_created" : "ingest_key_rotated", null);
  return Response.json({ ok: true, secret, url: new URL("/api/ingest", request.url).toString() }, { headers: { "cache-control": "no-store" } });
}
