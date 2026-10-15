import { landingCopy } from "@/content/marketing";
import { Reveal } from "@/components/marketing/sections/reveal";

/** Testimonials — three knowledge-team quotes with initials avatars. */
export function Testimonials() {
  const { testimonials } = landingCopy;

  return (
    <section aria-labelledby="testimonials-title" className="border-y border-border band-deep py-20 sm:py-28">
      <div className="container-page">
        <Reveal className="max-w-2xl">
          <p className="eyebrow">{testimonials.eyebrow}</p>
          <h2 id="testimonials-title" className="section-title mt-4 text-balance">
            {testimonials.title}
          </h2>
        </Reveal>

        <div className="mt-12 grid gap-5 md:grid-cols-3">
          {testimonials.items.map((item, index) => {
            const initials = item.name
              .split(" ")
              .map((part) => part[0])
              .join("")
              .slice(0, 2);
            return (
              <Reveal key={item.name} delay={index * 0.08}>
                <figure className="flex h-full flex-col rounded-2xl border border-border bg-surface p-6">
                  <span aria-hidden="true" className="text-4xl leading-none text-gold">
                    &ldquo;
                  </span>
                  <blockquote className="mt-3 flex-1 text-sm leading-relaxed text-muted">
                    {item.quote}
                  </blockquote>
                  <figcaption className="mt-6 flex items-center gap-3 border-t border-border pt-4">
                    <span
                      aria-hidden="true"
                      className="grid h-10 w-10 place-items-center rounded-full border border-[color-mix(in_srgb,var(--brand)_55%,transparent)] bg-brand-soft text-xs font-bold text-[var(--ring)]"
                    >
                      {initials}
                    </span>
                    <span>
                      <span className="block text-sm font-semibold">{item.name}</span>
                      <span className="block text-xs text-subtle">{item.role}</span>
                    </span>
                  </figcaption>
                </figure>
              </Reveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}
