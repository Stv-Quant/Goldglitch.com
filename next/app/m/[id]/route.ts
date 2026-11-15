import { getDB } from "@/lib/env";

/** Public image for social posts: /m/<id>.jpg */
export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const key = id.replace(/\.(jpg|jpeg|png)$/i, "");
  if (!/^[a-f0-9]{32}$/.test(key)) return new Response("Not found", { status: 404 });
  const db = await getDB();
  const r = await db.prepare("SELECT ct, data FROM social_media WHERE id = ?").bind(key).first<{ ct: string; data: string }>();
  if (!r) return new Response("Not found", { status: 404 });
  const bin = Uint8Array.from(atob(r.data), (c) => c.charCodeAt(0));
  return new Response(bin, { headers: { "content-type": r.ct, "cache-control": "public, max-age=1209600, immutable" } });
}
