import type { Metadata } from "next";
import { landingCopy } from "@/content/marketing";
import { site } from "@/content/site";
import { ScrollNarrativeContainer } from "@/components/cinematic/scroll-narrative-container";
import { CinematicHero } from "@/components/marketing/sections/cinematic-hero";
import {
  DepartmentSectionCard,
  FinalUnifiedSection,
} from "@/components/cinematic/department-narrative-sections";
import { PlatformPreview } from "@/components/marketing/sections/platform-preview";
import { SecuritySection } from "@/components/marketing/sections/security-section";
import { CinematicCta } from "@/components/marketing/sections/cinematic-cta";

export const metadata: Metadata = {
  title: landingCopy.meta.title,
  description: landingCopy.meta.description,
  alternates: { canonical: "/" },
  openGraph: {
    title: landingCopy.meta.title,
    description: landingCopy.meta.description,
    url: site.url,
  },
};

const faqJsonLd = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: landingCopy.faq.items.map((item) => ({
    "@type": "Question",
    name: item.q,
    acceptedAnswer: { "@type": "Answer", text: item.a },
  })),
};

const appJsonLd = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: site.name,
  applicationCategory: "BusinessApplication",
  operatingSystem: "Web",
  description: landingCopy.meta.description,
  url: site.url,
  offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
  featureList: landingCopy.features.items.map((item) => item.title),
};

export default function HomePage() {
  return (
    <>
      <ScrollNarrativeContainer>
        {/* Stage 0: Hero — Authenticated Gross-Anatomical Brain */}
        <CinematicHero />

        {/* Stage 1: Legal / Compliance — Brass Balance Scale on Marble Base */}
        <DepartmentSectionCard
          id="legal"
          tag="01 — LEGAL & COMPLIANCE"
          title="Judgment, remembered."
          description="Precedents, regulatory filings, and clause interpretations are synthesized into an immutable reasoning lattice. Every contract risk is flagged before signing."
          tags={["Contract Analysis", "Statutory Corpus", "Precedent Memory"]}
        />

        {/* Stage 2: Human Resources — Connected Human Figures & Organizational Network */}
        <DepartmentSectionCard
          id="hr"
          tag="02 — HUMAN RESOURCES"
          title="People, connected."
          description="Skills, organizational roles, and tacit workflows form an adaptive network. Knowledge remains permanently preserved across employee transitions."
          tags={["Organizational Graph", "Tacit Knowledge", "Succession Mapping"]}
        />

        {/* Stage 3: Sales — Volumetric 3D Growth Bars & Ascending Golden Arrow */}
        <DepartmentSectionCard
          id="sales"
          tag="03 — SALES & REVENUE"
          title="Growth, explained."
          description="Customer signals, winning deal strategies, and objections become shared company intelligence. Pipeline forecasts are backed by deterministic proof."
          tags={["Win/Loss Forensics", "Deal Intelligence", "Revenue Vectors"]}
        />

        {/* Stage 4: Finance — Tilted Orbital Coin Ring & Central Reserve Stack */}
        <DepartmentSectionCard
          id="finance"
          tag="04 — FINANCE & AUDIT"
          title="Every flow, traceable."
          description="Audits, transaction paths, and ledger reconciliation operate across a single continuous ledger. Discrepancies are identified at origin."
          tags={["Continuous Audit", "Ledger Synthesis", "Variance Engine"]}
        />

        {/* Stage 5: Operations — 3 Connected Translucent Layer Disks & Conduits */}
        <DepartmentSectionCard
          id="operations"
          tag="05 — OPERATIONS"
          title="Systems that learn."
          description="Cross-departmental processes, operational playbooks, and system telemetry converge into autonomous feedback loops that refine execution."
          tags={["Autonomous Runbooks", "SLA Optimization", "System Conduits"]}
        />

        {/* Supporting Platform Architecture Deep-Dives */}
        <PlatformPreview />
        <SecuritySection />

        {/* Stage 6: Final Unified System — Return to Coalesced Brain */}
        <FinalUnifiedSection />
        <CinematicCta />
      </ScrollNarrativeContainer>

      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(appJsonLd) }}
      />
    </>
  );
}
