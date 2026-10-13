import { useState } from "react";
import {
  Card,
  CardHeader,
  CardContent,
  CardTitle,
  CardDescription,
} from "cursor/canvas/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "cursor/canvas/components/ui/tabs";
import { Badge } from "cursor/canvas/components/ui/badge";
import { Separator } from "cursor/canvas/components/ui/separator";
import { useHostTheme } from "cursor/canvas/hooks/useHostTheme";

const REPORT_METADATA = {
  title: "Project Context & Ring Architecture Master Report",
  repository: "brain-co",
  remote: "https://github.com/mustafayouniss/brain-co.git",
  investigationDate: "2026-10-12",
  investigator: "Devin AI Agent",
  mode: "READ-ONLY INVESTIGATION",
  version: "1.0",
};

const DOCUMENTATION_INVENTORY = [
  {
    path: "docs/project-specifications/ORGANIZATIONAL_BRAIN_MASTER_PROJECT_CONSTITUTION.md",
    title: "Master Project Constitution v2.0",
    purpose: "Highest authority document defining vision, architecture, invariants, Ring specifications, and complete roadmap",
    scope: "Entire project",
    authority: "Normative (LEVEL 0)",
    status: "Current",
    evidence: "Document version 2.0, September 2026, explicitly stated as highest authority",
  },
  {
    path: "docs/project-specifications/REQUIREMENTS_SPECIFICATION.md",
    title: "Requirements Specification (Step 2)",
    purpose: "Detailed functional and non-functional requirements for Legal V1",
    scope: "Legal V1 domain",
    authority: "Normative",
    status: "Current",
    evidence: "Step 2 of software analysis, baseline for subsequent design phases",
  },
  {
    path: "docs/project-specifications/PROJECT_SCOPE.md",
    title: "Project Scope (Step 1)",
    purpose: "System boundary definition, in-scope vs out-of-scope, scope invariants",
    scope: "Entire project",
    authority: "Normative",
    status: "Current",
    evidence: "Step 1 scope definition, explicitly marked COMPLETE",
  },
  {
    path: "docs/backend/decisions.md",
    title: "Backend Decisions",
    purpose: "Implementation choices, technology stack, architectural decisions, overrides Constitution",
    scope: "Backend implementation",
    authority: "Normative (overrides Constitution)",
    status: "Current",
    evidence: "Explicitly stated: 'Highest authority for implementation choices'",
  },
  {
    path: "docs/backend/rings/ring-00-foundation.md",
    title: "Ring 0 Foundation Specification",
    purpose: "Detailed Ring 0 tasks, boundaries, exit criteria, implementation guidance",
    scope: "Ring 0 backend",
    authority: "Normative",
    status: "In Progress",
    evidence: "Status: 'in progress', explicit task list T1-T11",
  },
  {
    path: "docs/backend/constitution.md",
    title: "Backend Constitution (condensed)",
    purpose: "Condensed version of Master Constitution for backend context",
    scope: "Backend",
    authority: "Normative (derivative)",
    status: "Current",
    evidence: "Condensed from v2.0 Constitution",
  },
  {
    path: "docs/backend/vision.md",
    title: "Backend Vision",
    purpose: "Condensed vision document for AI agents",
    scope: "Backend",
    authority: "Normative (derivative)",
    status: "Current",
    evidence: "Explicitly for AI agent consumption",
  },
  {
    path: "docs/backend/architecture.md",
    title: "Backend Architecture Documentation",
    purpose: "Verified structural layout, configuration flows, component versions",
    scope: "Backend implementation",
    authority: "Explanatory",
    status: "Current",
    evidence: "Verified from live migration and database schema",
  },
  {
    path: "docs/backend/data-model.md",
    title: "Data Model Documentation",
    purpose: "Verified database schema for users table",
    scope: "Backend data layer",
    authority: "Explanatory",
    status: "Current",
    evidence: "Verified from live migration 778be99882b6",
  },
  {
    path: "docs/backend/how-it-works.md",
    title: "How It Works Guide",
    purpose: "Beginner's guide to backend components",
    scope: "Backend",
    authority: "Explanatory",
    status: "Current",
    evidence: "Educational document",
  },
  {
    path: "docs/source-ingestion.md",
    title: "Source Ingestion Technical Documentation",
    purpose: "Foundational Source Ingestion Pipeline architecture and testing",
    scope: "Data engineering + backend integration",
    authority: "Explanatory",
    status: "Current",
    evidence: "Verified 24 passing tests, migration written",
  },
  {
    path: "docs/adrs/README.md",
    title: "Architecture Decision Records",
    purpose: "Record of architectural decisions (7 ADRs listed)",
    scope: "Entire project",
    authority: "Normative",
    status: "Current",
    evidence: "7 ADRs documented (ADR-001 through ADR-007)",
  },
  {
    path: "docs/backend/progress.md",
    title: "Backend Progress Log",
    purpose: "Ring 0 task completion status",
    scope: "Ring 0 backend",
    authority: "Status tracking",
    status: "Current",
    evidence: "Task completion checklist with verification evidence",
  },
  {
    path: "docs/progress.md",
    title: "Overall Progress Log",
    purpose: "High-level project progress",
    scope: "Entire project",
    authority: "Status tracking",
    status: "Current",
    evidence: "Documents Source Ingestion completion",
  },
  {
    path: "docs/journal/2026-10-12.md",
    title: "Journal 2026-10-12",
    purpose: "Daily work log for Source Ingestion implementation",
    scope: "Source Ingestion task",
    authority: "Historical record",
    status: "Historical",
    evidence: "Commands executed, results, issues documented",
  },
  {
    path: "docs/backend/journal/2026-10-12.md",
    title: "Backend Journal 2026-10-12",
    purpose: "Backend-specific daily work log",
    scope: "Backend",
    authority: "Historical record",
    status: "Historical",
    evidence: "Identical to root journal (duplicate)",
  },
  {
    path: "ai/README.md",
    title: "AI Engine Documentation",
    purpose: "Provider-agnostic AI architecture, capabilities, testing",
    scope: "AI package",
    authority: "Explanatory",
    status: "Current",
    evidence: "54 passing unit tests verified",
  },
  {
    path: "data-science/evaluation/README.md",
    title: "Retrieval Evaluation Metrics",
    purpose: "Evaluation metrics foundation (Precision@k, Recall@k, MRR, NDCG@k)",
    scope: "Data science evaluation",
    authority: "Explanatory",
    status: "Current",
    evidence: "Metrics implemented, but retrieval not yet implemented",
  },
  {
    path: "README.md",
    title: "Repository README",
    purpose: "Project overview, architecture description, team information",
    scope: "Entire repository",
    authority: "Explanatory",
    status: "Current",
    evidence: "Standard repository overview",
  },
  {
    path: "AGENTS.md",
    title: "Agent Operating Rules",
    purpose: "Backend-specific rules for AI agents, stack definition, workflow",
    scope: "Backend AI agent operations",
    authority: "Normative",
    status: "Current with conflicts",
    evidence: "Contains merge conflict markers (lines 37-48)",
  },
];

