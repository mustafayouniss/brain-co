/**
 * All copy reproduced 1:1 from the source app (grad_flutter/newflutter.zip,
 * src/App.tsx). Nothing here may be reworded — it is the product's voice.
 */

export type DomainKey = "legal" | "sales" | "hr";
export type Shape = "dust" | "brain" | "legal" | "sales" | "hr";
export type AccountMode = "personal" | "company";

export const shapeUrls: Record<Shape, string> = {
  dust: "/morphs/morph-00-dust.svg",
  brain: "/morphs/morph-01-brain.svg",
  legal: "/morphs/morph-02-legal.svg",
  sales: "/morphs/morph-03-sales.svg",
  hr: "/morphs/morph-04-hr.svg",
};

export const domainDetails: Record<
  DomainKey,
  { title: string; status: string; color: "gold" | "mint" | "violet" }
> = {
  legal: { title: "Legal", status: "Available", color: "gold" },
  sales: { title: "Sales", status: "Planned", color: "mint" },
  hr: { title: "HR", status: "Planned", color: "violet" },
};

/* --- Home ---------------------------------------------------------------- */
export const homeCopy = {
  brand: "Brain-co",
  infoAria: "About Brain-co",
  kicker: "Enterprise Intelligence Platform",
  /** h1 renders "The <em>intelligence layer</em> of your organization." */
  titleLead: "The",
  titleAccent: "intelligence layer",
  titleTail: "of your organization.",
  description:
    "One General Brain, taught your domain, configured to how your organization actually works.",
  primaryCta: "Discover the Brain",
  secondaryCta: "Explore Modules",
  taglineLead: "People may leave.",
  taglineTail: "Organizational knowledge never does.",
  brainLabel: "General Brain",
  brainAria: "Connected General Brain network",
  /** Hero morph: supporting line shown during the domain phases. */
  brainSupport: "One General Brain. Different domain knowledge and context.",
  /** Hero morph: chip marking Sales/HR as concept phases (only Legal is V1). */
  brainConcept: "Concept",
} as const;

/* --- Discover sheet ------------------------------------------------------ */
export const discoverCopy = {
  closeAria: "Close discovery panel",
  eyebrow: "Inside Brain-co",
  title: "Intelligence that compounds,\ninstead of walking out the door.",
  cta: "See how it works",
  sections: [
    {
      number: "01",
      title: "General Brain",
      subtitle: "The reusable intelligence infrastructure",
      items: [
        "Knowledge and memory",
        "Reasoning and retrieval",
        "Learning and validation",
        "Permissions and auditability",
      ],
    },
    {
      number: "02",
      title: "Domain Modules",
      subtitle: "Intelligence specialized for each field",
      items: [
        "Legal intelligence, available now",
        "Sales and HR modules, coming soon",
        "Domain-specific language and workflows",
        "One shared foundation across every team",
      ],
    },
    {
      number: "03",
      title: "Your Organization",
      subtitle: "Configured to how your company works",
      items: [
        "Your documents, policies and decisions",
        "Your roles, rules and approval paths",
        "Human-validated organizational memory",
        "Private, secure and built to evolve",
      ],
    },
  ],
} as const;

/* --- Intro sequence ------------------------------------------------------ */
export const introCopy = {
  skip: "Skip",
  steps: [
    {
      shape: "dust" as Shape,
      title: "Your team's knowledge is everywhere.",
      tag: null,
      duration: 0,
      wait: 1800,
    },
    {
      shape: "brain" as Shape,
      title: "Meet your Organizational Brain.",
      tag: null,
      duration: 1600,
      wait: 2000,
    },
    {
      shape: "legal" as Shape,
      title: "Legal Mind. Every case remembered.",
      tag: "Available",
      duration: 1200,
      wait: 2000,
    },
    {
      shape: "sales" as Shape,
      title: "Sales Mind. Every deal explained.",
      tag: "Planned",
      duration: 1200,
      wait: 2000,
    },
    {
      shape: "hr" as Shape,
      title: "HR Mind. Every policy kept.",
      tag: "Planned",
      duration: 1200,
      wait: 1500,
    },
  ],
} as const;

