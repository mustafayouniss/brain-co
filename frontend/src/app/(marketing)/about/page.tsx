import type { Metadata } from "next";
import Link from "next/link";
import { aboutCopy } from "@/content/marketing";
import { Breadcrumbs } from "@/components/marketing/breadcrumbs";
import { ArrowIcon } from "@/components/brand/icons";
import { buttonClasses } from "@/components/ui/button";
import { Reveal } from "@/components/marketing/sections/reveal";
import { cn } from "@/lib/utils";

export const metadata: Metadata = {
  title: aboutCopy.meta.title,
  description: aboutCopy.meta.description,
  alternates: { canonical: "/about" },
};

export default function AboutPage() {
  return (
    <div className="relative min-h-screen bg-[#020409] text-white">
      <Breadcrumbs items={[{ label: "About" }]} />

      <section className="container-page py-16 sm:py-24" aria-labelledby="about-title">
        <Reveal className="max-w-3xl">
          <div className="text-xs font-mono uppercase tracking-[0.2em] text-cyan-400">
            {aboutCopy.eyebrow}
          </div>
          <h1 id="about-title" className="cinematic-title mt-4 font-normal tracking-tight text-white text-balance">
            {aboutCopy.title}
          </h1>
          <p className="mt-6 max-w-2xl text-base sm:text-lg text-zinc-400 font-light leading-relaxed">
            {aboutCopy.intro}
          </p>
        </Reveal>

        {/* 3 Core Architecture Pillars */}
        <div className="mt-16 grid gap-6 md:grid-cols-3">
          {aboutCopy.sections.map((section, index) => (
            <Reveal key={section.number} delay={index * 0.1}>
              <article className="flex h-full flex-col justify-between rounded-2xl border border-white/[0.08] bg-black/40 p-8 transition-all duration-300 hover:border-white/20 hover:bg-black/60">
                <div>
                  <span className="text-xs font-mono font-medium tracking-wider text-cyan-400">
                    {section.number}
                  </span>
                  <h2 className="mt-4 text-xl font-medium tracking-tight text-white">
                    {section.title}
                  </h2>
                  <p className="mt-1 text-xs font-mono uppercase tracking-wider text-zinc-500">
                    {section.subtitle}
                  </p>
                  <p className="mt-4 text-sm font-light leading-relaxed text-zinc-300">
                    {section.body}
                  </p>
                </div>
              </article>
            </Reveal>
          ))}
        </div>

        {/* Guiding Principles */}
        <div className="mt-20 border-t border-white/[0.08] pt-16">
          <Reveal className="max-w-2xl">
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-cyan-400">
              Guiding Directives
            </div>
            <h2 className="text-2xl sm:text-3xl font-medium tracking-tight text-white mt-2">
              {aboutCopy.principles.title}
            </h2>
          </Reveal>

          <div className="mt-10 grid gap-6 md:grid-cols-3">
            {aboutCopy.principles.items.map((item, index) => (
              <Reveal key={item.title} delay={index * 0.1}>
                <div className="h-full rounded-2xl border border-white/[0.06] bg-black/40 p-8">
                  <h3 className="text-base font-medium text-white">{item.title}</h3>
                  <p className="mt-3 text-sm font-light leading-relaxed text-zinc-400">
                    {item.body}
                  </p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>

        {/* Bottom CTAs */}
        <Reveal delay={0.15} className="mt-16 flex flex-wrap gap-4 border-t border-white/[0.08] pt-12">
          <Link
            href="/onboarding"
            className={cn(buttonClasses("pill-white", "lg"), "text-xs font-semibold px-8")}
          >
            <span>See how it works</span>
            <ArrowIcon />
          </Link>
          <Link
            href="/contact"
            className={cn(buttonClasses("pill-glass", "lg"), "text-xs px-8")}
          >
            <span>Talk to us</span>
            <ArrowIcon />
          </Link>
        </Reveal>
      </section>
    </div>
  );
}