const RING_SPECIFICATIONS = [
  {
    number: 0,
    name: "Foundation",
    purpose: "Establish development environment and core infrastructure",
    whyNow: "Cannot build anything without foundation",
    dependencies: "None",
    classification: "[GB]",
    capabilities: [
      "Development environment setup",
      "Database infrastructure",
      "Basic API framework",
      "Frontend framework",
      "AI/LLM infrastructure",
      "Data pipeline infrastructure",
    ],
    implementationStatus: "In Progress",
    backendStatus: "T1-T6 complete, T7-T11 pending, blocked by merge conflicts",
    frontendStatus: "Not started (Constitution guidance overridden for Python stack)",
    aiStatus: "Complete (54 passing tests)",
    dataScienceStatus: "Evaluation metrics complete, retrieval not implemented",
    exitCriteria: [
      "All team members can run project locally",
      "All infrastructure services accessible",
      "Basic API endpoints respond",
      "Basic UI renders",
      "CI/CD passes",
    ],
    evidence: "backend/progress.md shows T1-T6 complete, T7-T11 pending",
  },
  {
    number: 1,
    name: "Brain Core",
    purpose: "Implement core General Brain engines",
    whyNow: "Foundation ready, need core intelligence infrastructure",
    dependencies: "Ring 0",
    classification: "[GB]",
    capabilities: [
      "Perception Engine",
      "Observation Engine",
      "Context Engine",
      "Basic Memory Engine",
      "Basic Retrieval Engine",
    ],
    implementationStatus: "Not Started",
    backendStatus: "Not Started",
    frontendStatus: "Not Started",
    aiStatus: "Not Started",
    dataScienceStatus: "Not Started",
    exitCriteria: [
      "Can observe events",
      "Can resolve context (organization, domain, case)",
      "Can store observations",
      "Can retrieve stored observations",
      "Context isolation verified",
    ],
    evidence: "Specified in Constitution, Ring 0 not complete",
  },
  {
    number: 2,
    name: "Knowledge & Memory",
    purpose: "Implement knowledge extraction, storage, and retrieval",
    whyNow: "Brain core ready, need knowledge infrastructure",
    dependencies: "Ring 1",
    classification: "[GB]",
    capabilities: [
      "Knowledge Engine",
      "Memory/Storage Engine",
      "Retrieval Engine",
      "Provenance Engine",
    ],
    implementationStatus: "Not Started",
    backendStatus: "Not Started",
    frontendStatus: "Not Started",
    aiStatus: "Not Started",
    dataScienceStatus: "Not Started",
    exitCriteria: [
      "Can extract knowledge from documents",
      "Can store in multi-store architecture",
      "Can retrieve with measurable quality",
      "Provenance tracked for all knowledge",
      "Retrieval evaluation meets baseline metrics",
    ],
    evidence: "Specified in Constitution, Ring 1 not complete",
  },
  {
    number: 3,
    name: "Legal Domain",
    purpose: "Load Legal domain knowledge and implement domain-specific engines",
    whyNow: "Knowledge infrastructure ready, need first domain",
    dependencies: "Ring 2",
    classification: "[DOMAIN]",
    capabilities: [
      "Legal Domain Knowledge",
      "Legal Retrieval",
      "Legal Classification",
      "Legal Document Understanding",
    ],
    implementationStatus: "Not Started",
    backendStatus: "Not Started",
    frontendStatus: "Not Started",
    aiStatus: "Not Started",
    dataScienceStatus: "Not Started",
    exitCriteria: [
      "Legal domain knowledge available",
      "Can retrieve legal knowledge with domain-specific quality",
      "Can classify legal documents",
      "Can understand legal documents",
      "Legal evaluation meets baseline",
      "Domain isolated from General Brain",
    ],
    evidence: "Specified in Constitution, Ring 2 not complete",
  },
  {
    number: 4,
    name: "Organization Context",
    purpose: "Implement organization configuration, roles, and permissions",
    whyNow: "Domain ready, need organization layer",
    dependencies: "Ring 3",
    classification: "[ORG]",
    capabilities: [
      "Organization Configuration",
      "Roles & Permissions",
      "Validation Authority setup",
      "Organization Knowledge base",
    ],
    implementationStatus: "Not Started",
    backendStatus: "Not Started",
    frontendStatus: "Not Started",
    aiStatus: "Not Started",
    dataScienceStatus: "Not Started",
    exitCriteria: [
      "Can configure organization",
      "Can define roles and permissions",
      "Can set validation authority",
      "Organization context isolated",
      "Permissions enforced",
    ],
    evidence: "Specified in Constitution, Ring 3 not complete",
  },
  {
    number: 5,
    name: "Case Intelligence",
    purpose: "Implement case model, client management, and case isolation",
    whyNow: "Organization context ready, need case model",
    dependencies: "Ring 4",
    classification: "[SHARED]",
    capabilities: [
      "Case Model",
      "Client Management",
      "Case Isolation",
      "Case Knowledge",
    ],
    implementationStatus: "Not Started",
    backendStatus: "Not Started",
    frontendStatus: "Not Started",
    aiStatus: "Not Started",
    dataScienceStatus: "Not Started",
    exitCriteria: [
      "Can create cases and clients",
      "Case knowledge strictly isolated",
      "No knowledge leaks between cases",
      "Case context correctly resolved",
      "Case isolation tests pass",
    ],
    evidence: "Specified in Constitution, Ring 4 not complete",
  },
  {
    number: 6,
    name: "Observation (WhatsApp)",
    purpose: "Implement WhatsApp observation and conversation understanding",
    whyNow: "Case model ready, need observation channel",
    dependencies: "Ring 5",
    classification: "[SHARED]",
    capabilities: [
      "WhatsApp Integration",
      "Real-time Capture",
      "Observation Buffer",
      "Conversation Understanding",
      "Client Identification",
      "Case Resolution",
    ],
    implementationStatus: "Not Started",
    backendStatus: "Not Started",
    frontendStatus: "Not Started",
    aiStatus: "Not Started",
    dataScienceStatus: "Not Started",
    exitCriteria: [
      "Can receive WhatsApp messages in real-time",
      "Messages buffered and processed asynchronously",
      "Can identify clients from conversations",
      "Can resolve to existing or new cases",
      "Can understand conversation structure",
      "Can extract facts",
      "Case context maintained",
      "Observation buffer handles load",
    ],
    evidence: "Specified in Constitution, Ring 5 not complete",
  },
  {
    number: 7,
    name: "Reasoning & Assistance",
    purpose: "Implement reasoning, assistance, and lawyer support",
    whyNow: "Observations flowing, need to provide value",
    dependencies: "Ring 6",
    classification: "[GB], [DOMAIN]",
    capabilities: [
      "Reasoning Engine",
      "Legal Reasoning",
      "Assistance Generation",
      "Similar Case Retrieval",
      "Conflict Detection",
      "Missing Information Identification",
    ],
    implementationStatus: "Not Started",
    backendStatus: "Not Started",
    frontendStatus: "Not Started",
    aiStatus: "Not Started",
    dataScienceStatus: "Not Started",
    exitCriteria: [
      "Reasoning working",
      "Legal reasoning working",
      "Assistance quality acceptable",
      "Similar case retrieval working",
      "Conflict detection working",
      "Missing information identification working",
      "End-to-end assistance tests pass",
    ],
    evidence: "Specified in Constitution, Ring 6 not complete",
  },
  {
    number: 8,
    name: "Learning & Validation",
    purpose: "Implement learning loop and validation workflow",
    whyNow: "Reasoning working, need learning from validated knowledge",
    dependencies: "Ring 7",
    classification: "[GB]",
    capabilities: [
      "Learning Engine",
      "Validation/Governance Engine",
      "Candidate promotion",
      "Learning signals",
    ],
    implementationStatus: "Not Started",
    backendStatus: "Not Started",
    frontendStatus: "Not Started",
    aiStatus: "Not Started",
    dataScienceStatus: "Not Started",
    exitCriteria: [
      "Candidates can be promoted to trusted knowledge",
      "Validation workflow working",
      "Learning signals generated",
      "Validation audit trail maintained",
    ],
    evidence: "Specified in Constitution, Ring 7 not complete",
  },
  {
    number: 9,
    name: "Insights & Governance",
    purpose: "Implement insights dashboard and governance controls",
    whyNow: "Learning working, need organizational visibility",
    dependencies: "Ring 8",
    classification: "[GB], [ORG]",
    capabilities: [
      "Insight Engine",
      "Audit Engine",
      "Governance dashboard",
      "Autonomy control",
    ],
    implementationStatus: "Not Started",
    backendStatus: "Not Started",
    frontendStatus: "Not Started",
    aiStatus: "Not Started",
    dataScienceStatus: "Not Started",
    exitCriteria: [
      "Insights dashboard working",
      "Audit trail accessible",
      "Governance controls functional",
      "Autonomy levels manageable",
    ],
    evidence: "Specified in Constitution, Ring 8 not complete",
  },
  {
    number: 10,
    name: "Legal V1",
    purpose: "End-to-end integration, evaluation, and demo",
    whyNow: "All capabilities ready, need integrated demonstration",
    dependencies: "Rings 0-9",
    classification: "[SHARED]",
    capabilities: [
      "End-to-end Legal V1 system",
      "Integrated testing",
      "Evaluation against unseen corpus",
      "Demo preparation",
    ],
    implementationStatus: "Not Started",
    backendStatus: "Not Started",
    frontendStatus: "Not Started",
    aiStatus: "Not Started",
    dataScienceStatus: "Not Started",
    exitCriteria: [
      "End-to-end Legal V1 flow working",
      "All Ring 0-9 exit criteria met",
      "Evaluation metrics meet thresholds",
      "Demo successful",
      "Architecture validated for domain expansion",
    ],
    evidence: "Specified in Constitution, Rings 0-9 not complete",
  },
  {
    number: 11,
    name: "Future Domains",
    purpose: "Sales, HR, Finance, etc. reusing General Brain",
    whyNow: "Legal V1 proves architecture",
    dependencies: "Ring 10",
    classification: "[DOMAIN]",
    capabilities: [
      "Domain modules for Sales, HR, Finance, etc.",
      "Domain-specific knowledge loading",
      "Domain-specific evaluation",
    ],
    implementationStatus: "Not Started",
    backendStatus: "Not Started",
    frontendStatus: "Not Started",
    aiStatus: "Not Started",
    dataScienceStatus: "Not Started",
    exitCriteria: [
      "New domain can be added without Brain rebuild",
      "Domain isolation verified",
      "Domain evaluation meets baseline",
    ],
    evidence: "Specified in Constitution as future scope",
  },
];

