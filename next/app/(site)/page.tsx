import { FounderLetter } from "@/components/experience/FounderLetter";
import { MethodRing } from "@/components/experience/MethodRing";
import { ProbabilityTicker } from "@/components/experience/ProbabilityTicker";
import { RevealObserver } from "@/components/experience/RevealObserver";
import { SignalStory } from "@/components/experience/SignalStory";
import { PlanCards } from "@/components/site/PlanCards";

export default function Home() {
  return (
    <div className="grain -mt-16">
      <SignalStory />
      <ProbabilityTicker />
      <MethodRing />
      <FounderLetter />
      <section className="reveal-on-enter relative mx-auto max-w-6xl px-5 sm:px-6 pt-24 pb-10" id="planes">
        <div>
          <p className="num text-[11px] tracking-[0.22em] text-lo uppercase">Planes</p>
          <h2 className="display mt-4 text-[2.6rem] sm:text-[4rem]">
            Empieza gratis. <em>Paga por profundidad</em>, no por promesas.
          </h2>
        </div>
        <div className="mt-10">
          <PlanCards />
        </div>
      </section>
      <RevealObserver />
    </div>
  );
}
