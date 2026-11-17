# Technical Analysis: Organizational Brain Reference Experience & Production Blueprint

**Target Document:** `Organizational Brain Refrence (1).html`  
**Live Browser Reference URL:** `http://localhost:8862/reference.html`  
**Visual Target Anchor:** Dala Hero Brain Reference (`media_1794927730645_f4c9a769.jpg`)  
**Production Destination:** Brain-Co Marketing Frontend (`frontend/src/`)  
**Date:** 2026-11-17  

---

## 1. Executive Summary

The reference HTML document (`Organizational Brain Refrence (1).html`, 35,247 bytes) implements a continuous, scroll-driven WebGL experience where a single unified population of geometric elements (faceted triangular shards) morphs smoothly across 7 distinct narrative stages:

1. **Hero**: Organizational Brain
2. **01 — Legal / Compliance**: Brass Balance Scale on Marble Base
3. **02 — Human Resources**: 3 Connected Human Figures & Organization Network
4. **03 — Sales**: Volumetric Growth Bars & Ascending Golden Growth Arrow
5. **04 — Finance**: Tilted Gold Coin Ring & Central Stack
6. **05 — Operations**: 3 Connected Translucent Layer Disks & Vertical Flow Nodes
7. **Final**: Return to Unified System / Coalesced Brain

The reference achieves its visual impact through a **dual-layer rendering architecture**:
- **Layer 1: Solid PBR Template Meshes** with procedural 3D Simplex/Value noise dissolve shaders (`uD` erosion parameter and luminous emissive edge burn).
- **Layer 2: Unified Morphing Triangular Shard Population** (26,000 facets on desktop, 9,000 on mobile) sampled using surface-area-weighted cumulative distribution functions (CDF). Every shard carries coordinates and normals for all shapes simultaneously, detaching, tumbling organically via 3D noise + rotation around random axes, and re-tiling into the next structure.

---

## 2. Mathematical & Architectural Decompilation

### 2.1 Area-Weighted Facet Sampling (`prep` & `draw`)

In standard point-cloud or particle morphing, naive vertex sampling clumps points on dense sub-meshes and starves large surfaces. The reference solves this with an exact surface-area-weighted CDF:

1. **Geometry Triangle Extraction (`prep`)**:
   For each mesh in the target shape group $G$, it iterates through all triangles $t = (a, b, c)$:
   $$\mathbf{u} = b - a, \quad \mathbf{v} = c - a$$
   $$\text{Area}(t) = \frac{1}{2} \|\mathbf{u} \times \mathbf{v}\| \cdot w_{\text{emissive}}$$
   Where $w_{\text{emissive}} = 8.0$ for luminous core elements and $0.35$ for thin translucent parts.
   The cumulative area array $A_k = \sum_{j=0}^k \text{Area}(t_j)$ is constructed.

2. **Uniform Surface Sampling (`draw`)**:
   For each particle $i \in [0, N-1]$:
   - Draw random scalar $r \sim \mathcal{U}(0, A_{\text{total}})$.
   - Perform binary search over $A$ to find the containing triangle $t$ in $\mathcal{O}(\log M)$.
   - Generate uniform barycentric coordinates $(u, v)$ on the triangle:
     $$\text{If } u + v > 1 \implies u = 1 - u, \quad v = 1 - v; \quad w = 1 - u - v$$
   - Interpolate 3D position $\mathbf{p} = w \cdot a + u \cdot b + v \cdot c$ and surface normal $\mathbf{n}$.
   - Store normal and color code $c \in [0, 15]$ corresponding to the palette index.

### 2.2 Shader Attribute Packing

All $N$ triangles are stored in a single `THREE.BufferGeometry` with $3N$ vertices:
- `position`: Base 3D coordinate for Shape 0 (Brain).
- `aO`: `vec4(normal.xyz, cornerIndex * 16.0 + colorCode)`. The `cornerIndex` $\in \{0, 1, 2\}$ allows the vertex shader to expand each point into a planar triangle facet in screen/world space.
- `aR`: `vec4(random_x, random_y, random_z, random_w)` for deterministic per-shard turbulence, tumble axis, and timing jitter.
- `t1` .. `t5`: `vec4(pos_x, pos_y, pos_z, shard_size)` for shapes 1 through 5.
- `n1` .. `n5`: `vec4(norm_x, norm_y, norm_z, colorCode)` for shapes 1 through 5.

