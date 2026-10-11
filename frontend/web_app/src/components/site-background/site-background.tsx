"use client";

import * as React from "react";
import { usePathname } from "next/navigation";
import { SiteBackgroundCanvas } from "./site-background-canvas";

/**
 * Root-layout background host. Re-reads the existing selected-module state
 * (onboarding sessionStorage — the same source the workspace reads) on mount
 * and on every navigation, so the neuron→legal transition triggers when the
 * user selects Legal and moves on, on reload, or on a direct Legal route.
 * No new store and no changes to the onboarding hook. The re-read uses the
 * guarded render-adjust pattern (state adjusts during render when the path
 * changes — never setState inside an effect).
 */

const ONBOARDING_KEY = "brainco:onboarding";

/**
 * Route families for icon placement (see contentBox in legal-icons.ts):
 * prose routes use a max-w-3xl document column, everything else must clear
 * the wide containers (container-page / max-w-5xl). Both stay deterministic
 * — no random scatter behind body text on any route.
 */
const PROSE_ROUTES = new Set(["/terms", "/privacy", "/login"]);

function readSelectedDomain(): string | null {
  if (typeof window === "undefined") return null; // SSR: nothing selected yet
  try {
    const raw = window.sessionStorage.getItem(ONBOARDING_KEY);
    if (!raw) return null;
    return (JSON.parse(raw) as { domain?: string }).domain ?? null;
  } catch {
    return null;
  }
}

function prefersReducedMotion(): boolean {
  try {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch {
    return false;
  }
}

export function SiteBackground() {
  const pathname = usePathname();
  const [reduced] = React.useState(prefersReducedMotion);
  const [prevPath, setPrevPath] = React.useState<string | null>(null);
  const [legal, setLegal] = React.useState(false);

  if (prevPath !== pathname) {
    setPrevPath(pathname);
    setLegal(readSelectedDomain() === "legal");
  }

  const quiet = pathname === "/workspace";
  const zone: "wide" | "prose" = PROSE_ROUTES.has(pathname) ? "prose" : "wide";

  return <SiteBackgroundCanvas legal={legal} quiet={quiet} reduced={reduced} zone={zone} />;
}
