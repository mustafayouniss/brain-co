/**
 * Brain-Co Cinematic Redesign — Generative Neural Geometric System
 * Generates multi-scale synaptic nodes, connecting geometric neural filaments,
 * and deterministic multi-state morphing targets:
 * State 1 (Fragmented Shards) -> State 2 (Converging Streamlines) -> State 3/4 (Coherent Dual-Hemisphere Brain).
 * Reference: docs/architecture/cinematic_frontend_redesign_plan.md (V3.3)
 */

import * as THREE from "three";

export function createMulberry32(seed: number = 0x6d2b79f5) {
  let s = seed >>> 0;
  return function next(): number {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * State 1: Fragmented Information Shards (Expansive turbulent field)
 */
export function generateFragmentedState(count: number, prng: () => number): Float32Array {
  const positions = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    // Turbulent, expansive geometric cloud
    const theta = prng() * 2.0 * Math.PI;
    const phi = Math.acos(2.0 * prng() - 1.0);
    const radius = 2.0 + Math.cbrt(prng()) * 3.5;

    // Dispersed turbulent displacement
    const x = radius * Math.sin(phi) * Math.cos(theta);
    const y = radius * Math.sin(phi) * Math.sin(theta) * 0.9;
    const z = radius * Math.cos(phi) * 1.1;

    const idx = i * 3;
    positions[idx] = x;
    positions[idx + 1] = y;
    positions[idx + 2] = z;
  }
  return positions;
}

/**
 * State 2: Converging Streamlines (Vortex of information organizing inward)
 */
export function generateConvergingState(count: number, prng: () => number): Float32Array {
  const positions = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    const t = i / count;
    const spiralAngle = t * Math.PI * 16.0 + prng() * 0.5;
    const height = (prng() - 0.5) * 3.2;
    const radius = 0.8 + Math.sqrt(prng()) * 2.2;

    const x = radius * Math.cos(spiralAngle);
    const y = height + Math.sin(spiralAngle * 0.5) * 0.3;
    const z = radius * Math.sin(spiralAngle);

    const idx = i * 3;
    positions[idx] = x;
    positions[idx + 1] = y;
    positions[idx + 2] = z;
  }
  return positions;
}

/**
 * Harmonic gyri & sulci surface perturbation
 */
function computeGyriHarmonics(theta: number, phi: number): { rho: number; sulcusDepth: number } {
  // Primary lobar expansion
  const primary = 0.10 * Math.sin(3.0 * theta) * Math.cos(4.0 * phi);
  // Secondary gyral folds with phase coupling
  const secondary = 0.085 * Math.sin(7.0 * theta + 1.8 * Math.cos(5.0 * phi)) * Math.cos(6.0 * phi + Math.sin(3.0 * theta));
  // Tertiary sulcal grooves
  const tertiary = 0.045 * Math.sin(13.0 * phi) * Math.cos(11.0 * theta);

  // Inward plunge along medial boundary (phi -> 0 or phi -> PI) forming the deep longitudinal fissure
  const medialAngle = Math.sin(phi);
  const medialSulcus = medialAngle < 0.28 ? -0.12 * (1.0 - medialAngle / 0.28) : 0.0;

  const total = primary + secondary + tertiary + medialSulcus;
  return {
    rho: 1.0 + total,
    sulcusDepth: secondary + tertiary + medialSulcus,
  };
}

/**
 * State 3/4: Coherent Dual-Hemisphere Brain-Co Architecture
 */
export interface AnatomicalBrainData {
  positions: Float32Array;
  normals: Float32Array;
  regions: Float32Array;
  phases: Float32Array;
  sizes: Float32Array;
  alphas: Float32Array;
}

