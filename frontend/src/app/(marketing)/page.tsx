import type { Metadata } from "next";
import { landingCopy } from "@/content/marketing";
import { site } from "@/content/site";
import { Hero } from "@/components/marketing/sections/hero";
import { Stats } from "@/components/marketing/sections/stats";
import { Features } from "@/components/marketing/sections/features";
import { HowItWorks } from "@/components/marketing/sections/how-it-works";
import { Showcase } from "@/components/marketing/sections/showcase";
import { Testimonials } from "@/components/marketing/sections/testimonials";
import { Faq } from "@/components/marketing/sections/faq";
import { CallToAction } from "@/components/marketing/sections/cta";

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
      <Hero />
      <Stats />
      <Features />
      <HowItWorks />
      <Showcase />
      <Testimonials />
      <Faq />
      <CallToAction />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(appJsonLd) }} />
    </>
  );
}
