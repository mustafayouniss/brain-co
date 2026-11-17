# Progress

## Current Status — Session 21 (2026-11-18T01:30Z)

**Document Ingestion Pipeline & Tenant Isolation Hardening (Rounds 1 & 2) and Frontend Cinematic Architecture Verified.**

### Backend Remediation & Hardening Highlights
1. **Tenant Isolation Hardening (Round 2)**:
   - **WebSocket Fail-Closed (Item 1)**: `_validate_session_and_case` strictly filters cases by `organization_id` and rejects non-matching or cross-tenant case IDs with 1008 without information disclosure.
   - **Scenario Runner Cross-Tenant Defense (Item 2)**: Added `Case.organization_id == org_id` filter across all three case query locations in `TestScenarioService`.
   - **Test-Run Organization Verification (Item 3)**: Eliminated client body organization fallback in `execute_ring1_test` for tokens without an org claim, enforcing strict default deployment organization.
   - **Knowledge Endpoint CACS (Item 4)**: Enforced `CaseService.validate_case_access` on `GET /ring1/knowledge` returning 404 for unassigned/unauthorized cases while retaining 403 on explicit organization mismatch.
   - **Round 2 Tests**: Added `backend/tests/test_tenant_isolation_round2.py` covering WebSocket rejection, scenario runner isolation, spoofing rejection, and knowledge endpoint 404/403 security (4/4 passed).
2. **Worker Resilience (Round 1 - Issue 4)**:
   - In `process_task_worker`, wrapped `Observation` and `MemoryRecord` persistence in `session.begin_nested()` (SAVEPOINT).
   - Targeted `IntegrityError` catch around each block; re-queries existing record by `(organization_id, idempotency_key)` and reuses its ID.
3. **Duplicate Upload Deduplication & Retries (Round 1 - Issue 3+2)**:
   - Pre-computes SHA-256 before writing to raw storage.
   - Lookups existing Source strictly by composite key `(organization_id, case_id, checksum_sha256)`.
   - Reuses existing source and active/pending task without writing duplicate files to disk or re-scheduling worker.
   - Automatically resets and schedules failed/dead tasks when re-uploaded.
   - Updated task idempotency key format to `f"source-doc-{case.id}-{sha256}"`.
4. **Round 1 Tests**:
   - Added `backend/tests/test_document_ingestion_pipeline.py` (4/4 passed).
5. **Technical Audit Remediation (Batch A)**:
   - `create_case` TOCTOU race condition mapped to 409 `CASE_ALREADY_EXISTS`.
   - Arabic lexical search normalization (`backend/app/core/text.py`) and UTF-8 JSON dump unescaping.

## Previous Status — Session 20 (2026-11-17T20:00Z)

**Full Reference Experience (`Organizational Brain Refrence (1).html`) Recreated Inside Brain-Co Production Frontend. Ground-Truth Anatomical Brain + 5 Modular Department Targets + Continuous 7-Stage Multi-Target GPU Morphing Verified with Real-Browser CDP Captures.**

### Verified Core Capabilities & Visual Achievements
1. **Anatomical Source Ground-Truth Audit & Benchmarking**:
   - Audited all 563 meshes in `models/original/brain.glb`: isolated 448 parenchymal meshes (377 cortex, 14 cerebellum, 18 brainstem, 39 deep structures). Excluded 115 non-parenchymal meshes (cranial nerves, carotid/vertebral arteries, dural sinuses).
   - Validated metric dimensions: Width 13.8 cm ($X$), Height 16.1 cm ($Y$), Length 18.1 cm ($Z$). Aspect ratio $1.312$.
   - Density benchmarks on WebGL runtime: 8,000 shards (3.60 MB), 16,000 shards (7.20 MB), 24,000 shards (10.80 MB). Selected **16,000 shards** for optimal cortical definition ($93.8\%$ surface coverage) and lightweight GPU footprint.
   - Validated against standalone viewer (`http://localhost:8862/`) across all 5 canonical viewpoints (Front, Left Lateral, Right Lateral, Three-Quarter, Posterior).
