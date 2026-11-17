"use client";

import React, { useRef, useEffect, useCallback, useState } from "react";
import dynamic from "next/dynamic";
import { useScroll } from "framer-motion";
import { DeviceTier } from "./types";
import type { BrainCanvasHandle } from "./brain-canvas";
import type { ThreeBrainEngine } from "./brain-engine";

// Dynamically import BrainCanvas with ssr: false
const BrainCanvas = dynamic(
  () => import("./brain-canvas").then((mod) => mod.BrainCanvas),
  {
    ssr: false,
    loading: () => (
      <div
        className="fixed inset-0 w-full h-full bg-[#050505] pointer-events-none"
        aria-hidden="true"
      />
    ),
  }
);

interface ScrollNarrativeContainerProps {
  children: React.ReactNode;
}

export function ScrollNarrativeContainer({ children }: ScrollNarrativeContainerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasHandleRef = useRef<BrainCanvasHandle | null>(null);
  const engineRef = useRef<ThreeBrainEngine | null>(null);
  const [tier, setTier] = useState<DeviceTier>(DeviceTier.Tier2_DesktopStandard);
  const [scrollFraction, setScrollFraction] = useState<number>(0);

  // Detect device tier based on screen dimensions and hardware capabilities
  useEffect(() => {
    if (typeof window === "undefined") return;
    const width = window.innerWidth;
    if (width < 640) {
      setTier(DeviceTier.Tier4_Mobile);
    } else if (width < 1024) {
      setTier(DeviceTier.Tier3_Tablet);
    } else if (width >= 1920 && (window.navigator?.hardwareConcurrency || 4) >= 8) {
      setTier(DeviceTier.Tier1_DesktopHigh);
    } else {
      setTier(DeviceTier.Tier2_DesktopStandard);
    }
  }, []);

  const handleEngineReady = useCallback((engine: ThreeBrainEngine) => {
    engineRef.current = engine;
    // Initial hero presentation: Authenticated Gross-Anatomical Human Brain (0.0)
    engine.setTargetScroll(0.0);
  }, []);

  // Framer Motion continuous scroll tracking across all 7 narrative stages
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  useEffect(() => {
    const unsubscribe = scrollYProgress.on("change", (latest) => {
      setScrollFraction(latest);
      if (!engineRef.current) return;

      // Map [0.0, 1.0] to [0.0, 6.0] matching reference HTML:
      // 0.0 - 1.0: Hero Brain -> 01 Legal Balance Scale
      // 1.0 - 2.0: 01 Legal Scale -> 02 HR Figures
      // 2.0 - 3.0: 02 HR Figures -> 03 Sales Growth Bars
      // 3.0 - 4.0: 03 Sales Growth -> 04 Finance Coin Ring
      // 4.0 - 5.0: 04 Finance -> 05 Operations Layers
      // 5.0 - 6.0: 05 Operations -> Final Unified Living Brain
      const morphTarget = Math.max(0.0, Math.min(6.0, latest * 6.0));
      engineRef.current.setTargetScroll(morphTarget);
    });

    return () => {
      unsubscribe();
    };
  }, [scrollYProgress]);

  return (
    <div ref={containerRef} className="cinematic-theme relative w-full bg-[#050505] text-white">
      {/* Sleek Vertical Progress Bar (Reference HTML #bar) */}
      <div
        className="fixed top-0 right-0 w-[3px] z-50 bg-gradient-to-b from-[#7E5BC4] via-[#A98CE6] to-[#9ADCEB] pointer-events-none transition-all duration-75"
        style={{ height: `${scrollFraction * 100}%` }}
        aria-hidden="true"
      />

      {/* Floating Scroll Indicator Prompt (Reference HTML .sc) */}
      <div
        className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 flex flex-col items-center gap-1 pointer-events-none transition-opacity duration-500"
        style={{ opacity: scrollFraction > 0.05 ? 0 : 0.8 }}
        aria-hidden="true"
      >
        <span className="text-[10px] font-mono uppercase tracking-[0.22em] text-zinc-400">
          Scroll to explore
        </span>
        <div className="w-5 h-9 rounded-full border border-white/30 flex items-start justify-center p-1">
          <div className="w-1 h-2 rounded-full bg-white animate-bounce mt-1" />
        </div>
      </div>

      {/* Fixed WebGL Generative Background Canvas */}
      <div
        className="fixed inset-0 w-full h-full pointer-events-none z-0 overflow-hidden"
        aria-hidden="true"
      >
        <BrainCanvas
          ref={canvasHandleRef}
          tier={tier}
          onEngineReady={handleEngineReady}
          className="w-full h-full block"
        />
      </div>

      {/* Interactive Marketing Content Layers */}
      <div className="relative z-10 w-full">
        {children}
      </div>
    </div>
  );
}

export default ScrollNarrativeContainer;
