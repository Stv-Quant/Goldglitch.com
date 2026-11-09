import type { Metadata } from "next";
import { Clause, COMPANY, LegalPage } from "@/components/site/LegalPage";

export const metadata: Metadata = { title: "Cookies" };

export default function CookiesPage() {
  return (
    <LegalPage title="Cookies" intro={`${COMPANY.brand} usa una sola cookie, y es imprescindible. No hay cookies de publicidad ni de seguimiento.`}>
      <Clause n="01" title="La cookie que usamos">
        <div className="card p-4 num text-[13px] grid gap-1">
          <div><span className="text-lo">Nombre:</span> <span className="text-hi">gg_session</span></div>
          <div><span className="text-lo">Tipo:</span> estrictamente necesaria · propia · HttpOnly</div>
          <div><span className="text-lo">Finalidad:</span> mantener tu sesión iniciada de forma segura</div>
          <div><span className="text-lo">Duración:</span> 30 días o hasta que cierres sesión</div>
        </div>
      </Clause>
      <Clause n="02" title="Almacenamiento de la app">
        <p>
          Como aplicación instalable (PWA), guardamos en tu dispositivo copias de las páginas que visitas para que funcionen
          sin conexión. Se borran al cerrar sesión.
        </p>
      </Clause>
      <Clause n="03" title="Terceros">
        <p>Las fuentes tipográficas se sirven desde nuestro propio dominio. Al pagar, Wompi puede usar sus propias cookies dentro de su página de pago.</p>
      </Clause>
    </LegalPage>
  );
}
