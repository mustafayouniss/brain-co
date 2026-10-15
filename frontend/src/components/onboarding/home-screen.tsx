"use client";

import * as React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { homeCopy, discoverCopy } from "@/content/app";
import { BrainNetwork } from "@/components/brand/brain-network";
import { BrandMark, ArrowIcon } from "@/components/brand/icons";
import { Dialog, DialogClose } from "@/components/ui/dialog";
import { buttonClasses } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/**
 * Onboarding entry point (source view `home`): header, kicker, H1, animated
 * General Brain, CTAs and the Discover bottom sheet with 3 sections.
 */
export function HomeScreen() {
  const [discoverOpen, setDiscoverOpen] = React.useState(false);

  return (
    <div className="relative min-h-[calc(100dvh-3.5rem)] overflow-hidden bg-black">
      <div className="grid-overlay" aria-hidden="true" />
      <div
        className="pointer-events-none absolute left-1/2 top-1/2 h-[700px] w-[700px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(circle,rgba(128,82,255,0.18),transparent_65%)]"
        aria-hidden="true"
      />

      <div className="relative mx-auto flex min-h-[calc(100dvh-3.5rem)] w-full max-w-3xl flex-col items-center px-5 pb-14 pt-12 text-center sm:px-8">
        {/* Info button → Discover sheet (source header info button) */}
        <button
          type="button"
          aria-label={homeCopy.infoAria}
          onClick={() => setDiscoverOpen(true)}
          className="absolute right-5 top-6 grid h-11 w-11 place-items-center rounded-full border border-[#34405a] bg-[#0a1222] transition-colors hover:border-[#946eff] sm:right-8"
        >
          <span className="font-[Georgia,serif] text-lg italic text-[#a7b0c1]">i</span>
        </button>

        <motion.p
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="eyebrow justify-center"
        >
          {homeCopy.kicker}
        </motion.p>

        <motion.h1
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.06 }}
          className="mt-6 max-w-2xl text-balance text-4xl font-medium leading-[1.06] tracking-[-0.05em] sm:text-6xl"
        >
          {homeCopy.titleLead}{" "}
          <em className="not-italic text-[#9a76ff]">{homeCopy.titleAccent}</em>{" "}
          {homeCopy.titleTail}
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.14 }}
          className="mt-5 max-w-md text-sm leading-relaxed text-[#8a8a92] sm:text-base"
        >
          {homeCopy.description}
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.22 }}
          className="mt-8 flex w-full max-w-md flex-col gap-2.5 sm:flex-row sm:justify-center"
        >
          <button
            type="button"
            onClick={() => setDiscoverOpen(true)}
            className={buttonClasses("primary", "lg", "w-full sm:w-auto")}
          >
            <span>{homeCopy.primaryCta}</span>
            <ArrowIcon />
          </button>
          <Link
            href="/onboarding/domains"
            className={buttonClasses("secondary", "lg", "w-full sm:w-auto")}
          >
            <span>{homeCopy.secondaryCta}</span>
            <ArrowIcon />
          </Link>
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.34 }}
          className="mt-5 text-xs text-[#8a8a92]"
        >
          {homeCopy.taglineLead}{" "}
          <span className="text-white">{homeCopy.taglineTail}</span>
        </motion.p>

        <motion.div
          initial={{ opacity: 0, scale: 0.94 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.7, delay: 0.4 }}
          className="mt-10 w-full"
        >
          <div className="mx-auto w-[min(100%,400px)] sm:w-[min(100%,460px)]">
            <BrainNetwork />
          </div>
        </motion.div>

        <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
          <Link href="/onboarding/intro" className={buttonClasses("secondary", "md")}>
            <span>Watch the brand story</span>
            <ArrowIcon />
          </Link>
          <Link href="/onboarding/story" className={buttonClasses("ghost", "md")}>
            <span>Skip to product walkthrough</span>
          </Link>
        </div>
      </div>

      <DiscoverDialog open={discoverOpen} onClose={() => setDiscoverOpen(false)} />
    </div>
  );
}

/** Discover sheet — sections 01 General Brain / 02 Domain Modules / 03 Your Organization. */
function DiscoverDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <Dialog open={open} onClose={onClose} labelledBy="discover-title" variant="sheet">
      <div className="p-6 sm:p-8">
        <span className="sr-only">{discoverCopy.closeAria}</span>
        <DialogClose onClose={onClose} />

        <p className="eyebrow justify-center">{discoverCopy.eyebrow}</p>
        <h2
          id="discover-title"
          className="mt-4 whitespace-pre-line text-center text-2xl font-medium leading-snug tracking-[-0.03em] sm:text-3xl"
        >
          {discoverCopy.title}
        </h2>

        <div className="mt-8 flex flex-col gap-7">
          {discoverCopy.sections.map((section, index) => (
            <section key={section.number} aria-labelledby={`discover-${section.number}`}>
              <div className="flex items-baseline gap-3">
                <span className="text-xs font-bold text-[#f3ca78]">{section.number}</span>
                <div>
                  <h3 id={`discover-${section.number}`} className="text-base font-semibold">
                    {section.title}
                  </h3>
                  <p className="text-xs text-[#8a8a92]">{section.subtitle}</p>
                </div>
              </div>
              <ul className="mt-3 grid gap-x-6 gap-y-1.5 sm:grid-cols-2">
                {section.items.map((item, itemIndex) => (
                  <li
                    key={item}
                    className={cn(
                      "flex items-start gap-2 text-left text-sm text-[#a7b0c1]",
                      "animate-text-in",
                    )}
                    style={{ animationDelay: `${index * 90 + itemIndex * 45}ms` }}
                  >
                    <span
                      aria-hidden="true"
                      className="mt-1.5 h-1.5 w-1.5 flex-none rounded-full bg-[#8052ff]"
                    />
                    {item}
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>

        <div className="mt-8 flex justify-center">
          <Link
            href="/onboarding/intro"
            onClick={onClose}
            className={buttonClasses("primary", "lg", "w-full sm:w-auto")}
          >
            <span>{discoverCopy.cta}</span>
            <ArrowIcon />
          </Link>
        </div>

        <div className="mt-6 flex justify-center" aria-hidden="true">
          <BrandMark />
        </div>
      </div>
    </Dialog>
  );
}
