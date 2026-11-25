import type { Metadata } from "next";
import { SlipsPage } from "@/components/app/SlipsPage";
import { LockedPanel } from "@/components/stats/LockedPanel";
import { getViewer } from "@/lib/auth";
import { hasTier } from "@/lib/plans";

export const metadata: Metadata = { title: "Combinadas" };
export const dynamic = "force-dynamic";

export default async function CombinadasPage() {
  const v = await getViewer();
  if (!v || !hasTier(v.tier, "pro")) {
    return (
      <div className="max-w-xl space-y-4">
        <h1 className="text-3xl font-semibold tracking-tight">Combinadas</h1>
        <LockedPanel tier="Pro" title="Arma y guarda tus combinadas">
          {"Junta picks de 80% o más de varios partidos, mira la probabilidad conjunta, el riesgo y la nota de la combinada, y sigue cómo terminó cada selección."}
        </LockedPanel>
      </div>
    );
  }
  return <SlipsPage />;
}
