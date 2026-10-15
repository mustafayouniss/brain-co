import { landingCopy } from "@/content/marketing";
import { Accordion } from "@/components/ui/accordion";
import { Reveal } from "@/components/marketing/sections/reveal";

/** FAQ accordion (also exposed as FAQPage JSON-LD on the landing page). */
export function Faq() {
  const { faq } = landingCopy;

  return (
    <section aria-labelledby="faq-title" className="section-base py-20 sm:py-28">
      <div className="container-page grid gap-10 lg:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)]">
        <Reveal>
          <p className="eyebrow">{faq.eyebrow}</p>
          <h2 id="faq-title" className="section-title mt-4 text-balance">
            {faq.title}
          </h2>
          <p className="mt-4 max-w-sm text-sm leading-relaxed text-muted">
            Everything the product promises, in plain language. Still curious?{" "}
            <a href="/contact" className="text-[var(--ring)] underline underline-offset-4">
              Talk to a human.
            </a>
          </p>
        </Reveal>

        <Reveal delay={0.08}>
          <Accordion items={faq.items} />
        </Reveal>
      </div>
    </section>
  );
}
