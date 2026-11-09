import type { Metadata } from "next";
import { Clause, COMPANY, LegalPage } from "@/components/site/LegalPage";

export const metadata: Metadata = { title: "Política de privacidad" };

export default function PrivacidadPage() {
  return (
    <LegalPage
      title="Política de privacidad"
      intro={`Política de tratamiento de datos personales de ${COMPANY.brand}, conforme a la Ley 1581 de 2012 y el Decreto 1377 de 2013 de Colombia. Recogemos lo mínimo para que el servicio funcione.`}
    >
      <Clause n="01" title="Responsable del tratamiento">
        <p>{COMPANY.legalName}, NIT {COMPANY.taxId}, {COMPANY.address}. Contacto: {COMPANY.email}.</p>
      </Clause>
      <Clause n="02" title="Qué datos tratamos">
        <ul className="list-disc pl-5 space-y-2">
          <li><span className="text-hi">Correo electrónico</span>: para crear tu cuenta y enviarte el enlace de acceso.</li>
          <li><span className="text-hi">Datos de sesión</span>: un identificador de sesión cifrado y el tipo de navegador, para mantenerte conectado de forma segura.</li>
          <li><span className="text-hi">Datos de pago</span>: plan, valor, estado y referencia de cada transacción. Los datos de tarjeta o cuenta bancaria los procesa directamente Wompi; nosotros nunca los vemos ni almacenamos.</li>
        </ul>
        <p>No usamos herramientas de publicidad ni vendemos ni compartimos tus datos con terceros para fines comerciales.</p>
      </Clause>
      <Clause n="03" title="Finalidades">
        <p>Prestar el servicio, gestionar tu membresía, prevenir fraude, cumplir obligaciones legales y contables, y responder tus solicitudes.</p>
      </Clause>
      <Clause n="04" title="Encargados">
        <p>
          Para operar usamos proveedores que tratan datos por nuestra cuenta: Cloudflare (infraestructura y base de datos),
          Wompi (pagos) y nuestro proveedor de correo transaccional. Algunos pueden almacenar datos fuera de Colombia, con
          medidas de seguridad adecuadas.
        </p>
      </Clause>
      <Clause n="05" title="Tus derechos">
        <p>
          Como titular puedes conocer, actualizar, rectificar y suprimir tus datos, solicitar prueba de la autorización, ser
          informado sobre su uso, revocar la autorización y presentar quejas ante la Superintendencia de Industria y Comercio.
        </p>
        <p>Escríbenos a {COMPANY.email}. Respondemos consultas en máximo 10 días hábiles y reclamos en máximo 15 días hábiles.</p>
      </Clause>
      <Clause n="06" title="Conservación y seguridad">
        <p>
          Conservamos tus datos mientras tengas una cuenta activa y durante el tiempo que exijan las obligaciones legales y
          contables. Los tokens de acceso y sesión se guardan únicamente como huellas criptográficas.
        </p>
      </Clause>
      <Clause n="07" title="Menores de edad">
        <p>El servicio no está dirigido a menores de 18 años y no recolectamos conscientemente sus datos.</p>
      </Clause>
    </LegalPage>
  );
}
