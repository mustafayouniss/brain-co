"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { readyCopy } from "@/content/app";
import { FlowBody, FlowContinue, FlowShell, FlowTitle } from "@/components/onboarding/flow";
import { PrototypeBadge } from "@/components/auth/prototype-badge";
import { Button } from "@/components/ui/button";
import { useOnboarding } from "@/hooks/use-onboarding";

/**
 * Organization ready (source views `ready*` / `readyPartial`). Honest states
 * (reference doc, Screen 12 — never show false completion):
 * - any upload failed → partial state with REAL counts + retry;
 * - otherwise the full state, with the prototype/readiness caveat spelled out
 *   because no backend status API exists (docs/FLOW_AUDIT.md, D6-D8).
 */
export default function ReadyScreen() {
  const router = useRouter();
  const { state, hydrated } = useOnboarding();
  const [entering, setEntering] = React.useState(false);

  // Deep-link/refresh guards: upload stage must have been completed.
  React.useEffect(() => {
    if (!hydrated) return;
    if (!state.domain) router.replace("/onboarding/domains");
    else if (!state.accountMode) router.replace("/onboarding/usage");
    else if (!state.account) router.replace("/onboarding/account");
    else if (!state.survey) router.replace("/onboarding/survey");
    else if (!state.uploaded) router.replace("/onboarding/upload");
  }, [hydrated, state.domain, state.accountMode, state.account, state.survey, state.uploaded, router]);

  async function enterWorkspace() {
    if (entering) return; // double-submit guard
    setEntering(true);
    try {
      const res = await fetch("/api/auth/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: state.account?.email,
          name: state.account?.fullName,
        }),
      });
      if (!res.ok) {
        toast.error(readyCopy.sessionError);
        router.replace("/login?next=/workspace");
        return;
      }
      router.push("/workspace");
    } catch {
      toast.error(readyCopy.sessionError);
      setEntering(false);
    }
  }

  if (
    !hydrated ||
    !state.domain ||
    !state.accountMode ||
    !state.account ||
    !state.survey ||
    !state.uploaded
  ) {
    return null;
  }

  const upload = state.upload;
  const partial = (upload?.failed ?? 0) > 0;

  return (
    <FlowShell as="section">
      <PrototypeBadge className="mt-8" />
      <FlowTitle id="ready-title" className="mt-5">
        {partial ? readyCopy.partialTitle : readyCopy.fullTitle}
      </FlowTitle>
      <FlowBody>
        {partial && upload
          ? readyCopy.partialBodyReal(upload.failed, upload.total)
          : readyCopy.prototypeBody}
      </FlowBody>

      <div className="mt-8 flex w-full max-w-sm flex-col gap-2.5">
        <FlowContinue onClick={enterWorkspace} disabled={entering}>
          {entering ? readyCopy.entering : partial ? readyCopy.partialCta : readyCopy.fullCta}
        </FlowContinue>
        {partial && (
          <Button
            variant="secondary"
            size="lg"
            onClick={() => router.push("/onboarding/upload")}
            className="w-full"
          >
            {readyCopy.retry}
          </Button>
        )}
      </div>
    </FlowShell>
  );
}