const ARCHITECTURAL_INVARIANTS = [
  {
    number: 1,
    invariant: "General Brain capabilities must remain reusable",
    rationale: "No domain-specific logic in General Brain components without architectural review",
    enforcement: "Code review, architectural review",
    currentStatus: "Maintained - Backend and AI packages are domain-agnostic",
    evidence: "ai/ package is provider-agnostic, backend has no legal-specific code",
  },
  {
    number: 2,
    invariant: "Domain logic must not leak into General Brain",
    rationale: "Domain adapters are the only acceptable mechanism",
    enforcement: "Code review, architectural review",
    currentStatus: "Maintained - No legal code in General Brain components",
    evidence: "backend/ contains only foundation, no legal domain logic",
  },
  {
    number: 3,
    invariant: "Organization-specific logic must not become hardcoded domain logic",
    rationale: "Organization configuration must remain configurable",
    enforcement: "Ring 4 implementation",
    currentStatus: "Not Applicable - Ring 4 not started",
    evidence: "Ring 4 will implement configurable organization settings",
  },
  {
    number: 4,
    invariant: "Legal must remain a Domain Module, not a separate Brain",
    rationale: "Legal is the first domain, not a separate product",
    enforcement: "Architectural review",
    currentStatus: "Maintained - Legal not implemented yet",
    evidence: "Constitution explicitly states this",
  },
  {
    number: 5,
    invariant: "AI Employees operate on top of the Brain",
    rationale: "AI Employees are role-specific workers, not separate intelligence systems",
    enforcement: "Implementation design",
    currentStatus: "Not Applicable - AI Employees not implemented",
    evidence: "Specified in Constitution",
  },
  {
    number: 6,
    invariant: "CRM is an operational system, not organizational memory",
    rationale: "The Brain observes and learns from CRM but does not replace it",
    enforcement: "Integration design",
    currentStatus: "Not Applicable - CRM not integrated",
    evidence: "Constitution and decisions.md D-006",
  },
  {
    number: 7,
    invariant: "Observation is not automatically Knowledge",
    rationale: "The learning loop must distinguish observation from knowledge",
    enforcement: "Implementation design, data model",
    currentStatus: "Maintained - Source Ingestion stores raw sources, not knowledge",
    evidence: "docs/source-ingestion.md documents the pipeline",
  },
  {
    number: 8,
    invariant: "Candidate Knowledge is not Trusted Knowledge",
    rationale: "Human validation is required before promotion",
    enforcement: "Ring 8 implementation",
    currentStatus: "Not Applicable - Validation not implemented",
    evidence: "Specified in Constitution",
  },
  {
    number: 9,
    invariant: "Human validation is required according to governance policy",
    rationale: "The Brain cannot auto-validate its own knowledge",
    enforcement: "Ring 8 implementation",
    currentStatus: "Not Applicable - Validation not implemented",
    evidence: "Specified in Constitution",
  },
  {
    number: 10,
    invariant: "AI autonomy must be permission-controlled",
    rationale: "Autonomy levels are organization-controlled",
    enforcement: "Ring 4 and Ring 9 implementation",
    currentStatus: "Not Applicable - Autonomy not implemented",
    evidence: "Specified in Constitution",
  },
  {
    number: 11,
    invariant: "Every important knowledge item must maintain provenance",
    rationale: "Source, validation history, and chain must be tracked",
    enforcement: "Data model, implementation",
    currentStatus: "Foundation laid - Source model includes provenance fields",
    evidence: "Source model has checksum_sha256, uploaded_by, created_at",
  },
  {
    number: 12,
    invariant: "Conflicts must be detectable and traceable",
    rationale: "Conflict detection must be implemented and auditable",
    enforcement: "Ring 7 implementation",
    currentStatus: "Not Applicable - Conflict detection not implemented",
    evidence: "Specified in Constitution",
  },
  {
    number: 13,
    invariant: "Case-specific knowledge must remain separated from general organizational knowledge",
    rationale: "Case isolation is mandatory",
    enforcement: "Data model, query filtering, tests",
    currentStatus: "Not Applicable - Case model not implemented",
    evidence: "Specified in Constitution",
  },
  {
    number: 14,
    invariant: "Multiple cases belonging to the same client must never be mixed",
    rationale: "Case isolation applies even for the same client",
    enforcement: "Data model, query filtering, tests",
    currentStatus: "Not Applicable - Case model not implemented",
    evidence: "Specified in Constitution",
  },
  {
    number: 15,
    invariant: "Permissions must be enforced server-side",
    rationale: "Frontend permissions are presentation controls, not security controls",
    enforcement: "Backend middleware, dependency injection",
    currentStatus: "Partially implemented - Auth dependencies defined but not mounted",
    evidence: "backend/app/api/deps.py has get_current_user (blocked by conflicts)",
  },
  {
    number: 16,
    invariant: "Frontend permissions are presentation controls, not security controls",
    rationale: "Security must be enforced at the server level",
    enforcement: "Frontend implementation, backend enforcement",
    currentStatus: "Not Applicable - Frontend not connected to backend",
    evidence: "Specified in Constitution",
  },
  {
    number: 17,
    invariant: "AI outputs must be auditable where appropriate",
    rationale: "Important AI decisions must be logged",
    enforcement: "Logging implementation",
    currentStatus: "Not Applicable - AI outputs not logged",
    evidence: "Specified in Constitution",
  },
  {
    number: 18,
    invariant: "No Ring may silently redefine shared architecture",
    rationale: "Architectural changes require documentation and review",
    enforcement: "ADR process, code review",
    currentStatus: "Maintained - No architectural changes without documentation",
    evidence: "decisions.md and ADRs documented",
  },
  {
    number: 19,
    invariant: "No team should duplicate an existing General Brain capability",
    rationale: "Reuse is mandatory before building new",
    enforcement: "Code review, architectural review",
    currentStatus: "Maintained - AI package provides reusable provider abstraction",
    evidence: "ai/ package implements provider-agnostic interface",
  },
  {
    number: 20,
    invariant: "New Domain Modules should reuse existing Brain infrastructure",
    rationale: "Domain expansion should not require Brain rebuild",
    enforcement: "Architectural review",
    currentStatus: "Not Applicable - No domains implemented yet",
    evidence: "Specified in Constitution",
  },
];