### 2.3 Morphing Vertex Shader Dynamics

During scroll, $u \in [0, 6]$ maps to active source shape $uA \in [0, 5]$ and target shape $uB \in [0, 5]$ with normalized morph parameter $uMix \in [0, 1]$.

1. **Per-Shard Progression Curve with Jitter**:
   $$m_i = \text{clamp}\left(\frac{uMix - aR.x \cdot 0.45}{0.55}, 0, 1\right)$$
   $$m_i = m_i^2 \cdot (3 - 2m_i) \quad \text{(Hermite smoothstep)}$$
   $$d_i = \sin(m_i \cdot \pi) \quad \text{(flight dispersion amplitude, peak at } m_i = 0.5\text{)}$$

2. **Base Position & Tangent Offset Interpolation**:
   $$\mathbf{c} = \text{mix}(\mathbf{p}_{uA}, \mathbf{p}_{uB}, m_i)$$
   $$\mathbf{o} = \text{mix}(\mathbf{off}(uA, aR.z \cdot 2\pi), \mathbf{off}(uB, aR.z \cdot 2\pi), m_i)$$

3. **3D Flight Turbulence & Swirl**:
   $$\mathbf{c} \mathrel{+}= \left(\mathbf{tb} \cdot 0.8 + \text{normalize}(aR.yzw - 0.5) \cdot 0.7\right) \cdot d_i$$
   $$\mathbf{c}_{xz} = \mathbf{R}_{2D}(\theta) \cdot \mathbf{c}_{xz}, \quad \theta = d_i \cdot (aR.y - 0.5) \cdot 2.2$$

4. **Tumbling Rotation Around Random 3D Axes**:
   Each facet rotates around a random unit axis $\mathbf{ax} = \text{normalize}(aR.wxy - 0.5)$:
   $$\theta_{\text{tumble}} = d_i \cdot (aR.w - 0.5) \cdot 10.0 + uT \cdot (aR.x - 0.5) \cdot 0.6$$
   Rodrigues rotation formula is applied to offset vector $\mathbf{o}$:
   $$\mathbf{o}' = \mathbf{o}\cos\theta + (\mathbf{ax} \times \mathbf{o})\sin\theta + \mathbf{ax}(\mathbf{ax} \cdot \mathbf{o})(1 - \cos\theta)$$

5. **Fresnel Silhouette Rim Glow**:
   $$rim = \left(1.0 - |\mathbf{n}_{\text{world}} \cdot \mathbf{v}_{\text{view}}|\right)^{1.6}$$
   Facet color blends toward warm pearl/gold highlights at glancing angles, matching the Dala reference.

### 2.4 Barycentric Wireframe Fragment Shader

The fragment shader uses the interpolated barycentric vector `vBc`:
$$mb = \min(\min(vBc.x, vBc.y), vBc.z)$$
$$ring = 1.0 - \text{smoothstep}(0.10, 0.22, mb)$$
$$\text{FragColor} = \left(\mathbf{vC} \cdot (0.8 + 0.3 \cdot ring), (0.24 + 0.5 \cdot ring) \cdot vA\right)$$

This creates an intense crystalline edge glow along the perimeter of every triangle with a translucent inner body, producing the distinctive Dala wireframe facet look.

---

## 3. Critical Improvements: Reference vs. Brain-Co Production

