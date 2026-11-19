import { NextResponse } from "next/server";
import { SOURCE_COOKIE, cleanTag, sourceFromReferrer, sourceFromRef } from "@/lib/attribution";
import { getDB } from "@/lib/env";

const SESSION_COOKIE = "gg_v";   // readable by the page: one beacon per 30-minute browsing session
const BOT = /bot|crawl|spider|slurp|preview|facebookexternalhit|whatsapp|telegram|headless|lighthouse/i;

/** Visit beacon from <Attribution/>: counts one visit per session and keeps the first-touch source for signup. */
export async function POST(request: Request) {
  const res = NextResponse.json({ ok: true });
  res.cookies.set(SESSION_COOKIE, "1", { secure: true, sameSite: "lax", path: "/", maxAge: 30 * 60 });
  if (BOT.test(request.headers.get("user-agent") ?? "")) return res;
  const body = (await request.json().catch(() => null)) as { ref?: string; utm?: string; referrer?: string; path?: string } | null;
  if (!body) return res;

  const own = new URL(request.url).hostname.replace(/^www\./, "");
  const ref = cleanTag(body.ref);
  const source = ref ? sourceFromRef(ref) : cleanTag(body.utm) ?? sourceFromReferrer(body.referrer, own);
  const path = String(body.path ?? "/");
  const landing = path.startsWith("/app") ? "/app" : (path.split("?")[0].split("/").slice(0, 2).join("/") || "/").slice(0, 40);
  const day = new Date(Date.now() - 5 * 3600_000).toISOString().slice(0, 10);

  await (await getDB())
    .prepare(
      `INSERT INTO traffic_daily (day, source, landing, visits) VALUES (?1, ?2, ?3, 1)
       ON CONFLICT(day, source, landing) DO UPDATE SET visits = visits + 1`,
    )
    .bind(day, ref ? `ref:${ref}` : source, landing)
    .run();

  const jar = request.headers.get("cookie") ?? "";
  if (!jar.includes(`${SOURCE_COOKIE}=`) && source !== "directo") {
    res.cookies.set(SOURCE_COOKIE, `${source}|${ref ?? ""}`, { httpOnly: true, secure: true, sameSite: "lax", path: "/", maxAge: 30 * 86400 });
  } else if (!jar.includes(`${SOURCE_COOKIE}=`)) {
    res.cookies.set(SOURCE_COOKIE, "directo|", { httpOnly: true, secure: true, sameSite: "lax", path: "/", maxAge: 30 * 86400 });
  }
  return res;
}
