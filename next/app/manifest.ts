import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    id: "/",
    name: "Goldglitch · Stats",
    short_name: "Goldglitch",
    description: "Estadísticas y probabilidades deportivas con incertidumbre visible e historial auditable.",
    lang: "es-CO",
    start_url: "/app?source=pwa",
    scope: "/",
    display: "standalone",
    orientation: "portrait",
    background_color: "#020202",
    theme_color: "#020202",
    categories: ["sports", "productivity"],
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
      { src: "/icons/maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
    shortcuts: [
      { name: "Partidos de hoy", url: "/app", icons: [{ src: "/icons/icon-192.png", sizes: "192x192" }] },
      { name: "Historial del modelo", url: "/historial", icons: [{ src: "/icons/icon-192.png", sizes: "192x192" }] },
    ],
  };
}