export function generateCoherentBrain(
  count: number,
  dx: number = 0.12,
  seed: number = 1337
): AnatomicalBrainData {
  const prng = createMulberry32(seed);

  const positions = new Float32Array(count * 3);
  const normals = new Float32Array(count * 3);
  const regions = new Float32Array(count);
  const phases = new Float32Array(count);
  const sizes = new Float32Array(count);
  const alphas = new Float32Array(count);

  const sx = 1.18; // Lateral hemisphere width
  const sy = 1.12; // Superior height
  const sz = 1.45; // Anterior-posterior length

  const cerebrumCount = Math.floor(count * 0.78);
  const cerebellumCount = Math.floor(count * 0.14);
  const stemCount = count - cerebrumCount - cerebellumCount;

  // --- CEREBRAL HEMISPHERES ---
  const halfCerebrum = Math.floor(cerebrumCount / 2);

  function makeCerebralPoint(isRight: boolean): {
    p: [number, number, number];
    n: [number, number, number];
    reg: number;
    size: number;
    alpha: number;
  } {
    // Area-uniform stratified sampling
    const u = prng();
    const theta = Math.acos(1.0 - 2.0 * (0.05 + 0.90 * u));
    const phi = 0.04 + prng() * (Math.PI - 0.08);

    const { rho, sulcusDepth } = computeGyriHarmonics(theta, phi);

    // Layering: 70% on outer cortex, 30% deep sub-cortical neural tracts
    const isDeep = prng() > 0.70;
    const depthScale = isDeep ? 0.50 + 0.45 * Math.cbrt(prng()) : 0.94 + 0.06 * prng();
    const r = rho * depthScale;

    let xp = r * Math.sin(theta) * Math.sin(phi);
    let yp = r * Math.cos(theta);
    let zp = r * Math.sin(theta) * Math.cos(phi);

    // Frontal Lobe expansion (+Z)
    if (zp > 0.15) {
      zp *= 1.14;
      yp *= 1.05;
      if (yp > 0.2) xp *= 1.05;
    }

    // Temporal Lobe lateral swell (-Y, lateral X)
    const isTemporal = yp < 0.05 && yp > -0.65 && zp > -0.35 && zp < 0.45;
    if (isTemporal) {
      xp *= 1.25;
      yp *= 1.10;
      zp *= 1.05;
    }

    // Occipital Lobe taper (-Z)
    if (zp < -0.25) {
      zp *= 1.10;
      xp *= 0.92;
    }

    // Lateral Sylvian Fissure Groove
    if (yp > -0.15 && yp < 0.15 && isTemporal) {
      yp -= 0.06;
    }

    // Apply hemisphere lateral displacement dx (creating visible longitudinal fissure)
    const x = isRight ? +(dx + sx * xp) : -(dx + sx * xp);
    const y = sy * yp;
    const z = sz * zp;

    // Normal calculation
    let nx = isRight ? xp / rho : -xp / rho;
    let ny = yp / rho;
    let nz = zp / rho;
    if (sulcusDepth < -0.02) {
      nx *= 0.65;
      nz *= 0.65;
    }
    const len = Math.hypot(nx, ny, nz) || 1.0;
    nx /= len;
    ny /= len;
    nz /= len;

    // Classification
    let reg = 0.0;
    let size = 1.0;
    let alpha = 0.85;

    if (sulcusDepth < -0.03 || isDeep) {
      reg = 1.0; // Deep sulcus / central fissure
      size = 0.80;
      alpha = 0.55;
    } else if (isTemporal) {
      reg = 2.0; // Temporal / lateral tracts
      size = 1.15;
      alpha = 0.88;
    } else if (prng() > 0.86) {
      reg = 3.0; // Active synaptic hotspot
      size = 1.45;
      alpha = 1.0;
    } else {
      reg = 0.0; // Gyrus crest
      size = 1.05;
      alpha = 0.82;
    }

    return { p: [x, y, z], n: [nx, ny, nz], reg, size, alpha };
  }

  // Right hemisphere
  for (let i = 0; i < halfCerebrum; i++) {
    const { p, n, reg, size, alpha } = makeCerebralPoint(true);
    const idx = i * 3;
    positions[idx] = p[0];
    positions[idx + 1] = p[1];
    positions[idx + 2] = p[2];
    normals[idx] = n[0];
    normals[idx + 1] = n[1];
    normals[idx + 2] = n[2];
    regions[i] = reg;
    phases[i] = prng();
    sizes[i] = size;
    alphas[i] = alpha;
  }

  // Left hemisphere
  for (let i = halfCerebrum; i < cerebrumCount; i++) {
    const { p, n, reg, size, alpha } = makeCerebralPoint(false);
    const idx = i * 3;
    positions[idx] = p[0];
    positions[idx + 1] = p[1];
    positions[idx + 2] = p[2];
    normals[idx] = n[0];
    normals[idx + 1] = n[1];
    normals[idx + 2] = n[2];
    regions[i] = reg;
    phases[i] = prng();
    sizes[i] = size;
    alphas[i] = alpha;
  }

  // --- CEREBELLUM ---
  const halfCerebellum = Math.floor(cerebellumCount / 2);
  const cerebellumStart = cerebrumCount;

  function makeCerebellumPoint(isRight: boolean): {
    p: [number, number, number];
    n: [number, number, number];
  } {
    const u = prng() * Math.PI * 2.0;
    const v = prng() * Math.PI;
    const r = 0.30 * Math.cbrt(prng());
    const folia = 0.04 * Math.sin(v * 24.0);

    const cx = isRight ? 0.44 : -0.44;
    const cy = -0.70;
    const cz = -0.72;

    const x = cx + (r + folia) * Math.sin(v) * Math.cos(u) * 1.25;
    const y = cy + (r + folia) * Math.cos(v) * 0.85;
    const z = cz + (r + folia) * Math.sin(v) * Math.sin(u) * 1.05;

    const nx = x - cx;
    const ny = y - cy;
    const nz = z - cz;
    const len = Math.hypot(nx, ny, nz) || 1.0;
    return { p: [x, y, z], n: [nx / len, ny / len, nz / len] };
  }

  for (let i = 0; i < halfCerebellum; i++) {
    const gIdx = cerebellumStart + i;
    const { p, n } = makeCerebellumPoint(true);
    const idx = gIdx * 3;
    positions[idx] = p[0];
    positions[idx + 1] = p[1];
    positions[idx + 2] = p[2];
    normals[idx] = n[0];
    normals[idx + 1] = n[1];
    normals[idx + 2] = n[2];
    regions[gIdx] = 4.0;
    phases[gIdx] = prng();
    sizes[gIdx] = 0.85;
    alphas[gIdx] = 0.70;
  }

  for (let i = halfCerebellum; i < cerebellumCount; i++) {
    const gIdx = cerebellumStart + i;
    const { p, n } = makeCerebellumPoint(false);
    const idx = gIdx * 3;
    positions[idx] = p[0];
    positions[idx + 1] = p[1];
    positions[idx + 2] = p[2];
    normals[idx] = n[0];
    normals[idx + 1] = n[1];
    normals[idx + 2] = n[2];
    regions[gIdx] = 4.0;
    phases[gIdx] = prng();
    sizes[gIdx] = 0.85;
    alphas[gIdx] = 0.70;
  }

  // --- BRAINSTEM ---
  const stemStart = cerebellumStart + cerebellumCount;
  for (let i = stemStart; i < count; i++) {
    const t = (i - stemStart) / stemCount;
    const angle = prng() * Math.PI * 2.0;
    const radius = (0.16 - t * 0.05) * Math.sqrt(prng());
    const x = radius * Math.cos(angle);
    const y = -0.65 - t * 0.75;
    const z = -0.20 - t * 0.12 + radius * Math.sin(angle);

    const idx = i * 3;
    positions[idx] = x;
    positions[idx + 1] = y;
    positions[idx + 2] = z;
    normals[idx] = Math.cos(angle);
    normals[idx + 1] = -0.2;
    normals[idx + 2] = Math.sin(angle);
    regions[i] = 4.0;
    phases[i] = prng();
    sizes[i] = 0.90;
    alphas[i] = 0.65;
  }

  return { positions, normals, regions, phases, sizes, alphas };
}

