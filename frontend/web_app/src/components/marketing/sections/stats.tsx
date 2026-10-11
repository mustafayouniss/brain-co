import { landingCopy } from "@/content/marketing";
import { Reveal } from "@/components/marketing/sections/reveal";

/** Trust band with animated counters-as-static stats. */
export function Stats() {
  return (
    <section aria-label="Platform statistics" className="border-y border-border section-base py-12">
      <div className="container-page grid grid-cols-2 gap-6 md:grid-cols-4">
        {landingCopy.stats.map((stat, index) => (
          <Reveal key={stat.label} delay={index * 0.06} className="text-center md:text-left">
            <p className="text-4xl font-semibold tracking-tight text-[var(--ring)] sm:text-5xl">
              {stat.value}
            </p>
            <p className="mt-2 text-sm text-muted">{stat.label}</p>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
