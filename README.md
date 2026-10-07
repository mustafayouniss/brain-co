# 🧠 brain-co

### Enterprise Intelligence Platform
#### Empower Your Organization with Our Intelligence Layer. 

**brain-co** is an enterprise intelligence platform designed to turn an organization's knowledge, experience, workflows, and systems into a reusable and continuously improving **Organizational Brain**.

Instead of building a separate AI system for every industry, brain-co follows a reusable architecture where a **General Brain** can be specialized through domain knowledge and customized with organization-specific intelligence.

> **One Brain → Multiple Domains → Multiple Organizations → Organization-Specific Intelligence**

---

## 🎯 Vision

Every organization has valuable knowledge trapped inside:

* Employees
* Documents
* Conversations
* Business processes
* Cases
* CRM / ERP systems
* Historical decisions
* Organizational experience

**brain-co** aims to transform this scattered knowledge into governed organizational memory and intelligence.

---

## 🏗️ Core Architecture

The platform is built around three distinct layers:

```text
┌─────────────────────────────────────┐
│           GENERAL BRAIN             │
│     Reusable Intelligence Layer     │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│       DOMAIN INTELLIGENCE           │
│ Legal • Sales • HR • Finance • ...  │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│     ORGANIZATION INTELLIGENCE       │
│ Policies • Workflows • Cases • Data │
└─────────────────────────────────────┘
```

### General Brain

Provides reusable intelligence capabilities such as:

* Perception
* Observation
* Knowledge
* Memory
* Retrieval
* Reasoning
* Context
* Learning
* Validation & Governance
* Permissions
* Provenance
* Audit
* Insight
* Workflow & Actions
* Autonomy Control

### Domain Intelligence

Provides domain-specific knowledge, terminology, workflows, reasoning patterns, and tools.

The first implementation focuses on:

**Legal Domain — Egyptian Civil Law**

Legal is treated as the first domain specialization rather than a separate "Legal Brain".

### Organization Intelligence

Provides organization-specific context such as:

* Policies
* Workflows
* Roles & permissions
* Employees
* Internal procedures
* Documents
* Cases
* Conversations
* Historical work
* Decisions
* Business rules
* Existing systems
* Validated organizational knowledge

---

## 📁 Project Structure & File Architecture

The repository is organized following an enterprise vertical-slice architecture across all technical domains:

```text
brain-co/
├── 📂 .github/                  # CI/CD Workflows & Ring-based Issue Templates
├── 📂 ai/                       # AI & LLM Engine (LangChain, Prompts, Autonomy Gates)
│   └── 📂 src/                  # config, engines, prompts, utils
├── 📂 backend/                  # Backend Modular Monolith / Microservices
│   ├── 📂 prisma/               # Master Schema (PostgreSQL + pgvector), Migrations & Seeds
│   └── 📂 src/                  # modules (brain-core, legal, case, knowledge, etc.), middleware, jobs
├── 📂 data-engineering/         # Data Pipelines & Event Streaming
│   ├── 📂 airflow/              # Airflow DAGs (Legal Corpus ETL, DWH Aggregations)
│   ├── 📂 dbt/                  # dbt Models (staging, intermediate, marts)
│   ├── 📂 lakehouse/            # MinIO Storage Zones (raw, processed, backup)
│   └── 📂 streaming/            # Kafka / Redis Stream Producers & Consumers
├── 📂 data-science/             # Data Science, ML & Arabic NLP
│   ├── 📂 evaluation_data/      # 🔒 Isolated Unseen Evaluation Corpus (Invariant #12)
│   ├── 📂 models/               # Case Similarity, Case Classification, Arabic NLP
│   ├── 📂 notebooks/            # Jupyter Notebooks per Ring (01 to 10)
│   └── 📂 scripts/              # Scraping, Normalization & Evaluation Runners
├── 📂 docs/                     # System Documentation & Specifications
│   ├── 📂 adrs/                 # Architecture Decision Records
│   ├── 📂 architecture/         # High-Level Architecture & 3-Layer Model
│   ├── 📂 legal-corpus/         # Egyptian Civil Law Index & Casation Precedents
│   ├── 📂 project-specifications/ # 🏛️ Core Specifications & Original Legal PDFs
│   ├── 📂 rings/                # Ring-by-Ring Specifications (0 to 11+)
│   └── 📂 software-analysis/    # Use Cases, Sequence & Domain Class Diagrams
├── 📂 frontend/                 # React 18 + Vite + Tailwind RTL Web Dashboard
│   └── 📂 src/                  # components (brain, legal, case workspace, assistance), pages
├── 📂 infrastructure/           # Docker, Kubernetes, Nginx & Database Scripts
├── 📂 mobile/                   # Flutter 3.x Mobile App (Clean Architecture + BLoC)
│   └── 📂 lib/                  # core (offline sync, biometrics, RTL) & features (case, legal chat)
├── 📂 shared/                   # Cross-stack Types, Contracts & Validators (National ID)
├── 📂 tests/                    # Unit, Isolation (Case Isolation), Invariant & E2E Tests
├── 📄 docker-compose.yml        # PostgreSQL+pgvector, Redis, Neo4j, MinIO
└── 📄 README.md                 # Project Overview
```

