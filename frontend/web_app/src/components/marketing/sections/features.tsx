import {
  AlertTriangle,
  Brain,
  CheckCircle2,
  Lock,
  Search,
  ShieldCheck,
} from "lucide-react";
import { landingCopy } from "@/content/marketing";
import { Reveal } from "@/components/marketing/sections/reveal";

const icons = {
  brain: Brain,
  search: Search,
  alert: AlertTriangle,
  check: CheckCircle2,
  shield: ShieldCheck,
  lock: Lock,
} as const;

/** Six capability cards from the product's discovery sheet + feature copy. */
export function Features() {
  const { features } = landingCopy;

  return (
    <section aria-labelledby="features-title" className="section-base py-20 sm:py-28">
      <div className="container-page">
        <Reveal className="max-w-2xl">
          <p className="eyebrow">{features.eyebrow}</p>
          <h2 id="features-title" className="section-title mt-4 text-balance">
            {features.title}
          </h2>
          <p className="mt-5 text-base leading-relaxed text-muted">{features.description}</p>
        </Reveal>

        <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.items.map((item, index) => {
            const Icon = icons[item.icon];
            return (
              <Reveal key={item.title} delay={(index % 3) * 0.07}>
                <article className="group h-full rounded-2xl border border-border bg-surface p-6 transition-colors duration-300 hover:border-[color-mix(in_srgb,var(--brand)_55%,transparent)]">
                  <span className="grid h-11 w-11 place-items-center rounded-xl border border-border-strong bg-surface-2 text-[var(--ring)] transition-colors duration-300 group-hover:border-[color-mix(in_srgb,var(--brand)_55%,transparent)] group-hover:bg-brand-soft">
                    <Icon aria-hidden="true" className="h-5 w-5" />
                  </span>
                  <h3 className="mt-5 text-base font-semibold tracking-tight">{item.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted">{item.body}</p>
                </article>
              </Reveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}
