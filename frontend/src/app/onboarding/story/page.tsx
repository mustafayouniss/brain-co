import type { Metadata } from "next";
import { StoryPlayer } from "@/components/onboarding/story-player";

export const metadata: Metadata = {
  title: "Product walkthrough",
  robots: { index: false, follow: false },
};

export default function StoryPage() {
  return <StoryPlayer />;
}
