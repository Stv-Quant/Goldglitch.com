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
      <Clause n="04" title="Gratuidad">
        <ul className="list-disc pl-5 space-y-2">
          <li>Goldglitch es gratuito: no hay planes de pago, suscripciones ni cobros. Solo pedimos una cuenta con tu correo.</li>
          <li>La cuenta sirve para recibir alertas y ver las estadísticas de cada partido a detalle.</li>
        </ul>
      </Clause>
      <Clause n="05" title="Uso permitido">
        <p>
          El contenido es para tu uso personal. No puedes revenderlo, redistribuirlo en grupos de pago, extraerlo de forma
          automatizada ni presentarlo como «pronósticos seguros». Hacerlo es causa de cierre de la cuenta.
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
