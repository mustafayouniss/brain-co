"use client";

import * as React from "react";
import { useSyncExternalStore } from "react";
import { domainDetails, homeCopy } from "@/content/app";
import { cn } from "@/lib/utils";
import { brainPhaseStore, type ShapeKey } from "@/components/brand/brain-phase";

/**
 * The "GENERAL BRAIN" pill under the hero visual. On every shape change the
 * pill fades out, swaps text + dot colour (450 ms round trip, in sync with the
 * canvas morph) and fades back in. A CONCEPT chip shows on the Sales/HR
 * phases and one supporting line fades in during the domain phases. Static
 * (plain "General Brain" pill) in reduced-motion/fallback mode.
 */

/** Dot colours are existing tokens only (no new hex). */
const DOT: Record<ShapeKey, string> = {
  brain: "var(--brand)",
  legal: "var(--gold)",
  sales: "var(--brand-hover)",
  hr: "color-mix(in srgb, var(--brand) 62%, #000)",
};

export function BrainPhaseLabel() {
  const snap = useSyncExternalStore(
    brainPhaseStore.subscribe,
    brainPhaseStore.get,
    brainPhaseStore.get,
  );
  const [shown, setShown] = React.useState<ShapeKey>(snap.shape);
  const [fading, setFading] = React.useState(false);
  const [prevShape, setPrevShape] = React.useState<ShapeKey>(snap.shape);

  // Fade-out, swap at the midpoint, fade back in (≈450 ms round trip).
  if (snap.shape !== prevShape) {
    setPrevShape(snap.shape);
    setFading(true);
  }
  React.useEffect(() => {
    if (!fading) return;
    const timer = window.setTimeout(() => {
      setShown(snap.shape);
      setFading(false);
    }, 225);
    return () => window.clearTimeout(timer);
  }, [fading, snap.shape]);

  const label = shown === "brain" ? homeCopy.brainLabel : domainDetails[shown].title;
  const concept = snap.live && shown !== "brain" && shown !== "legal";
  const support = snap.live && shown !== "brain";

  return (
    <>
      <span
        className={cn("brain-label brain-label--live", fading && "brain-label--fading")}
        style={{ "--label-dot": DOT[shown] } as React.CSSProperties}
      >
        <span className="brain-label-text">{label}</span>
        {concept && <span className="brain-label-chip">{homeCopy.brainConcept}</span>}
      </span>
      <span className={cn("brain-support", support && "brain-support--visible")}>
        {homeCopy.brainSupport}
      </span>
    </>
  );
}
