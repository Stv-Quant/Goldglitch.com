import { NextResponse } from "next/server";
import { SOURCE_COOKIE, cleanTag, sourceFromReferrer, sourceFromRef } from "@/lib/attribution";
import { BOT, SESSION_SOURCE_COOKIE, colombiaDay, countryOf, deviceOf } from "@/lib/analytics";
import { getDB } from "@/lib/env";

const SESSION_COOKIE = "gg_v";   // readable by the page: one beacon per 30-minute browsing session

/** Visit beacon from <Attribution/>: counts one visit per session and keeps the first-touch source for signup. */
export async function POST(request: Request) {
  const res = NextResponse.json({ ok: true });
  res.cookies.set(SESSION_COOKIE, "1", { secure: true, sameSite: "lax", path: "/", maxAge: 30 * 60 });
  if (BOT.test(request.headers.get("user-agent") ?? "")) return res;
  const body = (await request.json().catch(() => null)) as { ref?: string; utm?: string; referrer?: string; path?: string; w?: number } | null;
  if (!body) return res;

  const own = new URL(request.url).hostname.replace(/^www\./, "");
  const ref = cleanTag(body.ref);
  const source = ref ? sourceFromRef(ref) : cleanTag(body.utm) ?? sourceFromReferrer(body.referrer, own);
  const path = String(body.path ?? "/");
  const landing = path.startsWith("/app") ? "/app" : (path.split("?")[0].split("/").slice(0, 2).join("/") || "/").slice(0, 40);
  const day = colombiaDay();
  const country = countryOf(request), device = deviceOf(request, body.w);
  const db = await getDB();
  await db.batch([
    db.prepare(
      `INSERT INTO traffic_daily (day, source, landing, visits) VALUES (?1, ?2, ?3, 1)
       ON CONFLICT(day, source, landing) DO UPDATE SET visits = visits + 1`,
    ).bind(day, ref ? `ref:${ref}` : source, landing),
    db.prepare(
      `INSERT INTO visits_geo_daily (day, country, source, device, visits, single_page) VALUES (?1, ?2, ?3, ?4, 1, 1)
       ON CONFLICT(day, country, source, device) DO UPDATE SET visits = visits + 1, single_page = single_page + 1`,
    ).bind(day, country, source, device),
  ]);
  res.cookies.set(SESSION_SOURCE_COOKIE, `${day}|${source}|${device}`, { httpOnly: true, secure: true, sameSite: "lax", path: "/", maxAge: 30 * 60 });

  const jar = request.headers.get("cookie") ?? "";
  if (!jar.includes(`${SOURCE_COOKIE}=`) && source !== "directo") {
    res.cookies.set(SOURCE_COOKIE, `${source}|${ref ?? ""}`, { httpOnly: true, secure: true, sameSite: "lax", path: "/", maxAge: 30 * 86400 });
  } else if (!jar.includes(`${SOURCE_COOKIE}=`)) {
    res.cookies.set(SOURCE_COOKIE, "directo|", { httpOnly: true, secure: true, sameSite: "lax", path: "/", maxAge: 30 * 86400 });
  }
  return res;
}
