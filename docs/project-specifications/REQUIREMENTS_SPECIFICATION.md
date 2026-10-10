# Requirements Specification
## Organizational Brain — Legal V1 (Egyptian Civil Legal Domain)

---

## 1. Document Control

| Field | Value |
|---|---|
| Document | `REQUIREMENTS_SPECIFICATION.md` |
| Phase | Step 2 — Requirements Analysis |
| Supersedes (for the items below) | `PROJECT_SCOPE.md` (Step 1), wherever this document makes a more specific confirmed decision (see §23 for what changed and why) |
| Status | Baseline for all subsequent design phases |
| Out of scope for this document | Architecture, class diagrams, ERD, component diagrams, deployment design, DFD, WBS/PERT — all deferred to later phases |

**Relationship to Step 1 (`PROJECT_SCOPE.md`):** Step 1 established the product definition (General Brain + Industry Module), Legal as the first module, and the high-level V1 success capabilities (A–L). This document inherits all of that and adds the specific operating model that has since been confirmed: WhatsApp as the primary observation channel, the Client → Case → Conversation domain model, Case-centric (not only document-centric) knowledge acquisition, and the Egyptian Civil Legal domain as the specific V1 legal scope. Where Step 1 spoke generically about "a legal organization" and "documents," this document narrows that to the specific confirmed model without expanding the overall V1 boundary set in Step 1.

---

## 2. Purpose

This document specifies **what** the Organizational Brain — Legal V1 system must do: its actors, functional behavior, data/knowledge concepts, constraints, and testable acceptance criteria. It does not specify **how** the system is built. It is the baseline from which Actors, Use Cases, Use Case Specifications, Context Diagram, Activity/State/Sequence Diagrams, Domain/Class Model, ERD, Architecture, Components, Deployment, DFD, WBS/PERT, and the implementation plan will be derived in later phases, without needing to reinterpret the project's core behavior or philosophy.

---

## 3. Project Context

Organizational Brain is a graduation project building a persistent, governed organizational intelligence layer. It has already passed through conceptual analysis and scope definition (Step 1). This document is Step 2. It builds on, and does not redefine, the following already-established decisions:

- The product is **General Organizational Brain + Industry Module**, not a chatbot, CRM, ERP, document management system, vector database, RAG application, or a collection of disconnected AI agents.
- **Legal is the first and only industry module in current scope.**
- V1 is a **functional, integrated, end-to-end proof of the vision** at prototype scale — not a production-scale system, and not a system that fakes behavior it doesn't actually run.

This document adds the operating model and domain specifics that make those commitments concrete and testable.

---

## 4. System Vision

> The organization should have a persistent, governed intelligence layer that understands what is happening, remembers what happened, assists people with what they need, and learns from validated organizational experience.

The Brain is not a single feature. It is a lifecycle: it **observes** organizational activity, **understands** context, builds and maintains **Cases**, maintains **persistent memory**, **retrieves** relevant knowledge, **reasons** over available evidence, **assists** organizational actors, **detects** missing information and conflicts, **requests human clarification/validation** when necessary, maintains **provenance and history**, **learns** from validated organizational experience, supports **controlled actions**, **observes outcomes**, and progressively develops organizational intelligence.

---

## 5. System Boundary

### What is the Organizational Brain?
The Brain is the intelligence layer: observation processing, Client/Case context modeling, memory, knowledge validation and storage, retrieval, reasoning, conflict detection, governance enforcement, learning, and the AI Employee capability layer built on top of all of it.

### What belongs inside the Brain?
- Observation ingestion and buffering logic
- Client and Case domain model and lifecycle
- Case Memory and Organizational Knowledge stores
- Retrieval and reasoning over the Legal Knowledge Corpus and Case Memory
- Conflict detection and the human-resolution workflow
- Governance/authority/permission enforcement
- The Learning loop (observation → candidate → validation → knowledge)
- The AI Employee capability layer (Legal AI Employee for V1)
- Audit and provenance records for Brain-internal actions

