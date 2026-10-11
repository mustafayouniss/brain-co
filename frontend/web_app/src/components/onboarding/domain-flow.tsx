"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useReducedMotion } from "framer-motion";
import { domainDetails, destinationCopy, transitionCopy, type DomainKey } from "@/content/app";
import { ParticleMorph, StaticShape } from "@/components/brand/particle-morph";
import { ArrowIcon } from "@/components/brand/icons";
import { buttonClasses } from "@/components/ui/button";
import { FlowShell, FlowTitle, FlowBody, FlowActions, FlowBackLink } from "@/components/onboarding/flow";
import { useOnboarding } from "@/hooks/use-onboarding";

/**
 * Source views `transition` + `destination`: a 1.3s particle morph from the
 * brain into the chosen domain, then either the Legal welcome or the
 * "coming soon" holding state for planned domains.
 */
export function DomainFlow({ domain }: { domain: DomainKey }) {
  const router = useRouter();
  const reduced = useReducedMotion();
  const { update } = useOnboarding();
  const [phase, setPhase] = React.useState<"transition" | "destination">("transition");
  const detail = domainDetails[domain];

  React.useEffect(() => {
    const timer = window.setTimeout(() => setPhase("destination"), 1300);
    return () => window.clearTimeout(timer);
  }, []);

  if (phase === "transition") {
    return (
      <div className="relative flex min-h-[calc(100dvh-3.5rem)] flex-col items-center justify-center bg-black px-5 text-center">
        <div className="grid-overlay" aria-hidden="true" />
        <div className="relative flex h-[300px] w-full max-w-[360px] items-center justify-center sm:h-[380px]">
          {reduced ? (
            <StaticShape shape={domain} className="h-64 w-64" />
          ) : (
            <ParticleMorph from="brain" target={domain} duration={1300} className="h-64 w-64" />
          )}
        </div>
        <div className="animate-text-in mt-6 flex flex-col items-center gap-4">
          <h1 className="text-3xl font-medium tracking-[-0.04em] sm:text-4xl">
            {detail.title} {transitionCopy.titleSuffix}
          </h1>
          <span className={`tag ${detail.status === "Available" ? "tag-available" : "tag-planned"}`}>
            {detail.status}
          </span>
        </div>
        <p className="sr-only" aria-live="polite">
          Loading {detail.title} domain
        </p>
      </div>
    );
  }

  const available = domain === "legal";

  return (
    <div className="relative min-h-[calc(100dvh-3.5rem)] bg-black">
      <div className="grid-overlay" aria-hidden="true" />
      <div
        className="pointer-events-none absolute left-1/2 top-1/2 h-[560px] w-[560px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(circle,rgba(128,82,255,0.14),transparent_65%)]"
        aria-hidden="true"
      />
      <FlowShell as="section" className="relative min-h-[calc(100dvh-3.5rem)] justify-center">
        <StaticShape shape={domain} className="h-44 w-44 sm:h-56 sm:w-56" />

        <FlowTitle className="mt-8">
          {available
            ? destinationCopy.legalTitle
            : destinationCopy.plannedTitle(domain)}
        </FlowTitle>

        <FlowBody>
          {available
            ? "Your domain is ready. Create your account to start teaching the Brain how your organization works."
            : destinationCopy.plannedBody}
        </FlowBody>

        <FlowActions>
          {available ? (
            <button
              type="button"
              onClick={() => {
                update({ domain });
                // Integration fix: this previously pointed at "/onboarding/usage"
                // (404). Per the target journey the stage after module selection is
                // Login / Sign Up; the selected domain is preserved in
                // sessionStorage and the journey resumes at /onboarding/usage after
                // authentication.
                router.push("/login?next=/onboarding/usage");
              }}
              className={buttonClasses("primary", "lg", "w-full sm:w-auto")}
            >
              <span>{destinationCopy.legalCta}</span>
              <ArrowIcon />
            </button>
          ) : (
            <button
              type="button"
              onClick={() => router.push("/onboarding/domains")}
              className={buttonClasses("primary", "lg", "w-full sm:w-auto")}
            >
              <ArrowIcon className="rotate-180" />
              <span>{destinationCopy.plannedCta}</span>
            </button>
          )}
        </FlowActions>

        {!available && (
          <FlowBackLink href="/onboarding/domains">All domains</FlowBackLink>
        )}
      </FlowShell>
    </div>
  );
}
