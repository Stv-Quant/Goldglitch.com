import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [{ userAgent: "*", allow: "/", disallow: ["/app", "/admin", "/api/", "/auth/", "/acceso", "/i/", "/tiktok/"] }],
    sitemap: "https://easygoldglitch.com/sitemap.xml",
    host: "https://easygoldglitch.com",
  };
}
