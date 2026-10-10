
# Brain-co --- Flutter App UX Flow

## 1. Overview

**Brain-co** is an Enterprise Intelligence Platform built around a
reusable **General Organizational Brain**.

The intended user experience should explain the product visually, help
users select a domain, collect the necessary organization context,
introduce organizational knowledge, and then take the user into the
workspace for the selected domain.

The central idea is:

> **One General Brain. Different domain knowledge and context.
> Organizational intelligence that grows from validated knowledge.**

The first concrete domain in the graduation-project V1 is **Legal**,
specifically the Egyptian Civil Legal Domain. Sales and HR may appear in
the introductory visuals as examples of the reusable Brain concept, but
their full functionality must not be presented as implemented unless the
project scope confirms it.

------------------------------------------------------------------------

## 2. Complete User Journey

``` text
APP START
   |
   v
GENERAL BRAIN INTRO
   |
   v
BRAIN / DOMAIN VISUAL DEMONSTRATION
General Brain -> Legal -> Sales -> HR
   |
   v
WHAT THE BRAIN PROVIDES
Knowledge | Memory | Reasoning | Learning
   |
   v
CHOOSE YOUR DOMAIN
   |
   v
DOMAIN-SPECIFIC INTRO
   |
   v
LOGIN / SIGN UP
   |
   +-----------------------------+
   |                             |
   v                             v
PERSONAL USE                 COMPANY
                                 |
                                 v
                         COMPANY REGISTRATION
                                 |
                                 v
                         EMAIL VERIFICATION
                                 |
                                 v
                         ORGANIZATION ONBOARDING
                                 |
                                 v
                         SOP / DOCUMENT UPLOAD
                                 |
                                 v
                         BRAIN INITIALIZATION
                                 |
                                 v
                         ORGANIZATION READY
                                 |
                                 v
                         SELECTED DOMAIN WORKSPACE
                         (Legal for V1)
```

This is the proposed product journey. Exact authentication options,
survey fields, and onboarding steps are UX/product decisions unless they
are explicitly required by the project documents.

------------------------------------------------------------------------

## 3. Screen-by-Screen Experience

### Screen 1 --- General Brain Intro

When the user opens the app, the first major visual is an animated
digital Brain.

Possible visual elements: - Neural connections and nodes - Particles
moving through the Brain - Subtle data-flow effects - Controlled glow
and depth - Smooth motion that feels intelligent and professional

The goal is to communicate that the user is entering an Organizational
Intelligence Platform---not a generic chatbot or ordinary CRUD app.

The animation should be premium and enterprise-focused, not childish or
excessively sci-fi.

### Screen 2 --- One General Brain, Multiple Domains

The Brain demonstrates how the same General Brain can support different
domains.

Suggested visual sequence:

1.  General Brain
2.  Brain transitions into a Legal visual, such as scales of justice
3.  Returns to the General Brain
4.  Transitions into a Sales-related visual
5.  Returns to the General Brain
6.  Transitions into an HR-related visual

The intended message is:

> **One General Brain → Different domain knowledge and context**

This must not imply that the product has three independent brains. The
Brain is reusable; the domain-specific context and knowledge differ.

Sales and HR are introductory concepts unless their implementations are
confirmed in the project scope.

### Screen 3 --- What Does the Brain Provide?

A concise explanation of key capabilities can help users understand the
product before choosing a domain.

**Knowledge**\
Organizational information can be structured and made accessible.

**Memory**\
Relevant organizational experience can be retained as governed
knowledge.

**Reasoning**\
The Brain can use context and retrieved knowledge to support analysis
and decisions.

**Learning**\
Validated organizational experience can contribute to improving
organizational knowledge and processes.

The interface must not suggest that every capability is already fully
implemented if it is not available in the current V1.

### Screen 4 --- Choose Your Domain

Suggested heading:

**Choose the Domain You Want to Activate**

Possible options: - Legal - Sales - HR

For V1, Legal is the first concrete domain. If Sales and HR are not
implemented, display them as conceptual demonstrations, future domains,
or disabled/coming-soon options.

Selecting a domain means choosing the domain context for the experience.
It does not mean creating a completely separate Brain.

### Screen 5 --- Domain-Specific Introduction

If the user selects Legal, show a short transition from the General
Brain into the Legal identity.

Suggested sequence:

``` text
GENERAL BRAIN
      |
      v
TRANSFORMATION
      |
      v
LEGAL VISUAL / SCALES OF JUSTICE
      |
      v
LEGAL INTELLIGENCE
      |
      v
LOGIN
```

Suggested message:

**Welcome to Legal Intelligence**

This transition should make the relationship between the General Brain
and the selected domain visually understandable.

### Screen 6 --- Login / Sign Up