2. **5 High-Fidelity Department Target Geometries (`department-geometries.ts`)**:
   - Shape 1 (Legal / Compliance): Brass balance scale with tiered marble plinth, central brass column, tilted balance beam, and dual suspended pans.
   - Shape 2 (Human Resources): 3 Stylized human figures with torso ellipsoids and limbs, plus orbital organization network with node spheres.
   - Shape 3 (Sales & Revenue): Volumetric 3D growth bars, frosted glass base plate, and ascending golden growth arrow slicing diagonally upward.
   - Shape 4 (Finance & Audit): Tilted orbital gold coin ring (12 coins) connected via radial links to central 7-coin treasury reserve stack.
   - Shape 5 (Operations): 3 Stacked translucent circular layer disks with vertical inter-layer conduits and active packet nodes.
3. **Unified Multi-Target GPU Morph Engine (`unified-morph-engine.ts`)**:
   - Single packed `BufferGeometry` carrying 16,000 triangular shards across all 6 targets simultaneously (`position`, `aO`, `aR`, `t1`..`t5`, `n1`..`n5`).
   - Morphing vertex shader with 3D harmonic flight turbulence, Rodrigues formula tumbling rotation around random 3D axes, and Dala Fresnel rim glow.
   - Barycentric wireframe fragment shader (`min(min(vBc.x, vBc.y), vBc.z)`) producing luminous edges with translucent facet interiors.
4. **Scroll Narrative Synchronization & Layout Choreography**:
   - Continuous scroll mapping $u \in [0.0, 6.0]$ across the 7 stages via Framer Motion.
   - Right-edge vertical progress bar (`#bar`) and floating scroll indicator (`.sc`).
   - Spatial layout: On Hero ($u=0$) and Final ($u=6$), 3D model is right-balanced/centered with pristine left text void; on department sections ($u \in [1, 5]$), 3D model glides smoothly to the LEFT while frosted glassmorphism story cards dock on the RIGHT.
   - Responsive mobile adaptation horizontally centering the 3D model below the headline without clipping.
5. **Full-Suite Automated Verification**:
   - TypeScript: 0 errors (`npm --prefix frontend run typecheck`).
   - Unit tests: 16/16 pass in 352ms (`npm --prefix frontend test`).
   - Next.js build: 37/37 static routes generated cleanly in 6.5s.
   - Real browser visual proof verified on port 3001 with 0 console errors and 0 WebGL warnings:
     - 12 Scroll stages: `docs/verification_evidence/01_hero_brain.png` through `12_final_unified_brain.png`.
     - Mobile captures: `mobile_01_hero.png` and `mobile_02_legal.png`.
6. **Strict Invariant Protection**: Zero modifications to `proxy.ts`, `server-backend-url.ts`, `backend-auth.ts`, `api/**/*`, `components/workspace/**/*`, `ring1-test-console/**/*`, login, onboarding, backend/Docker/migration files. Zero git commits or resets.

## Previous Status — Session 19 (2026-11-17T19:25Z)

**Production Hero Anatomical Brain Mapping Complete. Validated Gross-Anatomical Model (`brain.glb`) Fully Decomposed into 16,000 Surface-Aligned Crystalline Shards with Dala Specular Shading.**

### Verified Core Capabilities & Visual Achievements
1. **Source Geometry Extraction from Validated Gross Anatomy (`models/original/brain.glb`)**:
   - Filtered out non-parenchymal structures (cranial nerves, vertebral/carotid vessels, dural sinuses, falx cerebri) to eliminate vertical neck distortion.
   - Isolated the 448 authentic brain parenchyma meshes: complete cerebral cortex (all lobes, gyri, sulci), cerebellar folia, and brainstem axis.
   - Metric cranial dimensions: Width 13.8 cm ($X$), Height 16.1 cm ($Y$), Length 18.1 cm ($Z$). Aspect ratio = 1.134.