/**
 * Creates the complete multi-state BufferGeometry for the Luminous Synaptic Nodes
 */
export function createGenerativeNeuralNodes(count: number): THREE.BufferGeometry {
  const geometry = new THREE.BufferGeometry();
  const prng = createMulberry32(42);

  const stateFragmented = generateFragmentedState(count, prng);
  const stateConverging = generateConvergingState(count, prng);
  const brainData = generateCoherentBrain(count, 0.12, 1337);

  // Spatially sort based on target brain position to ensure smooth, non-crossing morph trajectories
  const indices = new Array<number>(count);
  for (let i = 0; i < count; i++) indices[i] = i;

  indices.sort((a, b) => {
    const za = brainData.positions[a * 3 + 2];
    const zb = brainData.positions[b * 3 + 2];
    if (Math.abs(za - zb) > 0.02) return za - zb;
    const ya = brainData.positions[a * 3 + 1];
    const yb = brainData.positions[b * 3 + 1];
    return ya - yb;
  });

  const sFragmented = new Float32Array(count * 3);
  const sConverging = new Float32Array(count * 3);
  const sBrain = new Float32Array(count * 3);
  const sNormals = new Float32Array(count * 3);
  const sRegions = new Float32Array(count);
  const sPhases = new Float32Array(count);
  const sSizes = new Float32Array(count);
  const sAlphas = new Float32Array(count);

  for (let i = 0; i < count; i++) {
    const src = indices[i];
    const src3 = src * 3;
    const dst3 = i * 3;

    sFragmented[dst3] = stateFragmented[src3];
    sFragmented[dst3 + 1] = stateFragmented[src3 + 1];
    sFragmented[dst3 + 2] = stateFragmented[src3 + 2];

    sConverging[dst3] = stateConverging[src3];
    sConverging[dst3 + 1] = stateConverging[src3 + 1];
    sConverging[dst3 + 2] = stateConverging[src3 + 2];

    sBrain[dst3] = brainData.positions[src3];
    sBrain[dst3 + 1] = brainData.positions[src3 + 1];
    sBrain[dst3 + 2] = brainData.positions[src3 + 2];

    sNormals[dst3] = brainData.normals[src3];
    sNormals[dst3 + 1] = brainData.normals[src3 + 1];
    sNormals[dst3 + 2] = brainData.normals[src3 + 2];

    sRegions[i] = brainData.regions[src];
    sPhases[i] = brainData.phases[src];
    sSizes[i] = brainData.sizes[src];
    sAlphas[i] = brainData.alphas[src];
  }

  geometry.setAttribute("position", new THREE.BufferAttribute(sFragmented, 3));
  geometry.setAttribute("aTargetConverge", new THREE.BufferAttribute(sConverging, 3));
  geometry.setAttribute("aTargetBrain", new THREE.BufferAttribute(sBrain, 3));
  geometry.setAttribute("aNormal", new THREE.BufferAttribute(sNormals, 3));
  geometry.setAttribute("aRegion", new THREE.BufferAttribute(sRegions, 1));
  geometry.setAttribute("aPhase", new THREE.BufferAttribute(sPhases, 1));
  geometry.setAttribute("aSize", new THREE.BufferAttribute(sSizes, 1));
  geometry.setAttribute("aAlpha", new THREE.BufferAttribute(sAlphas, 1));

  return geometry;
}

