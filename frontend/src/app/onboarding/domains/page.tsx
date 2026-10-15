import type { Metadata } from "next";
import { DomainPicker } from "@/components/onboarding/domain-picker";

export const metadata: Metadata = {
  title: "Choose your domain",
  robots: { index: false, follow: true },
};

export default function DomainsPage() {
  return <DomainPicker />;
}
