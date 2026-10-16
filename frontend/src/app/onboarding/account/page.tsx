"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Info } from "lucide-react";
import { FlowBody, FlowShell, FlowTitle } from "@/components/onboarding/flow";
import { PrototypeBadge } from "@/components/auth/prototype-badge";
import { Button } from "@/components/ui/button";
import { useOnboarding } from "@/hooks/use-onboarding";

/**
 * Account creation page - DISABLED.
 * 
 * Public self-registration is not supported per project specifications.
 * Employee accounts must be created by an administrator.
 * 
 * Reference:
 * - Ring 0 Foundation (T9): "no public sign-up; the admin creates employee accounts"
 * - Backend API Auth Documentation: "Do not use public sign-up endpoints. Only admins can create employee accounts."
 */
export default function AccountScreen() {
  const router = useRouter();
  const { state, hydrated } = useOnboarding();

  // Deep-link/refresh guard: domain → usage → login
  React.useEffect(() => {
    if (!hydrated) return;
    if (!state.domain) router.replace("/onboarding/domains");
  }, [hydrated, state.domain, router]);

  if (!hydrated || !state.domain) return null;

  return (
    <FlowShell as="section">
      <PrototypeBadge className="mt-8" />
      <FlowTitle className="mt-5">
        Account Creation
      </FlowTitle>
      <FlowBody>
        Employee accounts must be created by your organization administrator.
      </FlowBody>

      <div className="mt-8 rounded-2xl border border-[#202a3e] bg-[#0b1425] p-6">
        <div className="flex items-start gap-3">
          <Info className="mt-0.5 size-5 shrink-0 text-[#946eff]" aria-hidden="true" />
          <div className="flex-1">
            <h3 className="mb-2 text-base font-semibold text-white">
              Administrator Account Provisioning
            </h3>
            <p className="mb-4 text-sm leading-relaxed text-[#a7b0c1]">
              Self-registration is not available. Please contact your organization administrator to create an employee account. Once your account is created, you can log in with your credentials.
            </p>
            <div className="space-y-2">
              <p className="text-xs text-[#6a748a]">
                <span className="font-semibold">To log in:</span> Use the email and password provided by your administrator.
              </p>
              <p className="text-xs text-[#6a748a]">
                <span className="font-semibold">To request an account:</span> Contact your organization's IT administrator or system owner.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-8 flex flex-col gap-3">
        <Link href="/login" className="w-full">
          <Button size="lg" className="w-full">
            Go to Login
          </Button>
        </Link>
        <Button variant="ghost" size="sm" onClick={() => router.back()} className="w-full">
          Back
        </Button>
      </div>
    </FlowShell>
  );
}