The proposed UX offers two paths:

-   Personal Use
-   Company / Organization

Example:

**How will you use the Organizational Brain?**

-   Personal Use
-   For a Company

These are proposed product choices. They should be checked against the
project's actual account, tenancy, and authorization requirements before
implementation.

### Screen 7 --- Company Registration

For the proposed Company path, the initial form could include:

-   Company name
-   Company email
-   Password
-   Confirm password, if required by the chosen authentication design

After registration, the user proceeds to email verification.

These exact fields and the order of registration are UX proposals, not
automatically project requirements.

### Screen 8 --- Email Verification

Suggested elements:

-   Verification-code input
-   Verify button
-   Resend-code action
-   Clear success and error feedback

The app should only proceed after the authentication service confirms
verification. It must not simulate successful verification in the real
integrated flow.

### Screen 9 --- Organization Onboarding Survey

After verification, the user provides context about the organization so
the system can establish its organizational context.

Potential fields to consider: - Organization name - Organization size or
employee count - Industry - Departments - Leadership information, if
relevant - User's role - Roles or groups that will use the system -
Organizational structure or other relevant context

The survey should preferably be split into short steps rather than one
long form.

Example:

``` text
Step 1 — Organization
Step 2 — People and Roles
Step 3 — Departments and Structure
Step 4 — Review
```

These fields are examples only. The final fields should be agreed with
the team and backend owners. Collect only information that the system
actually needs.

### Screen 10 --- SOP / Organizational Document Upload

Suggested heading:

**Teach Your Brain How Your Organization Works**

The user can upload supported SOPs and organizational documents.

Potential interface elements: - File picker or upload area - List of
selected documents - Upload progress - Processing status - Retry or
remove actions when appropriate - Supported-file guidance based on
actual backend capabilities

The upload screen should communicate that the user is providing
organizational knowledge---not merely attaching random files.

Supported file types, file-size limits, parsing behavior, and processing
capabilities must come from the actual technical design and backend
contract.

### Screen 11 --- Brain Initialization

After upload, show a meaningful initialization experience.

Possible visual story:

``` text
ORGANIZATIONAL DOCUMENTS
          |
          v
KNOWLEDGE EXTRACTION
          |
          v
CONTEXT AND STRUCTURE
          |
          v
MEMORY / KNOWLEDGE PROCESSING
          |
          v
VALIDATION AND STATUS CHECKS
          |
          v
ORGANIZATION READINESS
```

The Brain animation can gradually show connections and knowledge nodes
becoming active.

Possible messages: - "Preparing your organizational knowledge..." -
"Processing your documents..." - "Building your organizational
context..." - "Checking processing status..."

The exact messages should reflect real backend events and statuses.

**Important:** Do not claim that the system is training or fine-tuning
an LLM unless the technical architecture explicitly supports that. Do
not show "Learning complete" just because an animation has finished. The
UI must reflect actual processing status, failures, and partial
completion.

### Screen 12 --- Organization Ready

When the required initialization steps are actually complete, show a
completion screen.

Example:

**Your Organizational Brain Is Ready**

The screen may show: - Organization name - Selected domain - Readiness
or processing summary - Any remaining setup actions - Continue button

If some documents failed or processing is incomplete, show the actual
partial state and explain what remains. Never show false completion.

### Screen 13 --- Legal Intelligence Workspace

For the V1 Legal domain, the user enters the Legal workspace.

Potential capabilities, depending on the agreed V1 implementation: -
Clients - Cases - Conversations or observations - Case Memory - Legal
Knowledge and Search - Similar Cases - Missing Information - Conflict
Alerts - AI Assistance - Case Reports - Knowledge Validation -
Governance and Audit features

The Legal workspace may contain CRM-like features, but **Brain-co is not
simply a CRM**. The workspace is the operational experience for the
Legal domain, supported by the shared Brain, legal-domain knowledge,
organizational context, and case context.

Do not populate the interface with fake metrics or imply that a feature
works before its backend integration is complete.

------------------------------------------------------------------------

## 4. The Concept the User Should Understand

The whole journey should communicate the following story:

1.  A reusable General Organizational Brain exists.
2.  The Brain can work with different domains.
3.  A domain contributes specialized knowledge and context.
4.  An organization contributes its own context, structure, and
    knowledge.
5.  Organizational documents can be ingested and processed.
6.  Knowledge must be handled with appropriate validation and
    governance.
7.  The selected domain provides the operational workspace.
8.  For V1, the concrete workspace is Legal.

For the Legal V1, the conceptual relationship is:

