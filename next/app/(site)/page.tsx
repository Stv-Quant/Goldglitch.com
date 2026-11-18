import { FounderLetter } from "@/components/experience/FounderLetter";
import { RevealObserver } from "@/components/experience/RevealObserver";
import { SignalStory } from "@/components/experience/SignalStory";
import { Hero } from "@/components/landing/Hero";
import { MatchRadar } from "@/components/landing/MatchRadar";
import { Bento, FinalCta, MobileCta, Pipeline, ProofNumbers, ScrollProgress, Versus } from "@/components/landing/Sections";
import { PlanCards } from "@/components/site/PlanCards";

/**
 * Order follows the 10-second rule: what we sell (Hero + a real sample) → it is alive (Radar) → it is honest (Proof)
 * → how (Pipeline) → what we are not (Versus) → what you get (Bento) → the cinematic story → why → price → close.
 */
export default function Home() {
  return (
    <div className="grain -mt-[calc(4rem+36px)]">
      <ScrollProgress />
      <Hero />
      <MatchRadar />
      <ProofNumbers />
      <Pipeline />
      <Versus />
      <Bento />
      <SignalStory />
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
      <FinalCta />
      <MobileCta />
      <RevealObserver />
    </div>
  );
}
