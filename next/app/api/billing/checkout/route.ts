/** Goldglitch is free (since 2026-11-27): there is nothing to pay. Old checkout clients get a clear answer. */
export async function POST() {
  return Response.json({ error: "Goldglitch es gratis: no hay nada que pagar." }, { status: 410 });
}
