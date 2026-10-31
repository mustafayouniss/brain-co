# Ring 1 General Brain — Implementation Plan

## Phase 1: Architecture Audit Summary

### What exists and will be reused
| Component | Path | Reuse |
|---|---|---|
| LLM provider abstraction | `ai/core/interfaces/provider.py` → `ILLMProvider` | Yes — engines' Intelligence Layer uses `LLMService` |
| Provider registry | `ai/providers/registry.py` → `ProviderRegistry` | Yes — no new provider system |
| LLMService | `ai/core/services/llm_service.py` | Yes — via `AIConfig.create_service()` |
| FakeLLMProvider | `ai/providers/fake_provider.py` | Yes — tests use this |
| Pydantic v2 types | `ai/core/types/{request,response,error}.py` | Yes — `LLMRequest`, `LLMResponse`, `LLMError` |
| SQLAlchemy Base + session | `backend/app/db/{base,session}.py` | Yes — new models extend `Base` |
| Alembic migrations | `backend/migrations/` | Yes — new tables need migrations |
| Test fixtures | `backend/tests/conftest.py` → `test_engine`, `db_session`, `client` | Yes — all tests use these |
| Backend config | `backend/app/core/config.py` → `settings` | Yes — DB URLs etc. |
| AI config | `ai/config/ai_config.py` → `ai_config` | Yes — for engine Intelligence Layers |

### What is missing (to be created)
1. **Mesh contracts** — typed Pydantic envelopes for inter-engine communication
2. **Capability registry** — engine capability registration and lookup
3. **Six engines** — Perception, Observation, Context, Memory, Retrieval, Planning
4. **DB models** — `observations`, `memory_records` tables
5. **Alembic migration** for new tables
6. **ADR-008** — Planning Engine as approved Ring 1 engine
7. **Tests** — contracts, all engines, mesh integration, context isolation

### Conflicts / decisions needed
- **Planning Engine**: Constitution lists 5 Ring 1 capabilities. The task approves Planning as a 6th. This is documented as ADR-008; the Constitution is NOT modified.
- **Organization isolation**: D-004 says single org per deployment. Context isolation focuses on case-level boundaries as per D-006.
- **Mesh transport**: In-process service calls (no Kafka/Redis/bus needed per D-009).

## Phase 2–7: Implementation Structure

### File structure (all new files under `backend/app/ring1/`)
```
backend/app/ring1/
├── __init__.py
├── contracts/
│   ├── __init__.py
│   ├── envelopes.py          # MeshRequest, MeshResponse Pydantic models
│   ├── capabilities.py       # Capability names, registry
│   ├── context_ref.py        # ContextRef model
│   ├── errors.py             # Typed engine error models
│   └── plan_models.py        # Plan, PlanStep, ReplanRequest/Response
├── mesh/
│   ├── __init__.py
│   └── router.py             # MeshRouter: capability dispatch, validation, tracing
├── engines/
│   ├── __init__.py
│   ├── base.py               # BaseEngine with Intelligence Layer pattern
│   ├── perception.py         # PerceptionEngine
│   ├── observation.py        # ObservationEngine
│   ├── context.py            # ContextEngine
│   ├── memory.py             # BasicMemoryEngine
│   ├── retrieval.py          # BasicRetrievalEngine
│   └── planning.py           # PlanningEngine
└── models/
    ├── __init__.py
    └── observation.py         # SQLAlchemy models for observations + memory records

backend/tests/ring1/
├── __init__.py
├── conftest.py               # Ring 1 test fixtures (mesh setup, fake LLM)
├── test_contracts.py         # Envelope validation tests
├── test_perception.py
├── test_observation.py
├── test_context.py
├── test_memory.py
├── test_retrieval.py
├── test_planning.py
├── test_mesh_integration.py  # End-to-end peer-to-peer delegation
└── test_context_isolation.py # Cross-context security tests

backend/migrations/versions/
└── <new>_create_ring1_tables.py

docs/adrs/
└── ADR-008-planning-engine.md
```

### Capability names
- `perception.structure_input`
- `observation.record_event`
- `context.resolve`
- `memory.store_record`
- `memory.get_record`
- `retrieval.query`
- `planning.create_plan`
- `planning.request_replan`
- `planning.get_plan_status`

### Execution order
1. Write contracts (envelopes, capabilities, errors, plan models)
2. Write mesh router
3. Write DB models + Alembic migration
4. Implement BaseEngine
5. Implement 6 engines (deterministic core + intelligence layer stub)
6. Wire mesh integration
7. Write all tests
8. Run tests, fix issues
9. Write ADR-008 and update docs
