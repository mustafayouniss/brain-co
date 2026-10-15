import Link from "next/link";
import { landingCopy } from "@/content/marketing";
import { ArrowIcon } from "@/components/brand/icons";
import { buttonClasses } from "@/components/ui/button";
import { Reveal } from "@/components/marketing/sections/reveal";

/** 4-step "how it works" flow mirroring the actual onboarding journey. */
export function HowItWorks() {
  const { howItWorks } = landingCopy;

  return (
    <section aria-labelledby="how-title" className="border-y border-border band-deep py-20 sm:py-28">
      <div className="container-page">
        <Reveal className="max-w-2xl">
          <p className="eyebrow">{howItWorks.eyebrow}</p>
          <h2 id="how-title" className="section-title mt-4 text-balance">
            {howItWorks.title}
          </h2>
        </Reveal>

        <ol className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {howItWorks.steps.map((step, index) => (
            <li key={step.number} className="h-full">
              <Reveal delay={index * 0.08} className="h-full">
                <div className="relative h-full rounded-2xl border border-border bg-surface p-6">
                  <span
                    aria-hidden="true"
                    className="absolute -top-3 right-5 rounded-full border border-[color-mix(in_srgb,var(--brand)_55%,transparent)] bg-background px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-[0.1em] text-[var(--ring)]"
                  >
                    Step
                  </span>
                  <p className="text-xs font-bold tracking-[0.08em] text-gold">{step.number}</p>
                  <h3 className="mt-3 text-lg font-semibold tracking-tight">{step.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted">{step.body}</p>
                </div>
              </Reveal>
            </li>
          ))}
        </ol>

        <Reveal delay={0.1} className="mt-10">
          <Link href="/onboarding" className={buttonClasses("primary", "lg")}>
            <span>Start the walkthrough</span>
            <ArrowIcon />
          </Link>
        </Reveal>
      </div>
    </section>
  );
}
