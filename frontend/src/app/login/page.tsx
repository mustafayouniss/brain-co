import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { authCopy } from "@/content/marketing";
import { ArrowIcon, BrandMark } from "@/components/brand/icons";
import { PrototypeBadge } from "@/components/auth/prototype-badge";
import { LoginForm } from "@/components/auth/login-form";

export const metadata: Metadata = {
  title: { absolute: "Log in — Brain-co" },
  robots: { index: false, follow: false },
};

const copy = authCopy.login;

/**
 * Login / Sign Up stage of the journey (docs/FLOW_AUDIT.md §9.2).
 * Forced-dark, standalone auth screen — no marketing chrome, matching the
 * onboarding shell's brand treatment. Arrives from module selection with
 * `?next=/onboarding/usage` so the selected domain journey resumes after
 * authentication (the domain itself lives in sessionStorage).
 */
export default function LoginPage() {
  return (
    <main className="dark relative flex min-h-dvh flex-col screen-base text-white">
      <div className="grid-overlay" aria-hidden="true" />
      <div className="relative flex flex-1 items-center justify-center px-5 py-12">
        <div className="flex w-full max-w-md flex-col items-center text-center">
          <BrandMark className="h-12 w-12" />
          <PrototypeBadge className="mt-5" />
          <p className="eyebrow mt-5">{copy.eyebrow}</p>
          <h1 className="mt-3 text-3xl font-medium tracking-[-0.04em] sm:text-4xl">
            {copy.title}
          </h1>
          <p className="mt-3 text-sm text-[#a7b0c1]">{copy.description}</p>

          <Suspense fallback={null}>
            <LoginForm />
          </Suspense>

          <p className="mt-10 text-xs text-[#8a94a8]">
            <Link
              href="/onboarding/domains"
              className="inline-flex items-center gap-1.5 underline-offset-4 transition-colors hover:text-white hover:underline"
            >
              {copy.context}
              <ArrowIcon className="h-3 w-3" />
            </Link>
          </p>
          <p className="mt-3 max-w-sm text-xs leading-relaxed text-[#8a94a8]">
            {copy.prototypeNote}
          </p>
        </div>
      </div>
    </main>
  );
}