| Dimension | Reference HTML Implementation | Brain-Co Production Implementation |
|---|---|---|
| **Brain Anatomy** | Procedural `THREE.SphereGeometry` with value noise distortion. Lacks true gyri, cerebellar folia, brainstem, or bilateral hemisphere fissure. | **Gross-Anatomical Model (`brain.glb`)**: 448 parenchymal meshes (cortex, cerebellum, brainstem). True metric dimensions ($13.8 \times 16.1 \times 18.1\text{ cm}$, aspect ratio 1.134). |
| **Material Depth** | Solid mesh + facet overlay with basic dissolve noise. | **Multi-tier Specular Shading**: Flat per-facet normals for crisp Blinn-Phong glints, curvature sulcal depth metric $\kappa$, and single-pass screen-space barycentric edges. |
| **Color Palette** | 16-color rainbow mix (`PALC`) with saturated purple/pink. | **Refined Dala-Grade Corporate Identity**: Deep obsidian background (`#050505`), luminous golden-amber rim (`#ffb829`, `#d4af37`), platinum white crest highlights (`#fafaff`), icy cyan neural accents (`#22d3ee`), soft lavender midtones (`#a98ce6`). |
| **Hero Composition** | Centered in reference HTML; Dala uses left text / right 3D. | **Dala Layout on Hero**: Left text column ($X \in [0\%, 45\%]$) unobstructed obsidian void; 3D brain anchored in right column ($X \approx 75\%$, $Y \approx 50\%$). On scroll to departments, model glides to left ($X \approx -hw \cdot 0.5$) with text card on right. |
| **Mobile Architecture** | Simplistic CSS override with potential clipping. | **Dynamic Viewport Compensation**: Intelligently centers 3D brain on mobile (390×844) below headline with touch-action pan-y, zero horizontal overflow. |
| **Engineering Quality** | Monolithic single-file script (35KB). | **Modular Next.js/React Architecture**: Strict TypeScript types, component isolation, zero memory leaks, full cleanup on unmount, SSR compatibility. |

---

## 4. Target Geometries Specification

1. **Shape 0: Anatomical Brain (16,000 Shards)**:
   - Extracted from `models/original/brain.glb` parenchyma (448 meshes).
   - Bilateral hemispheres, deep longitudinal fissure, temporal lobes, cerebellar horizontal folia, brainstem.
2. **Shape 1: Legal / Compliance — Brass Balance Scale**:
   - Marble base plinth (`CylinderGeometry(1.25, 1.4, 0.22, 64)`).
   - Central brass column (`CylinderGeometry(0.09, 0.12, 3.2, 24)`), finial spire, fulcrum pivot sphere.
   - Horizontal balance beam (`CylinderGeometry(0.045, 0.045, 3.1, 16)`) tilted at $-0.12\text{ rad}$.
   - Dual suspended scale pans (`SphereGeometry` hemisphere bowls) with 3 suspension rods each.
3. **Shape 2: Human Resources — Connected Human Figures**:
   - 3 Stylized human figures (central lead figure + 2 flank figures): head spheres, torso cones, shoulder bars, limb cylinders.
   - Organizational network ring connecting the figures, with employee node spheres and communication links.
4. **Shape 3: Sales — Growth Bars & Ascending Arrow**:
   - Frosted circular glass base plate (`CylinderGeometry(1.6, 1.6, 0.08, 48)`).
   - 5 Volumetric quarterly growth bars with heights increasing exponentially ($0.4 \to 2.4$).
   - 3D Golden ascending growth arrow slicing diagonally upward through the bars.
5. **Shape 4: Finance — Coin Ring & Central Stack**:
   - Tilted orbital torus/ring composed of 12 gold coins (`CylinderGeometry(0.3, 0.3, 0.05, 32)`).
   - Central financial reserve stack (6 stacked gold coins).
   - Interconnected transaction flow rods linking peripheral coins to the center.
6. **Shape 5: Operations — Connected Translucent Layers**:
   - 3 Stacked circular operational layers (Data Layer, Processing Layer, Application Layer) at $y = -1.0, 0.0, +1.0$.
   - Vertical inter-layer conduit rods and active flow node spheres representing real-time system pipelines.

---

## 5. Execution Roadmap

- **Phase 1: Architecture & Department Geometry Generators** (`frontend/src/components/cinematic/department-geometries.ts`).
- **Phase 2: Unified Multi-Target Morph Engine** (`frontend/src/components/cinematic/unified-morph-engine.ts` & custom GLSL shaders).
- **Phase 3: Scroll Narrative Synchronization** (`scroll-narrative-container.tsx` & `page.tsx`).
- **Phase 4: Multi-Viewport Validation & Visual Verification** (Headless Chrome CDP captures across all 12 scroll states + mobile).
