import { FounderLetter } from "@/components/experience/FounderLetter";
import { RevealObserver } from "@/components/experience/RevealObserver";
import { SignalStory } from "@/components/experience/SignalStory";
import { FilmScrub } from "@/components/landing/FilmScrub";
import { MatchRadar } from "@/components/landing/MatchRadar";
import { FinalCta, MobileCta, ProofNumbers, ScrollProgress, Versus } from "@/components/landing/Sections";
import { PlanCards } from "@/components/site/PlanCards";

/**
 * The particle story is the page: its first frame now says what we sell (and shows a real sample) on top of the noise;
 * each sport act lands on today's real matches. After the signal: the radar, the proof, what we are not, why, price.
 */
export default function Home() {
  return (
    <div className="grain -mt-[calc(4rem+36px)]">
      <ScrollProgress />
      <SignalStory />
      <FilmScrub />
      <MatchRadar />
      <ProofNumbers />
      <Versus />
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
