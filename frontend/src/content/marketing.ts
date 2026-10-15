/**
 * Website-specific copy (Phase 3 extras). Written in the source app's voice:
 * confident, declarative, human-in-the-loop. Source-app strings live in app.ts.
 */

export const navCopy = {
  primary: [
    { href: "/", label: "Home" },
    { href: "/modules", label: "Modules" },
    { href: "/about", label: "About" },
    { href: "/contact", label: "Contact" },
  ],
  login: "Log in",
  start: "Get started",
  menuAria: "Open menu",
  closeAria: "Close menu",
  themeToggle: "Toggle theme",
} as const;

export const footerCopy = {
  blurb:
    "One General Brain, taught your domain, configured to how your organization actually works.",
  product: {
    title: "Product",
    links: [
      { href: "/modules", label: "Domain modules" },
      { href: "/onboarding", label: "See how it works" },
      { href: "/onboarding/domains", label: "Choose your domain" },
      { href: "/login", label: "Sign in" },
    ],
  },
  company: {
    title: "Company",
    links: [
      { href: "/about", label: "About" },
      { href: "/contact", label: "Contact" },
      { href: "/#faq", label: "FAQ" },
    ],
  },
  legal: {
    title: "Legal",
    links: [
      { href: "/privacy", label: "Privacy Policy" },
      { href: "/terms", label: "Terms of Service" },
    ],
  },
  rights: (year: number) => `© ${year} Brain-co Inc. All rights reserved.`,
  socialAria: (name: string) => `Brain-co on ${name}`,
  newsletter: {
    label: "Product updates",
    placeholder: "you@company.com",
    submit: "Subscribe",
    success: "You're on the list. Talk soon.",
    error: "Please enter a valid email address.",
  },
} as const;

