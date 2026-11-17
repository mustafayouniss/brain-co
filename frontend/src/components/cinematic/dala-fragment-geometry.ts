/**
 * Brain-Co Cinematic Engine — Dala-Grade Geometric Fragment System
 * Generates instanced 3D tetrahedral pyramids / faceted crystalline shards with:
 * 1. Independent flat facet normals for sharp specular reflection
 * 2. 4 continuous narrative morph targets:
 *    - State 0: Swirling Cosmic Vortex (Hero)
 *    - State 1: Turbulent Outward Fragmentation (The Crisis)
 *    - State 2: Gravitational Streamline Convergence (Cognitive Ingestion)
 *    - State 3: Coalesced Dual-Hemisphere Brain (The Hive Mind)
 * 3. Multi-tone color palette (Amber/Gold, Royal Violet, Electric Cyan, Platinum White)
 * 4. Spatial depth layering with optical near-field bokeh shards
 */

import * as THREE from "three";
import { createMulberry32 } from "./particle-geometry";

export interface DalaFragmentData {
  geometry: THREE.BufferGeometry;
  count: number;
  target0: Float32Array; // Hero Vortex
  target1: Float32Array; // Fragmentation Scatter
  target2: Float32Array; // Convergence Streamlines
  target3: Float32Array; // Coalesced Brain
  rotData: Float32Array; // Packed vec4: rotAxis.xyz, rotSpeed.w
  paramData: Float32Array; // Packed vec4: scale.x, colorGroup.y, phase.z, depthLayer.w
}

/**
 * Creates the base faceted tetrahedral pyramid geometry with non-indexed flat normals
 * and barycentric coordinates for rendering luminous wireframe edges + translucent glass facets.
 * 4 triangular faces = 12 vertices.
 */
export function createTetrahedralPyramidGeometry(radius: number = 0.048): THREE.BufferGeometry {
  const geom = new THREE.BufferGeometry();

  // Apex and base vertices of a regular tetrahedron
  const a = radius;
  const p0 = new THREE.Vector3(0, a * 1.25, 0); // Apex
  const p1 = new THREE.Vector3(a * Math.cos(0), -a * 0.65, a * Math.sin(0));
  const p2 = new THREE.Vector3(a * Math.cos((2 * Math.PI) / 3), -a * 0.65, a * Math.sin((2 * Math.PI) / 3));
  const p3 = new THREE.Vector3(a * Math.cos((4 * Math.PI) / 3), -a * 0.65, a * Math.sin((4 * Math.PI) / 3));

  // 4 triangular faces (3 vertices each)
  const vertices: number[] = [];
  const normals: number[] = [];
  const barycentric: number[] = [];

  function addFace(v0: THREE.Vector3, v1: THREE.Vector3, v2: THREE.Vector3) {
    const cb = new THREE.Vector3().subVectors(v2, v1);
    const ab = new THREE.Vector3().subVectors(v0, v1);
    const norm = new THREE.Vector3().crossVectors(cb, ab).normalize();

    vertices.push(v0.x, v0.y, v0.z, v1.x, v1.y, v1.z, v2.x, v2.y, v2.z);
    for (let k = 0; k < 3; k++) {
      normals.push(norm.x, norm.y, norm.z);
    }
    // Barycentric coordinates for edge detection
    barycentric.push(1, 0, 0, 0, 1, 0, 0, 0, 1);
  }

  // Face 1: Apex, p1, p2
  addFace(p0, p1, p2);
  // Face 2: Apex, p2, p3
  addFace(p0, p2, p3);
  // Face 3: Apex, p3, p1
  addFace(p0, p3, p1);
  // Face 4: Bottom base (p1, p3, p2)
  addFace(p1, p3, p2);

  geom.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
  geom.setAttribute("normal", new THREE.Float32BufferAttribute(normals, 3));
  geom.setAttribute("aBarycentric", new THREE.Float32BufferAttribute(barycentric, 3));

  return geom;
}

/**
 * Generates the full instanced shard dataset with 4 continuous narrative morph targets.
 */
