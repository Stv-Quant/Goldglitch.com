import type { Metadata } from "next";
import { Clause, COMPANY, LegalPage } from "@/components/site/LegalPage";

export const metadata: Metadata = { title: "Juego responsable" };

export default function JuegoResponsablePage() {
  return (
    <LegalPage
      title="Juego responsable"
      intro="Entender las probabilidades es la mejor protección contra la ilusión de control. Si apuestas, estas reglas importan más que cualquier modelo."
    >
      <Clause n="01" title="Solo mayores de 18 años">
        <p>{COMPANY.brand} está dirigido exclusivamente a mayores de edad. Al crear una cuenta confirmas que tienes al menos 18 años.</p>
      </Clause>
      <Clause n="02" title="Reglas que recomendamos">
        <ul className="list-disc pl-5 space-y-2">
          <li>Define antes un presupuesto para entretenimiento y no lo superes. Nunca uses dinero destinado a gastos básicos.</li>
          <li>No intentes recuperar pérdidas apostando más. Una racha mala es parte normal de la variancia.</li>
          <li>Fija límites de tiempo y toma pausas. No apuestes bajo efectos del alcohol, cansancio o emociones fuertes.</li>
          <li>Desconfía de cualquiera que te prometa ganancias seguras, incluidas «fijas», grupos VIP o métodos infalibles.</li>
          <li>Usa solo operadores autorizados. En Colombia, Coljuegos publica el listado de operadores legales.</li>
        </ul>
      </Clause>
      <Clause n="03" title="Señales de alerta">
        <ul className="list-disc pl-5 space-y-2">
          <li>Apuestas cada vez más para sentir la misma emoción.</li>
          <li>Ocultas a tu familia o amigos cuánto apuestas.</li>
          <li>Pides dinero prestado o dejas de pagar obligaciones para apostar.</li>
          <li>Te sientes irritable o ansioso cuando intentas dejarlo.</li>
        </ul>
        <p>Si reconoces alguna, detente y busca apoyo.</p>
      </Clause>
      <Clause n="04" title="Dónde pedir ayuda">
        <p>
          Habla con tu EPS o con un profesional de salud mental: la ludopatía es un trastorno reconocido y tratable. También
          puedes acudir a las líneas de salud mental de tu ciudad o departamento y a los programas de juego responsable de los
          operadores autorizados, que ofrecen límites de depósito y autoexclusión.
        </p>
      </Clause>
      <Clause n="05" title="Pausar tu cuenta">
        <p>
          Puedes pedirnos suspender o cerrar tu cuenta en cualquier momento escribiendo a {COMPANY.email}. Lo haremos sin
          preguntas.
        </p>
      </Clause>
    </LegalPage>
  );
}
