import type { Metadata } from "next";
import Link from "next/link";
import { modulesCopy } from "@/content/marketing";
import { shapeUrls, type DomainKey } from "@/content/app";
import { Breadcrumbs } from "@/components/marketing/breadcrumbs";
import { ArrowIcon } from "@/components/brand/icons";
import { Badge } from "@/components/ui/card";
import { buttonClasses } from "@/components/ui/button";
import { Reveal } from "@/components/marketing/sections/reveal";
import { cn } from "@/lib/utils";

export const metadata: Metadata = {
  title: modulesCopy.meta.title,
  description: modulesCopy.meta.description,
  alternates: { canonical: "/modules" },
};

const shapeClass: Record<DomainKey, string> = {
  legal: "text-gold",
  sales: "text-mint",
  hr: "text-violet",
};

export default function ModulesPage() {
  return (
    <>
      <Breadcrumbs items={[{ label: "Modules" }]} />

      <section className="container-page py-14 sm:py-20" aria-labelledby="modules-title">
        <Reveal className="max-w-3xl">
          <p className="eyebrow">{modulesCopy.eyebrow}</p>
          <h1 id="modules-title" className="section-title mt-4 text-balance">
            {modulesCopy.title}
          </h1>
          <p className="mt-6 max-w-2xl text-base leading-relaxed text-muted">
            {modulesCopy.description}
          </p>
        </Reveal>

        <div className="mt-12 grid gap-5 lg:grid-cols-3">
          {modulesCopy.modules.map((module, index) => {
            const available = module.status === "Available";
            return (
              <Reveal key={module.key} delay={index * 0.08}>
                <article
                  className={cn(
                    "flex h-full flex-col rounded-2xl border bg-surface p-6 transition-colors duration-300",
                    available
                      ? "border-[color-mix(in_srgb,var(--gold)_45%,transparent)]"
                      : "border-border",
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <img
                      src={shapeUrls[module.key]}
                      alt={`${module.title} domain shape`}
                      className="h-20 w-20"
                      decoding="async"
                    />
                    <Badge variant={available ? "available" : "planned"}>
                      {module.status}
                    </Badge>
                  </div>

                  <h2
                    className={cn(
                      "mt-5 text-2xl font-semibold tracking-tight",
                      shapeClass[module.key],
                    )}
                  >
                    {module.title}
                  </h2>
                  <p className="mt-1 text-sm font-semibold text-foreground">{module.tagline}</p>
                  <p className="mt-3 flex-1 text-sm leading-relaxed text-muted">{module.body}</p>

                  <ul className="mt-5 space-y-2 border-t border-border pt-4">
                    {module.points.map((point) => (
                      <li
                        key={point}
                        className="flex gap-2.5 text-sm leading-relaxed text-muted"
                      >
                        <span aria-hidden="true" className="mt-1.5 h-1.5 w-1.5 flex-none rounded-full bg-brand" />
                        {point}
                      </li>
                    ))}
                  </ul>

                  <Link
                    href={available ? "/onboarding/domains" : "/contact"}
                    className={cn(buttonClasses(available ? "primary" : "secondary", "md"), "mt-6 w-full")}
                  >
                    <span>{module.cta}</span>
                    <ArrowIcon />
                  </Link>
                </article>
              </Reveal>
            );
          })}
        </div>
      </section>
    </>
  );
}
