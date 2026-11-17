/**
 * Brain-Co Cinematic Engine — Reference-Driven 3D Brain Geometry System
 * Exact anatomical surface reconstruction of media_1794908221479_00ae4a3b.jpg.
 *
 * Anatomical Profile:
 * - Anterior Frontal Lobe (Left): Rounded frontal pole curving into orbital floor.
 * - Superior Parietal Crest (Top): High convex cranial vault.
 * - Posterior Occipital Lobe (Right): Protruding occipital pole.
 * - Cerebellum (Lower Right): Dedicated rounded foliated sub-structure beneath occipital shelf.
 * - Brainstem (Bottom Center): Vertical neural fiber column.
 * - Temporal Lobe (Lower Left/Mid): Lateral swell with horizontal Sylvian fissure.
 * - Golden-Amber Glowing Rim: Dense perimeter wireframe crystals lining the silhouette.
 * - Platinum Specular Dorsal Body: Uniformly covered lateral cortical face.
 * - Peripheral Anchor Crystals: Exact floating crystals matching reference image.
 */

import * as THREE from "three";
import { createMulberry32 } from "./particle-geometry";
import {
  SHARD_COUNT,
  BRAIN_COORDS_B64,
  BRAIN_NORMALS_B64,
  BRAIN_PARAMS_B64,
  decodeBase64Float32,
} from "./brain-reference-data";

export interface ExactBrainData {
  geometry: THREE.BufferGeometry;
  count: number;
  target0: Float32Array; // Hero Viewport Assembled Brain (Right Column)
  target1: Float32Array; // Fragmentation Scatter
  target2: Float32Array; // Inward Convergence Streamlines
  target3: Float32Array; // Exact Reference Coalesced Brain Shape
  rotData: Float32Array; // Packed vec4: rotAxis.xyz, rotSpeed.w
  paramData: Float32Array; // Packed vec4: scale.x, colorGroup.y, phase.z, depthLayer.w
  normalData: Float32Array; // True outward anatomical surface normals
}

/**
 * Creates the base faceted tetrahedral pyramid geometry with non-indexed flat normals
 * and barycentric coordinates for screen-space wireframe anti-aliasing.
 */
export function createTetrahedralPyramidGeometry(radius: number = 0.046): THREE.BufferGeometry {
  const geom = new THREE.BufferGeometry();

  const a = radius;
  const p0 = new THREE.Vector3(0, a * 1.25, 0); // Apex
  const p1 = new THREE.Vector3(a * Math.cos(0), -a * 0.65, a * Math.sin(0));
  const p2 = new THREE.Vector3(a * Math.cos((2 * Math.PI) / 3), -a * 0.65, a * Math.sin((2 * Math.PI) / 3));
  const p3 = new THREE.Vector3(a * Math.cos((4 * Math.PI) / 3), -a * 0.65, a * Math.sin((4 * Math.PI) / 3));

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
    barycentric.push(1, 0, 0, 0, 1, 0, 0, 0, 1);
  }

  addFace(p0, p1, p2);
  addFace(p0, p2, p3);
  addFace(p0, p3, p1);
  addFace(p1, p3, p2);

  geom.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
  geom.setAttribute("normal", new THREE.Float32BufferAttribute(normals, 3));
  geom.setAttribute("aBarycentric", new THREE.Float32BufferAttribute(barycentric, 3));

  return geom;
}

// Cached decoded datasets for instantaneous zero-latency initialization
let cachedCoords: Float32Array | null = null;
let cachedNormals: Float32Array | null = null;
let cachedParams: Float32Array | null = null;

function getReferenceBrainData(): { coords: Float32Array; normals: Float32Array; params: Float32Array } {
  if (!cachedCoords || !cachedNormals || !cachedParams) {
    cachedCoords = decodeBase64Float32(BRAIN_COORDS_B64);
    cachedNormals = decodeBase64Float32(BRAIN_NORMALS_B64);
    cachedParams = decodeBase64Float32(BRAIN_PARAMS_B64);
  }
  return { coords: cachedCoords, normals: cachedNormals, params: cachedParams };
}

/**
 * Generates the full reference-driven dataset for 3D wireframe crystals.
 */
