import type { MetadataRoute } from "next";

const SITE = "https://easygoldglitch.com";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  return [
    { url: `${SITE}/`, lastModified: now, changeFrequency: "daily", priority: 1 },
    { url: `${SITE}/historial`, lastModified: now, changeFrequency: "daily", priority: 0.8 },
    { url: `${SITE}/planes`, lastModified: now, changeFrequency: "monthly", priority: 0.7 },
    ...["terminos", "privacidad", "riesgo", "juego-responsable", "cookies"].map((p) => ({
      url: `${SITE}/legal/${p}`, lastModified: now, changeFrequency: "yearly" as const, priority: 0.2,
    })),
  ];
}
