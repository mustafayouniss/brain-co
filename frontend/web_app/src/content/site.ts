/**
 * Site-wide configuration: branding, URLs, socials, integrations.
 * Every environment-driven value is read here so no secret or host is
 * hardcoded in components.
 */
export const site = {
  name: "Brain-co",
  legalName: "Brain-co Inc.",
  tagline: "The intelligence layer of your organization.",
  description:
    "Transform organizational knowledge into actionable insights with this AI-driven platform designed for enterprises, enhancing decision-making and efficiency.",
  /** Primary keyword-rich description used on the landing page. */
  keywords: [
    "organizational memory",
    "enterprise AI",
    "knowledge management",
    "legal intelligence",
    "general brain",
    "AI platform",
  ],
  /** Set NEXT_PUBLIC_SITE_URL in production (e.g. https://brain-co.example). */
  url: process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000",
  locale: "en",
  /** Company details used for JSON-LD and the footer. */
  email: "hello@brain-co.app",
  supportEmail: "support@brain-co.app",
  address: {
    street: "100 Knowledge Way",
    city: "San Francisco",
    region: "CA",
    postalCode: "94107",
    country: "US",
  },
  social: {
    linkedin: "https://www.linkedin.com/company/brain-co",
    x: "https://x.com/brainco_app",
    github: "https://github.com/brain-co",
    youtube: "https://www.youtube.com/@brain-co",
  },
  /**
   * Optional integrations. When unset, tracking is disabled entirely and no
   * cookie consent banner is rendered.
   */
  gaId: process.env.NEXT_PUBLIC_GA_ID ?? "",
  /** Optional external endpoint the contact form forwards to. */
  contactEndpoint: process.env.NEXT_PUBLIC_CONTACT_ENDPOINT ?? "",
  /** VAPID key for web push (optional, PWA install works without it). */
  vapidPublicKey: process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY ?? "",
} as const;

export type SiteConfig = typeof site;