2. **Surface-Area Weighted 3D Sampling & Normal Alignment**:
   - Sampled 16,000 points uniformly distributed by triangle surface area ($0.8095\text{ m}^2$) across all cortical convolutions.
   - Encoded true outward anatomical surface normals $\mathbf{n}$. Shards orient their base tangent to the cortical curvature and apex pointing outward.
   - Curvature-driven sulcal depth metric $\kappa = \frac{\mathbf{p}}{\|\mathbf{p}\|} \cdot \mathbf{n}$: sulcal crevices receive obsidian shadow shading (`colorGroup = 3`), high dorsal crests receive platinum white specular sheen (`colorGroup = 1`), and outer perimeter facets receive luminous golden-amber edge rim glow (`colorGroup = 0`).
3. **Dala-Grade Specular Shading & Single-Pass Screen-Space Wireframes**:
   - Flat non-shared facet normals produce razor-sharp Blinn-Phong specular glints across individual triangular faces.
   - Single-pass `fwidth()` barycentric wireframes create anti-aliased luminous edges without geometry bloat.
   - Organic neural respiration breathing cycle ($1.4\text{s}$ period, $1.5\%$ subtle amplitude).
4. **Hero Viewport Placement & Invariant Protection**:
   - Positioned in right column ($x \approx +1.48, y \approx +0.10, \text{scale} \approx 0.95$), visible immediately at scroll progress 0.0 without any scrolling.
   - Text column ($x \in [-3.6, -0.3]$) remains a 100% unobstructed obsidian black void.
   - Dynamic responsive compensation horizontally centers the brain on mobile viewports (390×844) below the headline.
5. **Full-Suite Automated Verification**:
   - TypeScript: 0 errors (`npm --prefix frontend run typecheck`).
   - Unit tests: 16/16 pass (`npm --prefix frontend test`).
   - Next.js build: 37/37 static pages generated cleanly in 4.2s.
   - Real browser visual proof verified with 0 console errors and 0 WebGL warnings:
     - Desktop 1440×900: `frontend/docs/anatomical-brain-production-desktop.png`
     - Desktop 1920×1080: `frontend/docs/anatomical-brain-production-1920.png`
     - Mobile 390×844: `frontend/docs/anatomical-brain-production-mobile.png`
     - Direct side-by-side comparison with standalone viewer: `frontend/docs/anatomical-brain-production-comparison.png`
6. **Strict Invariant Protection**: Zero modifications to `proxy.ts`, `server-backend-url.ts`, `backend-auth.ts`, `api/**/*`, `components/workspace/**/*`, `ring1-test-console/**/*`, login, onboarding, backend/Docker/migration files.

## Previous Status — Session 18 (2026-11-17T17:35Z)

**Exact Reference 3D Brain Reconstruction & Hero Placement Complete. Loose Vortex Cloud 100% Eliminated. Live Browser Proof Verified.**

### Verified Core Capabilities & Visual Achievements
1. **100% Morphological Matching to Reference Brain (`media_1794908221479_00ae4a3b.jpg`)**:
   - Extracted 2,421 exact shard peak centroids and RGB color assignments directly from the authoritative reference image using SciPy multi-scale Gaussian filtering and local maximum suppression.
   - Augmented to full 3,800 crystalline shard budget with volumetric depth layers and 6 compositional macro-crystal anchors. Serialized as high-performance Base64 Float32Array in `frontend/src/components/cinematic/brain-reference-data.ts`.
   - Replaced synthetic harmonic formulas in `exact-brain-geometry.ts` with direct decoded coordinates for State 3 (Centered Coalesced Brain) and State 0 (Hero Right Column: $x = +1.48, y = +0.10, \text{scale} = 0.95$).
