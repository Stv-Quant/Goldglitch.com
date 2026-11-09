import type { Metadata } from "next";

export const metadata: Metadata = { title: "Confirmar acceso", robots: { index: false } };

// The emailed link lands here; the token is only consumed by the explicit POST below,
// so mail-scanner prefetches can't burn it.
export default async function VerifyPage({ searchParams }: { searchParams: Promise<{ token?: string }> }) {
  const { token = "" } = await searchParams;
  return (
    <section className="mx-auto max-w-md px-4 py-24 text-center">
      <p className="eyebrow">Acceso</p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight">Confirma tu entrada</h1>
      <p className="mt-2 text-mid">Un clic más y estás dentro.</p>
      <form method="post" action="/api/auth/verify" className="mt-8">
        <input type="hidden" name="token" value={token} />
        <button type="submit" className="btn-gold w-full py-3" disabled={!token}>Entrar a Goldglitch</button>
      </form>
    </section>
  );
}