export function createExactReferenceBrain(count: number = SHARD_COUNT, seed: number = 0xda1a7c): ExactBrainData {
  const prng = createMulberry32(seed);
  const geometry = createTetrahedralPyramidGeometry(0.046);

  const target0 = new Float32Array(count * 3); // Hero Assembled Brain
  const target1 = new Float32Array(count * 3); // Fragmentation Scatter
  const target2 = new Float32Array(count * 3); // Convergence Streamlines
  const target3 = new Float32Array(count * 3); // Centered Reference Brain Shape
  const normalData = new Float32Array(count * 3); // Outward Surface Normals

  const rotData = new Float32Array(count * 4); // Packed vec4: rotAxis.xyz, rotSpeed.w
  const paramData = new Float32Array(count * 4); // Packed vec4: scale.x, colorGroup.y, phase.z, depthLayer.w

  const { coords: refCoords, normals: refNormals, params: refParams } = getReferenceBrainData();
  const availableCount = Math.min(count, SHARD_COUNT);

  // Hero Brain Placement Parameters (matches Dala hero reference media_1794911875437_0bb2c31a.jpg)
  const HERO_BRAIN_SCALE = 0.95;
  const HERO_BRAIN_OFFSET_X = 1.48;
  const HERO_BRAIN_OFFSET_Y = 0.10;

  // Macro crystal explicit Hero positions (matching Dala hero layout)
  const heroMacroPositions: Array<[number, number, number]> = [
    [3.10, 0.22, 1.10],   // Large Teal crystal on right edge
    [1.15, -0.75, 1.85],  // Warm Amber crystal in foreground
    [0.05, 1.70, 0.70],   // High ambient pyramid above crest
    [2.45, 2.05, 0.60],   // High right ambient floater
    [-2.20, 1.85, 0.80],  // High left ambient floater
    [2.80, -1.65, 0.75],  // Low right ambient floater
  ];

  for (let i = 0; i < count; i++) {
    const idx = i * 3;
    const rIdx = i * 4;
    const u = i / count;

    // 1. Target 3: Centered Coalesced Reference Brain
    if (i < availableCount) {
      target3[idx] = refCoords[idx];
      target3[idx + 1] = refCoords[idx + 1];
      target3[idx + 2] = refCoords[idx + 2];

      normalData[idx] = refNormals[idx];
      normalData[idx + 1] = refNormals[idx + 1];
      normalData[idx + 2] = refNormals[idx + 2];

      paramData[rIdx] = refParams[rIdx];         // scale
      paramData[rIdx + 1] = refParams[rIdx + 1]; // colorGroup
      paramData[rIdx + 2] = refParams[rIdx + 2]; // phase
      paramData[rIdx + 3] = refParams[rIdx + 3]; // depthLayer
    } else {
      // Fallback interpolation for larger budgets
      const srcIdx = (i % availableCount) * 3;
      const srcRIdx = (i % availableCount) * 4;
      target3[idx] = refCoords[srcIdx] + (prng() - 0.5) * 0.04;
      target3[idx + 1] = refCoords[srcIdx + 1] + (prng() - 0.5) * 0.04;
      target3[idx + 2] = refCoords[srcIdx + 2] + (prng() - 0.5) * 0.04;

      normalData[idx] = refNormals[srcIdx];
      normalData[idx + 1] = refNormals[srcIdx + 1];
      normalData[idx + 2] = refNormals[srcIdx + 2];

      paramData[rIdx] = refParams[srcRIdx];
      paramData[rIdx + 1] = refParams[srcRIdx + 1];
      paramData[rIdx + 2] = prng() * Math.PI * 2.0;
      paramData[rIdx + 3] = refParams[srcRIdx + 3];
    }

    // Align rotation axis with outward normal, gentle tumble speed
    rotData[rIdx] = normalData[idx];
    rotData[rIdx + 1] = normalData[idx + 1];
    rotData[rIdx + 2] = normalData[idx + 2];
    rotData[rIdx + 3] = 0.45 + prng() * 0.4;

    // 2. Target 0: Hero Viewport Exact Reference Brain (Right Column)
    // Visible immediately on page load without scrolling.
    // Left text column (x in [-3.6, -0.3]) remains pristine obsidian void.
    if (i < 6) {
      // Peripheral macro crystals
      const hPos = heroMacroPositions[i];
      target0[idx] = hPos[0];
      target0[idx + 1] = hPos[1];
      target0[idx + 2] = hPos[2];
    } else {
      target0[idx] = target3[idx] * HERO_BRAIN_SCALE + HERO_BRAIN_OFFSET_X;
      target0[idx + 1] = target3[idx + 1] * HERO_BRAIN_SCALE + HERO_BRAIN_OFFSET_Y;
      target0[idx + 2] = target3[idx + 2] * HERO_BRAIN_SCALE;
    }

    // 3. Target 1: Fragmentation Scatter (The Crisis)
    const theta1 = prng() * 2.0 * Math.PI;
    const phi1 = Math.acos(2.0 * prng() - 1.0);
    const radius1 = 2.4 + Math.cbrt(prng()) * 3.8;

    target1[idx] = radius1 * Math.sin(phi1) * Math.cos(theta1);
    target1[idx + 1] = radius1 * Math.sin(phi1) * Math.sin(theta1) * 0.85;
    target1[idx + 2] = radius1 * Math.cos(phi1) * 1.2;

    // 4. Target 2: Convergence Streamlines (Order from Chaos)
    const spiralTurns = 16.0;
    const spiralAngle = u * Math.PI * spiralTurns + prng() * 0.35;
    const spiralRadius = 0.28 + Math.sqrt(prng()) * 2.1;

    target2[idx] = spiralRadius * Math.cos(spiralAngle);
    target2[idx + 1] = (u - 0.5) * 3.4 + Math.sin(spiralAngle) * 0.22;
    target2[idx + 2] = spiralRadius * Math.sin(spiralAngle) * 0.6 + (prng() - 0.5) * 1.2;

    // 5. Rotation Dynamics (Packed rotData: xyz = outward normal, w = tumble speed)
    rotData[rIdx] = normalData[idx];
    rotData[rIdx + 1] = normalData[idx + 1];
    rotData[rIdx + 2] = normalData[idx + 2];
    rotData[rIdx + 3] = 0.45 + prng() * 0.45;
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
    normalData,
  };
}
