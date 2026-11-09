import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { Logo } from "@/components/brand/Logo";
import { AdminNav, ViewAs } from "@/components/admin/AdminNav";
import { LogoutButton } from "@/components/app/LogoutButton";
import { getViewer } from "@/lib/auth";

export const metadata: Metadata = { title: "Administración", robots: { index: false, follow: false } };
export const dynamic = "force-dynamic";

export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const viewer = await getViewer();
  if (!viewer) redirect("/acceso");
  if (viewer.mustChangePassword) redirect("/acceso/nueva-clave");
  if (!viewer.isAdmin) redirect("/app");

  return (
    <div className="min-h-dvh">
      <header className="sticky top-0 z-30 border-b border-line bg-[rgba(10,9,7,0.9)] backdrop-blur-md">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 h-14 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Logo href="/admin" />
            <span className="num text-[10px] tracking-[0.2em] uppercase rounded border border-[var(--flare)] text-flare px-1.5 py-0.5">Admin</span>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <span className="hidden sm:inline text-lo num text-xs">{viewer.email}</span>
            <LogoutButton />
          </div>
        </div>
      </header>
      <div className="mx-auto max-w-7xl px-4 sm:px-6 py-6 grid gap-6 lg:grid-cols-[200px_1fr]">
        <aside className="lg:sticky lg:top-20 self-start space-y-6">
          <AdminNav />
          <div className="hidden lg:block border-t border-line pt-5">
            <ViewAs current={viewer.viewingAs ?? "elite"} />
          </div>
        </aside>
        <main className="min-w-0">{children}</main>
      </div>
    </div>
  );
}
