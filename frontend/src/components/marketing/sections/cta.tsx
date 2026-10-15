import Link from "next/link";
import { landingCopy } from "@/content/marketing";
import { ArrowIcon } from "@/components/brand/icons";
import { buttonClasses } from "@/components/ui/button";
import { Reveal } from "@/components/marketing/sections/reveal";

/** Final call-to-action band. */
export function CallToAction() {
  const { cta } = landingCopy;

  return (
    <section aria-labelledby="cta-title" className="relative overflow-hidden band-deep py-24">
      <div className="grid-overlay" aria-hidden="true" />
      <div
        className="purple-glow pointer-events-none absolute left-1/2 top-1/2 h-[560px] w-[560px] -translate-x-1/2 -translate-y-1/2"
        aria-hidden="true"
      />
      <div className="container-page relative text-center">
        <Reveal>
          <h2 id="cta-title" className="section-title mx-auto max-w-2xl text-balance">
            {cta.title}
          </h2>
          <p className="mx-auto mt-5 max-w-xl text-base leading-relaxed text-muted">{cta.body}</p>
          <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link href="/onboarding" className={buttonClasses("primary", "lg")}>
              <span>{cta.primary}</span>
              <ArrowIcon />
            </Link>
            <Link href="/contact" className={buttonClasses("secondary", "lg")}>
              <span>{cta.secondary}</span>
              <ArrowIcon />
            </Link>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
