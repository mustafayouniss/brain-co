"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowIcon } from "@/components/brand/icons";
import { buttonClasses } from "@/components/ui/button";
import { landingCopy } from "@/content/marketing";
import { Reveal } from "./reveal";
import { cn } from "@/lib/utils";

export function CinematicCta() {
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  const toggleFaq = (index: number) => {
    setOpenFaq(openFaq === index ? null : index);
  };

  return (
    <section className="relative py-28 px-4 sm:px-6 lg:px-8 border-t border-white/[0.06] bg-transparent overflow-hidden">
      <div className="max-w-5xl mx-auto">
        {/* Editorial Final Call to Action */}
        <div className="text-center max-w-3xl mx-auto py-12">
          <Reveal>
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-white/10 bg-black/40 mb-6">
              <span className="text-[11px] font-mono uppercase tracking-[0.18em] text-cyan-400">
                Ready for Immediate Deployment
              </span>
            </div>

            <h2 className="cinematic-title text-3xl sm:text-5xl md:text-6xl font-medium tracking-tight text-white text-balance leading-tight">
              Build the brain <br className="hidden sm:inline" />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-zinc-200 to-cyan-300">
                your organization deserves.
              </span>
            </h2>

            <p className="mt-6 text-base sm:text-lg text-zinc-400 font-light leading-relaxed text-balance">
              Six minutes from first click to a functioning, deterministic organizational intelligence layer.
              Upload policies and agreements. Prevent institutional memory from walking out the door.
            </p>

            <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
              <Link
                href="/onboarding"
                className={cn(buttonClasses("pill-white", "lg"), "group px-8 text-sm font-semibold")}
              >
                <span>Get Started in 6 Minutes</span>
                <ArrowIcon className="transition-transform duration-200 group-hover:translate-x-1" />
              </Link>
              <Link
                href="/contact"
                className={cn(buttonClasses("pill-glass", "lg"), "px-8 text-sm")}
              >
                <span>Schedule Enterprise Consultation</span>
              </Link>
            </div>
          </Reveal>
        </div>

        {/* FAQ Accordion */}
        <div id="faq" className="mt-28 border-t border-white/[0.08] pt-16">
          <Reveal className="max-w-2xl">
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-cyan-400">
              Frequently Answered Questions
            </div>
            <h3 className="text-2xl sm:text-3xl font-medium tracking-tight text-white mt-3">
              Clear answers to critical questions.
            </h3>
          </Reveal>

          <div className="mt-10 divide-y divide-white/[0.06] border-y border-white/[0.06]">
            {landingCopy.faq.items.map((item, index) => {
              const isOpen = openFaq === index;
              return (
                <div key={item.q} className="py-5">
                  <button
                    type="button"
                    onClick={() => toggleFaq(index)}
                    aria-expanded={isOpen}
                    className="flex w-full items-center justify-between text-left text-base sm:text-lg font-medium text-white transition-colors hover:text-cyan-300 cursor-pointer"
                  >
                    <span>{item.q}</span>
                    <span className="ml-4 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-white/10 text-xs font-mono text-zinc-400">
                      {isOpen ? "−" : "+"}
                    </span>
                  </button>

                  {isOpen && (
                    <div className="mt-4 pr-12 text-sm font-light text-zinc-400 leading-relaxed">
                      {item.a}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
