"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { storyCopy, shapeUrls } from "@/content/app";
import { StaticShape } from "@/components/brand/particle-morph";
import { ArrowIcon } from "@/components/brand/icons";
import { buttonClasses } from "@/components/ui/button";
import { StepDots, FlowActions, FlowShell } from "@/components/onboarding/flow";
import { cn } from "@/lib/utils";

const steps = storyCopy.steps;

/**
 * 6-step onboarding story (source view `splash`): progress dots, Continue/Skip,
 * the three-layer stack visual, paired Sales/HR cards and the final CTA.
 */
export function StoryPlayer() {
  const router = useRouter();
  const [index, setIndex] = React.useState(0);
  const step = steps[index];
  const isLast = index === steps.length - 1;

  const advance = () => {
    if (!isLast) setIndex(index + 1);
    else router.push("/onboarding/domains");
  };

  const skip = () => router.push("/onboarding/domains");

  return (
    <div className="relative min-h-[calc(100dvh-3.5rem)] overflow-hidden bg-black">
      <div className="grid-overlay" aria-hidden="true" />
      <div
        className="pointer-events-none absolute left-1/2 top-1/3 h-[560px] w-[560px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(circle,rgba(128,82,255,0.14),transparent_65%)]"
        aria-hidden="true"
      />

      <button
        type="button"
        onClick={skip}
        className="absolute right-5 top-6 z-10 flex h-9 items-center gap-1.5 rounded-full border border-[#34405a] px-3.5 text-xs font-semibold text-[#a7b0c1] transition-colors hover:border-[#946eff] hover:text-white sm:right-8"
      >
        {storyCopy.skip}
        <ArrowIcon className="h-3.5 w-3.5" />
      </button>

      <FlowShell as="section" className="relative min-h-[calc(100dvh-3.5rem)] justify-center pt-6">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#8a94a8]">
          {storyCopy.progressLabel(index + 1)}
        </p>

        <div className="mt-8 flex min-h-[210px] w-full items-center justify-center sm:min-h-[250px]">
          <AnimatePresence mode="wait">
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 10, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.98 }}
              transition={{ duration: 0.35, ease: [0.2, 0.8, 0.2, 1] }}
              className="flex w-full items-center justify-center"
            >
              {step.shape && (
                <img
                  src={shapeUrls[step.shape]}
                  alt={`${step.shape} dot shape`}
                  className="h-44 w-44 sm:h-56 sm:w-56"
                  decoding="async"
                />
              )}
              {index === 2 && <LayerStack />}
              {index === 4 && <PairedDomains />}
            </motion.div>
          </AnimatePresence>
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={`copy-${index}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.32 }}
            className="flex flex-col items-center"
          >
            {step.tag && (
              <span className={`tag ${step.tag === "Available" ? "tag-available" : "tag-planned"}`}>
                {step.tag}
              </span>
            )}
            <h1 className="mt-4 max-w-lg text-balance text-3xl font-medium leading-tight tracking-[-0.04em] sm:text-4xl">
              {step.title}
            </h1>
            {step.body && (
              <p className="mt-4 max-w-md text-sm leading-relaxed text-[#a7b0c1] sm:text-base">
                {step.body}
              </p>
            )}
            {step.lines && (
              <ul className="mt-5 grid w-full max-w-sm gap-2.5 text-left">
                {step.lines.map((line) => (
                  <li
                    key={line}
                    className="flex items-start gap-3 rounded-xl border border-[#202a3e] bg-[#0a1222] px-4 py-3 text-sm text-[#a7b0c1]"
                  >
                    <span
                      aria-hidden="true"
                      className="mt-1.5 h-1.5 w-1.5 flex-none rounded-full bg-[#8052ff]"
                    />
                    {line}
                  </li>
                ))}
              </ul>
            )}
            {isLast && (
              <p className="mt-5 max-w-xs text-xs leading-relaxed text-[#8a8a92]">
                {storyCopy.humanNote}
              </p>
            )}
          </motion.div>
        </AnimatePresence>

        <div className="mt-9 flex flex-col items-center gap-6">
          <StepDots
            total={steps.length}
            active={index}
            ariaLabel={storyCopy.progressLabel(index + 1)}
          />
          <FlowActions>
            <button
              type="button"
              onClick={advance}
              className={buttonClasses("primary", "lg", "w-full sm:w-auto")}
            >
              <span>{isLast ? storyCopy.finalCta : storyCopy.next}</span>
              <ArrowIcon />
            </button>
          </FlowActions>
          {!isLast && (
            <button
              type="button"
              onClick={skip}
              className={cn(
                buttonClasses("ghost", "sm"),
                "text-[13px] text-[#8a94a8]",
              )}
            >
              Skip this section
            </button>
          )}
        </div>
      </FlowShell>
    </div>
  );
}

/** Three-layer stack visual (source: Shared Brain / Field expertise / Your organization). */
function LayerStack() {
  return (
    <div className="layer-stack" role="img" aria-label={storyCopy.layersAria}>
      {storyCopy.layers.map((layer, index) => (
        <div key={layer} className={cn("animate-fade-up")} style={{ animationDelay: `${index * 110}ms` }}>
          <span>{layer}</span>
        </div>
      ))}
    </div>
  );
}

/** Paired Sales / HR "planned" cards (source: PairedDomains). */
function PairedDomains() {
  return (
    <div className="flex w-full max-w-sm flex-col gap-3 sm:flex-row">
      {storyCopy.pairedDomains.map((domain, index) => (
        <div
          key={domain.name}
          className="flex flex-1 animate-fade-up items-center gap-3 rounded-2xl border border-[#202a3e] bg-[#0a1222] p-4"
          style={{ animationDelay: `${index * 110}ms` }}
        >
          <img
            src={shapeUrls[domain.shape]}
            alt=""
            aria-hidden="true"
            className="h-12 w-12"
            decoding="async"
          />
          <div className="text-left">
            <p className="text-sm font-semibold">{domain.name}</p>
            <span className="tag tag-planned mt-1">{domain.status}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