const OPEN_DECISIONS = [
  {
    id: "OPEN-2",
    question: "Which CRM product for the required integration?",
    impact: "Ring 6 (Observation/WhatsApp) and Ring 7 (Reasoning) depend on CRM integration",
    evidence: "decisions.md D-006 states 'A CRM integration is required (which product: see OPEN-2)'",
    status: "Open",
  },
  {
    id: "OPEN-3",
    question: "Which file/object storage for uploaded documents?",
    impact: "Source Ingestion currently uses LocalStorageBackend, needs production decision",
    evidence: "decisions.md OPEN-3: 'File/object storage for uploaded documents (not chosen)'",
    status: "Open",
  },
  {
    id: "OPEN-4",
    question: "Which LLM provider and embedding model?",
    impact: "Rings 1-10 all depend on LLM provider and embedding model selection",
    evidence: "decisions.md OPEN-4: 'LLM provider and embedding model. The Constitution says OpenAI or local; nothing is chosen'",
    status: "Open",
  },
  {
    id: "OPEN-5",
    question: "Frontend contract - who builds which consumer and when?",
    impact: "API contracts (starting with auth) must be agreed before consumers build",
    evidence: "decisions.md OPEN-5: 'The team repository has two API consumers: a React web dashboard and a Flutter mobile app. Who builds which, and when each needs authentication, is NOT confirmed'",
    status: "Open",
  },
  {
    id: "OPEN-7",
    question: "Repository layout and where the Python backend lives?",
    impact: "Cannot push to remote until this is decided",
    evidence: "decisions.md OPEN-7: 'How the Python backend, its migrations, tests, Docker setup and these docs fit into the team's folders'",
    status: "Open",
  },
];

const CONTRADICTIONS = [
  {
    location: "AGENTS.md",
    issue: "Merge conflict markers in safety rules section (lines 37-48)",
    details: "Contains <<<<<<< HEAD / ======= / >>>>>>> origin/main conflict markers",
    impact: "Documentation inconsistency, does not affect runtime",
    severity: "Low",
    evidence: "Direct observation of file content",
  },
  {
    location: "docs/backend/progress.md vs docs/progress.md",
    issue: "Progress tracking duplicated across two files",
    details: "backend/progress.md has detailed Ring 0 task status; root progress.md has high-level status",
    impact: "Confusion about which progress document is authoritative",
    severity: "Low",
    evidence: "Both files exist with overlapping content",
  },
  {
    location: "README.md vs backend/decisions.md",
    issue: "README describes Node/Prisma scaffold, but backend uses Python/FastAPI",
    details: "README: 'backend/prisma (Node/TypeScript scaffold)', decisions.md D-001: 'Python 3.12, FastAPI... Not used: Node, Express, Prisma'",
    impact: "README is outdated, conflicts with actual implementation",
    severity: "Medium",
    evidence: "README is team repository document, decisions.md is authoritative",
  },
  {
    location: "README.md vs docker-compose.yml",
    issue: "README lists Redis, Neo4j, MinIO, but decisions.md states Neo4j not adopted for V1",
    details: "README: 'docker-compose with PostgreSQL + pgvector, Redis, Neo4j, MinIO', decisions.md D-003: 'Neo4j is NOT adopted for V1'",
    impact: "README suggests infrastructure not used in V1",
    severity: "Medium",
    evidence: "README is outdated, decisions.md is authoritative",
  },
  {
    location: "Constitution vs backend implementation",
    issue: "Constitution's IMPLEMENTATION GUIDANCE sections describe Node/Express/Prisma",
    details: "Constitution has detailed Node.js implementation guidance for all Rings",
    impact: "None for backend - overridden by decisions.md D-002",
    severity: "None",
    evidence: "decisions.md D-002: 'The Constitution's IMPLEMENTATION GUIDANCE & TOOLS sections do NOT apply'",
  },
  {
    location: "frontend/web_app/app/api/auth/login/route.ts vs backend/app/api/v1/auth.py",
    issue: "Frontend implements simulated cookie auth, backend implements JWT auth",
    details: "Frontend: HMAC-signed HTTP-only session cookie, no user database; Backend: JWT Bearer token, PostgreSQL user lookup",
    impact: "API contract mismatch, frontend not connected to backend",
    severity: "High",
    evidence: "Direct code inspection of both files",
  },
];

