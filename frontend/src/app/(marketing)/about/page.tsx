import type { Metadata } from "next";
import Link from "next/link";
import { aboutCopy } from "@/content/marketing";
import { Breadcrumbs } from "@/components/marketing/breadcrumbs";
import { ArrowIcon } from "@/components/brand/icons";
import { buttonClasses } from "@/components/ui/button";
import { Reveal } from "@/components/marketing/sections/reveal";

export const metadata: Metadata = {
  title: aboutCopy.meta.title,
  description: aboutCopy.meta.description,
  alternates: { canonical: "/about" },
};

export default function AboutPage() {
  return (
    <>
      <Breadcrumbs items={[{ label: "About" }]} />

      <section className="container-page py-14 sm:py-20" aria-labelledby="about-title">
        <Reveal className="max-w-3xl">
          <p className="eyebrow">{aboutCopy.eyebrow}</p>
          <h1 id="about-title" className="section-title mt-4 text-balance">
            {aboutCopy.title}
          </h1>
          <p className="mt-6 max-w-2xl text-base leading-relaxed text-muted">{aboutCopy.intro}</p>
        </Reveal>

        <div className="mt-14 grid gap-5 md:grid-cols-3">
          {aboutCopy.sections.map((section, index) => (
            <Reveal key={section.number} delay={index * 0.08}>
              <article className="h-full rounded-2xl border border-border bg-surface p-6">
                <span className="text-xs font-bold tracking-[0.08em] text-gold">
                  {section.number}
                </span>
                <h2 className="mt-3 text-lg font-semibold tracking-tight">{section.title}</h2>
                <p className="mt-1 text-xs font-semibold uppercase tracking-[0.1em] text-subtle">
                  {section.subtitle}
                </p>
                <p className="mt-4 text-sm leading-relaxed text-muted">{section.body}</p>
              </article>
            </Reveal>
          ))}
        </div>

        <div className="mt-16 border-t border-border pt-12">
          <Reveal>
            <h2 className="text-2xl font-semibold tracking-tight">{aboutCopy.principles.title}</h2>
          </Reveal>
          <div className="mt-6 grid gap-5 md:grid-cols-3">
            {aboutCopy.principles.items.map((item, index) => (
              <Reveal key={item.title} delay={index * 0.08}>
                <div className="h-full rounded-2xl border border-border bg-deep p-6">
                  <h3 className="text-base font-semibold">{item.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted">{item.body}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>

        <Reveal delay={0.1} className="mt-12 flex flex-wrap gap-3">
          <Link href="/onboarding" className={buttonClasses("primary", "lg")}>
            <span>See how it works</span>
            <ArrowIcon />
          </Link>
          <Link href="/contact" className={buttonClasses("secondary", "lg")}>
            <span>Talk to us</span>
            <ArrowIcon />
          </Link>
        </Reveal>
      </section>
    </>
  );
}
