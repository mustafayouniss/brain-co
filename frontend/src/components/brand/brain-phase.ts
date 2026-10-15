import type { ShapeKey } from "./brain-shapes";

/**
 * Phase schedule + tiny external store shared by the hero canvas (which
 * drives the clock) and the animated label (which mirrors it). One source of
 * truth so label text swaps stay in sync with the particle morphs without
 * per-frame React renders. The morph itself is continuous (spring catch-up
 * after each change), exactly like the reference engine.
 */

export type { ShapeKey };

export interface TimelinePhase {
  shape: ShapeKey;
  /** Seconds the target shape is held before advancing. */
  hold: number;
}

/** 27 s loop: BRAIN 4s → LEGAL 5s → BRAIN 4s → SALES 5s → BRAIN 4s → HR 5s. */
export const TIMELINE: readonly TimelinePhase[] = [
  { shape: "brain", hold: 4 },
  { shape: "legal", hold: 5 },
  { shape: "brain", hold: 4 },
  { shape: "sales", hold: 5 },
  { shape: "brain", hold: 4 },
  { shape: "hr", hold: 5 },
];

export const TIMELINE_TOTAL = TIMELINE.reduce((a, p) => a + p.hold, 0);

const CUMULATIVE: number[] = [];
let acc = 0;
for (const phase of TIMELINE) {
  acc += phase.hold;
  CUMULATIVE.push(acc);
}

/** Maps absolute elapsed seconds (looping) onto the timeline — used by the SVG fallback. */
export function sampleTimeline(elapsedSeconds: number): { index: number; phase: TimelinePhase } {
  const t = ((elapsedSeconds % TIMELINE_TOTAL) + TIMELINE_TOTAL) % TIMELINE_TOTAL;
  for (let i = 0; i < CUMULATIVE.length; i++) {
    if (t < CUMULATIVE[i]) return { index: i, phase: TIMELINE[i] };
  }
  return { index: TIMELINE.length - 1, phase: TIMELINE[TIMELINE.length - 1] };
}

/* ------------------------------------------------------------------ */
/* External store (React 19 useSyncExternalStore compatible)           */
/* ------------------------------------------------------------------ */

export interface BrainPhaseSnapshot {
  /** false → static fallback mode: no cycling, no chip, no support line. */
  live: boolean;
  /** Shape shown by the label right now. */
  shape: ShapeKey;
  /** Monotonic phase index — changes force the label fade/swap. */
  index: number;
}

let snapshot: BrainPhaseSnapshot = { live: false, shape: "brain", index: 0 };
const listeners = new Set<() => void>();

function getSnapshot(): BrainPhaseSnapshot {
  return snapshot;
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function setSnapshot(next: BrainPhaseSnapshot): void {
  if (next.live === snapshot.live && next.shape === snapshot.shape && next.index === snapshot.index) {
    return;
  }
  snapshot = next;
  for (const listener of listeners) listener();
}

export const brainPhaseStore = { get: getSnapshot, subscribe, set: setSnapshot };