const GIT_STATE = {
  currentBranch: "main",
  currentCommit: "318683ef",
  commitMessage: "Add retrieval evaluation metrics and documentation",
  remoteStatus: "Aligned with origin/main",
  workingTreeStatus: "Clean",
  backupBranches: [
    { name: "backup-before-recovery-2026-10-13", commit: "08659997" },
    { name: "backup-recovered-work", commit: "08659997" },
    { name: "fix/resolve-committed-conflicts", commit: "38151563" },
    { name: "recover-my-lost-work", commit: "318683ef" },
    { name: "recovery-before-pull", commit: "38151563" },
    { name: "restore-3148170f", commit: "3148170f" },
  ],
  stashes: [
    { name: "stash@{0}", description: "backup before pull recovery" },
    { name: "stash@{1}", description: "backup-before-reset" },
    { name: "stash@{2}", description: "backup before syncing origin main" },
  ],
  worktrees: [
    {
      path: "/tmp/brain-co-webapp-test",
      status: "Prunable (directory no longer exists)",
    },
  ],
  recoveryTimeline: "Git recovery incident occurred 2026-10-12 to 2026-10-13. Frontend/backend/AI integration work at commit 3148170f was recovered via branches restore-3148170f and recovery-before-pull. Current main was reset to origin/main at 318683ef. No work was permanently lost - all recoverable work remains in backup branches and reflog.",
  evidence: "git log, git branch, git reflog inspection",
};

const IMPLEMENTATION_STATUS = {
  backend: {
    framework: "FastAPI (Python 3.12)",
    database: "PostgreSQL 17 with pgvector extension",
    orm: "SQLAlchemy 2.0.54 (synchronous)",
    migrations: "Alembic 1.20.0",
    authentication: "Argon2id password hashing, PyJWT HS256 tokens",
    tables: ["users (migration 778be99882b6)", "sources (migration e819b932c01a)"],
    endpoints: [
      "GET /health (implemented, tested)",
      "GET /api/v1/health/db (implemented, tested)",
      "POST /api/v1/auth/login (written, not mounted)",
      "GET /api/v1/auth/me (written, not mounted)",
      "POST /api/v1/sources (written, not mounted)",
    ],
    blockers: [
      "Merge conflicts in config.py, deps.py, v1/__init__.py, errors.py",
      "Prevents Alembic execution",
      "Prevents endpoint mounting",
      "Prevents backend test execution",
    ],
    tests: "Comprehensive test suite written, blocked by conflicts",
    evidence: "backend/progress.md, docs/source-ingestion.md",
  },
  ai: {
    language: "Python 3.12",
    architecture: "Provider-agnostic async foundation",
    providers: [
      "OpenAI",
      "DeepSeek",
      "OpenRouter",
      "Kimi (Moonshot AI)",
      "Ollama",
      "FakeLLMProvider (for testing)",
    ],
    tests: "54 passing unit tests",
    integration: "Backend integration dependency injection written, blocked by conflicts",
    evidence: "ai/README.md, ai/tests/",
  },
  dataEngineering: {
    pipeline: "Foundational Source Ingestion Pipeline",
    components: [
      "Validation (PDF/TXT, max 50MB)",
      "SHA-256 fingerprinting",
      "Raw storage abstraction",
      "LocalStorageBackend implementation",
      "Orchestration pipeline",
    ],
    tests: "24 passing unit tests",
    fixtures: "Deterministic evaluation fixtures created",
    integration: "Backend Source model and service written, migration written",
    evidence: "docs/source-ingestion.md, data-engineering/tests/",
  },
  dataScience: {
    evaluation: "Retrieval evaluation metrics implemented",
    metrics: ["Precision@k", "Recall@k", "MRR", "NDCG@k"],
    retrieval: "Not implemented (metrics foundation only)",
    models: "Not implemented",
    evidence: "data-science/evaluation/README.md",
  },
  frontend: {
    framework: "Next.js 16.4.0, React 19.3.0, TypeScript",
    styling: "Tailwind CSS 4",
    state: "React Hook Form, Zod",
    authentication: "Simulated cookie-based auth (not connected to backend)",
    components: "Marketing pages, login, onboarding, workspace",
    status: "Substantial but disconnected from backend",
    evidence: "frontend/web_app/README.md, code inspection",
  },
  mobile: {
    framework: "Flutter",
    architecture: "Clean Architecture + BLoC",
    status: "Not investigated in detail",
    evidence: "README.md mentions Flutter mobile app",
  },
  infrastructure: {
    docker: "Docker Compose",
    postgresql: "pgvector/pgvector:pg17 container",
    neo4j: "neo4j:5-community container (prepared for future use)",
    redis: "Listed in README but not used in V1",
    minio: "Listed in README but not used in V1",
    evidence: "docker-compose.yml, decisions.md D-003, D-015",
  },
};

const KNOWLEDGE_LIFECYCLE = [
  { stage: "Raw Observation", description: "Unprocessed input" },
  { stage: "Structured Observation", description: "Parsed and categorized" },
  { stage: "Extracted Fact", description: "Meaningful information extracted" },
  { stage: "Case/Organization Update", description: "Contextual update" },
  { stage: "Knowledge Candidate", description: "Proposed knowledge awaiting review" },
  { stage: "Validation", description: "Human review and approval" },
  { stage: "Trusted Knowledge", description: "Human-validated organizational knowledge" },
  { stage: "Persistent Memory", description: "Stored in organizational memory" },
  { stage: "Retrieval", description: "Fetched for queries" },
  { stage: "Reasoning", description: "Multi-step reasoning with citations" },
  { stage: "Decision Support/Action", description: "Assist or execute" },
];

const THREE_LAYER_MODEL = [
  {
    layer: "Layer 1: General Brain [GB]",
    purpose: "Reusable intelligence infrastructure",
    capabilities: [
      "Perception Engine",
      "Observation Engine",
      "Knowledge Engine",
      "Memory/Storage Engine",
      "Retrieval Engine",
      "Reasoning Engine",
      "Context Engine",
      "Learning Engine",
      "Validation/Governance Engine",
      "Autonomy Controller",
      "Provenance Engine",
      "Permission/Authorization Engine",
      "Audit Engine",
      "Conflict Detection Engine",
      "Insight Engine",
      "Workflow/Action Engine",
    ],
    implementationStatus: "Foundation in progress (Ring 0)",
  },
  {
    layer: "Layer 2: Domain Intelligence [DOMAIN]",
    purpose: "Domain-specific knowledge and capabilities",
    examples: ["Legal (Egyptian Civil Law)", "Sales", "HR", "Finance", "Customer Support"],
    provides: [
      "Domain Knowledge",
      "Domain Ontology/Taxonomy",
      "Domain terminology",
      "Domain workflows",
      "Domain-specific reasoning patterns",
      "Domain-specific tools",
      "Domain-specific engines (where genuinely required)",
      "Domain-specific evaluation",
      "Domain-specific constraints",
      "Domain-specific document types",
    ],
    implementationStatus: "Not started (Ring 3)",
  },
  {
    layer: "Layer 3: Organization Intelligence [ORG]",
    purpose: "Organization-specific context and learning",
    provides: [
      "Organization policies",
      "Workflows",
      "Roles",
      "Permissions",
      "Employees",
      "Internal procedures",
      "Organizational knowledge",
      "Historical work",
      "Documents",
      "Cases",
      "Conversations",
      "Decisions",
      "Outcomes",
      "Business rules",
      "Templates",
      "Existing systems",
      "CRM data",
      "Operational patterns",
      "Human corrections",
      "Validated organizational knowledge",
    ],
    implementationStatus: "Not started (Ring 4)",
  },
];