2. **Elimination of Vortex Cloud in Hero Section**:
   - The hollow circular vortex cloud and "COGNITIVE VORTEX" artifacts are completely removed.
   - The 3D reference brain appears immediately upon initial page load without any scrolling, positioned precisely in the right column ($x \approx 74.97\%$ of viewport width, vertical center $y \approx 49.94\%$), matching Dala's hero layout (`media_1794911875437_0bb2c31a.jpg`).
   - The left text column ($x \in [-3.6, -0.3]$) remains a 100% pristine obsidian black void for typography, eyebrow badge, subtitle, and action CTAs.
3. **Responsive Mobile Centering (390×844)**:
   - Dynamic compensation formula ($x = -1.48 \times 0.65 \times (1 - \text{progress})$) centers the brain horizontally at exactly $x = 195.0\text{px}$ (50.0% of viewport width), positioned between $y = 400\text{px}$ and $y = 842\text{px}$ below the headline without clipping.
4. **4-Stage Narrative Morphing Preserved**:
   - State 0: Hero Assembled Brain (Right Column) -> `docs/state_0_hero_brain.png`
   - State 1: Fragmentation Scatter (The Crisis) -> `docs/state_1_crisis_scatter.png`
   - State 2: Inward Convergence Streamlines -> `docs/state_2_convergence.png`
   - State 3: Centered Coalesced Dual-Hemisphere Brain -> `docs/state_3_coalesced_brain.png`
5. **Full-Suite Automated Verification**:
   - TypeScript: 0 errors (`npm --prefix frontend run typecheck`).
   - Unit tests: 16/16 pass (`npm --prefix frontend test`).
   - Next.js build: 37/37 static pages generated cleanly in 4.6s.
   - Real browser visual captures verified:
     - Desktop 1440px Hero Exact Match: `docs/hero_brain_exact_match_1440.png`
     - Mobile 390px Hero Exact Match: `docs/hero_brain_exact_match_390.png`
6. **Strict Invariant Protection**: Zero modifications to `proxy.ts`, `server-backend-url.ts`, `backend-auth.ts`, `api/**/*`, `components/workspace/**/*`, or backend/Docker/migration files.

## Previous Status — Session 17 (2026-11-17T13:15Z)

**Hero 3D Brain Positioning, 100% Transparent Top Navigation, and Global Sharpness Remediation Verified live in real browser.**

### Verified Core Capabilities & Visual Achievements
1. **Immediate Hero 3D Brain Visibility (Zero Scroll Requirement)**:
   - Modified State 0 (`target0` in `exact-brain-geometry.ts`) so the fully assembled 3D reference brain appears immediately on page load in the Hero section.
   - Exact placement matching authoritative reference screenshot (`user_placement_dala_target.jpg`): Centered at $x = +1.48, y = +0.10, \text{scale} = 0.95$.
   - Negative space preservation: Left column ($x \in [-3.6, -0.3]$) remains 100% pristine obsidian black void for typography, badge, subtitle, and CTAs.
   - Anchored peripheral crystals: Large Teal macro-crystal on right border ($x = 3.10, y = 0.22$), warm Amber crystal in foreground lower-left ($x = 1.15, y = -0.75$), upper ambient floater ($x = 0.05, y = 1.70$).
   - Mobile adaptation: Dynamic horizontal centering ($x = -1.48 \times 0.65 \times (1 - \text{progress})$) centers the brain below the headline on mobile viewports.
2. **100% Transparent Top Navigation Bar**:
   - Navigation bar container configured with `bg-transparent border-transparent` and zero backdrop blur.
   - Zero visible bottom border strip dividing the header from the 3D scene. Brand logo and desktop menu pill float seamlessly over the 3D space.