export function createDalaFragments(count: number, seed: number = 0xda1a7c): DalaFragmentData {
  const prng = createMulberry32(seed);
  const geometry = createTetrahedralPyramidGeometry(0.052);

  const target0 = new Float32Array(count * 3); // Hero Vortex
  const target1 = new Float32Array(count * 3); // Fragmentation Scatter
  const target2 = new Float32Array(count * 3); // Convergence Streamlines
  const target3 = new Float32Array(count * 3); // Coalesced Brain

  const rotData = new Float32Array(count * 4); // Packed vec4: rotAxis.xyz, rotSpeed.w
  const paramData = new Float32Array(count * 4); // Packed vec4: scale.x, colorGroup.y, phase.z, depthLayer.w

  const dxHalfGap = 0.12; // Central fissure gap

  for (let i = 0; i < count; i++) {
    const idx = i * 3;
    const u = i / count;

    // --- State 0: Swirling Cosmic Vortex (Hero) ---
    // In Dala, the vortex sweeps gracefully across the right 55% of the screen.
    // The left 45% (where the editorial headline lives) is clean obsidian void,
    // accented by only a few artistic slow-drifting hollow macro-crystals on the periphery.
    if (i < 6) {
      // Artistic ambient macro anchor crystals (matching Dala's peripheral compositional anchors)
      const anchorPositions = [
        [-2.85, 2.30, 1.5],  // Top-left peripheral anchor (above headline)
        [-3.25, -0.65, 0.8], // Mid-left offscreen edge
        [-2.55, -2.40, 1.2], // Bottom-left void anchor (below CTAs)
        [-1.95, 2.45, 0.5],  // High subtle floater
        [-2.95, 1.40, 1.8],  // Distant near-field bokeh shard
        [-1.75, -2.65, 0.8], // Low ground anchor
      ];
      const p = anchorPositions[i];
      target0[idx] = p[0];
      target0[idx + 1] = p[1];
      target0[idx + 2] = p[2];
    } else {
      // Swirling golden/violet vortex centered on the right side (x = +1.85)
      const vortexAngle = u * Math.PI * 20.0 + prng() * 0.45;
      const vortexRadius = 0.25 + Math.pow(prng(), 0.72) * 1.80;
      const vortexY = (prng() - 0.5) * 4.4;
      const vortexZ = Math.sin(vortexAngle * 0.75) * 1.4 + (prng() - 0.5) * 1.5;

      target0[idx] = 1.85 + vortexRadius * Math.cos(vortexAngle);
      target0[idx + 1] = vortexY + Math.sin(vortexAngle * 0.35) * 0.35;
      target0[idx + 2] = vortexZ;
    }

    // --- State 1: Fragmentation Scatter (The Crisis) ---
    // Violent outward explosion of shards across wide 3D space
    const theta1 = prng() * 2.0 * Math.PI;
    const phi1 = Math.acos(2.0 * prng() - 1.0);
    const radius1 = 2.2 + Math.cbrt(prng()) * 3.8;

    target1[idx] = radius1 * Math.sin(phi1) * Math.cos(theta1);
    target1[idx + 1] = radius1 * Math.sin(phi1) * Math.sin(theta1) * 0.8;
    target1[idx + 2] = radius1 * Math.cos(phi1) * 1.2;

    // --- State 2: Convergence Streamlines (Cognitive Ingestion) ---
    // High-velocity inward helical vortex condensing into an organizing eye
    const spiralTurns = 18.0;
    const spiralAngle = u * Math.PI * spiralTurns + prng() * 0.4;
    const spiralRadius = 0.35 + Math.sqrt(prng()) * 2.0;
    const spiralZ = (prng() - 0.5) * 2.8;

    target2[idx] = spiralRadius * Math.cos(spiralAngle);
    target2[idx + 1] = (u - 0.5) * 3.2 + Math.sin(spiralAngle) * 0.25;
    target2[idx + 2] = spiralZ;

    // --- State 3: Coalesced Dual-Hemisphere Brain (The Hive Mind) ---
    // Anatomical cranial dome with longitudinal fissure and gyri convolutions
    const hemisphereSign = i % 2 === 0 ? 1 : -1;
    const uTheta = prng();
    const thetaBrain = Math.acos(1.0 - 2.0 * uTheta);
    const phiBrain = prng() * Math.PI;

    // Multi-harmonic gyri convolutions
    const gyriPrimary = 0.12 * Math.sin(3.0 * thetaBrain) * Math.cos(4.0 * phiBrain);
    const gyriSecondary = 0.08 * Math.sin(7.0 * thetaBrain + 1.5 * Math.cos(5.0 * phiBrain)) * Math.cos(6.0 * phiBrain);
    const medialFissureDip = Math.sin(phiBrain) < 0.28 ? -0.15 * (1.0 - Math.sin(phiBrain) / 0.28) : 0.0;

    const brainR = 1.0 + gyriPrimary + gyriSecondary + medialFissureDip;
    const rx = 1.08;
    const ry = 0.92;
    const rz = 1.28;

    let bX = brainR * rx * Math.sin(thetaBrain) * Math.sin(phiBrain);
    let bY = brainR * ry * Math.cos(thetaBrain);
    let bZ = brainR * rz * Math.sin(thetaBrain) * Math.cos(phiBrain);

    // Frontal curvature and temporal swell
    if (bZ > 0 && bY > 0) {
      bY *= 1.06;
      bZ *= 1.05;
    }
    if (Math.abs(bX) > 0.45 && bY < -0.15) {
      bY -= 0.12;
    }

    target3[idx] = (bX + dxHalfGap) * hemisphereSign;
    target3[idx + 1] = bY;
    target3[idx + 2] = bZ;

    // --- Dynamic Parameters (Packed vec4s) ---
    // 1. Packed rotData: rotAxis.xyz, rotSpeed.w
    const tRot = prng() * 2.0 * Math.PI;
    const zRot = 2.0 * prng() - 1.0;
    const rRot = Math.sqrt(Math.max(0, 1.0 - zRot * zRot));
    const rIdx = i * 4;
    rotData[rIdx] = rRot * Math.cos(tRot);
    rotData[rIdx + 1] = rRot * Math.sin(tRot);
    rotData[rIdx + 2] = zRot;
    rotData[rIdx + 3] = 0.35 + prng() * 1.25; // rotSpeed

    // 2. Packed paramData: scale.x, colorGroup.y, phase.z, depthLayer.w
    // Multi-scale hierarchy:
    // 3% Macro shards (scale 1.8 to 2.5) — prominent foreground tumbling crystals
    // 35% Meso shards (scale 0.95 to 1.35) — main body facets
    // 62% Micro shards (scale 0.45 to 0.75) — fine glittering cosmic trails
    let shardScale = 0.55;
    const scaleRoll = prng();
    if (i < 6) {
      shardScale = 2.4 + prng() * 0.8; // Majestic large macro crystal on the periphery
    } else if (scaleRoll < 0.03) {
      shardScale = 1.6 + prng() * 0.5; // Foreground macro crystals in vortex
    } else if (scaleRoll < 0.38) {
      shardScale = 0.88 + prng() * 0.35; // Meso shards
    } else {
      shardScale = 0.40 + prng() * 0.25; // Micro glittering shards
    }

    const shardPhase = prng() * Math.PI * 2.0;

    // Color group distribution matching Dala's exact ratio:
    // 45% Amber/Gold (#ffb829, #f59e0b) — warm, luminous core
    // 28% Royal Violet (#7c3aed, #6d28d9) — cognitive depth
    // 15% Electric Cyan (#00f2ff) — synaptic signals
    // 12% Platinum Specular White (#fafaff) — brilliant highlights
    let colorGroup = 0;
    const colorRoll = prng();
    if (colorRoll < 0.45) {
      colorGroup = 0; // Amber/Gold
    } else if (colorRoll < 0.73) {
      colorGroup = 1; // Royal Violet
    } else if (colorRoll < 0.88) {
      colorGroup = 2; // Electric Cyan
    } else {
      colorGroup = 3; // Platinum White
    }

    // Depth layer (for optical depth of field blur):
    // 0: Near plane (Z > 2.2) -> soft optical defocus
    // 1: Mid plane (-1.5 < Z < 2.2) -> pin sharp
    // 2: Far plane (Z < -1.5) -> soft distance haze
    let depthLayer = 1;
    if (target0[idx + 2] > 2.2) {
      depthLayer = 0;
    } else if (target0[idx + 2] < -1.5) {
      depthLayer = 2;
    }

    paramData[rIdx] = shardScale;
    paramData[rIdx + 1] = colorGroup;
    paramData[rIdx + 2] = shardPhase;
    paramData[rIdx + 3] = depthLayer;
  }

  return {
    geometry,
    count,
    target0,
    target1,
    target2,
    target3,
    rotData,
    paramData,
  };
}
