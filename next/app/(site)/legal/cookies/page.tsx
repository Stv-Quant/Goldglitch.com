import type { Metadata } from "next";
import { Clause, COMPANY, LegalPage } from "@/components/site/LegalPage";

export const metadata: Metadata = { title: "Cookies" };

export default function CookiesPage() {
  return (
    <LegalPage title="Cookies" intro={`${COMPANY.brand} usa una cookie imprescindible para tu sesión y tres cookies propias de medición anónima. No hay cookies de publicidad ni de terceros.`}>
      <Clause n="01" title="Cookie de sesión">
        <div className="card p-4 num text-[13px] grid gap-1">
          <div><span className="text-lo">Nombre:</span> <span className="text-hi">gg_session</span></div>
          <div><span className="text-lo">Tipo:</span> estrictamente necesaria · propia · HttpOnly</div>
          <div><span className="text-lo">Finalidad:</span> mantener tu sesión iniciada de forma segura</div>
          <div><span className="text-lo">Duración:</span> 30 días o hasta que cierres sesión</div>
        </div>
      </Clause>
      <Clause n="02" title="Medición propia y anónima">
        <div className="card p-4 num text-[13px] grid gap-2">
          <div><span className="text-hi">gg_v</span> <span className="text-lo">· 30 min ·</span> cuenta una visita por sesión de navegación</div>
          <div><span className="text-hi">gg_vs</span> <span className="text-lo">· 30 min · HttpOnly ·</span> canal y dispositivo de la sesión, para saber si viste una o más páginas</div>
          <div><span className="text-hi">gg_src</span> <span className="text-lo">· 30 días · HttpOnly ·</span> por qué canal llegaste la primera vez (redes, buscadores, enlace)</div>
        </div>
        <p className="mt-3">
          Medimos, sin terceros y de forma agregada, el país (según la red, no tu ubicación exacta), el tipo de dispositivo, las
          páginas vistas, el tiempo con la página visible, hasta dónde bajas y en qué zonas y botones de las páginas públicas se
          hace clic (mapas de calor). No guardamos tu dirección IP, lo que escribes ni ningún dato que te identifique, y la
          parte privada de la app no se graba en mapas de calor.
        </p>
      </Clause>
      <Clause n="03" title="Almacenamiento de la app">
        <p>
          Como aplicación instalable (PWA), guardamos en tu dispositivo copias de las páginas que visitas para que funcionen
          sin conexión. Se borran al cerrar sesión.
        </p>
      </Clause>
      <Clause n="04" title="Terceros">
        <p>Las fuentes tipográficas se sirven desde nuestro propio dominio.</p>
      </Clause>
    </LegalPage>
  );
}