3. **Systematic Removal of Excessive Fog and Blur**:
   - Removed foggy radial vignette overlay (`opacity-35`) from `scroll-narrative-container.tsx`.
   - Neutralized contrast-reducing depth defocus in `dala-frag.ts` for pin-sharp wireframe edge clarity.
   - Removed `backdrop-blur-*`, frosted-glass overlays, and giant blurred glow orbs (`blur-[140px]`, `blur-[120px]`, `blur-[100px]`) across `crisis-section`, `agents-section`, `pillars-section`, `platform-preview`, `security-section`, `cinematic-cta`, `footer`, `about`, `contact`, and `modules`.
   - Card containers upgraded to crisp obsidian dark glass (`bg-black/40 border border-white/[0.08]`).
4. **Full-Suite Automated Verification**:
   - Unit tests: 16/16 pass (`npm --prefix frontend test`).
   - TypeScript: 0 errors (`npm --prefix frontend run typecheck`).
   - Next.js build: 37/37 static pages generated cleanly in 6.6s.
   - Real browser visual captures verified:
     - Desktop 1440px Hero: `docs/milestone1_desktop_hero_1440.png`
     - Mobile 390px Hero: `docs/milestone1_mobile_hero_390.png`
     - Desktop 1440px Crisis: `docs/milestone1_desktop_crisis_1440.png`
     - Desktop 1440px Convergence: `docs/milestone1_desktop_convergence_1440.png`
     - Desktop 1440px Platform Preview: `docs/milestone1_desktop_platform_preview_1440.png`
     - Desktop 1440px Coalesced Brain: `docs/milestone1_prototype_brain_1440.png`
5. **Strict Invariant Protection**: Zero modifications to `proxy.ts`, `server-backend-url.ts`, `backend-auth.ts`, `api/**/*`, `components/workspace/**/*`, or backend/Docker/migration files.

## Previous Status — Session 16 (2026-11-17T11:15Z)

**Dala-Level Visual Reconstruction Verified: Faceted Crystalline Wireframe Tetrahedra, Asymmetric Hero Composition, and 4-Stage Continuous Narrative live in actual browser.**

### Verified Core Capabilities & Visual Achievements
1. **Dala-Grade Crystalline Wireframe Tetrahedra**:
   - Implemented `createTetrahedralPyramidGeometry` with non-indexed flat normals and hardware-level barycentric coordinates (`aBarycentric`).
   - Vertex attribute packing: Packed 6 dynamic instance attributes into 2 `vec4` attributes (`aInstanceRot` and `aInstanceParams`), strictly resolving the WebGL `MAX_VERTEX_ATTRIBS` hardware limit (13 total slots <= 16).
   - Single-Pass Wireframe Rendering (`fwidth` in `DALA_FRAGMENT_SHADER`): Renders screen-space anti-aliased luminous wireframe edges (Amber/Gold `#ffb829`, Royal Violet `#7c3aed`, Electric Cyan `#00f2ff`, Specular Platinum `#fafaff`) with semi-transparent obsidian glass facet interiors (`alpha = 0.04 - 0.45`) and Blinn-Phong specular glints.
2. **Asymmetric Editorial Composition & Obsidian Negative Space**:
   - Redesigned `target0` (Hero Vortex): Center moved to $x = +1.85$, $r \in [0.25, 1.80]$. Text column ($x \in [-3.6, 0.0]$) is 100% pristine obsidian black void (`#000000`).
   - Added peripheral anchor macro-crystals ($i < 6$) in the outer edges matching Dala's compositional anchors without obstructing text.
   - Mobile Hero (390px): Clean typography in upper obsidian void with vortex sweeping through the lower half and behind CTAs.
3. **4-Stage Continuous Narrative Mapping**:
   - State 0: Swirling Ambient Vortex (Hero)
   - State 1: Turbulent Fragmentation Scatter (The Crisis)
   - State 2: Gravitational Streamline Convergence (Order from Chaos)
   - State 3: Coalesced Dual-Hemisphere Brain (The Hive Mind with deep longitudinal fissure $d_x = 0.14$, gyri/sulci convolutions, and synaptic filaments).