export const landingCopy = {
  meta: {
    title: "Brain-co — The intelligence layer of your organization",
    description:
      "One General Brain, taught your domain and configured to how your organization actually works. Organizational knowledge that never walks out the door.",
  },
  hero: {
    eyebrow: "Enterprise Intelligence Platform",
    titleLead: "The",
    titleAccent: "intelligence layer",
    titleTail: "of your organization.",
    description:
      "One General Brain, taught your domain, configured to how your organization actually works.",
    primary: "Discover the Brain",
    secondary: "Explore Modules",
    taglineLead: "People may leave.",
    taglineTail: "Organizational knowledge never does.",
  },
  stats: [
    { value: "3", label: "Domain modules on the roadmap" },
    { value: "4", label: "Intelligence layers per Brain" },
    { value: "100%", label: "Human-validated knowledge" },
    { value: "6", label: "Minutes to a working Brain" },
  ],
  features: {
    eyebrow: "What's inside",
    title: "One shared foundation, specialized for every team",
    description:
      "The General Brain carries the heavy machinery. Domain modules teach it the language of your field. Your organization configures it with the documents, roles and rules that make it yours.",
    items: [
      {
        title: "Knowledge and memory",
        body: "Every contract, case and decision is remembered in one place — not in chats, files and people's heads.",
        icon: "brain" as const,
      },
      {
        title: "Reasoning and retrieval",
        body: "Ask in plain language. Answers come back sourced from your own documents, with the context attached.",
        icon: "search" as const,
      },
      {
        title: "Flags and conflicts",
        body: "Missing information is flagged and conflicts are caught early — before they become expensive.",
        icon: "alert" as const,
      },
      {
        title: "Learning from approval",
        body: "Nothing becomes company knowledge without a human's yes. The Brain learns from what your people approve.",
        icon: "check" as const,
      },
      {
        title: "Permissions and auditability",
        body: "Roles, rules and approval paths are enforced end to end, with an audit trail for every decision.",
        icon: "shield" as const,
      },
      {
        title: "Private and yours alone",
        body: "Your documents, policies and structure stay inside your organization. The Brain is yours alone.",
        icon: "lock" as const,
      },
    ],
  },
  howItWorks: {
    eyebrow: "How it works",
    title: "From scattered knowledge to an Organizational Brain",
    steps: [
      {
        number: "01",
        title: "Choose your domain",
        body: "Start with Legal Intelligence today. Sales and HR modules are on the way.",
      },
      {
        number: "02",
        title: "Create your account",
        body: "Personal or company — verify your email and tell us how your organization is structured.",
      },
      {
        number: "03",
        title: "Teach your Brain",
        body: "Upload SOPs, policies and procedures in PDF, DOCX or TXT. We extract, connect and validate.",
      },
      {
        number: "04",
        title: "Enter your workspace",
        body: "Cases, clients, knowledge and insights — one workspace on top of everything your team knows.",
      },
    ],
  },
  showcase: {
    eyebrow: "Product tour",
    title: "Built for the people who carry the knowledge",
    description:
      "A guided onboarding builds your Brain step by step, then hands you a workspace your whole team can use.",
    shots: [
      {
        title: "Organizational story",
        body: "A six-step walkthrough of what the Brain remembers, flags and learns.",
        accent: "violet" as const,
      },
      {
        title: "Domain selection",
        body: "Legal available now. Sales and HR planned. One foundation across every team.",
        accent: "gold" as const,
      },
      {
        title: "Document ingestion",
        body: "Drop in SOPs and policies — track every file from upload to processed.",
        accent: "mint" as const,
      },
    ],
    cta: "Start the walkthrough",
  },
  testimonials: {
    eyebrow: "Trusted by knowledge teams",
    title: "What changes when nothing is forgotten",
    items: [
      {
        quote:
          "Every case we closed last decade is now searchable in one sentence. Onboarding a new associate went from months to days.",
        name: "Amelia Hartford",
        role: "Managing Partner, Hartford & Cole",
      },
      {
        quote:
          "The conflict flags alone paid for themselves. It caught an overlap in two supplier agreements we would have missed.",
        name: "Diego Ramírez",
        role: "Head of Operations, Northwind Group",
      },
      {
        quote:
          "People leave and the context used to leave with them. Now the Brain keeps it — and nothing ships without a human approval.",
        name: "Priya Nadar",
        role: "Chief People Officer, Lumen Labs",
      },
    ],
  },
  faq: {
    eyebrow: "FAQ",
    title: "Questions, answered",
    items: [
      {
        q: "What exactly is the General Brain?",
        a: "It is the reusable intelligence infrastructure at the core of Brain-co: knowledge and memory, reasoning and retrieval, learning and validation, and permissions and auditability. Domain modules and your own organization configure it — the foundation itself is shared.",
      },
      {
        q: "Which domains are available today?",
        a: "Legal Intelligence is available now. Sales and HR modules are planned and share the same foundation, so your teams keep one consistent Brain across every field.",
      },
      {
        q: "Does the Brain learn without our approval?",
        a: "No. Nothing becomes company knowledge without a human's yes. Your people approve what is learned, and every approval is recorded.",
      },
      {
        q: "What happens when someone leaves the company?",
        a: "Their knowledge stays. Contracts, cases, decisions and procedures live in the Brain, so organizational memory never walks out the door.",
      },
      {
        q: "Which file formats can I upload?",
        a: "PDF, DOCX and TXT. Upload SOPs, handbooks, policies and procedures during onboarding — you can add more at any time.",
      },
      {
        q: "Is my organization's data private?",
        a: "Yes. Your documents, policies, roles and structure are configured to your company alone, with permissions and auditability enforced end to end.",
      },
    ],
  },
  cta: {
    title: "Build the Brain your organization deserves",
    body: "Six minutes from first click to a working Organizational Brain. See how it works, then choose your domain.",
    primary: "Get started",
    secondary: "Talk to us",
  },
} as const;

export const aboutCopy = {
  meta: {
    title: "About",
    description:
      "Brain-co builds the intelligence layer of the organization — a General Brain that keeps what your team knows, so knowledge compounds instead of walking out the door.",
  },
  eyebrow: "About Brain-co",
  title: "Intelligence that compounds, instead of walking out the door",
  intro:
    "Every company runs on knowledge that is barely written down: the contract that was negotiated last spring, the exception that finance approved, the reason a policy exists at all. It lives in chats, files and people's heads — and it leaves when they do.",
  sections: [
    {
      number: "01",
      title: "General Brain",
      subtitle: "The reusable intelligence infrastructure",
      body: "Knowledge and memory, reasoning and retrieval, learning and validation, permissions and auditability — one foundation every team can build on.",
    },
    {
      number: "02",
      title: "Domain Modules",
      subtitle: "Intelligence specialized for each field",
      body: "Legal intelligence is available now, with Sales and HR on the way. Domain-specific language and workflows, one shared foundation across every team.",
    },
    {
      number: "03",
      title: "Your Organization",
      subtitle: "Configured to how your company works",
      body: "Your documents, policies and decisions. Your roles, rules and approval paths. Human-validated organizational memory — private, secure and built to evolve.",
    },
  ],
  principles: {
    title: "What we believe",
    items: [
      {
        title: "A human's yes is the product",
        body: "Nothing becomes company knowledge without a human's yes. Approval is not a setting — it is the mechanism.",
      },
      {
        title: "Knowledge should outlive tenure",
        body: "People may leave. Organizational knowledge never does. That is the whole point.",
      },
      {
        title: "One foundation, many fields",
        body: "Legal, Sales and HR should share one Brain instead of buying three disconnected tools.",
      },
    ],
  },
} as const;

