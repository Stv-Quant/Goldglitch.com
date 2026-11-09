import { SignalStory } from "@/components/experience/SignalStory";
import { PlanCards } from "@/components/site/PlanCards";

export default function Home() {
  return (
    <div className="grain -mt-16">
      <SignalStory />
      <section className="relative mx-auto max-w-6xl px-5 sm:px-6 pt-24 pb-10" id="planes">
        <p className="num text-[11px] tracking-[0.22em] text-lo uppercase">06 — Profundidad</p>
        <h2 className="display mt-4 text-[2.6rem] sm:text-[4rem]">
          Empieza gratis. <em>Paga por profundidad</em>, no por promesas.
        </h2>
        <div className="mt-10">
          <PlanCards />
        </div>
      </section>
    </div>
  );
}