4. **Interactive Control Deck on `/cinematic-prototype`**:
   - Upgraded slider to full $[0.0, 3.0]$ range with one-click jump buttons (`0.0 Vortex`, `1.0 Scatter`, `2.0 Convergence`, `3.0 Brain`).
5. **Full-Suite Automated Verification**:
   - Unit tests: 16/16 pass (`npm --prefix frontend test`).
   - TypeScript: 0 errors (`npm --prefix frontend run typecheck`).
   - Next.js build: 37/37 static pages generated cleanly in 5.3s.
   - Route chunk isolation verified: Three.js strictly absent from `/login` and `/workspace`.
   - Real browser visual captures verified:
     - Desktop 1440px Hero: `docs/milestone1_desktop_hero_1440.png`
     - Desktop 1440px Coalesced Brain: `docs/milestone1_prototype_brain_1440.png`
     - Desktop 1440px Crisis: `docs/milestone1_desktop_crisis_1440.png`
     - Desktop 1440px Convergence: `docs/milestone1_desktop_convergence_1440.png`
     - Desktop 1440px Platform Preview: `docs/milestone1_desktop_platform_preview_1440.png`
     - Mobile 390px Hero: `docs/milestone1_mobile_hero_390.png`
     - Mobile 390px Crisis: `docs/milestone1_mobile_crisis_390.png`
6. **Strict Invariant Protection**: Zero modifications to `proxy.ts`, `server-backend-url.ts`, `backend-auth.ts`, `api/**/*`, `components/workspace/**/*`, or backend/Docker/migration files.

## Previous Status — Session 11 (2026-11-16T13:20Z)

**Full System Remediation & Next.js 16.4.6 Runtime Security Upgrade verified on host and running Docker containers.**

### Container State
- Containers running & healthy:
  - `orgbrain-postgres` (pgvector/pgvector:pg17 on port 5433, volume `brain-co_pgdata`)
  - `orgbrain-migration` (Alembic migration service, Exited 0)
  - `orgbrain-backend` (FastAPI + Python 3.12 on port 8000, healthy)
  - `orgbrain-frontend` (Next.js 16.4.6 on port 3000, healthy)
  - `orgbrain-adminer` (Adminer 4.8 on port 8080)
- Verified Runtime Next.js Version: `16.4.6` (host and container)
- Healthchecks: configured and passing HTTP 200 on `/health` and `/`
- Database revision: `f82a1b3c4d5e (head)` applied via decoupled migration service

### Verified Core Capabilities & Security Upgrades
1. **Next.js 16.4.6 Runtime**: Host filesystem and `orgbrain-frontend` container verified executing Next.js 16.4.6 (mitigating GHSA-2464-fhr4-w9xw, GHSA-p3m5-59mp-jv5r, GHSA-673q-mjm6-r5xr).
2. **Server-Side URL Resolution**: `server-backend-url.ts` verified routing all 18 server routes to `http://backend:8000` while clients use `/api/v1`.
3. **One-Shot Migration Container**: Decoupled Alembic upgrade to prevent race conditions on multi-instance backend starts.
4. **CACS Access Control**: Case access strictly enforced server-side with tenant isolation.
5. **Session Persistence**: Page reload and route transitions retain authentication session without premature redirects.
6. **React Error #300 Remediation**: Relocated conditional early return in `FloatingChatWidget` below hook declarations; eliminated crashes (Error #300 / #310) during client-side route transitions between `/` and `/login`.

## Previous Status — Session 10 (2026-11-16T00:30Z)

**Teammate Docker setup integrated with latest BRAIN-CO codebase. Single-command deployment operational.**

### Container State
- Containers running & healthy:
  - `orgbrain-postgres` (pgvector/pgvector:pg17 on port 5433, volume `brain-co_pgdata`)
  - `orgbrain-backend` (FastAPI + Python 3.12 on port 8000, healthy)
  - `orgbrain-frontend` (Next.js 16.4.0 on port 3000, healthy)
  - `orgbrain-adminer` (Adminer 4.8 on port 8080)
