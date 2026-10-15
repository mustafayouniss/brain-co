import type { Metadata } from "next";
import { HomeScreen } from "@/components/onboarding/home-screen";

export const metadata: Metadata = {
  title: "Brain-co",
  description:
    "One General Brain, taught your domain, configured to how your organization actually works.",
  alternates: { canonical: "/onboarding" },
};

export default function OnboardingHomePage() {
  return <HomeScreen />;
}
