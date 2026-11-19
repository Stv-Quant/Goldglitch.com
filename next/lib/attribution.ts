import { cookies } from "next/headers";
import { getDB } from "./env";

/** First-touch attribution cookie: "source|ref" (30 days). Written by /api/t, read when an account is created. */
export const SOURCE_COOKIE = "gg_src";

const CLEAN = /[^a-z0-9_.:-]/g;

export function cleanTag(v: unknown, max = 48): string | null {
  const s = String(v ?? "").toLowerCase().replace(CLEAN, "").slice(0, max);
  return s || null;
}

/** Referrer host → channel. */
export function sourceFromReferrer(ref: string | null | undefined, ownHost: string): string {
  let host = "";
  try {
    host = ref ? new URL(ref).hostname.toLowerCase() : "";
  } catch {
    host = "";
  }
  if (!host || host === ownHost || host.endsWith("." + ownHost)) return "directo";
  const map: [RegExp, string][] = [
    [/(^|\.)(instagram\.com|l\.instagram\.com)$/, "instagram"],
    [/(^|\.)(facebook\.com|fb\.com|fb\.me|l\.facebook\.com|m\.facebook\.com)$/, "facebook"],
    [/(^|\.)tiktok\.com$/, "tiktok"],
    [/(^|\.)(t\.co|x\.com|twitter\.com)$/, "x"],
    [/(^|\.)(whatsapp\.com|wa\.me)$/, "whatsapp"],
    [/(^|\.)(youtube\.com|youtu\.be)$/, "youtube"],
    [/(^|\.)google\./, "google"],
    [/(^|\.)(bing\.com|duckduckgo\.com|search\.yahoo\.com)$/, "buscadores"],
  ];
  for (const [re, name] of map) if (re.test(host)) return name;
  return "otros";
}

/** ?ref=ig_… → channel from its prefix, so a tagged link is credited to its network. */
export function sourceFromRef(ref: string): string {
  const p = ref.split(/[_:-]/)[0];
  return ({ ig: "instagram", fb: "facebook", tt: "tiktok", wa: "whatsapp", yt: "youtube", x: "x" } as Record<string, string>)[p] ?? "campana";
}

/** Stamp the first-touch source on a brand-new account (never overwrites). */
export async function tagSignupSource(userId: string): Promise<void> {
  const raw = (await cookies()).get(SOURCE_COOKIE)?.value ?? "";
  const [src, ref] = raw.split("|");
  const source = cleanTag(src) ?? "desconocido";
  await (await getDB())
    .prepare("UPDATE users SET signup_source = ?, signup_ref = ? WHERE id = ? AND signup_source IS NULL")
    .bind(source, cleanTag(ref), userId)
    .run();
}
