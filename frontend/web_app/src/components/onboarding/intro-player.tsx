"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useReducedMotion } from "framer-motion";
import { introCopy, type Shape } from "@/content/app";
import { ParticleMorph, StaticShape } from "@/components/brand/particle-morph";
import { ArrowIcon } from "@/components/brand/icons";
import { buttonClasses } from "@/components/ui/button";

const steps = introCopy.steps;

/**
 * Auto-advancing 5-step particle sequence (source view `intro`).
 * Timings are ported exactly: each step morphs for `duration` ms, then waits
 * `wait` ms before advancing; the final step routes into the story.
 */
export function IntroPlayer() {
  const router = useRouter();
  const reduced = useReducedMotion();
  const [index, setIndex] = React.useState(0);
  const step = steps[index];

  React.useEffect(() => {
    const timer = window.setTimeout(() => {
      if (index < steps.length - 1) setIndex(index + 1);
      else router.push("/onboarding/story");
    }, step.duration + step.wait);
    return () => window.clearTimeout(timer);
  }, [index, step.duration, step.wait, router]);

  const from: Shape = index > 0 ? steps[index - 1].shape : step.shape;

  return (
    <div className="relative flex min-h-[calc(100dvh-3.5rem)] flex-col items-center justify-center overflow-hidden bg-black px-5 pb-16 pt-10 text-center">
      <div className="grid-overlay" aria-hidden="true" />
      <div
        className="pointer-events-none absolute left-1/2 top-1/2 h-[640px] w-[640px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(circle,rgba(128,82,255,0.16),transparent_65%)]"
        aria-hidden="true"
      />

      <button
        type="button"
        onClick={() => router.push("/onboarding/story")}
        className="absolute right-5 top-6 flex h-9 items-center gap-1.5 rounded-full border border-[#34405a] px-3.5 text-xs font-semibold text-[#a7b0c1] transition-colors hover:border-[#946eff] hover:text-white sm:right-8"
      >
        {introCopy.skip}
        <ArrowIcon className="h-3.5 w-3.5" />
      </button>

      <p className="eyebrow justify-center text-[#8a94a8]">Brand story</p>

      <div className="relative mx-auto mt-10 flex h-[280px] w-full max-w-[340px] items-center justify-center sm:h-[340px]">
        {reduced ? (
          <StaticShape shape={step.shape} className="h-56 w-56 sm:h-72 sm:w-72" />
        ) : (
          <ParticleMorph
            from={from}
            target={step.shape}
            duration={step.duration}
            drifting={index === 0}
            className="h-56 w-56 sm:h-72 sm:w-72"
          />
        )}
      </div>

      <div key={index} className="animate-text-in mt-6 flex flex-col items-center">
        <h1 className="max-w-lg text-balance text-2xl font-medium leading-snug tracking-[-0.035em] sm:text-4xl">
          {step.title}
        </h1>
        {step.tag && (
          <span className={`tag mt-4 ${step.tag === "Available" ? "tag-available" : "tag-planned"}`}>
            {step.tag}
          </span>
        )}
      </div>

      {/* Step indicator for assistive tech */}
      <p className="sr-only" aria-live="polite">
        Step {index + 1} of {steps.length}: {step.title}
      </p>

      <div className="progress-dots mt-8" aria-hidden="true">
        {steps.map((_, dotIndex) => (
          <i key={dotIndex} className={dotIndex === index ? "active" : undefined} />
        ))}
      </div>

      <button
        type="button"
        onClick={() => (index < steps.length - 1 ? setIndex(index + 1) : router.push("/onboarding/story"))}
        className={`${buttonClasses("ghost", "md")} mt-6`}
      >
        <span>{index < steps.length - 1 ? "Next" : "Continue"}</span>
        <ArrowIcon />
      </button>
    </div>
  );
}
