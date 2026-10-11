"use client";

import * as React from "react";
import dynamic from "next/dynamic";
import { cn } from "@/lib/utils";
import { brainPhaseStore, sampleTimeline, TIMELINE } from "./brain-phase";
import { buildShapeBuffers, SHAPE_KEYS, type ShapeBuffers, type ShapeKey } from "./brain-shapes";

/**
 * Hero center visual host. After hydration it probes the environment:
 *
 * - prefers-reduced-motion  → static brain-of-particles SVG + static label.
 * - canvas 2D unavailable or very low-end device → four static SVGs
 *   (brain, scales, sales, HR) crossfading on the same timeline + labels.
 * - otherwise → the 2D canvas engine, mounted only after requestIdleCallback
 *   so the extra chunk and engine build never delay first paint/LCP.
 *
 * The SVG fallbacks sample the SAME shape module as the canvas (square dots,
 * same perspective projection) — one source of truth for every shape.
 */

interface IdleWindowish {
  requestIdleCallback?(cb: () => void): number;
  cancelIdleCallback?(id: number): void;
}

/* --- static SVG shapes (fallbacks) ------------------------------------ */

const SVG_N = 1200;
type SvgDot = readonly [x: number, y: number, size: number, gold: boolean, depth: number, v: 0 | 1 | 2];

let svgCache: Record<ShapeKey, SvgDot[]> | null = null;
function svgDots(shape: ShapeKey): SvgDot[] {
  if (!svgCache) {
    const bufs = buildShapeBuffers(SVG_N);
    const cache = {} as Record<ShapeKey, SvgDot[]>;
    for (const key of SHAPE_KEYS) {
      const b: ShapeBuffers = bufs[key];
      const dots: SvgDot[] = [];
      for (let i = 0; i < SVG_N; i++) {
        const z = b.Z[i];
        const f = 3.2 / (3.2 - z);
        const v = b.V[i] as 0 | 1 | 2;
        const size = v === 1 ? 0.016 : v === 2 ? 0.024 : 0.0066;
        const gold = key === "legal" && v === 0 && i % 5 < 3;
        dots.push([b.X[i] * f, -b.Y[i] * f, size, gold, (z + 0.5) / 1, v]);
      }
      cache[key] = dots;
    }
    svgCache = cache;
  }
  return svgCache[shape];
}

function ShapeSvg({ shape, on }: { shape: ShapeKey; on: boolean }) {
  const dots = React.useMemo(() => svgDots(shape), [shape]);
  return (
    <svg
      className={cn("brain-fallback-svg", on && "is-on")}
      viewBox="-1.25 -1.25 2.5 2.5"
      aria-hidden="true"
    >
      {dots.map(([x, y, size, gold, depth, v], i) => (
        <rect
          key={i}
          x={x - size / 2}
          y={y - size / 2}
          width={size}
          height={size}
          fill={gold ? "var(--gold)" : v > 0 ? "var(--brand-hover)" : "var(--brand)"}
          fillOpacity={v > 0 ? 1 : 0.45 + depth * 0.5}
        />
      ))}
    </svg>
  );
}

function BrainFallbackCrossfade() {
  const [index, setIndex] = React.useState(0);
  React.useEffect(() => {
    brainPhaseStore.set({ live: true, shape: TIMELINE[0].shape, index: 0 });
    const t0 = performance.now();
    const id = window.setInterval(() => {
      const sample = sampleTimeline((performance.now() - t0) / 1000);
      setIndex(sample.index);
      brainPhaseStore.set({ live: true, shape: sample.phase.shape, index: sample.index });
    }, 120);
    return () => window.clearInterval(id);
  }, []);
  const shape = TIMELINE[index].shape;
  return (
    <div className="brain-fallback-stack">
      {SHAPE_KEYS.map((k) => (
        <ShapeSvg key={k} shape={k} on={k === shape} />
      ))}
    </div>
  );
}

/* --- canvas path (dynamic, error-guarded) ------------------------------ */

const BrainHeroCanvas = dynamic(
  () => import("./brain-hero-canvas").then((m) => m.BrainHeroCanvas),
  { ssr: false },
);

function hasCanvas2D(): boolean {
  try {
    return document.createElement("canvas").getContext("2d") !== null;
  } catch {
    return false;
  }
}

function prefersReducedMotion(): boolean {
  return (
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}

function isLowEndDevice(): boolean {
  const nav = navigator as Navigator & { deviceMemory?: number };
  return (
    (nav.deviceMemory !== undefined && nav.deviceMemory <= 2) || navigator.hardwareConcurrency <= 2
  );
}

interface BoundaryProps {
  fallback: React.ReactNode;
  onFail: () => void;
  children: React.ReactNode;
}
interface BoundaryState {
  failed: boolean;
}

class CanvasBoundary extends React.Component<BoundaryProps, BoundaryState> {
  state: BoundaryState = { failed: false };

  static getDerivedStateFromError(): BoundaryState {
    return { failed: true };
  }

  componentDidCatch(): void {
    this.props.onFail();
  }

  render(): React.ReactNode {
    return this.state.failed ? this.props.fallback : this.props.children;
  }
}

type Mode = "static" | "crossfade" | "canvas";

export function BrainHero() {
  // null = probing. The SSR/paint render shows the static brain placeholder
  // immediately (reserved space, no pop-in); once the canvas has drawn its
  // first frame — or a fallback mounted — the placeholder crossfades out.
  const [mode, setMode] = React.useState<Mode | null>(null);
  const [ready, setReady] = React.useState(false);

  React.useEffect(() => {
    let cancelIdle: (() => void) | null = null;
    const probe = () => {
      if (prefersReducedMotion()) {
        setMode("static");
        return;
      }
      if (!hasCanvas2D() || isLowEndDevice()) {
        setMode("crossfade");
        return;
      }
      if (cancelIdle) return;
      const go = () => setMode("canvas");
      const w = window as unknown as IdleWindowish;
      if (typeof w.requestIdleCallback === "function") {
        const id = w.requestIdleCallback(go);
        cancelIdle = () => w.cancelIdleCallback?.(id);
      } else {
        const id = window.setTimeout(go, 250);
        cancelIdle = () => window.clearTimeout(id);
      }
    };
    probe();
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    mq.addEventListener("change", probe);
    return () => {
      cancelIdle?.();
      mq.removeEventListener("change", probe);
    };
  }, []);

  // Static mode freezes the shared phase store → static label, no chip/support.
  React.useEffect(() => {
    if (mode === "static") brainPhaseStore.set({ live: false, shape: "brain", index: 0 });
  }, [mode]);

  // The fallback stack re-draws the same brain SVG → release the placeholder
  // as soon as it mounts (derived from mode — no extra state/effect).

  const handleFail = React.useCallback(() => setMode("crossfade"), []);
  const handleCanvasReady = React.useCallback(() => setReady(true), []);

  return (
    <div className="brain-hero-slot">
      {/* Server-rendered placeholder: the brain-glyph SVG, visible from the
          first paint and crossfaded (~600ms) into the canvas once ready. */}
      <ShapeSvg shape="brain" on={!ready && mode !== "crossfade"} />
      {mode === "canvas" && (
        <CanvasBoundary fallback={<BrainFallbackCrossfade />} onFail={handleFail}>
          <BrainHeroCanvas ready={ready} onReady={handleCanvasReady} />
        </CanvasBoundary>
      )}
      {mode === "crossfade" && <BrainFallbackCrossfade />}
    </div>
  );
}