const AUTONOMY_LEVELS = [
  {
    level: 0,
    name: "Observe",
    description: "Brain watches and learns, no actions taken, purely passive",
    targetForV1: "Yes",
  },
  {
    level: 1,
    name: "Assist",
    description: "Brain suggests and recommends, human makes decisions",
    targetForV1: "Yes",
  },
  {
    level: 2,
    name: "Execute with Human Approval",
    description: "Brain proposes actions, human approves before execution",
    targetForV1: "No",
  },
  {
    level: 3,
    name: "Authorized Automation",
    description: "Brain executes approved workflows autonomously",
    targetForV1: "No",
  },
];

const CASE_MODEL = {
  hierarchy: [
    "Organization",
    "Client",
    "Case A → Conversations, Documents, Events, Facts, Decisions, Knowledge",
    "Case B → Different Conversations, Documents, Facts, Knowledge",
  ],
  invariants: [
    "Cases are first-class objects",
    "Cases must remain isolated",
    "Knowledge from Case A must NEVER leak into Case B",
    "This applies even for the same client",
    "Conversations belong to cases",
    "Three-Level Knowledge Distinction: General Legal Knowledge, Organization Knowledge, Case Knowledge",
  ],
  stateModel: ["New", "Active", "In Progress", "Resolved", "Archived"],
  implementationStatus: "Not started (Ring 5)",
  evidence: "Constitution, requirements.md",
};