### What is external to the Brain?
The Brain interacts with the following through **defined interfaces/integrations**, rather than owning them:
- **WhatsApp** (primary observation and interaction channel)
- **CRM** (operational system of record for client/case operational state)
- Document sources (uploaded/received legal and case documents)
- External legal sources (statutes, regulations, judicial decisions)
- Employees (lawyers, reviewers, managers, CEO/GM)
- Clients (the organization's own clients)
- Other organizational systems, where applicable

"Outside the system" does not mean "irrelevant" — the Brain depends on and exchanges data with these entities through explicit boundaries (§12.12, §33–34), but does not internally implement them (e.g., the Brain does not implement WhatsApp messaging or the CRM's operational record-keeping).

### System Boundary vs. Business Domain
The **system boundary** is an architectural/integration concept (what the Brain owns vs. exchanges data with). The **business domain** (§6) is *what real-world subject matter* the Brain currently reasons about (Egyptian Civil Legal practice). These are independent: the system boundary would remain structurally the same if the business domain changed to a different industry module in the future.

---

## 6. V1 Domain

```
Organizational Brain
        ↓
General intelligence / memory / governance / learning
        ↓
Legal Module V1
        ↓
Egyptian Civil Legal Domain
```

The current V1 implementation domain is **Legal**, specifically the **Egyptian Civil Legal Domain**. The initial real-world organization modeled is conceptually a legal organization / law firm. The Legal Module is the first concrete domain implementation used to demonstrate the general Organizational Brain — it is not the entire product, and its functionality must not be duplicated inside the General Brain (§7).

---

## 7. Scope

V1 must demonstrate, as real running behavior:

1. Observation of real organizational interaction via WhatsApp (§10, §12.1).
2. Client identification/creation and Case creation, with Client ≠ Case as an enforced invariant (§11, §12.2–12.3).
3. Progressive Case understanding maintained as persistent Case Memory (§15, §21, §12.4–12.5).
4. Detection of missing information and conflicting information, with human clarification/validation in the loop (§17–18, §12.7).
5. Retrieval and reasoning over a bounded Egyptian Civil Legal Knowledge Corpus, with citations and source authority (§25–29, §12.9).
6. Case Similarity and Case Classification as real ML capabilities (§36, §12.14).
7. A Legal AI Employee operating on the shared Brain under explicit permissions and autonomy levels (§31–32, §12.10–12.11).
8. Real integration with WhatsApp and at least one operational external system (CRM) (§33–34, §12.12).
9. Case Report generation that reconstructs Case context without manual re-reading (§22, §12.15).
10. A learning loop that converts validated observations into Organizational Knowledge without silently generalizing unvalidated Case data (§23, §35, §12.13).
11. A separate, unseen Evaluation Corpus used to assess the above (§30, §12.16).

## 8. Out of Scope

The following are explicitly **not** part of V1 (see also §45 "What V1 Is NOT"):

- A complete Egyptian legal database, or coverage of legal domains beyond Civil Law
- Legal outcome / case-result prediction (explicitly deferred; not silently added under "analysis")
- A complete ERP or a CRM replacement — the CRM remains external and operational
- Fully autonomous action execution for capabilities not explicitly marked Autonomous (§32)
- Support for organizational domains other than Legal
- Large-scale, multi-organization production deployment
- Any redefinition of the Brain as a generic chatbot or a purely retrieval (RAG-only) system

---

## 9. Actors and External Entities

### Human Actors
| Actor | Role summary |
|---|---|
| **Client** | The organization's own client; source of Case-originating interactions, primarily via WhatsApp. |
| **Lawyer** | Primary case-handling employee; interacts with Cases, supplies clarifications, makes decisions. |
| **Knowledge Reviewer** | Authorized to validate Candidate Knowledge into Trusted/Organizational Knowledge; resolves detected conflicts. |
| **Manager** | Organizational oversight; consumes organizational-level intelligence (§38) without unrestricted access to individual Case data. |
| **CEO/GM** | Highest organizational governance authority (§19); can delegate validation authority. |
| **Admin** | Organization/user/role administration (inherited from Step 1's RBAC model). |

### System / AI Actors
| Actor | Role summary |
|---|---|
| **Organizational Brain (General)** | The reusable core: observation, memory, knowledge, retrieval, reasoning, governance, learning. |
| **Legal AI Employee** | Role/capability layer over the shared Brain, specialized for Legal (§31). |

### External Entities (Integrated, Not Owned)
| Entity | Nature of exchange |
|---|---|
| **WhatsApp** | Primary real-time observation and Client/Lawyer interaction channel (§10, §33). |
| **CRM** | Operational system of record; exchanges Client/Case/operational data with the Brain (§33–34). |
| **External Legal Sources** | Egyptian Civil Code and related legislation/judicial decisions ingested into the bounded Legal Knowledge Corpus (§25–26). |
| **Document Sources** | Case-related documents supplied by Clients/Lawyers. |

---

## 10. Brain Operating Model

### 10.1 Core Operating Loop
```
OBSERVE → UNDERSTAND → IDENTIFY CONTEXT → CREATE/UPDATE CASE →
DETECT MISSING INFORMATION → DETECT UNCERTAINTY/CONFLICT →
ASK HUMAN WHEN REQUIRED → VALIDATE → REMEMBER → RETRIEVE →
REASON/ANALYZE → ASSIST → PROPOSE/EXECUTE AUTHORIZED ACTION →
OBSERVE OUTCOME → FEEDBACK → LEARNING → VALIDATED ORGANIZATIONAL KNOWLEDGE
```
Every functional requirement in §12 must be traceable to one or more stages of this loop.

### 10.2 Observation Processing Model
```
WhatsApp Message → Real-Time Event → Observation → Buffer → Asynchronous Processing
```
The Brain must **not** trigger expensive full reasoning synchronously on every incoming message. Real-time capture (observation, buffering) is separated from asynchronous understanding/reasoning (§12.1, FR-OBS-*).

### 10.3 Autonomy Maturity Model
```
Observe → Assist → Execute with Approval → Autonomous
```
Autonomy is **capability-specific**, not system-wide. Every action the Brain or an AI Employee can take must have an explicit, assigned authority level from this model (§32, FR-AUTO-*).

---

## 11. Core Concepts and Terminology

| Term | Definition | Explicitly distinct from |
|---|---|---|
| **Observation** | A captured unit of organizational activity (e.g., a WhatsApp message, a document upload) recorded by the Brain. | Knowledge, Learning |
| **Case** | A bounded unit of legal work associated with a Client, containing its own conversations, documents, events, decisions, and actions. | Client, Conversation |
| **Client** | The organizational counterparty (person/entity) the organization serves. A Client may have multiple Cases. | Case (Client ≠ Case) |
| **Conversation** | A sequence of observed interactions (e.g., a WhatsApp thread) associated with a Case. | Case (a Case has conversations; a conversation is not itself a Case) |
| **Case Memory** | Persistent, structured, continuously updated understanding of a specific Case. | Raw Interaction History, Organizational Knowledge |
| **Raw Interaction History** | The unprocessed record of what happened (messages, events) for a Case. | Case Memory (interpreted/structured) |
| **Candidate Pattern** | A possible recurring organizational pattern noticed across one or more Cases, not yet validated. | Organizational Knowledge |
| **Candidate Knowledge** | Potential reusable knowledge (from a Case observation, a legal source, or an employee explanation) awaiting human validation. | Organizational Knowledge, LLM Output |
| **Organizational Knowledge** | Validated, reusable knowledge trusted at the organization level. | Case Memory, Candidate Knowledge |
| **Legal Knowledge** | External/domain knowledge sourced from authoritative Egyptian Civil legal sources, version- and authority-aware. | Organizational Knowledge (internally validated) |
| **LLM Output** | A generated response from the language model. | Trusted organizational fact — never automatically equivalent |
| **Fact / Inference / Uncertainty / Conflict** | Four explicitly distinguishable epistemic states the Brain must be able to represent about any piece of information. | Each other |

**Foundational principles** (elaborated as invariants in §18):
- Observation ≠ Knowledge. Observation ≠ Learning.
- Case-specific information ≠ General Organizational Knowledge.
- LLM response ≠ Trusted organizational fact.
- Client ≠ Case.

---

## 12. Functional Requirements

Each requirement includes: ID, Name, Description, Priority (P0/P1/P2, see §40), Rationale/Source, Dependencies, Acceptance Criteria (Given/When/Then where applicable), Verification Method.

### 12.1 Observation

**FR-OBS-001 — Real-time WhatsApp message capture**
- *Description*: The Brain must capture inbound/outbound WhatsApp messages associated with the organization as real-time Observations.
- *Priority*: P0
- *Rationale/Source*: §10, §33
- *Dependencies*: WhatsApp integration boundary (§12.12)
- *Acceptance Criteria*: Given a WhatsApp message is sent/received on an organization-connected number, When the message arrives, Then an Observation record is created referencing the raw message content, timestamp, and channel within a bounded, documented delay.
- *Verification*: Integration test against a real/sandboxed WhatsApp channel.

**FR-OBS-002 — Observation buffering before reasoning**
- *Description*: Observations must be buffered and processed asynchronously; the Brain must not perform full contextual reasoning synchronously per message.
- *Priority*: P0
- *Rationale/Source*: §10
- *Dependencies*: FR-OBS-001
- *Acceptance Criteria*: Given a burst of N WhatsApp messages arrives in quick succession, When they are captured, Then Observation records are created immediately while reasoning/understanding is performed by a separate asynchronous process, verifiably decoupled in timing from message receipt.
- *Verification*: Load/timing test; architecture trace (non-blocking ingestion).

**FR-OBS-003 — Minimally intrusive observation**
- *Description*: The Brain may observe a Case while a Lawyer is still understanding it, without interrupting normal work, intervening only when a defined trigger condition applies (§16).
- *Priority*: P0
- *Rationale/Source*: §16
- *Dependencies*: FR-CASE-002, FR-CONFLICT-001
- *Acceptance Criteria*: Given a Case with ordinary, non-critical activity, When the Brain observes it, Then no interruption/notification is generated unless a defined trigger (missing critical info, blocking ambiguity, conflict, required validation, or a genuine assistance opportunity) is met.
- *Verification*: Scenario test against defined trigger list.

**FR-OBS-004 — Observation provenance**
- *Description*: Every Observation must record its source, timestamp, and originating actor/channel.
- *Priority*: P0
- *Rationale/Source*: §9, §17, §24
- *Dependencies*: —
- *Acceptance Criteria*: Given any Observation, When it is inspected, Then its source, source type, timestamp, and originating actor/channel are retrievable.
- *Verification*: Data inspection test.

### 12.2 Client Management

**FR-CLIENT-001 — Client identification/creation from observation**
- *Description*: The Brain must be able to identify an existing Client or create a new Client record from observed interaction (e.g., WhatsApp contact), capturing available attributes (name, phone number, channel, and domain-specific fields where relevant).
- *Priority*: P0
- *Rationale/Source*: §11, §14
- *Dependencies*: FR-OBS-001
- *Acceptance Criteria*: Given a new WhatsApp contact initiates interaction, When the Brain processes the Observation, Then a Client record is created or matched, with captured attributes marked with their extraction provenance.
- *Verification*: Scenario test with new and returning contacts.

**FR-CLIENT-002 — Extraction is not automatically validated truth**
- *Description*: Client attributes extracted from Observations must be flagged as unvalidated until confirmed; when ambiguity/uncertainty is material, the Brain must be able to request clarification.
- *Priority*: P0
- *Rationale/Source*: §14
- *Dependencies*: FR-CLIENT-001, FR-CASE-005
- *Acceptance Criteria*: Given an extracted Client attribute with low confidence or ambiguity, When the attribute is material to a downstream action, Then the Brain surfaces a clarification request rather than treating the attribute as confirmed.
- *Verification*: Scenario test with ambiguous input.

**FR-CLIENT-003 — Duplicate Client detection**
- *Description*: The Brain must detect potential duplicate Client records (e.g., same phone number/name variants) and surface them rather than silently merging or silently duplicating.
- *Priority*: P1
- *Rationale/Source*: §43 (duplicate Client)
- *Dependencies*: FR-CLIENT-001
- *Acceptance Criteria*: Given two Client-creation events with matching key identifiers, When both are processed, Then the system flags a potential duplicate for human review rather than auto-merging.
- *Verification*: Scenario test with duplicate data.

### 12.3 Case Management

**FR-CASE-001 — Case creation and Client association**
- *Description*: The Brain must be able to detect a potential Case from Client interaction and create a Case explicitly associated with exactly one Client (a Client may have multiple Cases).
- *Priority*: P0
- *Rationale/Source*: §11, §13
- *Dependencies*: FR-CLIENT-001
- *Acceptance Criteria*: Given a Client interaction that indicates a new legal matter, When the Brain processes it, Then a new Case is created and linked to the Client, distinct from any of the Client's existing Cases.
- *Verification*: Scenario test; DB-level referential check.

**FR-CASE-002 — Case isolation**
- *Description*: Information belonging to one Case must not silently become associated with another Case, even for the same Client.
- *Priority*: P0
- *Rationale/Source*: §12, Invariant #3–4
- *Dependencies*: FR-CASE-001
- *Acceptance Criteria*: Given one Client has Case A and Case B, When the Brain retrieves Case A, Then Case B information must not be returned as Case A information unless an explicit relationship between the Cases is recorded.
- *Verification*: Automated isolation test (mirrors organization-isolation test pattern from Ring 1).

**FR-CASE-003 — Ambiguous Case association**
- *Description*: When an Observation's Case association is unclear, the Brain must represent that uncertainty explicitly rather than guessing silently.
- *Priority*: P0
- *Rationale/Source*: §12, §43
- *Dependencies*: FR-CASE-002
- *Acceptance Criteria*: Given an Observation that could plausibly belong to more than one open Case for the same Client, When the Brain processes it, Then the Observation is marked as Case-ambiguous and surfaced for clarification rather than auto-assigned.
- *Verification*: Scenario test with multi-Case Client.

**FR-CASE-004 — Duplicate Case detection**
- *Description*: The Brain must detect potential duplicate Case creation for the same underlying matter.
- *Priority*: P1
- *Rationale/Source*: §43
- *Dependencies*: FR-CASE-001
- *Acceptance Criteria*: Given interaction patterns suggesting an existing open Case for the same matter, When a new Case would otherwise be created, Then the system flags the potential duplicate for human confirmation.
- *Verification*: Scenario test.

**FR-CASE-005 — Missing information detection**
- *Description*: The Brain must detect information that appears necessary for a Case but is absent (e.g., missing contact, date, document, party identity, decision context) and may request clarification from an authorized actor.
- *Priority*: P0
- *Rationale/Source*: §17
- *Dependencies*: FR-CASE-002
- *Acceptance Criteria*: Given a Case missing an attribute the Brain's Case model marks as expected/necessary, When Case understanding is (re)computed, Then a Missing Information item is recorded, referencing who/when it is eventually supplied.
- *Verification*: Scenario test with incomplete Case data.

### 12.4 Case Understanding

**FR-CASE-UND-001 — Progressive, persistent Case understanding**
- *Description*: The Brain must connect Client, facts, conversations, documents, events, decisions, actions, current state, missing information, conflicts, and relevant knowledge into a continuously updated understanding of the Case — not a single static summary.
- *Priority*: P0
- *Rationale/Source*: §15
- *Dependencies*: FR-CASE-001, FR-MEM-002
- *Acceptance Criteria*: Given new Observations are added to a Case over time, When Case understanding is recomputed, Then previously captured facts/decisions persist and are augmented (not replaced/erased) unless explicitly superseded with a recorded reason.
- *Verification*: Longitudinal scenario test (multi-session Case).

**FR-CASE-UND-002 — Low-intervention observation during lawyer-led understanding**
- *Description*: While a Lawyer is actively working a Case, the Brain builds preliminary context in the background per FR-OBS-003's trigger model.
- *Priority*: P0
- *Rationale/Source*: §16
- *Dependencies*: FR-OBS-003, FR-CASE-UND-001
- *Acceptance Criteria*: Given a Lawyer is actively adding Case information, When the Brain observes in parallel, Then Case context is updated without requiring Lawyer confirmation for non-trigger updates.
- *Verification*: Scenario test.

### 12.5 Memory

**FR-MEM-001 — Memory-type separation**
- *Description*: The system must represent and store Raw Interaction History, Case Memory, Candidate Pattern, Candidate Knowledge, Organizational Knowledge, and Legal Knowledge as distinct, identifiable record types (§20).
- *Priority*: P0
- *Rationale/Source*: §20
- *Dependencies*: —
- *Acceptance Criteria*: Given any stored memory/knowledge item, When its type is queried, Then it is classified as exactly one of the six defined types, each with its own schema/fields.
- *Verification*: Data model inspection.

**FR-MEM-002 — Persistent Case Memory**
- *Description*: The Brain must maintain persistent Case Memory containing Client, Case identity, facts, conversations, documents, events, timeline, decisions, actions, current state, missing information, conflicts, relevant knowledge, outcomes, feedback, and history.
- *Priority*: P0
- *Rationale/Source*: §21
- *Dependencies*: FR-CASE-UND-001
- *Acceptance Criteria*: Given a Case last touched N days/weeks ago, When a Lawyer reopens it, Then the Case's current and historical context is retrievable without manual reconstruction from raw conversations/documents.
- *Verification*: "Cold Case" scenario test.

**FR-MEM-003 — No silent generalization from Case to Organization**
- *Description*: A Case-level observation must not automatically become Organizational Knowledge; it must pass through Candidate Pattern → Candidate Knowledge → human validation.
- *Priority*: P0
- *Rationale/Source*: §23, Invariant #5, #16
- *Dependencies*: FR-KNOW-001, FR-LEARN-001
- *Acceptance Criteria*: Given a single Case exhibits a novel pattern, When the Brain processes it, Then the pattern is recorded as Candidate, not Organizational, Knowledge, until validated.
- *Verification*: Scenario test; data model check.

### 12.6 Knowledge

**FR-KNOW-001 — Candidate vs. Trusted/Organizational Knowledge lifecycle**
- *Description*: The system must implement the lifecycle: Case observation → Candidate pattern → (optionally) Candidate Knowledge → human validation → Trusted Organizational Knowledge.
- *Priority*: P0
- *Rationale/Source*: §23, Step 1 §7(D)
- *Dependencies*: FR-MEM-003, FR-GOV-002
- *Acceptance Criteria*: Given a Candidate Knowledge item, When it has not been explicitly validated, Then it must not be returned by retrieval as Organizational Knowledge (it may be returned separately, clearly labeled as Candidate).
- *Verification*: Retrieval-labeling test.

**FR-KNOW-002 — Knowledge versioning and history**
- *Description*: Knowledge must be versioned; updates must not silently overwrite prior versions. Provenance fields (source, source type, source authority, version, effective date, creation date, validation date, validator, organization, related Case, confidence, conflict history) must be preserved where applicable.
- *Priority*: P0
- *Rationale/Source*: §24
- *Dependencies*: FR-KNOW-001
- *Acceptance Criteria*: Given a Knowledge item is updated, When the update is saved, Then the prior version remains retrievable with its own timestamp and the new version references it.
- *Verification*: Versioning test.

### 12.7 Conflict and Validation

**FR-CONFLICT-001 — Conflict detection**
- *Description*: The Brain must detect conflicting information (e.g., two Lawyers describing different workflows for the same situation) and must not silently pick one side.
- *Priority*: P0
- *Rationale/Source*: §18, Invariant #7
- *Dependencies*: FR-KNOW-001
- *Acceptance Criteria*: Given two pieces of knowledge/evidence that materially conflict, When the Brain processes both, Then a Conflict record is created referencing both pieces of evidence and is routed to an Authorized Reviewer, with no automatic resolution.
- *Verification*: Scenario test with contradictory inputs (mirrors the refund-policy example pattern from Step 1).

**FR-CONFLICT-002 — Conflict resolution history**
- *Description*: The Brain must retain the history of a conflict and its resolution, including who resolved it and when.
- *Priority*: P0
- *Rationale/Source*: §18, §24
- *Dependencies*: FR-CONFLICT-001
- *Acceptance Criteria*: Given a resolved Conflict, When it is inspected later, Then the original conflicting evidence, the resolver, the resolution date, and the resulting Trusted Knowledge are all retrievable.
- *Verification*: Data inspection test.

**FR-GOV-002 — Human validation workflow**
- *Description*: An authorized Knowledge Reviewer must be able to inspect Candidate Knowledge/Conflicts (evidence, source, context, confidence, related/conflicting knowledge) and Approve, Reject, Edit, Request Clarification, Mark as Conflicting, or Supersede.
- *Priority*: P0
- *Rationale/Source*: Step 1 §13, §18
- *Dependencies*: FR-KNOW-001, FR-CONFLICT-001
- *Acceptance Criteria*: Given a pending Candidate Knowledge item, When a Knowledge Reviewer takes any of the defined actions, Then the item's status and the action's audit record update accordingly.
- *Verification*: Workflow test covering all five actions.

### 12.8 Governance

**FR-GOV-001 — Authority model (CEO/GM, delegated authority)**
- *Description*: The system must represent CEO/GM as the highest organizational authority, support delegation of validation authority to authorized actors, and enforce that delegated scope in all governance-gated actions.
- *Priority*: P0
- *Rationale/Source*: §19
- *Dependencies*: Ring 1 RBAC (existing)
- *Acceptance Criteria*: Given an actor with delegated validation authority for a defined scope, When they attempt an action outside that scope, Then the action is rejected.
- *Verification*: Permission-boundary test.

**FR-GOV-003 — No AI self-escalation of authority**
- *Description*: The Brain and AI Employees must never grant themselves permissions, and must never infer authority merely because an action is technically executable.
- *Priority*: P0
- *Rationale/Source*: §19, Invariant #6, #17
- *Dependencies*: FR-AUTO-001
- *Acceptance Criteria*: Given an AI Employee capability that is technically able to perform an action but lacks an explicitly assigned authority level for it, When the action is attempted, Then it is blocked and logged, not executed.
- *Verification*: Negative permission test.

### 12.9 Legal Intelligence

**FR-LEGAL-001 — Bounded Legal Knowledge Corpus**
- *Description*: The system must operate over a defined, bounded Egyptian Civil Legal Knowledge Corpus (Foundation, Civil Legal Sources, Judicial Knowledge) as described in §25, not an unbounded/open legal database.
- *Priority*: P0
- *Rationale/Source*: §25
- *Dependencies*: FR-LEGAL-002
- *Acceptance Criteria*: Given the Legal Knowledge Corpus, When its contents are enumerated, Then every item traces to one of the defined corpus categories with recorded provenance.
- *Verification*: Corpus audit.

**FR-LEGAL-002 — Legal source acquisition with provenance**
- *Description*: Legal source ingestion must be repeatable, provenance-preserving, version-aware, and traceable; scraped/ingested text is not automatically treated as authoritative.
- *Priority*: P0
- *Rationale/Source*: §26
- *Dependencies*: FR-LEGAL-001
- *Acceptance Criteria*: Given a legal source is ingested, When it is queried, Then its source, version, and effective date are retrievable, and its authority status is explicit (not assumed).
- *Verification*: Ingestion audit test.

**FR-LEGAL-003 — Legal retrieval, reasoning, and citation**
- *Description*: The Brain must retrieve relevant legal sources for a Case, interpret them in Case context, connect Case facts + legal provisions + relevant sources + historical Cases + validated organizational knowledge, generate grounded analysis, and cite traceable source references.
- *Priority*: P0
- *Rationale/Source*: §27
- *Dependencies*: FR-LEGAL-001, FR-CASE-UND-001
- *Acceptance Criteria*: Given a Case question requiring legal grounding, When the Brain answers, Then the answer includes at least one traceable citation to the Legal Knowledge Corpus, and is distinguishable from an ungrounded LLM response.
- *Verification*: Grounded-answer scenario test.

**FR-LEGAL-004 — Legal source authority and conflict handling**
- *Description*: When multiple legal sources conflict or carry different authority, the Brain must preserve provenance, expose the conflict, weigh source authority and version/effective date, and request human review where required — never blindly trust retrieval order.
- *Priority*: P0
- *Rationale/Source*: §28
- *Dependencies*: FR-CONFLICT-001, FR-LEGAL-002
- *Acceptance Criteria*: Given two ingested legal sources with conflicting provisions relevant to a query, When the Brain retrieves both, Then both are surfaced with their authority/version metadata rather than one being silently preferred without explanation.
- *Verification*: Conflicting-source scenario test.

**FR-LEGAL-005 — Version / effective-date awareness**
- *Description*: The Brain must track legal source version, effective date, and (where known) current applicability, and must not silently treat outdated legal text as current.
- *Priority*: P0
- *Rationale/Source*: §29
- *Dependencies*: FR-LEGAL-002
- *Acceptance Criteria*: Given a legal source with a known effective-date range that does not cover "now," When the Brain uses it in reasoning, Then the response flags it as historical/non-current rather than presenting it as presently applicable.
- *Verification*: Version-awareness scenario test.

### 12.10 AI Employee

**FR-AI-001 — Legal AI Employee as a role over the shared Brain**
- *Description*: The Legal AI Employee must operate through the shared Organizational Brain (permissions, capabilities, context, allowed actions, autonomy) rather than maintaining an independent knowledge base.
- *Priority*: P0
- *Rationale/Source*: §31
- *Dependencies*: FR-GOV-001, FR-LEGAL-003
- *Acceptance Criteria*: Given the Legal AI Employee answers a Case question, When its data sources are inspected, Then they resolve to the same Case Memory / Organizational Knowledge / Legal Knowledge Corpus used elsewhere in the Brain, not a separate store.
- *Verification*: Data-source trace test.

**FR-AI-002 — Legal AI Employee capability set**
- *Description*: The Legal AI Employee must assist authorized legal employees with Case retrieval, Case understanding, Case summaries, Case Reports, legal retrieval, Case similarity, Case classification, analysis assistance, information retrieval, and workflow assistance, subject to governance and permissions.
- *Priority*: P0
- *Rationale/Source*: §31
- *Dependencies*: FR-LEGAL-003, FR-ML-001, FR-ML-002, FR-REPORT-001
- *Acceptance Criteria*: Given an authorized Lawyer, When they invoke each listed capability, Then the Legal AI Employee produces the corresponding output grounded in Brain data, respecting the Lawyer's permission scope.
- *Verification*: Capability-by-capability scenario test.

### 12.11 Autonomy

**FR-AUTO-001 — Per-capability autonomy level**
- *Description*: Every Brain/AI Employee action must have an explicit authority level from {Observe, Assist, Execute with Approval, Autonomous}. No capability may operate beyond its assigned level.
- *Priority*: P0
- *Rationale/Source*: §32
- *Dependencies*: FR-GOV-003
- *Acceptance Criteria*: Given a capability assigned "Execute with Approval," When the Brain attempts to execute it, Then execution is blocked pending an explicit approval action; it is never silently promoted to Autonomous.
- *Verification*: Autonomy-boundary test per capability.

### 12.12 External Integrations

**FR-INT-001 — WhatsApp integration**
- *Description*: The Brain must integrate with WhatsApp as the primary real-time Client/Lawyer interaction channel (real integration, not a mock UI).
- *Priority*: P0
- *Rationale/Source*: §10, §33
- *Dependencies*: FR-OBS-001
- *Acceptance Criteria*: Given a real (or sandboxed real-protocol) WhatsApp account connected to the organization, When a message is sent, Then it is observably received/processed by the Brain end-to-end.
- *Verification*: Integration test against a real/sandbox WhatsApp API.

**FR-INT-002 — CRM integration (operational system)**
- *Description*: The Brain must exchange real data with at least one operational CRM: receiving Client data, interactions, Cases/leads, appointments, statuses, and operational events; and returning approved updates, Case state changes, relevant context, authorized actions, and workflow results. The CRM remains external and operational — it is not the Brain.
- *Priority*: P0
- *Rationale/Source*: §33–34, Step 1 §7(I)
- *Dependencies*: FR-GOV-001 (for authorized-action gating)
- *Acceptance Criteria*: Given a Case state change approved within the Brain, When the change is applied, Then it is observably reflected in the connected CRM through a real (simplified allowed) integration, and the exchange is audit-logged.
- *Verification*: Integration test with real data flow.

**FR-INT-003 — Auditable external actions**
- *Description*: All important external actions (Brain → external system) must be auditable.
- *Priority*: P0
- *Rationale/Source*: §34
- *Dependencies*: FR-INT-002
- *Acceptance Criteria*: Given any external action taken by the Brain, When the audit log is queried, Then actor, timestamp, action, target, and outcome are retrievable.
- *Verification*: Audit log inspection.

### 12.13 Learning

**FR-LEARN-001 — Operational learning loop**
- *Description*: The system must implement Observe → Interpret → Assist → Human correction/decision/feedback → Outcome → Candidate learning → Validation → Updated organizational intelligence as a real, traceable mechanism — not LLM retraining/fine-tuning per interaction.
- *Priority*: P0
- *Rationale/Source*: §35
- *Dependencies*: FR-MEM-003, FR-KNOW-001
- *Acceptance Criteria*: Given a Lawyer correction/feedback on a Brain-provided answer, When the correction is submitted, Then a Candidate Learning item is created and, upon validation, measurably changes future retrieval/answers for equivalent queries.
- *Verification*: Before/after retrieval scenario test.

### 12.14 ML / Data Science

**FR-ML-001 — Case Similarity**
- *Description*: The system must be able to find semantically relevant historical Cases for a given Case, as a real, measurable capability.
- *Priority*: P0
- *Rationale/Source*: §36
- *Dependencies*: FR-CASE-UND-001
- *Acceptance Criteria*: Given a Case and a corpus of historical Cases, When Case Similarity is invoked, Then a ranked list of historical Cases is returned with a similarity score and the score is not fabricated (computed from a defined, inspectable method).
- *Verification*: ML evaluation against the Evaluation Corpus (§12.16).

**FR-ML-002 — Case Classification**
- *Description*: The system must classify Cases into meaningful legal categories using a real, evaluable model.
- *Priority*: P0
- *Rationale/Source*: §36
- *Dependencies*: FR-CASE-UND-001
- *Acceptance Criteria*: Given a Case, When classification is invoked, Then a category and confidence are returned, with model evaluation metrics available and honestly reported (including on the Evaluation Corpus).
- *Verification*: ML evaluation.

**FR-ML-003 — Workflow Pattern Learning (infrastructure/observation only)**
- *Description*: The system must provide the infrastructure and observation mechanism for recurring organizational patterns, without claiming mature predictive learning.
- *Priority*: P1
- *Rationale/Source*: §36
- *Dependencies*: FR-LEARN-001
- *Acceptance Criteria*: Given repeated similar Case-handling patterns, When observed across multiple Cases, Then they are recorded as Candidate Patterns available for human review — no autonomous policy change occurs.
- *Verification*: Scenario test.

**FR-ML-004 — Legal outcome prediction is explicitly excluded**
- *Description*: The system must NOT implement or claim legal outcome/case-result prediction in V1.
- *Priority*: P0 (as an exclusion constraint)
- *Rationale/Source*: §36
- *Dependencies*: —
- *Acceptance Criteria*: Given the V1 capability set, When audited, Then no component claims or performs outcome/result prediction for a legal Case.
- *Verification*: Scope audit (see §53 self-audit pattern).

### 12.15 Reporting

**FR-REPORT-001 — Case Report / Case Brief generation**
- *Description*: The Brain must generate a Case Report summarizing, where available: Client, Case, summary, key facts, timeline, important conversations, documents, decisions, actions, current status, missing information, conflicts, relevant legal sources, relevant organizational knowledge, recent changes, next relevant actions, and evidence/provenance — distinguishing facts from inference/uncertainty.
- *Priority*: P0
- *Rationale/Source*: §22
- *Dependencies*: FR-MEM-002, FR-LEGAL-003
- *Acceptance Criteria*: Given a Case with populated Case Memory, When a Case Report is requested, Then the report is generated containing the applicable sections above, with each factual claim distinguishable from inferred/uncertain content.
- *Verification*: Report-generation scenario test; manual fact/inference audit.

### 12.16 Evaluation

**FR-EVAL-001 — Separate, unseen Evaluation Corpus**
- *Description*: The Evaluation Corpus must be kept separate from the Knowledge Corpus and must not leak into the knowledge index, retrieval corpus, training data, or development prompts before evaluation.
- *Priority*: P0
- *Rationale/Source*: §30
- *Dependencies*: FR-LEGAL-001
- *Acceptance Criteria*: Given the Evaluation Corpus, When the Knowledge Corpus/retrieval index is audited, Then no Evaluation Corpus content is present in it prior to the evaluation run.
- *Verification*: Corpus-overlap audit (automated content hash/ID comparison).

**FR-EVAL-002 — Evaluation task coverage**
- *Description*: The Evaluation Corpus/process must support: unseen legal Cases, legal questions, Case→relevant-law tasks, Case→similar-Case tasks, Case classification tasks, citation verification, source verification, version/effective-date tasks, and conflict scenarios.
- *Priority*: P1
- *Rationale/Source*: §30
- *Dependencies*: FR-EVAL-001, FR-ML-001, FR-ML-002, FR-LEGAL-003–005
- *Acceptance Criteria*: Given the defined task list, When the evaluation suite is run, Then results are produced for each task type against the Evaluation Corpus.
- *Verification*: Evaluation run + report.

---

## 13. Non-Functional Requirements

| ID | Area | Requirement | Notes |
|---|---|---|---|
| NFR-SEC-001 | Security | All Brain endpoints/actions require authentication; unauthenticated access to Case/Client data is rejected. | Builds on existing Ring 1 auth. |
| NFR-SEC-002 | Authorization | All governance-gated actions (validation, conflict resolution, external actions) enforce role/delegated-authority checks (§19). | — |
| NFR-ISO-001 | Organization isolation | No organization may retrieve another organization's Clients, Cases, or Knowledge. | Inherited/extended from Ring 1. |
| NFR-ISO-002 | Case isolation | See FR-CASE-002; stated here as a system-wide non-functional guarantee, testable across all retrieval paths, not just direct Case queries. | — |
| NFR-AUDIT-001 | Auditability | Knowledge created/modified/approved/rejected, conflicts resolved, employee answers submitted, ML predictions created, AI Employee actions, and external-system events must all be audit-logged with actor, timestamp, action, target, and before/after state where applicable. | — |
| NFR-PROV-001 | Provenance | Every Knowledge and Legal Knowledge item must carry provenance fields per §24. | — |
| NFR-REL-001 | Reliability | The Brain must degrade gracefully on LLM/retrieval/external-system failure (see §17 failure list) rather than fabricate certainty. | See §17. |
| NFR-OBS-001 | Observability | Ingestion, retrieval, LLM calls, ML predictions, validation activity, and connector activity must be logged for diagnosis. | — |
| NFR-PERF-001 | Performance | Real-time WhatsApp ingestion must not be blocked by synchronous reasoning (FR-OBS-002). Specific latency targets: **TBD / OPEN DECISION**. | Numeric SLAs not yet decided. |
| NFR-MAINT-001 | Maintainability | Components must be modular per the general-Brain-vs-Legal-Module boundary (§6–7) to support future industry modules without Brain redesign. | — |
| NFR-INTEG-001 | Data integrity | Case Memory and Knowledge updates must be atomic with respect to their audit trail (no update without a corresponding audit record). | — |
| NFR-PRIV-001 | Privacy | Individual Case data must not automatically become unrestricted organizational-level intelligence (§38); Manager/CEO views must respect authorization scope. | — |
| NFR-VER-001 | Versioning | Knowledge and Legal Source versioning per FR-KNOW-002 and FR-LEGAL-005 applies system-wide, not only to flagged items. | — |

Where a concrete numeric target has not been established by prior project artifacts, it is marked **TBD / OPEN DECISION** rather than invented (see §23).

---

## 14. Data / Information Requirements

At requirements level (not schema level), the system must be able to represent, at minimum:

- **Organization, User, Role** (inherited from existing Ring 1 implementation)
- **Client** (identity, contact, provenance of extracted attributes)
- **Case** (identity, Client reference, status, timeline)
- **Conversation** (Case reference, channel, raw messages)
- **Observation** (source, timestamp, actor/channel, raw content, processing status)
- **Document** (Case reference, source, type, provenance)
- **Event / Decision / Action** (Case reference, actor, timestamp, description, outcome where known)
- **Missing Information Item** (Case reference, what is missing, who supplied it and when, if resolved)
- **Candidate Pattern / Candidate Knowledge / Organizational Knowledge / Legal Knowledge** (per §11, §20, each with the provenance fields in §24)
- **Conflict** (conflicting evidence references, status, resolver, resolution, history)
- **Case Memory** (an aggregate/derived structure over the above, per Case)
- **Case Report** (generated artifact referencing the above with fact/inference/uncertainty labeling)
- **Legal Source** (corpus category, version, effective date, authority)
- **Evaluation Item** (task type, input, expected/gold reference where applicable, kept isolated from Knowledge Corpus)
- **Audit Record** (actor, timestamp, action, target, before/after, source, organization)
- **Permission / Delegation Record** (actor, scope, delegator, validity)
- **Autonomy Assignment** (capability, assigned autonomy level)

Exact field-level schema, keys, and normalization are deferred to the ERD/Database Design phase.

---

## 15. Security and Authorization

- Authentication and RBAC are inherited from the existing implementation (Ring 1: Organization/User/Role, JWT-based auth, per-organization email uniqueness, organization isolation).
- This document extends that model with: delegated validation authority (§19, FR-GOV-001), per-capability autonomy gating (§32, FR-AUTO-001), and AI self-escalation prevention (FR-GOV-003).
- Case-level access control (which Lawyers/Reviewers can see which Cases) is required at a behavioral level (Case data must not leak across unauthorized actors) but exact permission-model mechanics (e.g., per-Case ACL vs. role-based Case visibility) are **OPEN DECISION**, to be resolved in system design.

---

## 16. Auditability and Provenance

Every one of the following must be independently auditable, per NFR-AUDIT-001 and the provenance fields in §24:
- Knowledge created / modified / approved / rejected
- Conflict detected / resolved
- Missing information detected / resolved
- Observation → Case association (including ambiguous/ corrected associations)
- AI Employee actions and their authority level at time of execution
- ML predictions (Case Similarity, Case Classification) with method/version reference
- External system (WhatsApp, CRM) exchanges
- Case Report generation events

---

## 17. Error and Failure Requirements

The Brain must fail safely and must not fabricate certainty. Required behavior for each listed case:

| Failure/Edge Case | Required Brain Behavior |
|---|---|
| Ambiguous Client | Do not silently pick a match; flag for clarification (FR-CLIENT-002). |
| Duplicate Client | Flag, do not auto-merge (FR-CLIENT-003). |
| Ambiguous Case | Flag Case-ambiguous, do not auto-assign (FR-CASE-003). |
| Multiple Cases for same Client | Preserve Case isolation; never conflate (FR-CASE-002). |
| Conflicting facts | Route to Conflict workflow, no silent resolution (FR-CONFLICT-001). |
| Missing information | Record as Missing Information item; may trigger clarification (FR-CASE-005). |
| Incomplete conversation | Treat as partial Observation; do not infer missing content as fact. |
| Duplicate Case | Flag for human confirmation (FR-CASE-004). |
| WhatsApp interruption | Buffer/retry per FR-OBS-002 design; no silent data loss — **exact retry policy: OPEN DECISION**. |
| External system unavailable | Degrade gracefully; queue/report failure via NFR-REL-001; do not fabricate a successful exchange. |
| LLM failure | Return an explicit failure/uncertainty state, not a fabricated answer. |
| Retrieval failure | Same as above; the Brain must distinguish "no relevant knowledge found" from "retrieval system error." |
| Legal source unavailable | Reasoning must note the gap rather than proceeding as if the source were retrieved. |
| Outdated legal source | Flag as historical/non-current (FR-LEGAL-005). |
| Unauthorized action | Blocked and logged (FR-GOV-003, NFR-SEC-002). |
| Rejected approval | Action does not execute; rejection is recorded with reason where supplied. |
| Stale Case | Case Memory must still be reconstructible (FR-MEM-002); no automatic archival/deletion without an explicit policy — **policy: OPEN DECISION**. |
| Contradictory organizational knowledge | Routed through Conflict workflow (FR-CONFLICT-001), not silently overwritten. |
| Human correction | Feeds the Learning loop (FR-LEARN-001) with full provenance of who corrected what. |
| Rollback/versioning | Prior Knowledge/Legal Source versions remain retrievable (FR-KNOW-002). |

---

## 18. Core System Invariants

1. Observation ≠ Knowledge.
2. Observation ≠ Learning.
3. Client ≠ Case.
4. Case isolation is mandatory.
5. Case-specific knowledge ≠ General Organizational Knowledge.
6. AI authority cannot exceed delegated authority.
7. Conflicts requiring human resolution cannot be silently resolved.
8. Knowledge must have provenance.
9. Knowledge history/versioning must be preserved.
10. AI Employees operate through the shared Brain.
11. CRM is an operational system, not the Brain.
12. Evaluation data must remain unseen before evaluation.
13. External actions require authorization.
14. The Brain must distinguish fact, inference, uncertainty, and conflict.
15. Missing information must not be silently fabricated.
16. One unvalidated observation must not automatically become organizational truth.
17. The Brain cannot grant itself additional authority.

Every functional requirement in §12 is traceable to at least one invariant above; conversely, no invariant should be left without at least one enforcing requirement (cross-check performed in §53-equivalent self-audit, below).

---

## 19. V1 Core Scenarios

Per the earlier project analysis, five high-level scenarios represent the Organizational Brain. Each is stated here as a requirements-level capability set (full Use Case Specifications are deferred to the next phase):

1. **Organization Onboarding** — requires: Organization/User/Role setup (existing Ring 1), industry-module assignment (Legal), initial Legal Knowledge Corpus availability (FR-LEGAL-001), initial governance setup (FR-GOV-001).
2. **Knowledge Acquisition** — requires: Observation capture (§12.1), Candidate Knowledge creation (FR-KNOW-001), Legal source ingestion (FR-LEGAL-002).
3. **Brain Question** — requires: a mechanism for the Brain to ask a human for clarification/explanation (FR-CLIENT-002, FR-CASE-005), and to convert the answer into Candidate Knowledge (FR-KNOW-001, FR-LEARN-001).
4. **Learning** — requires: the full operational learning loop (FR-LEARN-001) and knowledge validation workflow (FR-GOV-002).
5. **Decision Intelligence** — requires: combining Case Memory + Legal Knowledge + ML outputs (Case Similarity/Classification) + governance context into a decision-support surface (FR-REPORT-001, FR-AI-002), explicitly not replacing human decision authority (Invariant #6, §19).

---

## 20. Legal V1 End-to-End Scenario

```
Client contacts organization
        ↓
WhatsApp interaction                              [FR-INT-001, FR-OBS-001]
        ↓
Brain observes                                    [FR-OBS-002, FR-OBS-003]
        ↓
Client identified / created                       [FR-CLIENT-001, FR-CLIENT-002]
        ↓
Potential Case detected
        ↓
Case created                                       [FR-CASE-001]
        ↓
Brain observes lawyer interaction                  [FR-CASE-UND-002]
        ↓
Case understanding progressively built             [FR-CASE-UND-001]
        ↓
Missing information detected                       [FR-CASE-005]
        ↓
Clarification when necessary                        [FR-CLIENT-002, FR-CASE-005]
        ↓
Documents / facts / decisions / actions captured    [FR-CASE-UND-001, §14 data model]
        ↓
Relevant legal knowledge retrieved                  [FR-LEGAL-003]
        ↓
Relevant historical Cases identified                [FR-ML-001]
        ↓
Case analyzed                                       [FR-LEGAL-003, FR-AI-002]
        ↓
Sources cited                                       [FR-LEGAL-003]
        ↓
Conflict detected if applicable                     [FR-CONFLICT-001]
        ↓
Authorized human resolves                           [FR-CONFLICT-002, FR-GOV-002]
        ↓
Case Memory updated                                 [FR-MEM-002]
        ↓
Lawyer later requests Case
        ↓
Brain reconstructs Case context                     [FR-MEM-002]
        ↓
Case Report generated                               [FR-REPORT-001]
        ↓
Outcome observed
        ↓
Feedback / learning                                 [FR-LEARN-001]
        ↓
Candidate organizational pattern                    [FR-MEM-003]
        ↓
Validation                                          [FR-GOV-002]
        ↓
Organizational knowledge                            [FR-KNOW-001]
```

This is a **primary V1 acceptance scenario**: V1 is not considered demonstrated unless this scenario can be executed end-to-end against the running system with real (if simplified) data at each step.

---

## 21. Acceptance Criteria

All P0 functional requirements' acceptance criteria are given inline in §12 (Given/When/Then format). Section-level acceptance for V1 as a whole is defined by:
1. Successful end-to-end execution of the Legal V1 scenario (§20).
2. Independent, automated verification of each Core System Invariant (§18) with at least one passing test per invariant.
3. An Evaluation Corpus run per FR-EVAL-001/002 with honestly reported results (no fabricated metrics, per Step 1 §11).

---

## 22. Traceability Foundation

Every requirement in §12 carries a stable ID (`FR-<CATEGORY>-<NNN>`) and an explicit Dependencies field, enabling the following downstream derivation without reinterpretation:

```
Requirement (FR-xxx-NNN)
   ↓
Use Case (named per requirement group, e.g., "Create Case from WhatsApp Observation")
   ↓
Activity Diagram (derived from the requirement's Description + Acceptance Criteria steps)
   ↓
State Diagram (derived from lifecycle-bearing entities: Case, Knowledge, Conflict)
   ↓
Sequence Diagram (derived from Dependencies chains between requirements)
   ↓
Domain / Class Model (derived from §14 Data/Information Requirements)
   ↓
Database Entity (derived from the Domain Model)
   ↓
API (derived from each requirement's actor + action)
   ↓
UI (derived from each actor-facing requirement)
   ↓
Test (derived directly from each requirement's Acceptance Criteria)
```

Category prefixes used: `FR-OBS`, `FR-CLIENT`, `FR-CASE` (incl. `FR-CASE-UND`), `FR-MEM`, `FR-KNOW`, `FR-CONFLICT`, `FR-GOV`, `FR-LEGAL`, `FR-AI`, `FR-AUTO`, `FR-INT`, `FR-LEARN`, `FR-ML`, `FR-REPORT`, `FR-EVAL`.

---

## 23. Open Decisions

These are genuine ambiguities/undecided points identified while writing this specification. They are not silently resolved:

1. **Exact retry/durability policy for WhatsApp interruption** (§17) — not yet specified.
2. **Stale Case archival/deletion policy** (§17) — retention duration and any auto-archival behavior undecided.
3. **Case-level permission mechanics** (§15) — per-Case ACL vs. role-based visibility vs. a hybrid is undecided.
4. **Numeric performance/reliability SLAs** (NFR-PERF-001 and related) — no targets have been set; all such NFRs are marked TBD.
5. **Specific CRM product/target for the V1 integration** — Step 1 already flagged this as open; it remains open here. FR-INT-002 is written against "a" CRM generically.
6. **Exact scope/size of the Egyptian Civil Legal Knowledge Corpus** (§25) — categories are defined (Foundation, Civil Legal Sources, Judicial Knowledge, Evaluation Set) but specific document counts/coverage are not yet fixed.
7. **Exact delegation model mechanics for CEO/GM-delegated authority** (§19, FR-GOV-001) — how delegation is granted, revoked, and scoped is not yet specified beyond "must be enforced."
8. **Whether Workflow Pattern Learning (FR-ML-003) is P1 or gets pulled into P0** — currently P1 per §36's "infrastructure and observation" framing, which is lighter-weight than Case Similarity/Classification; confirm before design phase.

Relationship to Step 1's open decisions: items 1–5 of Step 1's "Scope Questions / Open Decisions" are now partially resolved by this document (WhatsApp is confirmed as the channel; the Client→Case model is confirmed; Case Similarity/Classification are confirmed as the ML use cases) — Step 1's open item on the specific CRM target remains open here as item 5 above.

---

## 24. Assumptions

- The existing Ring 1 implementation (Organization/User/Role, JWT auth, per-organization isolation) is assumed to remain the identity/tenancy foundation; this document does not restate or redesign it, only extends it (§15).
- "WhatsApp" refers to the WhatsApp Business Platform (or an equivalent sandboxed/simulated channel for V1 demonstration purposes) rather than requiring a production WhatsApp Business Solution Provider contract; the exact integration mechanism is a design-phase decision.
- The organization modeled for V1 is a single fictional/demo Egyptian law firm (per Step 1 §39/§40's demo-company requirement), not a real client's confidential data.
- "Real" external integration (§33) is interpreted, per Step 1's acceptable/not-acceptable distinction, as a genuine data exchange with a real or realistically simulated system — not a purely decorative UI element.

---

## 25. Future / Post-V1

Explicitly deferred, consistent with Step 1 §12 and this document's §8/§36/§45:
- Industry modules beyond Legal (Sales, Support, HR, Finance, Procurement, etc.)
- Legal outcome / case-result prediction
- Fully autonomous action execution beyond explicitly assigned Autonomous-level capabilities
- Multi-organization, production-scale deployment
- Comprehensive Egyptian legal coverage beyond the bounded Civil Law corpus
- Mature, tuned production ML models (V1 models must be real and evaluated, but are not required to be production-grade)

---

## 26. Final V1 Definition

V1 is successful when the project demonstrates that:

> A governed Organizational Brain can observe real organizational interactions, identify and maintain Client and Case context, progressively understand Cases, preserve Case isolation, detect missing or conflicting information, request human clarification/validation, maintain persistent Case Memory, retrieve and reason over a bounded Egyptian Civil Legal Knowledge Corpus, provide traceable legal assistance, support a Legal AI Employee under defined permissions and autonomy, integrate with real operational channels/systems, generate useful Case reports, observe outcomes, and create validated organizational learning without silently converting observations into organizational truth.

This is not permission to implement every possible future capability. The V1 boundary defined in §7–8 and §45 remains explicit and binding.

### What V1 Is NOT (§45)

V1 is **not**:
- a complete Egyptian legal database
- a replacement for lawyers
- an autonomous legal decision maker
- a complete ERP
- a replacement for CRM
- a generic chatbot
- unrestricted autonomous AI
- a fully autonomous organization
- mature legal outcome prediction
- a system that treats every observation as knowledge
- a system that automatically generalizes every Case into organizational policy

---

## Appendix: Consistency Self-Audit

- **Product**: Organizational Brain defined (§4); not reduced to a chatbot (§2, §45). ✔
- **Domain**: V1 is Legal (§6); domain is Egyptian Civil Law (§6, §25). ✔
- **Process**: Requirements separated from design (§2, §1 table); no premature architecture (§1, verified — no schema/API/framework commitments made). ✔
- **Brain loop**: Full Observe→...→Learn loop represented (§10.1) and mapped to requirement IDs (§20). ✔
- **Cases**: Client ≠ Case (§11, FR-CASE-001); Case isolation explicit and testable (FR-CASE-002); persistent Case Memory exists (FR-MEM-002). ✔
- **Knowledge**: Observation ≠ Knowledge (§11, §18); Case knowledge ≠ Organizational Knowledge (FR-MEM-003); provenance/versioning exist (FR-KNOW-002, §24 fields). ✔
- **Governance**: CEO/GM governance (FR-GOV-001); delegated authority (FR-GOV-001); conflicts to humans (FR-CONFLICT-001); no AI self-escalation (FR-GOV-003). ✔
- **Legal**: Corpus bounded (FR-LEGAL-001); Egyptian Civil domain explicit (§6); source authority (FR-LEGAL-004); version/effective date (FR-LEGAL-005); citations (FR-LEGAL-003); Evaluation Corpus unseen and separate (FR-EVAL-001). ✔
- **AI Employee**: Role over shared Brain (FR-AI-001); permissions and autonomy exist (FR-AI-002, §12.11). ✔
- **Integration**: WhatsApp primary (FR-INT-001); real external-system integration required (FR-INT-002); CRM operational, not the Brain (§5, Invariant #11). ✔
- **ML**: Case Similarity (FR-ML-001); Case Classification (FR-ML-002); Workflow Pattern Learning bounded (FR-ML-003, P1); outcome prediction NOT silently added (FR-ML-004, explicit exclusion). ✔
- **Reporting**: Case Reports exist (FR-REPORT-001); old Cases reconstructible without manual re-reading (FR-MEM-002 acceptance criteria). ✔
- **Scope**: V1 boundary explicit (§7–8, §26); P0/P1/P2 used throughout §12; open decisions marked (§23). ✔
- **Traceability**: Requirements map to Use Cases/Models/APIs/UI/Tests per §22. ✔

**Step 2 status: Requirements baseline complete. Design phases (Actors, Use Cases, diagrams, architecture, ERD, etc.) have not been started in this document.**
