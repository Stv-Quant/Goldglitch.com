import type { Metadata } from "next";

export const metadata: Metadata = { title: "Conectar TikTok", robots: { index: false } };

/** Redirect target for TikTok Login Kit: shows the code so it can be pasted into the social agents on the PC. */
export default async function TikTokCallback({ searchParams }: { searchParams: Promise<{ code?: string; error?: string; error_description?: string }> }) {
  const { code, error, error_description } = await searchParams;
  return (
    <section className="mx-auto max-w-xl px-4 py-20">
      <p className="eyebrow">TikTok</p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight">{code ? "Cuenta autorizada" : "No se pudo autorizar"}</h1>
      {code ? (
        <>
          <p className="mt-3 text-mid">Copia este código y pégalo en la ventana de los agentes de redes en tu PC:</p>
          <pre className="card mt-4 overflow-x-auto p-4 num text-sm text-gold select-all">{code}</pre>
          <p className="mt-3 text-xs text-lo">El código vence en pocos minutos y sirve una sola vez.</p>
        </>
      ) : (
        <p className="mt-3 text-mid">{error_description ?? error ?? "Vuelve a intentarlo desde tu PC."}</p>
      )}
    </section>
  );
}
