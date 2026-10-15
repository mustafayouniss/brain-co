import type { Metadata } from "next";
import { IntroPlayer } from "@/components/onboarding/intro-player";

export const metadata: Metadata = {
  title: "Brand story",
  robots: { index: false, follow: false },
};

export default function IntroPage() {
  return <IntroPlayer />;
}
