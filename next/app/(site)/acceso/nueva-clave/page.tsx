import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { ChangePasswordForm } from "@/components/site/ChangePasswordForm";
import { getViewer } from "@/lib/auth";

export const metadata: Metadata = { title: "Nueva contraseña", robots: { index: false } };
export const dynamic = "force-dynamic";

export default async function NuevaClavePage() {
  const viewer = await getViewer();
  if (!viewer) redirect("/acceso");

  return (
    <section className="mx-auto max-w-md px-5 py-20">
      <p className="num text-[11px] tracking-[0.22em] text-gold uppercase">Seguridad</p>
      <h1 className="display mt-3 text-[2.4rem]">{viewer.mustChangePassword ? "Crea tu contraseña" : "Cambiar contraseña"}</h1>
      <p className="mt-3 text-mid">
        {viewer.mustChangePassword
          ? "Entraste con una contraseña temporal. Antes de continuar, define una propia. Al guardarla cerramos cualquier otra sesión abierta."
          : "Al guardarla cerramos cualquier otra sesión abierta con tu cuenta."}
      </p>
      <p className="mt-2 text-sm text-lo num">{viewer.email}</p>
      <div className="mt-8">
        <ChangePasswordForm />
      </div>
    </section>
  );
}
