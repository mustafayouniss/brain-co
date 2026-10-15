import type { Metadata } from "next";
import { OnboardingShell } from "@/components/onboarding/shell";

export const metadata: Metadata = {
  title: {
    absolute: "Onboarding — Brain-co",
  },
  robots: { index: false, follow: true },
};

export default function OnboardingLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return <OnboardingShell>{children}</OnboardingShell>;
}
