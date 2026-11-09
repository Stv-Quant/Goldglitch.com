import type { Metadata } from "next";
import Link from "next/link";
import { Clause, COMPANY, LegalPage } from "@/components/site/LegalPage";

export const metadata: Metadata = { title: "Términos y condiciones" };

export default function TerminosPage() {
  return (
    <LegalPage
      title="Términos y condiciones"
      intro={`Estas condiciones regulan el uso de ${COMPANY.site} y de la aplicación ${COMPANY.brand}. Al crear una cuenta o usar el servicio las aceptas.`}
    >
      <Clause n="01" title="Quiénes somos">
        <p>El servicio es prestado por {COMPANY.legalName}, NIT {COMPANY.taxId}, con domicilio en {COMPANY.address}. Contacto: {COMPANY.email}.</p>
      </Clause>
      <Clause n="02" title="El servicio">
        <p>
          {COMPANY.brand} ofrece estadísticas deportivas, probabilidades calculadas por modelos y un historial público de su
          rendimiento. No es un operador de juegos de suerte y azar, no recibe apuestas y no ofrece asesoría. Lee el{" "}
          <Link href="/legal/riesgo" className="text-gold underline underline-offset-4">descargo de responsabilidad</Link>.
        </p>
      </Clause>
      <Clause n="03" title="Cuenta">
        <p>
          Debes ser mayor de 18 años. Tu acceso es personal: el enlace de ingreso se envía a tu correo y eres responsable de
          mantenerlo seguro. Podemos suspender cuentas que incumplan estas condiciones.
        </p>
      </Clause>
      <Clause n="04" title="Membresías y pagos">
        <ul className="list-disc pl-5 space-y-2">
          <li>Los planes Pro y Elite se pagan por adelantado en pesos colombianos (COP) mediante Wompi.</li>
          <li>Cada pago activa el periodo elegido (30 o 365 días). No hay renovaciones ni cobros automáticos.</li>
          <li>Renovar el mismo plan suma el nuevo periodo al restante. Cambiar de plan inicia un periodo nuevo desde la fecha del pago.</li>
          <li>Reembolsos: [POLÍTICA DE REEMBOLSO — por definir], sin perjuicio del derecho de retracto previsto en la Ley 1480 de 2011 cuando aplique.</li>
        </ul>
      </Clause>
      <Clause n="05" title="Uso permitido">
        <p>
          El contenido es para tu uso personal. No puedes revenderlo, redistribuirlo en grupos de pago, extraerlo de forma
          automatizada ni presentarlo como «pronósticos seguros». Hacerlo es causa de cierre de la cuenta sin reembolso.
        </p>
      </Clause>
      <Clause n="06" title="Propiedad intelectual">
        <p>Los modelos, textos, diseños, código y la marca {COMPANY.brand} son de {COMPANY.legalName} o de sus licenciantes.</p>
      </Clause>
      <Clause n="07" title="Limitación de responsabilidad">
        <p>
          En la medida permitida por la ley, {COMPANY.brand} no responde por pérdidas económicas derivadas de decisiones de
          apuesta, inversión u otras tomadas con base en el contenido, ni por interrupciones o errores de datos de terceros.
        </p>
      </Clause>
      <Clause n="08" title="Cambios y ley aplicable">
        <p>
          Podemos actualizar estas condiciones; los cambios relevantes se avisarán en la aplicación. Se rigen por las leyes de
          la República de Colombia.
        </p>
      </Clause>
    </LegalPage>
  );
}
