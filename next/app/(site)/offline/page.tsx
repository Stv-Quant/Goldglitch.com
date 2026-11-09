export const metadata = { title: "Sin conexión" };

export default function OfflinePage() {
  return (
    <section className="mx-auto max-w-md px-4 py-24 text-center">
      <p className="eyebrow">Sin conexión</p>
      <h1 className="mt-3 text-2xl font-semibold">No hay red ahora mismo</h1>
      <p className="mt-2 text-mid">Las páginas que ya abriste siguen disponibles. Los datos se actualizan al volver la conexión.</p>
    </section>
  );
}
