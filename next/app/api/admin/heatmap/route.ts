import { requireAdmin } from "@/lib/auth";
import { heatmap } from "@/lib/analyticsReport";
import { normPath } from "@/lib/analytics";

export const dynamic = "force-dynamic";

/** Click and scroll heatmap data for one page (admin only). */
export async function GET(request: Request) {
  if (!(await requireAdmin())) return Response.json({ error: "forbidden" }, { status: 403 });
  const u = new URL(request.url);
  const device = ["mobile", "tablet", "desktop"].includes(u.searchParams.get("device") ?? "") ? u.searchParams.get("device")! : "mobile";
  const days = Math.max(1, Math.min(Number(u.searchParams.get("days")) || 30, 90));
  return Response.json(await heatmap(normPath(u.searchParams.get("path") ?? "/"), device, days));
}
