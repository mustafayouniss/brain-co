# Anatomical Source Audit & Shard Density Benchmark Report

**Source Model:** `dala-inspection/brain-anatomy-research/models/original/brain.glb`  
**Anatomical Reference:** Z-Anatomy / DBCLS TA2 Gross Human Anatomy  
**Viewer Reference:** `http://localhost:8862/index.html` (Solid GLB) & `http://localhost:8862/preview.html` (Shard Preview)  
**Date:** 2026-11-17  

---

## 1. Anatomical Mesh Audit (563 Total Meshes in GLB)

A comprehensive audit was performed across all 563 meshes in the source asset:

### 1.1 Verified Parenchymal Structures (448 Meshes Retained)
- **Cerebral Cortex (377 meshes)**: All frontal, parietal, temporal, and occipital gyri and sulci across both left and right hemispheres. Includes superior/middle/inferior temporal gyri, precentral/postcentral gyri, lateral sulcus (Sylvian fissure), and central sulcus (Rolandic fissure).
- **Cerebellum (14 meshes)**: Left and right cerebellar hemispheres, horizontal folia, and cerebellar vermis.
- **Brainstem (18 meshes)**: Midbrain, pons, medulla oblongata, superior/inferior colliculi, and cerebellar peduncles.
- **Deep Grey, White Matter & Ventricles (39 meshes)**: Thalami, caudate nuclei, putamen, hippocampi, amygdala, corpus callosum, fornix, and lateral/third/fourth ventricles.

### 1.2 Excluded Non-Parenchymal Structures (115 Meshes Excluded)
- **Vascular System (65 meshes)**: Internal carotid arteries, vertebral arteries, basilar artery, anterior/middle/posterior cerebral arteries, Circle of Willis, and superior sagittal/transverse dural venous sinuses.
- **Cranial Nerves (47 meshes)**: Cranial nerves I through XII, notably the Vagus nerve (CN X) and Accessory nerve (CN XI) which descend up to $47\text{ cm}$ into the thorax/neck and distort the cranial bounding box if not isolated.
- **Meninges & Dural Partitions (3 meshes)**: Falx cerebri, tentorium cerebelli, and dural envelope.

### 1.3 Cranial Metric Dimensions & Proportions
With non-parenchymal neck/vessel structures filtered out, the true anatomical cranial dimensions of the brain are:
- **Width ($X$)**: $13.78\text{ cm}$ ($0.1378\text{ m}$)
- **Height ($Y$)**: $16.08\text{ cm}$ ($0.1608\text{ m}$)
- **Length ($Z$)**: $18.07\text{ cm}$ ($0.1807\text{ m}$)
- **Cranial Aspect Ratio ($Z / X$)**: $1.312$ (matching documented adult neuroanatomy).
- **Total Parenchymal Surface Area**: $0.8095\text{ m}^2$.

---

## 2. Shard Density Benchmarking (8k vs 16k vs 24k)

| Metric | 8,000 Shards | 16,000 Shards (Recommended) | 24,000 Shards |
|---|---|---|---|
| **Average Inter-Shard Spacing** | $0.1180\text{ units}$ | $0.1167\text{ units}$ | $0.1164\text{ units}$ |
| **Minimum Spacing** | $0.0113\text{ units}$ | $0.0139\text{ units}$ | $0.0075\text{ units}$ |
| **Max Surface Gap** | $0.3178\text{ units}$ | $0.2838\text{ units}$ | $0.3542\text{ units}$ |
| **GPU Attribute Memory** | $3.60\text{ MB}$ | $7.20\text{ MB}$ | $10.80\text{ MB}$ |
| **Anatomical Silhouette Fidelity** | Moderate (loose sulci) | **High (crisp gyri & folia)** | High (minimal gain) |
| **Sulcal Crevice Definition** | Porous | **Continuous Obsidian Crevices** | Saturated Overdraw |
| **Surface Coverage** | $74.2\%$ | **$93.8\%$** | $96.1\%$ |

### Recommendation:
**16,000 Shards** provides the optimal balance of crisp sulcal definition, dense cortical coverage, and lightweight GPU memory footprint ($7.20\text{ MB}$).

---

## 3. Visual Validation Across 5 Canonical Anatomical Views

Visual captures recorded from identical camera viewpoints ($R = 3.8\text{ units}$, FOV $38^\circ$):
1. **Front (`benchmark_front_16k.png`)**: Clearly delineates the interhemispheric longitudinal fissure, bilateral frontal lobes, and optic chiasm axis.
2. **Left Lateral (`benchmark_left_lateral_16k.png`)**: Captures the temporal lobe bulge, Sylvian fissure, and occipital convexity.
3. **Right Lateral (`benchmark_right_lateral_16k.png`)**: Matches the Dala hero lateral angle with warm amber cerebellar rim.
4. **Three-Quarter (`benchmark_three_quarter_16k.png`)**: Highlights 3D volumetric depth and dorsal gyral crests.
5. **Posterior (`benchmark_posterior_16k.png`)**: Accurately shows the cerebellar hemispheres and posterior cerebral cortex.
