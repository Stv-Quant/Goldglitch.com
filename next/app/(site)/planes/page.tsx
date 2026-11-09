import type { Metadata } from "next";
import { PlanCards } from "@/components/site/PlanCards";

export const metadata: Metadata = { title: "Planes" };

export default function PlanesPage() {
  return (
    <section className="mx-auto max-w-6xl px-4 sm:px-6 py-16">
      <p className="eyebrow">Planes</p>
      <h1 className="mt-3 text-3xl sm:text-4xl font-semibold tracking-tight">Pagas por profundidad, no por promesas.</h1>
      <p className="mt-3 text-mid max-w-2xl">
        Ningún plan vende «picks seguros». Todos ven el mismo modelo; los planes pagos desbloquean más capas de análisis.
      </p>
      <div className="mt-10">
        <PlanCards />
      </div>
    </section>
  );
}