export const modulesCopy = {
  meta: {
    title: "Domain modules",
    description:
      "Legal intelligence available now. Sales and HR modules coming soon. One General Brain shared across every team.",
  },
  eyebrow: "Domain modules",
  title: "Intelligence specialized for each field",
  description:
    "Each module teaches the General Brain the language and workflows of a field — while everything your organization learns stays on one shared foundation.",
  modules: [
    {
      key: "legal" as const,
      title: "Legal",
      status: "Available",
      tagline: "Every case remembered.",
      body: "Missing information flagged. Conflicts caught early. Every matter, precedent and clause retrievable in plain language.",
      points: [
        "Case and matter memory",
        "Conflict and gap detection",
        "Clause-level retrieval across your own documents",
      ],
      cta: "Start with Legal",
    },
    {
      key: "sales" as const,
      title: "Sales",
      status: "Planned",
      tagline: "Every deal explained.",
      body: "We're preparing this field for the Organizational Brain. It isn't available yet.",
      points: [
        "Deal and account history",
        "Objection and pricing memory",
        "Pipeline reasoning over your own notes",
      ],
      cta: "Notify me",
    },
    {
      key: "hr" as const,
      title: "HR",
      status: "Planned",
      tagline: "Every policy kept.",
      body: "We're preparing this field for the Organizational Brain. It isn't available yet.",
      points: [
        "Policy and handbook answers",
        "Consistent, auditable responses",
        "Onboarding knowledge that survives turnover",
      ],
      cta: "Notify me",
    },
  ],
} as const;

export const contactCopy = {
  meta: {
    title: "Contact",
    description:
      "Talk to the Brain-co team about bringing organizational intelligence to your company.",
  },
  eyebrow: "Contact",
  title: "Tell us about your organization",
  description:
    "Questions about domains, security or rollout? Send a message and a human — not a Bot — will reply within one business day.",
  direct: {
    title: "Reach us directly",
    email: "hello@brain-co.app",
    support: "support@brain-co.app",
    address: "100 Knowledge Way, San Francisco, CA 94107, USA",
    hours: "Mon–Fri, 9:00–18:00 PT",
  },
  form: {
    name: "Full name",
    email: "Email",
    company: "Company (optional)",
    topic: "Topic",
    topics: ["Product demo", "Security & privacy", "Partnerships", "Support", "Other"],
    message: "Message",
    messagePlaceholder:
      "What would you like to know? Tell us a little about your organization.",
    submit: "Send message",
    sending: "Sending…",
    successTitle: "Message sent",
    successBody: "Thanks for reaching out — we'll reply within one business day.",
    errorBody: "Something went wrong. Please try again or email us directly.",
    honeypot: "website",
  },
} as const;

export const authCopy = {
  login: {
    eyebrow: "Welcome back",
    title: "Log in to your Brain",
    description: "Pick up where your organization left off.",
    email: "Email",
    password: "Password",
    submit: "Log in",
    submitting: "Signing in…",
    noAccount: "Don't have an account?",
    create: "Get started",
    invalid: "Enter a valid email and a password of at least 8 characters.",
    demoHint: "Demo: any valid email with a password of 8+ characters.",
    success: "Welcome back.",
    /* Additive entries for the login stage (auth journey). */
    context: "Continue to Legal Intelligence",
    prototypeNote:
      "Prototype build — authentication is simulated (MOCK). No real account is created.",
    showPassword: "Show password",
    hidePassword: "Hide password",
    networkError: "Something went wrong. Please try again.",
  },
  logout: "Log out",
  workspaceLocked: {
    title: "Sign in to continue",
    body: "Your workspace is protected. Log in — or start onboarding — to enter.",
    login: "Log in",
    start: "Start onboarding",
  },
} as const;

export const notFoundCopy = {
  code: "404",
  title: "This page wandered off",
  body: "The link you followed doesn't exist — but the Brain remembers where everything is.",
  home: "Back home",
  modules: "Explore modules",
} as const;

export const cookieCopy = {
  title: "Cookies & analytics",
  body: "We use essential cookies to keep you signed in. With your consent we also collect anonymized analytics to improve the product.",
  accept: "Accept",
  decline: "Essential only",
  policy: "Privacy Policy",
} as const;

export const miscCopy = {
  breadcrumbs: { home: "Home" },
  loading: "Loading…",
  retry: "Try again",
  search: "Search",
  sortBy: "Sort by",
  noResults: "Nothing matches your filters yet.",
  clearFilters: "Clear filters",
  page: (page: number, total: number) => `Page ${page} of ${total}`,
  previous: "Previous",
  next: "Next",
  sampleBadge: "Sample data",
} as const;
