import type { Metadata } from "next";
import Link from "next/link";
import { ChangePasswordForm } from "@/components/site/ChangePasswordForm";

export const metadata: Metadata = { title: "Nueva contraseña", robots: { index: false } };

// The token is only checked when the form is submitted, so mail-scanner prefetches can't burn it.
export default async function RestablecerPage({ searchParams }: { searchParams: Promise<{ token?: string }> }) {
  const { token = "" } = await searchParams;
  return (
    <section className="mx-auto max-w-md px-5 py-20">
      <p className="num text-[11px] tracking-[0.22em] text-gold uppercase">Seguridad</p>
      <h1 className="display mt-3 text-[2.4rem]">Crea una contraseña nueva</h1>
      {token ? (
        <>
          <p className="mt-3 text-mid">Al guardarla cerramos todas las sesiones abiertas con tu cuenta y entras con la nueva.</p>
          <div className="mt-8"><ChangePasswordForm resetToken={token} /></div>
        </>
      ) : (
        <p className="mt-3 text-mid">Este enlace no es válido. <Link href="/acceso/recuperar" className="text-gold underline underline-offset-4">Pide uno nuevo</Link>.</p>
      )}
    </section>
  );
}
