import Link from "next/link";
import { redirect } from "next/navigation";
import { Logo } from "@/components/brand/Logo";
import { AppNav } from "@/components/app/AppNav";
import { InstallButton } from "@/components/pwa/InstallButton";
import { getViewer } from "@/lib/auth";
import { PLANS } from "@/lib/plans";

export const dynamic = "force-dynamic";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const viewer = await getViewer();
  if (!viewer) redirect("/acceso");

  return (
    <div className="min-h-dvh pb-20 sm:pb-0">
      <header className="sticky top-0 z-30 border-b border-line bg-[rgba(2,2,2,0.82)] backdrop-blur-md pt-[env(safe-area-inset-top)]">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 h-14 flex items-center justify-between gap-4">
          <Logo href="/app" />
          <div className="hidden sm:block"><AppNav /></div>
          <div className="flex items-center gap-3">
            <InstallButton />
            <Link
              href="/app/cuenta"
              className="text-[11px] eyebrow px-2.5 py-1 rounded-md border border-line"
              style={viewer.tier !== "free" ? { color: "var(--gold)", borderColor: "var(--border-glass)" } : undefined}
            >
              {PLANS[viewer.tier].name}
            </Link>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 sm:px-6 py-6 sm:py-8">{children}</main>
      <div className="sm:hidden fixed bottom-0 inset-x-0 z-30 border-t border-line bg-[rgba(2,2,2,0.92)] backdrop-blur-md pb-[env(safe-area-inset-bottom)]">
        <AppNav mobile />
      </div>
    </div>
  );
}
