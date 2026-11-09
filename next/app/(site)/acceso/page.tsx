import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { LoginForm } from "@/components/site/LoginForm";
import { getViewer } from "@/lib/auth";

export const metadata: Metadata = { title: "Entrar" };
export const dynamic = "force-dynamic";

export default async function AccesoPage({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  if (await getViewer().catch(() => null)) redirect("/app");
  const { error } = await searchParams;

  return (
    <section className="mx-auto max-w-md px-4 py-20">
      <p className="eyebrow">Acceso</p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight">Entra sin contraseña</h1>
      <p className="mt-2 text-mid">Te enviamos un enlace al correo. Si no tienes cuenta, se crea al entrar — gratis.</p>
      {error === "link" && (
        <p role="alert" className="mt-6 card p-3 text-sm" style={{ borderColor: "rgba(255,77,109,.35)" }}>
          Ese enlace venció o ya se usó. Pide uno nuevo.
        </p>
      )}
      <div className="mt-8">
        <LoginForm />
      </div>
    </section>
  );
}
