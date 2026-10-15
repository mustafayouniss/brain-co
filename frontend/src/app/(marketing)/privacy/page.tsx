import type { Metadata } from "next";
import { privacyCopy } from "@/content/legal";
import { LegalDocument } from "@/components/marketing/legal-document";

export const metadata: Metadata = {
  title: privacyCopy.meta.title,
  description: privacyCopy.meta.description,
  alternates: { canonical: "/privacy" },
  robots: { index: true, follow: true },
};

export default function PrivacyPage() {
  return (
    <LegalDocument
      title={privacyCopy.title}
      updated={privacyCopy.updated}
      intro={privacyCopy.intro}
      sections={privacyCopy.sections}
      description={privacyCopy.meta.description}
    />
  );
}
