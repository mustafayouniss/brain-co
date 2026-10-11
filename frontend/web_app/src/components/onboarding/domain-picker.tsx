"use client";

import Link from "next/link";
import { domainDetails, domainsCopy, shapeUrls, type DomainKey } from "@/content/app";
import { ArrowIcon } from "@/components/brand/icons";
import { cn } from "@/lib/utils";

const order: DomainKey[] = ["legal", "sales", "hr"];

const accentBorder: Record<DomainKey, string> = {
  legal: "border-gold/50 hover:border-gold",
  sales: "border-mint/40 hover:border-mint",
  hr: "border-violet/40 hover:border-violet",
};

const accentText: Record<DomainKey, string> = {
  legal: "text-gold",
  sales: "text-mint",
  hr: "text-violet",
};

/** Domain picker (source view `domains`): Legal available, Sales/HR planned. */
export function DomainPicker() {
  return (
    <div className="relative min-h-[calc(100dvh-3.5rem)] bg-black">
      <div className="grid-overlay" aria-hidden="true" />
      <div className="relative mx-auto w-full max-w-4xl px-5 pb-16 pt-14 text-center sm:px-8">
        <p className="eyebrow justify-center">{domainsCopy.kicker}</p>
        <h1 className="mt-5 text-balance text-3xl font-medium tracking-[-0.04em] sm:text-5xl">
          {domainsCopy.title}
        </h1>
        <p className="mx-auto mt-4 max-w-md text-sm leading-relaxed text-[#a7b0c1]">
          One General Brain, specialized per field. Choose where your organization starts.
        </p>

        <div className="mt-10 grid gap-4 text-left sm:grid-cols-2 lg:grid-cols-3">
          {order.map((key, index) => {
            const detail = domainDetails[key];
            const available = detail.status === "Available";
            return (
              <Link
                key={key}
                href={`/onboarding/domains/${key}`}
                aria-label={`${detail.title} — ${detail.status}`}
                className={cn(
                  "group relative flex animate-fade-up flex-col overflow-hidden rounded-2xl border bg-[#0a1222] p-6 transition-all duration-300",
                  accentBorder[key],
                  "motion-safe:hover:-translate-y-1",
                )}
                style={{ animationDelay: `${index * 90}ms` }}
              >
                <div className="flex items-start justify-between gap-3">
                  <img
                    src={shapeUrls[key]}
                    alt=""
                    aria-hidden="true"
                    className="h-24 w-24 transition-transform duration-500 group-hover:scale-105"
                    decoding="async"
                  />
                  <span
                    className={cn(
                      "tag",
                      available ? "tag-available" : "tag-planned",
                    )}
                  >
                    {detail.status}
                  </span>
                </div>

                <h2 className={cn("mt-5 text-2xl font-semibold tracking-tight", accentText[key])}>
                  {detail.title}
                </h2>
                <p className="mt-2 flex-1 text-sm leading-relaxed text-[#a7b0c1]">
                  {available
                    ? "Available now. Every case remembered, missing information flagged, conflicts caught early."
                    : `Intelligence for ${detail.title} teams. Part of the roadmap — not available yet.`}
                </p>

                <span className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-white">
                  {available ? "Continue" : "See status"}
                  <ArrowIcon className="transition-transform duration-300 group-hover:translate-x-1" />
                </span>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
