import { getDB } from "@/lib/env";
import { readSigned } from "@/lib/signed";

export const dynamic = "force-dynamic";

/** Stores one JPEG/PNG from the social agents and returns its public URL (Instagram pulls images from a URL). */
export async function POST(req: Request) {
  const raw = await readSigned(req, 2_800_000);
  if (raw instanceof Response) return raw;
  const body = JSON.parse(raw) as { ct?: string; data?: string };
  const ct = body.ct === "image/png" ? "image/png" : "image/jpeg";
  if (typeof body.data !== "string" || !/^[A-Za-z0-9+/=]+$/.test(body.data.slice(0, 200))) {
    return Response.json({ ok: false, error: "bad_data" }, { status: 400 });
  }
  const id = crypto.randomUUID().replaceAll("-", "");
  const db = await getDB();
  await db.batch([
    db.prepare("DELETE FROM social_media WHERE created_at < ?").bind(Date.now() - 14 * 86_400_000),
    db.prepare("INSERT INTO social_media (id, ct, data, created_at) VALUES (?, ?, ?, ?)").bind(id, ct, body.data, Date.now()),
  ]);
  const ext = ct === "image/png" ? "png" : "jpg";
  return Response.json({ ok: true, url: `${new URL(req.url).origin}/m/${id}.${ext}` });
}
