"use client";

/**
 * Brain-Co Cinematic Redesign — Lazy-Loaded WebGL Canvas Component
 * Synchronous idempotent lifecycle supporting React 19 Strict Mode.
 * Reference: docs/architecture/cinematic_frontend_redesign_plan.md (V3.3)
 */

import React, { useEffect, useRef, useImperativeHandle, forwardRef } from "react";
import { ThreeBrainEngine } from "./brain-engine";
import { DeviceTier } from "./types";

export interface BrainCanvasProps {
  tier?: DeviceTier;
  scrollProgress?: number;
  asymmetric?: boolean;
  onContextLost?: () => void;
  onContextRestored?: () => void;
  onEngineReady?: (engine: ThreeBrainEngine) => void;
  className?: string;
}

export interface BrainCanvasHandle {
  setTargetScroll: (val: number) => void;
  setMorphProgress: (val: number) => void;
  getEngine: () => ThreeBrainEngine | null;
}

export const BrainCanvas = forwardRef<BrainCanvasHandle, BrainCanvasProps>(
  function BrainCanvas(
    {
      tier = DeviceTier.Tier2_DesktopStandard,
      scrollProgress,
      asymmetric,
      onContextLost,
      onContextRestored,
      onEngineReady,
      className = "w-full h-full block",
    },
    ref
  ) {
    const canvasRef = useRef<HTMLCanvasElement | null>(null);
    const engineRef = useRef<ThreeBrainEngine | null>(null);

    // Synchronous, paired setup / cleanup pattern (React 19 Strict Mode safe)
    useEffect(() => {
      const canvas = canvasRef.current;
      if (!canvas) return;

      const engine = new ThreeBrainEngine(canvas, {
        tier,
        asymmetric,
        onContextLost,
        onContextRestored,
      });

      engineRef.current = engine;
      engine.start();

      if (onEngineReady) {
        onEngineReady(engine);
      }

      return () => {
        engine.dispose();
        engineRef.current = null;
      };
    }, [tier, onContextLost, onContextRestored, onEngineReady]);

    // Handle incoming prop updates without React re-render of canvas internals
    useEffect(() => {
      if (scrollProgress !== undefined && engineRef.current) {
        engineRef.current.setTargetScroll(scrollProgress);
      }
    }, [scrollProgress]);

    // Expose imperative handle for direct scroll bridge linkage and testing
    useImperativeHandle(
      ref,
      () => ({
        setTargetScroll: (val: number) => {
          engineRef.current?.setTargetScroll(val);
        },
        setMorphProgress: (val: number) => {
          engineRef.current?.setMorphProgress(val);
        },
        getEngine: () => engineRef.current,
      }),
      []
    );

    return <canvas ref={canvasRef} className={className} />;
  }
);

BrainCanvas.displayName = "BrainCanvas";
export default BrainCanvas;