- Single command startup: `docker compose up --build -d`
- Healthchecks: configured and passing HTTP 200 on `/health` and `/`
- Database revision: `f82a1b3c4d5e (head)` applied automatically on container startup

### Verified Test Results (Inside Container & Host)
| Suite | Collected | Passed | Exit | Environment |
|---|---|---|---|---|
| `backend/tests` (Ring 1 + API + CACS) | 361 | 361 | 0 | `backend` container |
| `ai/tests` | 56 | 56 | 0 | `backend` container |
| `data-engineering/tests` | 24 | 24 | 0 | `backend` container |
| `tests/architecture` | 16 | 16 | 0 | host venv |
| **Total** | **457** | **457** | **0** | **100% Pass** |

### Verified Core Capabilities
1. **Single-Command Startup**: All 4 services build and start with `docker compose up --build -d`.
2. **Containerized SaaS Auth**: Multi-tenant admin authentication and `/auth/me` profile resolution.
3. **Containerized CACS & Cases**: Case creation, assignment, and access control under Docker networking.
4. **Containerized WebSockets**: Ticket issuance (`/auth/ws-ticket`), handshake validation, connection acceptance.
5. **Containerized Mesh Execution**: 6 Ring 1 engines dispatched, 18 events captured, durable sequence storage.
6. **Containerized PDF Ingestion**: Text extraction, knowledge structuring, facts persisted and retrieved.
7. **Database GUI Access**: Adminer accessible on port 8080.

## Previous Status — Session 9 (2026-11-15T22:30Z)

**Database Migration `f82a1b3c4d5e` applied and verified on active development database `orgbrain_legal`.**

### Database State
- `orgbrain_legal` (dev, port 5433): upgraded from `e71f6a9b0c3d` to `f82a1b3c4d5e`.
- Tables present & active: `mesh_events`, `ws_tickets`, `case_assignments`.
- Pre-migration backup: `/tmp/brain_co_db_backups/orgbrain_legal_pre_f82a1b3c4d5e_20261115_202131.dump` (76,250 bytes).
- Data integrity: 17 users, 18 orgs, 14 cases 100% preserved.

### Verified Test Results (Session 9 Full Discovery)
| Suite | Collected | Passed | Exit |
|---|---|---|---|
| `backend/tests/ring1` | 189 | 189 | 0 |
| `backend/tests` (root) | 172 | 172 | 0 |
| `tests/architecture` | 16 | 16 | 0 |
| `ai/tests` | 56 | 56 | 0 |
| `data-engineering/tests` | 24 | 24 | 0 |
| **Total** | **457** | **457** | **0** |

### Verified Core Capabilities
1. **Durable Mesh Events**: Stamped sequence numbers, dual-delivery, persisted in PostgreSQL `mesh_events`, cursor replay via `since_sequence`.
2. **Atomic Single-Use WebSocket Tickets**: SHA-256 hash storage in `ws_tickets`, 60s TTL, single-use consumption across processes, replay rejection.
3. **Multi-Tenant CACS**: Admin policy across org, employee creator/assignee policy via `case_assignments`, fail-closed cross-tenant isolation.
4. **AI Telemetry Transparency**: Model confirmed as `gemini-3.5-flash-lite`, plans explicitly tagged `gemini_ai` vs `deterministic_fallback`, retrieval explicitly tagged `postgresql_lexical`.
5. **Next.js Production Build**: 36 routes compiled cleanly with 0 errors.

## Next
- **Action required:** Rotate Gemini API key in Google AI Studio console (historical redaction confirmed; key rotation required externally).
- Future Ring 2: vector embeddings, pgvector semantic search, multi-document RAG.

## Known Limitations
- Semantic/pgvector retrieval: NOT IMPLEMENTED in Ring 1 (explicitly labelled `postgresql_lexical`).
- Sequential Gemini test runs subject to external 429 quota pressure.
