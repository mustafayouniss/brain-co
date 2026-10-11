import type { Metadata } from "next";
import { termsCopy } from "@/content/legal";
import { LegalDocument } from "@/components/marketing/legal-document";

export const metadata: Metadata = {
  title: termsCopy.meta.title,
  description: termsCopy.meta.description,
  alternates: { canonical: "/terms" },
  robots: { index: true, follow: true },
};

export default function TermsPage() {
  return (
    <LegalDocument
      title={termsCopy.title}
      updated={termsCopy.updated}
      intro={termsCopy.intro}
      sections={termsCopy.sections}
      description={termsCopy.meta.description}
    />
  );
}
