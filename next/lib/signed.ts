import "server-only";
import { hmacSha256Hex, safeEqual } from "./crypto";
import { getIngestSecret } from "./ingestKey";

/**
 * Requests from the PC (SQPC and the social agents), signed like /api/ingest:
 * X-GG-Timestamp (epoch ms) and X-GG-Signature = hex HMAC-SHA256(secret, `${timestamp}.${rawBody}`).
 * Returns the raw body, or a Response to send back when the signature is missing or wrong.
 */
export async function readSigned(request: Request, maxBytes = 3_000_000): Promise<string | Response> {
  const ts = Number(request.headers.get("x-gg-timestamp"));
  const sig = request.headers.get("x-gg-signature") ?? "";
  if (!Number.isFinite(ts) || Math.abs(Date.now() - ts) > 5 * 60_000) {
    return Response.json({ ok: false, error: "stale_or_missing_timestamp" }, { status: 401 });
  }
  const { secret } = await getIngestSecret();
  if (!secret) return Response.json({ ok: false, error: "not_configured" }, { status: 503 });
  const raw = await request.text();
  if (raw.length > maxBytes) return Response.json({ ok: false, error: "too_large" }, { status: 413 });
  const expected = await hmacSha256Hex(secret, `${ts}.${raw}`);
  if (!safeEqual(expected, sig)) return Response.json({ ok: false, error: "bad_signature" }, { status: 401 });
  return raw;
}