/**
 * Creates the geometric Neural Filaments linking adjacent nodes into a cohesive geometric grid.
 */
export function createGenerativeNeuralLines(
  nodeGeometry: THREE.BufferGeometry,
  lineCount: number
): THREE.BufferGeometry {
  const lineGeometry = new THREE.BufferGeometry();
  const brainPos = nodeGeometry.getAttribute("aTargetBrain");
  const fragPos = nodeGeometry.getAttribute("position");
  const totalNodes = brainPos.count;

  const prng = createMulberry32(888);
  const lineFrag = new Float32Array(lineCount * 6);
  const lineBrain = new Float32Array(lineCount * 6);
  const lineAlpha = new Float32Array(lineCount * 2);

  let createdLines = 0;
  for (let i = 0; i < lineCount; i++) {
    // Pick a primary node
    const n1 = Math.floor(prng() * totalNodes);
    // Find a near neighbor node
    let bestDist = Infinity;
    let n2 = (n1 + 1) % totalNodes;

    // Search window of 25 nearby sorted nodes for natural geometric connectivity
    for (let candidate = 1; candidate <= 25; candidate++) {
      const targetIdx = (n1 + candidate) % totalNodes;
      const dx = brainPos.getX(n1) - brainPos.getX(targetIdx);
      const dy = brainPos.getY(n1) - brainPos.getY(targetIdx);
      const dz = brainPos.getZ(n1) - brainPos.getZ(targetIdx);
      const dist = Math.hypot(dx, dy, dz);
      // Connect if within a tight geometric threshold (not crossing longitudinal fissure)
      if (dist > 0.04 && dist < 0.28 && dist < bestDist) {
        bestDist = dist;
        n2 = targetIdx;
      }
    }

    const baseIdx = createdLines * 6;
    // Fragmented state positions
    lineFrag[baseIdx] = fragPos.getX(n1);
    lineFrag[baseIdx + 1] = fragPos.getY(n1);
    lineFrag[baseIdx + 2] = fragPos.getZ(n1);
    lineFrag[baseIdx + 3] = fragPos.getX(n2);
    lineFrag[baseIdx + 4] = fragPos.getY(n2);
    lineFrag[baseIdx + 5] = fragPos.getZ(n2);

    // Brain state positions
    lineBrain[baseIdx] = brainPos.getX(n1);
    lineBrain[baseIdx + 1] = brainPos.getY(n1);
    lineBrain[baseIdx + 2] = brainPos.getZ(n1);
    lineBrain[baseIdx + 3] = brainPos.getX(n2);
    lineBrain[baseIdx + 4] = brainPos.getY(n2);
    lineBrain[baseIdx + 5] = brainPos.getZ(n2);

    lineAlpha[createdLines * 2] = 0.40;
    lineAlpha[createdLines * 2 + 1] = 0.40;
    createdLines++;
  }

  lineGeometry.setAttribute("position", new THREE.BufferAttribute(lineFrag, 3));
  lineGeometry.setAttribute("aTargetBrain", new THREE.BufferAttribute(lineBrain, 3));
  lineGeometry.setAttribute("aAlpha", new THREE.BufferAttribute(lineAlpha, 1));

  return lineGeometry;
}