/* --- Splash story (6 steps) ---------------------------------------------- */
export const storyCopy = {
  skip: "Skip",
  next: "Continue",
  finalCta: "Choose your domain",
  humanNote: "Nothing becomes company knowledge without a human's yes.",
  progressLabel: (step: number) => `Screen ${step} of 6`,
  layersAria: "Three intelligence layers",
  layers: ["Shared Brain", "Field expertise", "Your organization"],
  steps: [
    {
      shape: "dust" as Shape | null,
      tag: null,
      title: "Your team's knowledge walks out the door.",
      body: "Every contract, case and decision lives in chats, files and people's heads.",
      lines: null,
    },
    {
      shape: "brain" as Shape | null,
      tag: null,
      title: "Your organization, remembered.",
      body: "A Brain that keeps what your team knows, so nothing is lost when people move on.",
      lines: null,
    },
    {
      shape: null,
      tag: null,
      title: "Built around your organization.",
      body: "A shared Brain, plus your field's expertise, plus your own documents and rules. It is yours alone.",
      lines: null,
    },
    {
      shape: "legal" as Shape | null,
      tag: "Available",
      title: "Legal Mind.",
      body: "Every case remembered. Missing information flagged. Conflicts caught early.",
      lines: null,
    },
    {
      shape: null,
      tag: null,
      title: "More fields are on the way.",
      body: "",
      lines: null,
    },
    {
      shape: "brain" as Shape | null,
      tag: null,
      title: "What your Brain does for you.",
      body: "",
      lines: [
        "Remembers what your team knows.",
        "Finds answers in your own documents.",
        "Flags what is missing and what conflicts.",
        "Learns from what your people approve.",
      ],
    },
  ],
  pairedDomains: [
    { name: "Sales", status: "Planned", shape: "sales" as Shape },
    { name: "HR", status: "Planned", shape: "hr" as Shape },
  ],
} as const;

/* --- Domains -------------------------------------------------------------- */
export const domainsCopy = {
  kicker: "Organizational Brain",
  title: "Choose your domain",
} as const;

export const transitionCopy = {
  titleSuffix: "Mind.",
} as const;

export const destinationCopy = {
  legalTitle: "Welcome to Legal Intelligence",
  legalCta: "Continue",
  plannedCta: "Back to domains",
  plannedBody:
    "We're preparing this field for the Organizational Brain. It isn't available yet.",
  plannedTitle: (domain: DomainKey) =>
    `${domainDetails[domain].title} Mind is coming soon.`,
} as const;

/* Shared MOCK note for the post-selection journey (additive). */
export const prototypeNote =
  "Prototype build — this step is not connected to a backend yet (MOCK).";

/* --- Usage / account ------------------------------------------------------ */
export const usageCopy = {
  title: "How will you use your Brain?",
  personal: "Personal",
  company: "Company",
  /* Additive entries for the account-type stage (UX copy only — the real
     account/tenancy model is an open product decision, FLOW_AUDIT D2). */
  personalDesc: "Individual use.",
  companyDesc: "For an organization.",
} as const;

export const accountCopy = {
  title: "Create your account",
  fields: {
    companyName: "Company name",
    fullName: "Full name",
    email: "Email",
    password: "Password",
    confirmPassword: "Confirm password",
  },
  submit: "Continue",
  loginLead: "Already have an account?",
  loginLink: "Log in",
  /* Additive entries for the registration stage. */
  prototypeNote:
    "Prototype build — registration is simulated (MOCK). No real account is created.",
  submitting: "Creating your account…",
} as const;

/* --- Verify --------------------------------------------------------------- */
export const verifyCopy = {
  title: "Verify your email",
  subtitle: "We sent a 6-digit code to your email.",
  digitLabel: (index: number) => `Code digit ${index + 1}`,
  error: "The code is not correct",
  expired: "This code has expired",
  resend: "Resend code",
  submit: "Verify",
} as const;

/* --- Survey --------------------------------------------------------------- */
export const surveyCopy = {
  title: "Tell us about your organization",
  stepLabel: (step: number) => `Step ${step} of 4`,
  sections: ["Organization", "People", "Structure", "Your role"],
  back: "Back",
  next: "Next",
  final: "Continue",
  sizeLabel: "Size",
  sizeOptions: ["1-10", "11-50", "51-200", "200+"],
  departmentsLabel: "Departments",
  departmentOptions: ["Legal", "Sales", "HR", "Finance", "Operations"],
  steps: [
    {
      fields: [
        { name: "organizationName", label: "Organization name", type: "text" },
        { name: "industry", label: "Industry", type: "text" },
      ] as const,
      chips: "size" as const,
    },
    {
      fields: [
        { name: "employees", label: "Number of employees", type: "text" },
        { name: "leadershipName", label: "Leadership name", type: "text" },
        {
          name: "brainUsers",
          label: "Who will use the Brain",
          type: "text",
        },
      ] as const,
      chips: null,
    },
    {
      fields: [] as const,
      chips: "departments" as const,
    },
    {
      fields: [
        { name: "yourRole", label: "Your role", type: "text" },
        { name: "team", label: "Team", type: "text" },
      ] as const,
      chips: null,
    },
  ],
} as const;

