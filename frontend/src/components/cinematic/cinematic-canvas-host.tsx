"use client";

/**
 * Brain-Co Cinematic Redesign — Dynamic Import Boundary
 * Client Component boundary that dynamically loads BrainCanvas with ssr: false,
 * guaranteeing Three.js is excluded from the initial server bundle and only executed in browser.
 * Reference: docs/architecture/cinematic_frontend_redesign_plan.md (V3.3)
 */

import React from "react";
import dynamic from "next/dynamic";
import { DeviceTier } from "./types";
import type { BrainCanvasProps } from "./brain-canvas";

const BrainCanvas = dynamic<BrainCanvasProps>(
  () => import("./brain-canvas").then((mod) => mod.BrainCanvas),
  {
    ssr: false,
    loading: () => (
      <div
        className="w-full h-full bg-black flex items-center justify-center pointer-events-none"
        aria-hidden="true"
      />
    ),
  }
);

export interface CinematicCanvasHostProps {
  tier?: DeviceTier;
  scrollProgress?: number;
  className?: string;
}

export function CinematicCanvasHost({
  tier = DeviceTier.Tier2_DesktopStandard,
  scrollProgress,
  className = "w-full h-full",
}: CinematicCanvasHostProps) {
  return (
    <div className={`cinematic-canvas-container ${className}`}>
      <BrainCanvas tier={tier} scrollProgress={scrollProgress} />
    </div>
  );
}

export default CinematicCanvasHost;