``` text
GENERAL ORGANIZATIONAL BRAIN
             |
             v
        LEGAL DOMAIN
             |
             v
     ORGANIZATION CONTEXT
             |
             v
   ORGANIZATIONAL KNOWLEDGE
             |
             v
 LEGAL + ORGANIZATIONAL INTELLIGENCE
             |
             v
    LEGAL INTELLIGENCE WORKSPACE
```

------------------------------------------------------------------------

## 5. Important Product Distinctions

-   **One General Brain:** Do not present Legal, Sales, and HR as
    separate independent brains.
-   **Legal is the V1 domain:** Do not imply that Sales and HR
    functionality is fully implemented unless confirmed by project
    scope.
-   **Brain is not a chatbot:** The product is a persistent, governed
    organizational intelligence layer.
-   **Brain is not a CRM:** CRM-like features may exist inside the Legal
    workspace, but they do not define the whole product.
-   **Observation is not knowledge:** Incoming information should not
    automatically be treated as trusted organizational knowledge.
-   **Candidate knowledge is not validated knowledge:** The product must
    respect validation and governance rules.
-   **Learning is not automatically LLM fine-tuning:** Use the meaning
    defined by the technical architecture.
-   **The animation is not proof of processing:** UI status must be
    based on actual backend results.

------------------------------------------------------------------------

## 6. Project Requirements vs. UX Proposals

Keep these categories separate during planning and implementation.

### Core project concepts

The project concept includes the reusable General Brain, domain-specific
context, organization context, knowledge, memory, reasoning, learning,
validation, and the first concrete Legal domain implementation.

### UX/product proposals introduced for this journey

The following are proposed experience choices and should be confirmed
with the team: - Introductory Brain animation - Brain-to-domain
transformations - Showing Legal, Sales, and HR in the introduction -
Personal Use versus Company paths - Exact registration fields - Email
verification screen and flow - Exact organization-survey questions - SOP
upload screen and its wording - Brain initialization animation -
Organization-ready screen and summary

### Recommended implementation decisions to make later

These are technical decisions, not project requirements: - Flutter
navigation and routing - State management - Clean Architecture
structure - Authentication implementation - Upload and processing API
contracts - Rive, Lottie, CustomPainter, or other animation technology -
Local persistence and recovery after app restart - Handling interrupted
uploads and partial processing

If a detail is not specified by the project source, label it **"Not
specified by project source"** and, separately, offer a **"Recommended
implementation."**

------------------------------------------------------------------------

## 7. Animation and Flutter Direction

Flutter can implement this experience without requiring a website.

Potential options to evaluate:

-   **Rive:** Interactive, state-driven character or vector animations;
    a candidate for controlled Brain-to-domain transitions if the
    required artwork can be authored appropriately.
-   **Lottie:** Good for prepared motion-design sequences that do not
    require extensive runtime manipulation.
-   **Flutter animation APIs:** Useful for page transitions, opacity,
    scale, movement, sequencing, and interactive UI feedback.
-   **CustomPainter:** Useful for custom 2D visuals, particles, nodes,
    and connections when the team can maintain the implementation.
-   **Custom shaders or 3D/web-based approaches:** Consider only if the
    desired visual effect genuinely needs them and the extra complexity
    is justified.

Do not commit to a tool before testing a small proof of concept. The
designer/motion artist may need to prepare the Brain artwork, domain
symbols, transitions, and state definitions.

A corporate marketing website is a separate product surface. It may use
web-specific techniques, but it is not required for the Flutter
onboarding journey.

------------------------------------------------------------------------

## 8. Practical Implementation Order

Do not implement the entire experience in one step.

1.  Confirm the user journey and which options are actually in scope.
2.  Define the screen map and navigation rules.
3.  Choose the Flutter architecture and state-management approach.
4.  Build the app shell, theme, routing, and responsive layout.
5.  Prototype the Brain animation and test performance on target
    devices.
6.  Implement the intro and domain-selection screens.
7.  Implement the authentication flow against agreed API contracts.
8.  Implement organization onboarding.
9.  Implement document upload and real upload states.
10. Implement initialization status based on backend events or status
    APIs.
11. Connect the Legal workspace.
12. Test complete, failed, interrupted, and partially completed flows.
13. Integrate and verify each capability through the project's
    Ring-based process.

For every screen, support the relevant states: loading, success, empty,
error, and partial completion. Build mock-backed UI only where it is
clearly marked as mock data, and replace it with real integrations when
the required backend contract is available.

------------------------------------------------------------------------

## 9. Final UX Principle

The experience should not merely show a beautiful Brain animation. It
should tell a coherent product story:

**Meet the General Brain → Choose a domain → Introduce your organization
→ Provide organizational knowledge → See real processing progress →
Enter the domain workspace.**

Every screen, animation, and status message should reinforce that story
while remaining faithful to the project's real capabilities.
