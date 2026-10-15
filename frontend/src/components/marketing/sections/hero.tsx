import Link from "next/link";
import { landingCopy } from "@/content/marketing";
import { homeCopy } from "@/content/app";
import { BrainHero } from "@/components/brand/brain-hero";
import { BrainPhaseLabel } from "@/components/brand/brain-phase-label";
import { ArrowIcon } from "@/components/brand/icons";
import { buttonClasses } from "@/components/ui/button";
import { Reveal } from "@/components/marketing/sections/reveal";

const { hero } = landingCopy;

/**
 * Landing hero: brand headline + animated General Brain + primary CTAs.
 * Two-column from lg (copy left inside the container-page text column, brain
 * right in a reserved panel-free box that bleeds toward the viewport edge),
 * stacked on tablet/phone. The text content is unchanged — only arrangement.
 */
export function Hero() {
  return (
    <section className="relative overflow-hidden band-deep" aria-labelledby="hero-title">
      <div className="grid-overlay" aria-hidden="true" />

      <div className="container-page relative pb-16 pt-16 sm:pt-24">
        <div className="hero-grid">
          <div className="hero-copy">
            <Reveal>
              <p className="eyebrow justify-center lg:justify-start">{hero.eyebrow}</p>
            </Reveal>

            <Reveal delay={0.05}>
              <h1
                id="hero-title"
                className="hero-title mt-5 max-w-4xl text-balance text-[clamp(38px,7vw,72px)] font-medium leading-[1.02] tracking-[-0.052em]"
              >
                {hero.titleLead} <em className="not-italic text-[#9a76ff]">{hero.titleAccent}</em>
                <br />
                {hero.titleTail}
              </h1>
            </Reveal>

            <Reveal delay={0.1}>
              <p className="mt-6 max-w-xl text-balance text-base leading-relaxed text-muted sm:text-lg">
                {hero.description}
              </p>
            </Reveal>

            <Reveal delay={0.16}>
              <div className="hero-actions mt-9 flex w-full max-w-md flex-col gap-2.5 sm:flex-row sm:justify-center">
                <Link href="/onboarding" className={buttonClasses("primary", "lg", "w-full sm:w-auto")}>
                  <span>{hero.primary}</span>
                  <ArrowIcon />
                </Link>
                <Link
                  href="/onboarding/domains"
                  className={buttonClasses("secondary", "lg", "w-full sm:w-auto")}
                >
                  <span>{hero.secondary}</span>
                  <ArrowIcon />
                </Link>
              </div>
            </Reveal>

            <Reveal delay={0.22} className="mt-4">
              <p className="text-xs text-subtle">
                {hero.taglineLead} <span className="text-muted">{hero.taglineTail}</span>
              </p>
            </Reveal>
          </div>

          {/* No Reveal on the brain column: the server-rendered static brain
              must be visible from first paint, then crossfade into the canvas
              (its own entrance) — and the reserved box never shifts. */}
          <div className="hero-visual-wrap mt-14 w-full sm:mt-32 lg:mt-0 lg:w-auto">
            <div className="hero-visual">
              <div
                className="purple-glow pointer-events-none absolute left-1/2 top-1/2 h-[720px] w-[720px] -translate-x-1/2 -translate-y-1/2 opacity-70"
                aria-hidden="true"
              />
              <div className="hero-brain-box" role="img" aria-label={homeCopy.brainAria}>
                <BrainHero />
              </div>
              <div className="hero-brain-label">
                <BrainPhaseLabel />
              </div>
            </div>
          </div>
        </div>

        <p className="sr-only">{homeCopy.brainAria}</p>
      </div>

      <div
        className="pointer-events-none absolute inset-x-0 bottom-0 h-24 bg-gradient-to-b from-transparent to-background"
        aria-hidden="true"
      />
    </section>
  );
}