/* --- Upload --------------------------------------------------------------- */
export type UploadStatus = "Processed" | "Processing" | "Queued" | "Uploading" | "Failed";

export const uploadCopy = {
  title: "Teach your Brain how your organization works.",
  subtitle: "Upload your SOPs and organizational documents.",
  choose: "Choose documents",
  add: "Add documents",
  formats: "Supported formats: PDF, DOCX, TXT",
  sampleNote: "Sample, confirm with the backend",
  retry: "Retry",
  continue: "Continue",
  /* Additive entries for the upload stage (task G / FLOW_AUDIT D6). */
  blocker:
    "Upload status unavailable — no backend upload endpoint exists yet, so selected files are NOT uploaded. Blocker: docs/FLOW_AUDIT.md, contract 4.",
  dropHint: "or drag and drop here",
  empty: "No documents selected.",
  uploading: "Uploading…",
  uploadAll: "Upload documents",
  remove: "Remove",
  rejected: (names: string) =>
    `Skipped unsupported files: ${names}. Formats below are unconfirmed prototype copy.`,
  failedNetwork: "Failed — network error.",
  failedEndpoint: (status: number) =>
    `Failed — no upload endpoint (HTTP ${status}). Status unavailable.`,
  documents: [
    ["Operations handbook.pdf", "Processed"],
    ["Matter intake SOP.docx", "Processing"],
    ["Records policy.txt", "Queued"],
    ["Client procedure.pdf", "Uploading"],
  ] as Array<[string, UploadStatus]>,
  failure: ["Legacy policy.pdf", "Failed"] as [string, UploadStatus],
} as const;

/* --- Build / loading ------------------------------------------------------ */
export const buildCopy = {
  stages: [
    "Receiving your documents",
    "Extracting knowledge",
    "Building organizational memory",
    "Connecting context",
    "Validating",
    "Your Organizational Brain is ready",
  ],
  counter: (done: number) => `${Math.min(10, done * 2)} of 10 documents processed`,
  sample: "Sample",
  /* Additive (task D / FLOW_AUDIT D7): honest status note; the sample
     counter above stays unused — it invents document counts. */
  statusNote:
    "Initialization status unavailable — no processing API exists. The sequence below is a visual preview only (MOCK); no training or fine-tuning is performed.",
  done: "Continue",
} as const;

/* --- Ready ---------------------------------------------------------------- */
export const readyCopy = {
  fullTitle: "Your Organizational Brain is ready.",
  fullBody: "Your Brain now understands your organization.",
  fullCta: "Enter your workspace",
  partialTitle: "Your Brain is partly ready.",
  partialBody: "8 of 10 documents were processed. 2 need attention.",
  partialCta: "Continue with what is ready",
  retry: "Retry",
  /* Additive honest states (task D: never pretend; FLOW_AUDIT D6/D7). */
  prototypeBody:
    "Prototype: organization readiness is not verified — no backend status API exists yet.",
  partialBodyReal: (failed: number, total: number) =>
    `${failed} of ${total} documents could not be uploaded. The rest of your setup is complete.`,
  entering: "Entering your workspace…",
  sessionError: "Could not start your session. Please log in again.",
} as const;

/* --- Workspace ------------------------------------------------------------ */
export const workspaceCopy = {
  title: "Organizational Brain",
  subtitle: "Your organization",
  tabs: ["Overview", "Cases", "Clients", "Knowledge", "Insights", "AI Employee"],
  kicker: "Legal Intelligence",
  overview: "Overview",
  sampleData: "Sample data",
  cards: [
    { label: "Active cases", value: "12" },
    { label: "Clients", value: "24" },
    { label: "Pending actions", value: "7" },
    { label: "Knowledge updates", value: "18" },
  ],
  /* Additive honest states (task H / FLOW_AUDIT D8 — the sample metrics
     above stay unused; they were prototype-only copy). */
  noData: "No data yet",
  notConnected: "Backend not connected — MOCK",
  emptyNote: (tab: string) => `No ${tab.toLowerCase()} yet — not connected to a backend.`,
  aiUnavailable: "The AI Employee is not available yet.",
  noOrgTitle: "No organization setup yet",
  noOrgBody: "Finish onboarding to teach the Brain how your organization works.",
  startOnboarding: "Start onboarding",
  plannedTitle: "Not available yet",
  plannedBody: "This module is planned for a future release.",
  loading: "Checking your session…",
} as const;
