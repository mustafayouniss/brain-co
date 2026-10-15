"use client";

import * as React from "react";
import type { AccountMode, DomainKey } from "@/content/app";
import type { SurveyInput } from "@/lib/validation";

const STORAGE_KEY = "brainco:onboarding";

export interface OnboardingState {
  domain: DomainKey | null;
  accountMode: AccountMode | null;
  account: { fullName: string; email: string; companyName?: string } | null;
  survey: SurveyInput | null;
  uploaded: boolean;
  partial: boolean;
  /** Real counts from the upload stage (additive; FLOW_AUDIT stage 8/10). */
  upload: { total: number; failed: number } | null;
}

const defaultState: OnboardingState = {
  domain: null,
  accountMode: null,
  account: null,
  survey: null,
  uploaded: false,
  partial: false,
  upload: null,
};

/**
 * Onboarding state shared across routes and persisted to sessionStorage —
 * the source app kept these values in one root `useState`; on the web each
 * step is a real URL, so progress survives reloads and back/forward.
 */
export function useOnboarding() {
  const [state, setState] = React.useState<OnboardingState>(defaultState);
  const [hydrated, setHydrated] = React.useState(false);

  React.useEffect(() => {
    try {
      const raw = window.sessionStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as Partial<OnboardingState>;
        // Hydration read from an external system (sessionStorage) — the one
        // legal setState-in-effect per React docs; the Compiler lint rule
        // cannot see through the storage read.
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setState({ ...defaultState, ...parsed });
      }
    } catch {
      /* corrupted state → start fresh */
    }
    setHydrated(true);
  }, []);

  const update = React.useCallback((patch: Partial<OnboardingState>) => {
    setState((prev) => {
      const next = { ...prev, ...patch };
      try {
        window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      } catch {
        /* storage full or blocked — keep in-memory state */
      }
      return next;
    });
  }, []);

  return { state, update, hydrated };
}
