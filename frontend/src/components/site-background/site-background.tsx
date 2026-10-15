"use client";

import * as React from "react";
import { usePathname } from "next/navigation";
import { SiteBackgroundCanvas } from "./site-background-canvas";

/**
 * Root-layout background host. ONE decision chooses the scene:
 *
 *   mode = isWorkspaceRoute(pathname) && readSelectedDomain() === "legal"
 *
 * The legal world (scales of justice) renders only on the Legal workspace
 * routes (WORKSPACE_ROUTES below) and only while the saved domain is
 * "legal". Every other route — the marketing site, /login, every
 * /onboarding screen (domain selection, domain intro, all steps), /terms,
 * /privacy, 404, unknown paths — always shows the neural field, even when
 * the saved domain is "legal", with the existing stroke-by-stroke
 * transition (and its smooth mid-flight reversal) when the mode flips.
 * The mode is re-evaluated on pathname changes (client-side navigation and
 * Back/Forward via usePathname) and again on popstate/pageshow so history
 * navigation and bfcache restores re-read the saved state even when the
 * pathname is unchanged. The saved state is only ever read — never written
 * or cleared — and there is no new store and no change to the onboarding
 * hook. Re-reads use the guarded render-adjust pattern (state adjusts
 * during render — never setState inside an effect).
 */

const ONBOARDING_KEY = "brainco:onboarding";

/**
 * The one route config — the Legal workspace routes. Entries match the
 * exact path and its children (/workspace and /workspace/*); anything not
 * matched classifies as neural, which is every other route in the app:
 *
 *   /                              /about  /contact  /modules
 *   /login                         sign-in / sign-up entry
 *   /onboarding and every step     home, story, domain picker, domain
 *                                  intro (/onboarding/domains/legal),
 *                                  usage, account, verify (404 today),
 *                                  survey, upload, build, ready
 *   /terms  /privacy               legal prose
 *   anything unknown               404
 *
 * (API routes under /api/* and static assets render no background.)
 */
const WORKSPACE_ROUTES = ["/workspace"] as const;

function isWorkspaceRoute(pathname: string): boolean {
  return WORKSPACE_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`),
  );
}

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
  /* Bumped by popstate/pageshow so history navigation and bfcache restores
     re-read the saved onboarding state even when the pathname is unchanged. */
  const [recheck, setRecheck] = React.useState(0);
  const [prevKey, setPrevKey] = React.useState<string | null>(null);
  const [legal, setLegal] = React.useState(false);

  const key = `${recheck}:${pathname}`;
  if (prevKey !== key) {
    setPrevKey(key);
    setLegal(isWorkspaceRoute(pathname) && readSelectedDomain() === "legal");
  }

  React.useEffect(() => {
    const revalidate = (): void => setRecheck((n) => n + 1);
    window.addEventListener("popstate", revalidate);
    window.addEventListener("pageshow", revalidate);
    return () => {
      window.removeEventListener("popstate", revalidate);
      window.removeEventListener("pageshow", revalidate);
    };
  }, []);

  const quiet = isWorkspaceRoute(pathname);
  const zone: "wide" | "prose" = PROSE_ROUTES.has(pathname) ? "prose" : "wide";

  return <SiteBackgroundCanvas legal={legal} quiet={quiet} reduced={reduced} zone={zone} />;
}
