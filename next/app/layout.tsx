import type { Metadata, Viewport } from "next";
import { ServiceWorker } from "@/components/pwa/ServiceWorker";
import "@fontsource/instrument-serif/400.css";
import "@fontsource/instrument-serif/400-italic.css";
import "@fontsource-variable/bricolage-grotesque";
import "@fontsource-variable/jetbrains-mono";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://goldglitch.com"),
  title: { default: "Goldglitch · La objetividad de los datos", template: "%s · Goldglitch" },
  description:
    "Estadísticas y probabilidades de fútbol y MLB con incertidumbre visible e historial auditable. Datos, no corazonadas.",
  applicationName: "Goldglitch",
  appleWebApp: { capable: true, title: "Goldglitch", statusBarStyle: "black-translucent" },
  icons: {
    icon: [{ url: "/icons/icon-192.png", sizes: "192x192", type: "image/png" }, { url: "/icons/icon.svg", type: "image/svg+xml" }],
    apple: "/icons/apple-touch-icon.png",
  },
  openGraph: {
    title: "Goldglitch · La objetividad de los datos",
    description: "Probabilidades con incertidumbre visible e historial auditable.",
    type: "website",
    locale: "es_CO",
  },
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
      </body>
    </html>
  );
}