---

## 🔄 Knowledge Lifecycle

brain-co distinguishes between what the system observes and what it actually learns.

```text
Raw Observation
       ↓
Structured Observation
       ↓
Extracted Fact
       ↓
Knowledge Candidate
       ↓
Human Validation
       ↓
Trusted Knowledge
       ↓
Persistent Memory
       ↓
Retrieval
       ↓
Reasoning
       ↓
Decision Support / Action
```

Not every message or observation becomes organizational knowledge.

Human validation and governance remain fundamental parts of the system.

---

## ⚖️ First Domain: Legal

The first implementation of brain-co targets **Egyptian Civil Law**.

The Legal Domain includes:

* Legal knowledge
* Legal terminology
* Legal taxonomy
* Legal procedures
* Legal documents
* Public historical cases
* Legal reasoning patterns
* Case management
* Legal research
* Document review
* Client consultation
* Contract review

The Legal implementation serves as a real-world proof that the reusable General Brain architecture can operate in a high-stakes domain.

---

## 💬 Communication & Integrations

The platform is designed to observe and integrate with organizational systems and communication channels such as:

* WhatsApp
* CRM
* Email
* Documents
* ERP systems
* Other external systems

For communication channels such as WhatsApp, messages are captured in real time and processed asynchronously before being associated with the appropriate organizational and case context.

---

## 🔐 Governance & Security

brain-co follows a human-governed intelligence model.

Key principles include:

* Role-based access control
* Server-side permission enforcement
* Permission-aware retrieval
* Organization isolation
* Case isolation
* Knowledge provenance
* Validation history
* Auditability
* Human-in-the-loop governance
* Controlled AI autonomy

The system is designed so that AI cannot retrieve information that the current user is not authorized to access.

---

## 🤖 AI Autonomy

Autonomy is progressive rather than assumed.

```text
Level 0 → Observe
Level 1 → Assist
Level 2 → Execute with Human Approval
Level 3 → Authorized Automation
```

The initial V1 focuses primarily on **Observation and Assistance**.

---

## 🧪 Evaluation

AI capabilities are not considered complete simply because they produce impressive outputs.

The project includes measurable evaluation strategies covering areas such as:

* Retrieval quality
* Classification
* Document understanding
* Similarity
* End-to-end assistance
* Human satisfaction
* Task completion
* Time saved

Unseen evaluation data is kept separate from development and training data.

---

## 🛠️ Development Principles

brain-co follows several architectural principles:

1. **One General Brain**
2. **Reusability First**
3. **Clear separation between General, Domain, and Organization intelligence**
4. **Observation ≠ Knowledge**
5. **Human Governance**
6. **Strict Case Isolation**
7. **Permission-aware intelligence**
8. **Provenance & Auditability**
9. **Gradual Autonomy**
10. **Architecture before implementation**

---

## 📚 Project Documentation

All foundational project documentation has been organized under [`docs/project-specifications/`](docs/project-specifications/):

* [Master Project Constitution](docs/project-specifications/ORGANIZATIONAL_BRAIN_MASTER_PROJECT_CONSTITUTION.md)
* [Requirements Specification](docs/project-specifications/REQUIREMENTS_SPECIFICATION.md)
* [Project Scope](docs/project-specifications/PROJECT_SCOPE.md)
* [Architecture Roadmap](docs/project-specifications/Organizational_Brain_Architecture_Roadmap_Final_version.pdf)
* [Egyptian Legal References (Civil Code & Constitution)](docs/project-specifications/README.md)

The **Project Constitution** is the highest-level source of truth for the project, followed by approved architecture decisions, specifications, contracts, and implementation documentation.

---

## 🚀 Long-Term Direction

The long-term goal is to demonstrate that the same General Brain infrastructure can support multiple domains without rebuilding the core intelligence layer.

```text
             ONE GENERAL BRAIN
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
     LEGAL          SALES          HR
       │             │             │
       ▼             ▼             ▼
   Organization  Organization  Organization
```

Future domain specializations may include:

* Sales
* Customer Support
* HR
* Finance
* Real Estate
* Other enterprise domains

---

## 🎓 Graduation Project

**brain-co** is a graduation project developed by students of the **Faculty of Computers and Data Science**.

The project follows a ring-based development roadmap spanning:

**Frontend • Backend • AI • Data Science • Integrations**

---

## 👥 Team

**brain-co Team**<br>
Mohamed Alaa<br>
Yousef Mohamed Hamada<br>
Manar Mohammed Abdulkarim<br>
Faculty of Computers and Data Science<br>
Graduation Project 2026–2027

---

## 📄 License

This project is currently developed as an academic graduation project.
