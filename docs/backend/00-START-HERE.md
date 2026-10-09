# 00 — Start Here

Welcome to the **Organizational Brain — Legal V1** backend repository.

---

## 1. Project Summary (5 Lines)
1. **OrgBrain** is a reusable **General Brain** specialized by domain and customized by organization; Legal (Egyptian Civil Law) is the first domain — proof the architecture works, not the final product.
2. Built strictly on Python 3.12, FastAPI, PostgreSQL 17 with `pgvector`, SQLAlchemy 2.0, Alembic, and Pydantic v2.
3. Each **Ring** is a complete, tested, demonstrable vertical slice (database + backend + AI/data + tests). Rings 0–2 are General Brain only (`[GB]`); the Legal domain starts at Ring 3; the complete Legal V1 is Ring 10.
4. **Case isolation is the only mandatory data-isolation rule** and it applies from Ring 5 onward: knowledge from Case A must never reach Case B, even for the same client. Permissions are enforced server-side for every operation.
5. Development follows a disciplined protocol: plan first, small verifiable tasks, zero invented APIs, and all changes backed by real executed tests.

---

## 2. Reading Order

### Tier 1 — ALWAYS read before any task

1. **[`AGENTS.md`](file:///d:/Study/projects/OrgBrain/AGENTS.md)** — Rules of engagement, tech stack, source-of-truth hierarchy, start/end-of-task behaviors.
2. **[`docs/progress.md`](file:///d:/Study/projects/OrgBrain/docs/progress.md)** — Current state: what is done, what is next, any blockers.
3. **[`docs/decisions.md`](file:///d:/Study/projects/OrgBrain/docs/decisions.md)** — All settled architecture and design decisions.
4. **[`docs/vision.md`](file:///d:/Study/projects/OrgBrain/docs/vision.md)** — Project vision, layers, ring definitions, invariants, anti-patterns.
5. **Current ring spec in [`docs/rings/`](file:///d:/Study/projects/OrgBrain/docs/rings/)** — Scope, task list, and exit criteria for the ring in progress.

### Tier 2 — ONLY WHEN NEEDED

- **[`docs/architecture.md`](file:///d:/Study/projects/OrgBrain/docs/architecture.md)** — Directory layout, DB session flow, component versions. Read when proposing structural or infrastructure changes.
- **[`docs/environment.md`](file:///d:/Study/projects/OrgBrain/docs/environment.md)** — Prerequisites, Docker/WSL2 config, environment setup runbook. Read when setting up or debugging the environment.
- **[`docs/how-it-works.md`](file:///d:/Study/projects/OrgBrain/docs/how-it-works.md)** — Conceptual guide and operational commands. Read when explaining or extending existing behavior.
- **Latest entry in [`docs/journal/`](file:///d:/Study/projects/OrgBrain/docs/journal/)** — Recent daily log. Read when diagnosing a past error or continuing interrupted work.
- **[`docs/constitution.md`](file:///d:/Study/projects/OrgBrain/docs/constitution.md)** — Specific sections only, never in full. Read only when a specific constitutional rule is needed and not covered by `vision.md` or `decisions.md`.


---

## 3. Core Working Guidelines
- **No Guessing**: Documentation and code must describe only verified facts. If something is unknown or untested, state `UNVERIFIED`.
- **Plan First**: Write the plan, present it clearly, obtain approval, then write code.
- **Server-Side Enforcement**: Case permissions and isolation are always enforced server-side.
