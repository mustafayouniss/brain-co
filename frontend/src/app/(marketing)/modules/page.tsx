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

const domainAccents: Record<DomainKey, { border: string; glow: string; text: string }> = {
  legal: {
    border: "border-cyan-500/40",
    glow: "bg-cyan-500/[0.02]",
    text: "text-cyan-400",
  },
  sales: {
    border: "border-violet-500/40",
    glow: "bg-violet-500/[0.02]",
    text: "text-violet-400",
  },
  hr: {
    border: "border-zinc-700/60",
    glow: "bg-zinc-800/[0.02]",
    text: "text-zinc-300",
  },
};

export default function ModulesPage() {
  return (
    <div className="relative min-h-screen bg-[#020409] text-white">
      <Breadcrumbs items={[{ label: "Modules" }]} />

      <section className="container-page py-16 sm:py-24" aria-labelledby="modules-title">
        <Reveal className="max-w-3xl">
          <div className="text-xs font-mono uppercase tracking-[0.2em] text-cyan-400">
            {modulesCopy.eyebrow}
          </div>
          <h1 id="modules-title" className="cinematic-title mt-4 font-normal tracking-tight text-white text-balance">
            {modulesCopy.title}
          </h1>
          <p className="mt-6 max-w-2xl text-base sm:text-lg text-zinc-400 font-light leading-relaxed">
            {modulesCopy.description}
          </p>
        </Reveal>

        <div className="mt-16 grid gap-8 lg:grid-cols-3">
          {modulesCopy.modules.map((module, index) => {
            const isAvailable = module.status === "Available";
            const accent = domainAccents[module.key];

            return (
              <Reveal key={module.key} delay={index * 0.1}>
                <article
                  className={cn(
                    "flex h-full flex-col justify-between rounded-2xl border p-8 bg-black/40 transition-all duration-300 hover:bg-black/60",
                    isAvailable
                      ? cn("shadow-[0_12px_40px_rgba(0,0,0,0.6)]", accent.border)
                      : "border-white/[0.08]"
                  )}
                >
                  <div>
                    <div className="flex items-start justify-between gap-4 pb-6 border-b border-white/[0.06]">
                      <img
                        src={shapeUrls[module.key]}
                        alt={`${module.title} domain shape`}
                        className="h-16 w-16 opacity-90"
                        decoding="async"
                      />
                      <Badge variant={isAvailable ? "cyan" : "violet"}>
                        {isAvailable ? "Active (V1 Ready)" : module.status}
                      </Badge>
                    </div>

                    <h2 className="mt-6 text-2xl font-medium tracking-tight text-white">
                      {module.title}
                    </h2>
                    <p className={cn("mt-1 text-xs font-mono tracking-tight", accent.text)}>
                      {module.tagline}
                    </p>
                    <p className="mt-4 text-sm font-light leading-relaxed text-zinc-400">
                      {module.body}
                    </p>

                    <div className="mt-6 border-t border-white/[0.06] pt-6">
                      <span className="text-[11px] font-mono uppercase tracking-widest text-zinc-500">
                        Domain Capabilities
                      </span>
                      <ul className="mt-3 space-y-2.5">
                        {module.points.map((point) => (
                          <li
                            key={point}
                            className="flex items-start gap-2.5 text-xs font-light leading-relaxed text-zinc-300"
                          >
                            <span
                              aria-hidden="true"
                              className={cn(
                                "mt-1.5 h-1.5 w-1.5 flex-none rounded-full",
                                isAvailable ? "bg-cyan-400" : "bg-zinc-600"
                              )}
                            />
                            <span>{point}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  <div className="mt-8 pt-6 border-t border-white/[0.06]">
                    <Link
                      href={isAvailable ? "/onboarding/domains" : "/contact"}
                      className={cn(
                        buttonClasses(isAvailable ? "pill-white" : "pill-glass", "md"),
                        "w-full text-xs font-semibold"
                      )}
                    >
                      <span>{module.cta}</span>
                      <ArrowIcon />
                    </Link>
                  </div>
                </article>
              </Reveal>
            );
          })}
        </div>
      </section>
    </div>
  );
}
