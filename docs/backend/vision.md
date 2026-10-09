# Vision — Organizational Brain (Legal V1)

> Condensed from `docs/constitution.md` (v2.0, Sept 2026). This file is what an AI agent reads instead of the full Constitution.
> Priority if documents disagree: `decisions.md` > current ring spec in `docs/rings/` > this file > `constitution.md`.
> This file is stack-neutral. The stack is fixed in `decisions.md` (Python / FastAPI / PostgreSQL).

---

## 1. What we are building

**One reusable "General Brain"**, specialized by **domain**, customized by **organization**.

- Legal (Egyptian Civil Law) is the **first domain**. It is the proof that the architecture works, not the final product.
- Value proposition: every organization has knowledge trapped inside individual employees. We turn it into governed, validated organizational memory.
- Scale in V1 can be limited. **Behavior must be real** (no fake AI, no fake learning).

## 2. What we are NOT building

A chatbot. A generic AI assistant. A RAG app. A CRM. A pile of unrelated agents. A "Legal AI" product. A separate Brain per industry or per organization.

## 3. Three layers (every capability is labeled)

| Label | Layer | Meaning | Example |
|---|---|---|---|
| `[GB]` | General Brain | Reusable infrastructure, no domain logic | Retrieval, context, provenance, validation |
| `[DOMAIN]` | Domain intelligence | Knowledge and tools of one industry | Egyptian Civil Law corpus, legal classification |
| `[ORG]` | Organization intelligence | One organization's own data and rules | Its cases, roles, policies, validated knowledge |
| `[SHARED]` | Cross-layer | Used by more than one layer | Case model, WhatsApp integration |

Rule: a Domain Module does **not** create a new Brain. An Organization does **not** create a new Brain. Domain logic enters only through **domain adapters**, never inside `[GB]` code.

## 4. Knowledge lifecycle (the heart of the system)

```
Raw observation -> Structured observation -> Extracted fact -> Case/Org update
-> Knowledge CANDIDATE -> HUMAN VALIDATION -> Trusted knowledge
-> Persistent memory -> Retrieval -> Reasoning -> Decision support / action
```

- Observation is **not** knowledge. A candidate is **not** trusted knowledge.
- The Brain **can never validate its own knowledge**. A human with validation authority must.
- Every knowledge object carries: source, timestamp, actor, confidence, validation status (candidate / validated / rejected), scope (general / domain / organization / case), provenance chain, version, conflict state.
- Knowledge states: Raw Observation, Structured Observation, Extracted Fact, Knowledge Candidate, Trusted Knowledge, Archived Knowledge.

## 5. Domain model (Legal)

```
Organization -> Client -> Case A -> Conversations, Documents, Events, Facts, Decisions, Knowledge
                       -> Case B -> (completely separate set)
```

- A **Client is not a Case**. A client can have many cases.
- **Case isolation is mandatory and critical**: knowledge from Case A must NEVER reach Case B, even for the same client.
- Three knowledge scopes: general legal knowledge (public, shared), organization knowledge (one law office), case knowledge (one case only).
- Case states: New -> Active -> In Progress -> Resolved -> Archived.
- Conversations belong to cases.

## 6. Observation channels

- **WhatsApp** is the primary client channel in V1: real-time capture -> buffer -> **asynchronous** processing -> case context -> understanding -> missing-information questions -> case update or knowledge candidate. A message is not knowledge.
- **Phone calls**: the lawyer enters an update manually. The Brain may propose knowledge or detect conflicts but never treats it as trusted automatically.
- **CRM** is an operational system, not the Brain. The Brain observes and learns from it, and gives intelligence back. It does not replace it. (Which CRM product is still open, see `decisions.md`.)

## 7. Autonomy (earned, never assumed)

Level 0 Observe -> Level 1 Assist -> Level 2 Execute with human approval -> Level 3 Authorized routine automation.
The organization controls the allowed level. The Brain can never raise its own authority. **V1 target: mainly Observe + Assist.**

## 8. Governance and permissions

- The organization decides who may validate knowledge (validation authority). It must be configurable and audited.
- Permissions are enforced **server-side**. Frontend hiding is cosmetic, not security.
- **Permission-aware retrieval**: the AI must never retrieve anything the current user is not allowed to access. Enforced at the server for every AI operation.

## 9. General Brain engines (names only)