export default function ProjectContextReport() {
  const [activeTab, setActiveTab] = useState("executive");
  const theme = useHostTheme();

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">{REPORT_METADATA.title}</CardTitle>
          <CardDescription>
            <div className="space-y-1 mt-2">
              <p><strong>Repository:</strong> {REPORT_METADATA.repository}</p>
              <p><strong>Remote:</strong> {REPORT_METADATA.remote}</p>
              <p><strong>Investigation Date:</strong> {REPORT_METADATA.investigationDate}</p>
              <p><strong>Mode:</strong> {REPORT_METADATA.mode}</p>
              <p><strong>Version:</strong> {REPORT_METADATA.version}</p>
            </div>
          </CardDescription>
        </CardHeader>
      </Card>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="executive">Executive</TabsTrigger>
          <TabsTrigger value="rings">Rings</TabsTrigger>
          <TabsTrigger value="architecture">Architecture</TabsTrigger>
          <TabsTrigger value="implementation">Implementation</TabsTrigger>
          <TabsTrigger value="contradictions">Issues</TabsTrigger>
          <TabsTrigger value="decisions">Decisions</TabsTrigger>
        </TabsList>

        <TabsContent value="executive" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Executive Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">Project Identity</h3>
                <p className="text-sm">
                  <strong>Brain-Co</strong> is an Enterprise Intelligence Platform that transforms an organization's scattered knowledge into governed, validated organizational memory. The system is NOT a chatbot, CRM, RAG application, or collection of independent AI agents. It is a <strong>reusable General Brain</strong> that can be specialized by domain and customized by organization.
                </p>
              </div>

              <Separator />

              <div>
                <h3 className="font-semibold mb-2">Current State</h3>
                <p className="text-sm">
                  The project is in <strong>Ring 0 (Foundation)</strong> implementation phase. The backend is approximately 60% complete through Ring 0 tasks T1-T6, but blocked by pre-existing Git merge conflicts in critical files. The AI package is complete with 54 passing tests. Data engineering has a foundational Source Ingestion Pipeline with 24 passing tests. The frontend is substantial but uses simulated authentication and is not connected to the backend.
                </p>
              </div>

              <Separator />

              <div>
                <h3 className="font-semibold mb-2">Critical Blocker</h3>
                <p className="text-sm">
                  <strong>Git merge conflicts</strong> in <code>backend/app/core/config.py</code>, <code>backend/app/api/deps.py</code>, <code>backend/app/api/v1/__init__.py</code>, and <code>backend/app/core/errors.py</code> prevent Alembic execution, endpoint mounting, and backend test execution. These conflicts were left untouched per investigation policy and must be resolved before Ring 0 can proceed.
                </p>
              </div>

              <Separator />

              <div>
                <h3 className="font-semibold mb-2">Key Architectural Principles</h3>
                <ul className="text-sm space-y-1 list-disc list-inside">
                  <li>One General Brain reused across domains and organizations</li>
                  <li>Three-layer separation: General Brain → Domain Intelligence → Organization Intelligence</li>
                  <li>Observation ≠ Knowledge (not every message becomes organizational knowledge)</li>
                  <li>Human governance required (Brain cannot self-validate knowledge)</li>
                  <li>Case isolation is mandatory (knowledge from Case A never leaks to Case B)</li>
                  <li>Permissions enforced server-side (frontend hiding is cosmetic, not security)</li>
                  <li>Gradual autonomy (Observe → Assist → Execute with Approval → Authorized Automation)</li>
                </ul>
              </div>

              <Separator />

              <div>
                <h3 className="font-semibold mb-2">First Domain: Legal (Egyptian Civil Law)</h3>
                <p className="text-sm">
                  Legal is the first domain implementation, serving as proof that the General Brain architecture works in a high-stakes environment. Legal is NOT a separate Brain—it is a domain specialization. The Constitution specifies 11 Rings (0-10) for complete Legal V1 implementation.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Git State & Recovery</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium">Current Branch</p>
                  <p className="text-sm">{GIT_STATE.currentBranch}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Current Commit</p>
                  <p className="text-sm font-mono">{GIT_STATE.currentCommit}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Commit Message</p>
                  <p className="text-sm">{GIT_STATE.commitMessage}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Remote Status</p>
                  <p className="text-sm">{GIT_STATE.remoteStatus}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Working Tree</p>
                  <p className="text-sm">{GIT_STATE.workingTreeStatus}</p>
                </div>
              </div>

              <Separator />

              <div>
                <h3 className="font-semibold mb-2">Backup Branches (Recoverable Work)</h3>
                <div className="space-y-1">
                  {GIT_STATE.backupBranches.map((branch) => (
                    <div key={branch.name} className="text-sm flex justify-between">
                      <span className="font-mono">{branch.name}</span>
                      <span className="font-mono">{branch.commit}</span>
                    </div>
                  ))}
                </div>
              </div>

              <Separator />

              <div>
                <h3 className="font-semibold mb-2">Stashes</h3>
                <div className="space-y-1">
                  {GIT_STATE.stashes.map((stash) => (
                    <div key={stash.name} className="text-sm">
                      <span className="font-mono">{stash.name}</span>: {stash.description}
                    </div>
                  ))}
                </div>
              </div>

              <Separator />

              <div>
                <h3 className="font-semibold mb-2">Recovery Timeline</h3>
                <p className="text-sm">{GIT_STATE.recoveryTimeline}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Documentation Authority Hierarchy</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Badge variant="default">LEVEL 0</Badge>
                  <span className="text-sm font-medium">Project Constitution</span>
                  <span className="text-sm text-muted-foreground">— Highest authority</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">LEVEL 1</Badge>
                  <span className="text-sm font-medium">Backend Decisions (decisions.md)</span>
                  <span className="text-sm text-muted-foreground">— Overrides Constitution for implementation</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline">LEVEL 2</Badge>
                  <span className="text-sm font-medium">Ring Specifications</span>
                  <span className="text-sm text-muted-foreground">— Current ring spec wins over vision/constitution</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline">LEVEL 3</Badge>
                  <span className="text-sm font-medium">Vision (vision.md)</span>
                  <span className="text-sm text-muted-foreground">— Condensed for AI agents</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline">LEVEL 4</Badge>
                  <span className="text-sm font-medium">Constitution (full)</span>
                  <span className="text-sm text-muted-foreground">— Reference when ring spec is silent</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="rings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Ring Architecture Overview</CardTitle>
              <CardDescription>
                Each Ring is a complete, working vertical capability spanning Frontend, Backend, AI, and Data Science.
              </CardDescription>
            </CardHeader>
          </Card>

          {RING_SPECIFICATIONS.map((ring) => (
            <Card key={ring.number}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Ring {ring.number}: {ring.name}</CardTitle>
                  <Badge variant={ring.implementationStatus === "In Progress" ? "default" : ring.implementationStatus === "Not Started" ? "secondary" : "outline"}>
                    {ring.implementationStatus}
                  </Badge>
                </div>
                <CardDescription>{ring.purpose}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm font-medium">Classification</p>
                  <p className="text-sm">{ring.classification}</p>
                </div>

                <div>
                  <p className="text-sm font-medium">Dependencies</p>
                  <p className="text-sm">{ring.dependencies}</p>
                </div>

                <div>
                  <p className="text-sm font-medium">Capabilities Introduced</p>
                  <ul className="text-sm space-y-1 list-disc list-inside">
                    {ring.capabilities.map((cap) => (
                      <li key={cap}>{cap}</li>
                    ))}
                  </ul>
                </div>

                <Separator />

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium">Backend Status</p>
                    <p className="text-sm">{ring.backendStatus}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium">AI Status</p>
                    <p className="text-sm">{ring.aiStatus}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium">Data Science Status</p>
                    <p className="text-sm">{ring.dataScienceStatus}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium">Evidence</p>
                    <p className="text-sm">{ring.evidence}</p>
                  </div>
                </div>

                {ring.exitCriteria && (
                  <>
                    <Separator />
                    <div>
                      <p className="text-sm font-medium">Exit Criteria</p>
                      <ul className="text-sm space-y-1 list-disc list-inside">
                        {ring.exitCriteria.map((criteria) => (
                          <li key={criteria}>{criteria}</li>
                        ))}
                      </ul>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="architecture" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Three-Layer Intelligence Model</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {THREE_LAYER_MODEL.map((layer) => (
                <div key={layer.layer}>
                  <h3 className="font-semibold mb-2">{layer.layer}</h3>
                  <p className="text-sm mb-2">{layer.purpose}</p>
                  {layer.capabilities && (
                    <div className="mb-2">
                      <p className="text-sm font-medium">Capabilities:</p>
                      <ul className="text-sm space-y-1 list-disc list-inside">
                        {layer.capabilities.map((cap) => (
                          <li key={cap}>{cap}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {layer.examples && (
                    <div className="mb-2">
                      <p className="text-sm font-medium">Examples:</p>
                      <p className="text-sm">{layer.examples.join(", ")}</p>
                    </div>
                  )}
                  {layer.provides && (
                    <div className="mb-2">
                      <p className="text-sm font-medium">Provides:</p>
                      <ul className="text-sm space-y-1 list-disc list-inside">
                        {layer.provides.map((prov) => (
                          <li key={prov}>{prov}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <div>
                    <p className="text-sm font-medium">Implementation Status:</p>
                    <p className="text-sm">{layer.implementationStatus}</p>
                  </div>
                  <Separator className="mt-4" />
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Knowledge Lifecycle</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {KNOWLEDGE_LIFECYCLE.map((item, index) => (
                  <div key={item.stage} className="flex items-center gap-2">
                    <Badge variant="outline">{index + 1}</Badge>
                    <span className="text-sm font-medium">{item.stage}</span>
                    <span className="text-sm text-muted-foreground">— {item.description}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Architectural Invariants</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {ARCHITECTURAL_INVARIANTS.map((inv) => (
                <div key={inv.number}>
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant="outline">{inv.number}</Badge>
                    <span className="text-sm font-medium">{inv.invariant}</span>
                  </div>
                  <p className="text-sm text-muted-foreground mb-1">{inv.rationale}</p>
                  <div className="flex items-center gap-2">
                    <span className="text-xs">Enforcement:</span>
                    <span className="text-xs">{inv.enforcement}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs">Status:</span>
                    <Badge variant={inv.currentStatus === "Maintained" ? "default" : "secondary"} className="text-xs">
                      {inv.currentStatus}
                    </Badge>
                  </div>
                  <Separator className="mt-3" />
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Case Model</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm font-medium mb-2">Hierarchy</p>
                <div className="space-y-1">
                  {CASE_MODEL.hierarchy.map((item) => (
                    <p key={item} className="text-sm pl-4 border-l-2">{item}</p>
                  ))}
                </div>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium mb-2">Invariants</p>
                <ul className="text-sm space-y-1 list-disc list-inside">
                  {CASE_MODEL.invariants.map((inv) => (
                    <li key={inv}>{inv}</li>
                  ))}
                </ul>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium mb-2">State Model</p>
                <p className="text-sm">{CASE_MODEL.stateModel.join(" → ")}</p>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium">Implementation Status</p>
                <p className="text-sm">{CASE_MODEL.implementationStatus}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Autonomy Levels</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {AUTONOMY_LEVELS.map((level) => (
                  <div key={level.level} className="flex items-start gap-3">
                    <Badge variant={level.targetForV1 ? "default" : "secondary"}>
                      Level {level.level}
                    </Badge>
                    <div className="flex-1">
                      <p className="text-sm font-medium">{level.name}</p>
                      <p className="text-sm text-muted-foreground">{level.description}</p>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {level.targetForV1 ? "V1 Target" : "Post-V1"}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="implementation" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Backend Implementation Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium">Framework</p>
                  <p className="text-sm">{IMPLEMENTATION_STATUS.backend.framework}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Database</p>
                  <p className="text-sm">{IMPLEMENTATION_STATUS.backend.database}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">ORM</p>
                  <p className="text-sm">{IMPLEMENTATION_STATUS.backend.orm}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Migrations</p>
                  <p className="text-sm">{IMPLEMENTATION_STATUS.backend.migrations}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Authentication</p>
                  <p className="text-sm">{IMPLEMENTATION_STATUS.backend.authentication}</p>
                </div>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium mb-2">Database Tables</p>
                <ul className="text-sm space-y-1 list-disc list-inside">
                  {IMPLEMENTATION_STATUS.backend.tables.map((table) => (
                    <li key={table}>{table}</li>
                  ))}
                </ul>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium mb-2">Endpoints</p>
                <ul className="text-sm space-y-1 list-disc list-inside">
                  {IMPLEMENTATION_STATUS.backend.endpoints.map((endpoint) => (
                    <li key={endpoint}>{endpoint}</li>
                  ))}
                </ul>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium mb-2">Blockers</p>
                <ul className="text-sm space-y-1 list-disc list-inside text-red-600">
                  {IMPLEMENTATION_STATUS.backend.blockers.map((blocker) => (
                    <li key={blocker}>{blocker}</li>
                  ))}
                </ul>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium">Tests</p>
                <p className="text-sm">{IMPLEMENTATION_STATUS.backend.tests}</p>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium">Evidence</p>
                <p className="text-sm">{IMPLEMENTATION_STATUS.backend.evidence}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>AI Package Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium">Language</p>
                  <p className="text-sm">{IMPLEMENTATION_STATUS.ai.language}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Architecture</p>
                  <p className="text-sm">{IMPLEMENTATION_STATUS.ai.architecture}</p>
                </div>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium mb-2">Providers</p>
                <ul className="text-sm space-y-1 list-disc list-inside">
                  {IMPLEMENTATION_STATUS.ai.providers.map((provider) => (
                    <li key={provider}>{provider}</li>
                  ))}
                </ul>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium">Tests</p>
                <p className="text-sm">{IMPLEMENTATION_STATUS.ai.tests}</p>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium">Integration</p>
                <p className="text-sm">{IMPLEMENTATION_STATUS.ai.integration}</p>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium">Evidence</p>
                <p className="text-sm">{IMPLEMENTATION_STATUS.ai.evidence}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Data Engineering Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm font-medium">Pipeline</p>
                <p className="text-sm">{IMPLEMENTATION_STATUS.dataEngineering.pipeline}</p>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium mb-2">Components</p>
                <ul className="text-sm space-y-1 list-disc list-inside">
                  {IMPLEMENTATION_STATUS.dataEngineering.components.map((component) => (
                    <li key={component}>{component}</li>
                  ))}
                </ul>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium">Tests</p>
                <p className="text-sm">{IMPLEMENTATION_STATUS.dataEngineering.tests}</p>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium">Fixtures</p>
                <p className="text-sm">{IMPLEMENTATION_STATUS.dataEngineering.fixtures}</p>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium">Integration</p>
                <p className="text-sm">{IMPLEMENTATION_STATUS.dataEngineering.integration}</p>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium">Evidence</p>
                <p className="text-sm">{IMPLEMENTATION_STATUS.dataEngineering.evidence}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Data Science Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm font-medium">Evaluation</p>
                <p className="text-sm">{IMPLEMENTATION_STATUS.dataScience.evaluation}</p>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium mb-2">Metrics</p>
                <ul className="text-sm space-y-1 list-disc list-inside">
                  {IMPLEMENTATION_STATUS.dataScience.metrics.map((metric) => (
                    <li key={metric}>{metric}</li>
                  ))}
                </ul>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium">Retrieval</p>
                <p className="text-sm">{IMPLEMENTATION_STATUS.dataScience.retrieval}</p>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium">Models</p>
                <p className="text-sm">{IMPLEMENTATION_STATUS.dataScience.models}</p>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium">Evidence</p>
                <p className="text-sm">{IMPLEMENTATION_STATUS.dataScience.evidence}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Frontend Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium">Framework</p>
                  <p className="text-sm">{IMPLEMENTATION_STATUS.frontend.framework}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Styling</p>
                  <p className="text-sm">{IMPLEMENTATION_STATUS.frontend.styling}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">State</p>
                  <p className="text-sm">{IMPLEMENTATION_STATUS.frontend.state}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Authentication</p>
                  <p className="text-sm">{IMPLEMENTATION_STATUS.frontend.authentication}</p>
                </div>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium">Components</p>
                <p className="text-sm">{IMPLEMENTATION_STATUS.frontend.components}</p>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium">Status</p>
                <p className="text-sm">{IMPLEMENTATION_STATUS.frontend.status}</p>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium">Evidence</p>
                <p className="text-sm">{IMPLEMENTATION_STATUS.frontend.evidence}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Infrastructure Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm font-medium">Docker</p>
                <p className="text-sm">{IMPLEMENTATION_STATUS.infrastructure.docker}</p>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium">PostgreSQL</p>
                <p className="text-sm">{IMPLEMENTATION_STATUS.infrastructure.postgresql}</p>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium">Neo4j</p>
                <p className="text-sm">{IMPLEMENTATION_STATUS.infrastructure.neo4j}</p>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium">Redis</p>
                <p className="text-sm">{IMPLEMENTATION_STATUS.infrastructure.redis}</p>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium">MinIO</p>
                <p className="text-sm">{IMPLEMENTATION_STATUS.infrastructure.minio}</p>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium">Evidence</p>
                <p className="text-sm">{IMPLEMENTATION_STATUS.infrastructure.evidence}</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="contradictions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Documentation Contradictions & Issues</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {CONTRADICTIONS.map((contradiction, index) => (
                <div key={index}>
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant={contradiction.severity === "High" ? "destructive" : contradiction.severity === "Medium" ? "default" : "secondary"}>
                      {contradiction.severity}
                    </Badge>
                    <span className="text-sm font-medium">{contradiction.location}</span>
                  </div>
                  <p className="text-sm mb-1">{contradiction.issue}</p>
                  <p className="text-sm text-muted-foreground mb-1">{contradiction.details}</p>
                  <p className="text-sm text-muted-foreground mb-1">Impact: {contradiction.impact}</p>
                  <p className="text-xs text-muted-foreground">Evidence: {contradiction.evidence}</p>
                  <Separator className="mt-3" />
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="decisions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Open Decisions Requiring Human Input</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {OPEN_DECISIONS.map((decision) => (
                <div key={decision.id}>
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="outline">{decision.id}</Badge>
                    <Badge>{decision.status}</Badge>
                  </div>
                  <p className="text-sm font-medium mb-1">{decision.question}</p>
                  <p className="text-sm text-muted-foreground mb-1">Impact: {decision.impact}</p>
                  <p className="text-xs text-muted-foreground">Evidence: {decision.evidence}</p>
                  <Separator className="mt-3" />
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Documentation Inventory</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {DOCUMENTATION_INVENTORY.map((doc) => (
                  <div key={doc.path} className="border-l-2 pl-3">
                    <p className="text-sm font-medium">{doc.title}</p>
                    <p className="text-xs text-muted-foreground font-mono">{doc.path}</p>
                    <p className="text-sm mt-1">{doc.purpose}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant={doc.authority === "Normative" ? "default" : doc.authority === "Normative (LEVEL 0)" ? "default" : "secondary"} className="text-xs">
                        {doc.authority}
                      </Badge>
                      <Badge variant={doc.status === "Current" ? "default" : doc.status === "In Progress" ? "default" : "secondary"} className="text-xs">
                        {doc.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">Evidence: {doc.evidence}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
