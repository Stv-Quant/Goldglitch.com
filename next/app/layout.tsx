import type { Metadata, Viewport } from "next";
import { ServiceWorker } from "@/components/pwa/ServiceWorker";
import { Attribution } from "@/components/site/Attribution";
import "@fontsource/instrument-serif/400.css";
import "@fontsource/instrument-serif/400-italic.css";
import "@fontsource-variable/bricolage-grotesque";
import "@fontsource-variable/jetbrains-mono";
import "./globals.css";

const SITE = "https://easygoldglitch.com";
const TITLE = "Goldglitch · Probabilidades de fútbol y béisbol con datos, no fijas";
const DESC =
  "Probabilidades de cada partido de fútbol y béisbol calculadas por un modelo estadístico: ganador, goles, córners, tarjetas y jugadores. Historial público de aciertos y fallos. Gratis.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE),
  title: { default: TITLE, template: "%s · Goldglitch" },
  description: DESC,
  applicationName: "Goldglitch",
  keywords: [
    "probabilidades de fútbol", "pronósticos de fútbol", "estadísticas de fútbol", "predicciones de partidos",
    "estadísticas MLB", "Liga BetPlay", "Premier League", "Champions League", "córners", "tarjetas", "xG",
  ],
  alternates: { canonical: "/" },
  appleWebApp: { capable: true, title: "Goldglitch", statusBarStyle: "black-translucent" },
  icons: {
    icon: [{ url: "/icons/icon-192.png", sizes: "192x192", type: "image/png" }, { url: "/icons/icon.svg", type: "image/svg+xml" }],
    apple: "/icons/apple-touch-icon.png",
  },
  openGraph: {
    title: TITLE,
    description: "Te venden fijas. Nosotros, números. Probabilidades de cada partido e historial público de aciertos y fallos.",
    url: SITE,
    siteName: "Goldglitch",
    type: "website",
    locale: "es_CO",
    images: [{ url: "/icons/icon-512.png", width: 512, height: 512, alt: "Goldglitch" }],
  },
  twitter: {
    card: "summary",
    title: TITLE,
    description: "Probabilidades de cada partido con datos, no fijas. Historial público.",
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: "#0a0907",
  colorScheme: "dark",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body className="antialiased">
        {children}
        <ServiceWorker />
        <Attribution />
      </body>
    </html>
  );
}