Perception, Observation, Knowledge, Memory/Storage, Retrieval, Reasoning, Context, Learning, Validation/Governance, Autonomy Controller, Provenance, Permission/Authorization, Audit, Conflict Detection, Insight, Workflow/Action.
Legal adds **adapters** on top (legal retrieval, classification, document understanding, similarity, source reasoning), not separate engines.

## 10. Non-negotiable invariants

1. General Brain stays reusable. No domain logic inside `[GB]` code.
2. Observation is not knowledge. Candidate is not trusted.
3. Brain cannot self-validate. Human validation is required.
4. Autonomy is permission-controlled by the organization.
5. Every important knowledge item keeps provenance (source, validation history, chain).
6. Conflicts between knowledge must be detectable, traceable, auditable.
7. Case isolation always, even for the same client.
8. Permissions enforced server-side only.
9. Important AI decisions are logged and auditable.
10. No ring silently changes shared architecture. Changes need an ADR in `docs/adr/`.
11. Reuse before building new. No duplicating an existing `[GB]` capability.
12. Never silently drift from this vision. Document and get approval first.

## 11. Anti-patterns (do NOT do)

Separate Legal Brain. Treating every message as knowledge. Uncontrolled learning. Mixing cases. Hardcoding one organization's workflow into the General Brain. Fake AI behavior. Calling an LLM call "learning". Using RAG alone as "the Brain". Treating CRM as memory. Skipping case isolation, provenance, or human validation. Assuming full autonomy. Building ML without evaluation. Scope creep.

## 11b. AI rules

- **No AI feature without an evaluation strategy.** Impressive output is not acceptance.
- Keep training/development data separate from **unseen evaluation data**.
- Every AI capability must specify: input, processing, model, output, confidence, evaluation, fallback, human oversight, logging, failure modes.
- Metrics: retrieval (Precision@k, Recall@k, MRR, NDCG), classification (Precision, Recall, F1), extraction accuracy, similarity calibration, end-to-end lawyer satisfaction.

## 12. Rings (delivery method)

Each Ring is a **complete, working, tested vertical slice** (database + backend + AI/data + tests; frontend where relevant). It is NOT a concentric layer and NOT "backend phase then frontend phase".
A ring is done only when: implemented, integrated, tested, demonstrable, architecturally aligned, and documented.

Official ring list (Constitution v2.0 numbering, confirmed in `decisions.md` D-010):

| Ring | Name | Introduces |
|---|---|---|
| 0 | Foundation | Environment, infra, API skeleton, auth skeleton |
| 1 | Brain Core | Perception, observation, context, basic memory and retrieval |
| 2 | Knowledge & Memory | Knowledge engine, multi-store, provenance, advanced retrieval |
| 3 | Legal Domain | Legal corpus, legal retrieval/classification/understanding |
| 4 | Organization Context | Organization config, roles, permissions, validation authority |
| 5 | Case Intelligence | Case, client, case isolation, case knowledge |
| 6 | Observation (WhatsApp) | WhatsApp, buffer, async processing, client/case resolution |
| 7 | Reasoning & Assistance | Reasoning, similar cases, conflict detection, missing info |
| 8 | Learning & Validation | Candidates, validation workflow, promotion, learning signals |
| 9 | Insights & Governance | Insights, audit, governance, autonomy control |
| 10 | Legal V1 | End-to-end integration, evaluation, demo |
| 11+ | Future domains | Sales, HR, etc. reusing the General Brain |

## 13. V1 must-have

General Brain, Legal domain, organization context, knowledge acquisition, human validation, persistent memory, retrieval, reasoning, conflict detection, case understanding, WhatsApp integration, CRM integration, decision support, limited AI employee, learning feedback loop.
V1 should-have: insights dashboard, governance dashboard, activity monitoring. Post-V1: multiple domains, advanced autonomy, full CRM replacement, enterprise scale.

## 14. How to read the Constitution's "IMPLEMENTATION GUIDANCE & TOOLS" sections

Those sections were written for Node.js / Express / Prisma / React. **Ignore the tools and code.** Use them only as hints for *what entities and endpoints a ring needs*, then rebuild them in our Python stack (`decisions.md`). Never copy Prisma schemas or TypeScript names. Python replacements for tools like job queues, caching, real-time, and access control are **not decided yet**: propose them in a plan and record the choice as an ADR before using them.
