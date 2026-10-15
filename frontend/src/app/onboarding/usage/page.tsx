"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { usageCopy, type AccountMode } from "@/content/app";
import { FlowBody, FlowContinue, FlowShell, FlowTitle } from "@/components/onboarding/flow";
import { PrototypeBadge } from "@/components/auth/prototype-badge";
import { useOnboarding } from "@/hooks/use-onboarding";
import { cn } from "@/lib/utils";

const options: Array<{ mode: AccountMode; label: string; description: string }> = [
  { mode: "personal", label: usageCopy.personal, description: usageCopy.personalDesc },
  { mode: "company", label: usageCopy.company, description: usageCopy.companyDesc },
];

/**
 * Account-type choice (source view `usage`). Personal vs Company is a
 * proposed product path per the reference doc — whether the real account
 * model supports both is an open decision (docs/FLOW_AUDIT.md, D2). The
 * choice is persisted in the existing sessionStorage onboarding state.
 */
export default function UsageScreen() {
  const router = useRouter();
  const { state, update, hydrated } = useOnboarding();
  const [picked, setPicked] = React.useState<AccountMode | null>(null);

  // Deep-link/refresh guard: this stage follows module selection.
  React.useEffect(() => {
    if (hydrated && !state.domain) router.replace("/onboarding/domains");
  }, [hydrated, state.domain, router]);

  // Pre-select a mode already chosen (refresh, back/forward) — derived from
  // persisted state instead of an effect.
  const selected = picked ?? state.accountMode;

  if (!hydrated || !state.domain) return null;

  function choose() {
    if (!selected) return;
    update({ accountMode: selected });
    router.push("/onboarding/account");
  }

  return (
    <FlowShell as="section">
      <PrototypeBadge className="mt-8" />
      <FlowTitle id="usage-title" className="mt-5">
        {usageCopy.title}
      </FlowTitle>
      <FlowBody>Choose the path that fits you best.</FlowBody>

      <div
        role="radiogroup"
        aria-labelledby="usage-title"
        className="mt-8 grid w-full max-w-md gap-3 sm:grid-cols-2"
      >
        {options.map((option) => (
          <button
            key={option.mode}
            type="button"
            role="radio"
            aria-checked={selected === option.mode}
            onClick={() => setPicked(option.mode)}
            className={cn(
              "rounded-2xl border p-5 text-left transition-colors",
              "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
              selected === option.mode
                ? "border-[#946eff] bg-[#946eff]/10"
                : "border-[#202a3e] bg-[#0b1425] hover:border-[#34405a]",
            )}
          >
            <span className="block text-base font-semibold">{option.label}</span>
            <span className="mt-1 block text-sm text-[#a7b0c1]">{option.description}</span>
          </button>
        ))}
      </div>

      <FlowContinue onClick={choose} disabled={!selected}>
        Continue
      </FlowContinue>
    </FlowShell>
  );
}
