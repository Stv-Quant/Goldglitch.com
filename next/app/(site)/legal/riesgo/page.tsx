import type { Metadata } from "next";
import { Clause, COMPANY, LegalPage } from "@/components/site/LegalPage";

export const metadata: Metadata = { title: "Descargo de responsabilidad" };

export default function RiesgoPage() {
  return (
    <LegalPage
      title="Descargo de responsabilidad"
      intro={`${COMPANY.brand} publica estadísticas y probabilidades calculadas por modelos. Esta página explica, sin letra pequeña, qué son y qué no son.`}
    >
      <Clause n="01" title="No somos una casa de apuestas">
        <p>
          {COMPANY.brand} no recibe apuestas, no administra dinero de usuarios, no actúa como intermediario de ningún operador
          de juegos de suerte y azar y no está afiliado a ninguna casa de apuestas, liga, club o federación.
        </p>
      </Clause>
      <Clause n="02" title="Una probabilidad no es una predicción">
        <p>
          Un 60% significa que, en condiciones comparables, ese resultado ocurriría alrededor de 60 de cada 100 veces. Las
          otras 40 también ocurren. Ningún resultado individual confirma ni desmiente un modelo; solo la acumulación de muchos
          pronósticos lo hace, y por eso publicamos nuestro historial completo.
        </p>
      </Clause>
      <Clause n="03" title="Sin garantías de resultado ni de ganancia">
        <p>
          Ningún contenido de {COMPANY.brand} garantiza resultados deportivos, ganancias ni la recuperación de pérdidas.
        </p>
        <p>El rendimiento pasado del modelo no garantiza su rendimiento futuro.</p>
      </Clause>
      <Clause n="04" title="No es asesoría">
        <p>
          La información es de carácter general y educativo. No constituye asesoría financiera, de inversión, legal ni
          profesional de ningún tipo, ni una recomendación personalizada de apostar.
        </p>
      </Clause>
      <Clause n="05" title="Tu decisión, tu responsabilidad">
        <p>
          Cualquier decisión de apostar es exclusivamente tuya. Si decides hacerlo: hazlo solo con operadores autorizados en tu
          país (en Colombia, los autorizados por Coljuegos), solo con dinero que puedas permitirte perder, y solo si eres mayor
          de edad.
        </p>
      </Clause>
      <Clause n="06" title="Datos y errores">
        <p>
          Los datos provienen de fuentes públicas y pueden contener errores, retrasos u omisiones. Los modelos pueden fallar.
          Corregimos y documentamos los errores que detectamos, pero no respondemos por decisiones tomadas con base en
          información incorrecta o desactualizada.
        </p>
      </Clause>
      <Clause n="07" title="Marcas y nombres">
        <p>
          Los nombres de equipos, ligas y competiciones se usan únicamente para identificar los eventos analizados. Pertenecen a
          sus titulares y su uso no implica patrocinio ni asociación.
        </p>
      </Clause>
    </LegalPage>
  );
}
