import type { Metadata } from "next";
import { ForgotPasswordForm } from "@/components/site/ForgotPasswordForm";

export const metadata: Metadata = { title: "Recuperar contraseña", robots: { index: false } };

export default function RecuperarPage() {
  return (
    <section className="mx-auto max-w-md px-5 py-20">
      <p className="num text-[11px] tracking-[0.22em] text-gold uppercase">Acceso</p>
      <h1 className="display mt-3 text-[2.4rem]">Recupera tu contraseña</h1>
      <p className="mt-3 text-mid">Escribe el correo de tu cuenta. Te enviamos un enlace para crear una contraseña nueva; vence en 30 minutos.</p>
      <div className="mt-8"><ForgotPasswordForm /></div>
    </section>
  );
}
