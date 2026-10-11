"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowIcon, BrandMark } from "@/components/brand/icons";
import { ThemeToggle } from "@/components/theme-toggle";
import { cn } from "@/lib/utils";

/** Ordered steps of the onboarding journey (mirrors the source view machine). */
export const onboardingSteps = [
  { href: "/onboarding", label: "Home", key: "/onboarding" },
  { href: "/onboarding/intro", label: "Story", key: "/onboarding/intro" },
  { href: "/onboarding/story", label: "Walkthrough", key: "/onboarding/story" },
  { href: "/onboarding/domains", label: "Domain", key: "/onboarding/domains" },
  { href: "/onboarding/usage", label: "Account type", key: "/onboarding/usage" },
  { href: "/onboarding/account", label: "Sign up", key: "/onboarding/account" },
  { href: "/onboarding/verify", label: "Verify", key: "/onboarding/verify" },
  { href: "/onboarding/survey", label: "Organization", key: "/onboarding/survey" },
  { href: "/onboarding/upload", label: "Documents", key: "/onboarding/upload" },
  { href: "/onboarding/build", label: "Building", key: "/onboarding/build" },
  { href: "/onboarding/ready", label: "Ready", key: "/onboarding/ready" },
] as const;

function currentIndex(pathname: string): number {
  const exact = onboardingSteps.findIndex((step) => step.key === pathname);
  if (exact >= 0) return exact;
  if (pathname.startsWith("/onboarding/domains/")) return 3;
  return -1;
}

/**
 * App shell for the onboarding flow: forced dark brand chrome, compact
 * breadcrumbs, step progress, exit link and theme toggle.
 */
export function OnboardingShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const index = currentIndex(pathname);
  const step = index >= 0 ? onboardingSteps[index] : null;

  const crumbs = React.useMemo(() => {
    if (index <= 0) return [];
    return onboardingSteps.slice(1, index + 1).filter((s) => s.key === pathname || (s.key === "/onboarding/domains" && pathname.startsWith("/onboarding/domains")));
  }, [index, pathname]);

  return (
    <div className="dark min-h-dvh screen-base text-white">
      <a href="#main" className="skip-link">
        Skip to content
      </a>

      <header className="sticky top-0 z-30 border-b border-[#202a3e] bg-[#050b1a]/85 backdrop-blur-xl">
        <div className="mx-auto flex h-14 w-full max-w-5xl items-center justify-between gap-4 px-4 sm:px-6">
          <Link
            href="/onboarding"
            aria-label="Brain-co onboarding home"
            className="flex items-center gap-2.5"
          >
            <BrandMark />
            <strong className="hidden text-sm font-semibold tracking-[-0.03em] sm:block">
              Brain-co
            </strong>
          </Link>

          {/* Compact breadcrumbs (desktop) */}
          {crumbs.length > 0 && (
            <nav aria-label="Onboarding" className="hidden min-w-0 items-center gap-1.5 text-xs text-[#8a94a8] md:flex">
              <Link href="/onboarding" className="transition-colors hover:text-white">
                Onboarding
              </Link>
              {crumbs.map((crumb, crumbIndex) => (
                <React.Fragment key={crumb.key}>
                  <span aria-hidden="true">/</span>
                  <span
                    aria-current={crumbIndex === crumbs.length - 1 ? "step" : undefined}
                    className={cn(
                      "truncate",
                      crumbIndex === crumbs.length - 1 && "text-white",
                    )}
                  >
                    {crumb.label}
                  </span>
                </React.Fragment>
              ))}
            </nav>
          )}

          <div className="flex items-center gap-2">
            {index > 0 && (
              <Link
                href="/"
                className="flex h-9 items-center gap-1.5 rounded-full border border-[#34405a] px-3 text-xs font-semibold text-[#a7b0c1] transition-colors hover:border-[#946eff] hover:text-white"
              >
                Exit
                <ArrowIcon className="h-3.5 w-3.5 rotate-180" />
              </Link>
            )}
            <ThemeToggle />
          </div>
        </div>

        {/* Step progress rail */}
        {step && index > 0 && (
          <div
            className="mx-auto h-0.5 w-full max-w-5xl bg-[#202a3e]"
            role="progressbar"
            aria-label="Onboarding progress"
            aria-valuenow={index + 1}
            aria-valuemin={1}
            aria-valuemax={onboardingSteps.length}
          >
            <div
              className="h-full bg-gradient-to-r from-[#8052ff] to-[#f3ca78] transition-[width] duration-500"
              style={{ width: `${((index + 1) / onboardingSteps.length) * 100}%` }}
            />
          </div>
        )}
      </header>

      <main id="main">{children}</main>
    </div>
  );
}
