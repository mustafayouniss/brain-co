"use client";

import * as React from "react";
import { motion } from "framer-motion";

const REDUCED_MOTION_QUERY = "(prefers-reduced-motion: reduce)";

function subscribeReduced(onChange: () => void): () => void {
  const query = window.matchMedia(REDUCED_MOTION_QUERY);
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
}

/**
 * Read the user's reduced-motion preference reliably: framer's own
 * `useReducedMotion` snapshots `prefersReducedMotion.current` once at the
 * first (hydration) render — when it is still `false` — and never updates,
 * which left every Reveal wrapper stuck at its invisible `initial` state for
 * reduced-motion users. `useSyncExternalStore` re-reads the media query after
 * mount and keeps it live, so the reduced path (a plain, always-visible div)
 * is taken.
 */
function usePrefersReducedMotion(): boolean {
  return React.useSyncExternalStore(
    subscribeReduced,
    () => window.matchMedia(REDUCED_MOTION_QUERY).matches,
    () => false, // server: render the motion path (SSR markup matches hydration)
  );
}

interface RevealProps {
  children: React.ReactNode;
  delay?: number;
  className?: string;
  /** Elevation of the animation (px). */
  y?: number;
}

/**
 * Scroll-reveal wrapper: fades + rises into place once, respecting the user's
 * reduced-motion preference (content is static and fully visible).
 */
export function Reveal({ children, delay = 0, className, y = 18 }: RevealProps) {
  const reduced = usePrefersReducedMotion();

  if (reduced) return <div className={className}>{children}</div>;

  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.55, delay, ease: [0.2, 0.8, 0.2, 1] }}
    >
      {children}
    </motion.div>
  );
}
