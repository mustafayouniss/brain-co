/**
 * Brain-Co Cinematic Redesign — Instanced Crystalline Knowledge Geometry
 * Generates low-poly faceted 3D crystals with independent flat face normals,
 * per-instance dynamic morph targets, tumbling axes, and structural classifications.
 * 
 * Metaphor:
 * State 1 (Fragmented): Dispersed, tumbling knowledge shards (unindexed institutional memory)
 * State 2 (Converging): Magnetic vortex streamlines pulling inward (cognitive ingestion)
 * State 3 (Coherent): Dual-hemisphere crystalline neural architecture (governed organizational brain)
 */

import * as THREE from "three";
import { createMulberry32 } from "./particle-geometry";

export interface InstancedCrystalData {
  geometry: THREE.BufferGeometry;
  count: number;
  sourcePositions: Float32Array;      // State 1: Fragmented
  convergePositions: Float32Array;    // State 2: Converging
  brainPositions: Float32Array;       // State 3: Coherent Brain
  rotationAxes: Float32Array;         // 3D unit axis for tumbling
  rotationSpeeds: Float32Array;       // Tumbling angular velocity
  regions: Float32Array;              // Structural/lobar classification
  phases: Float32Array;               // Pulse wave propagation phase
  scales: Float32Array;               // Size variation
}

/**
 * Creates the base faceted octahedron with non-indexed flat face normals.
 * Each of the 8 triangular faces has 3 independent vertices, ensuring sharp specular glints.
 */
export function createBaseCrystalGeometry(radius: number = 0.045): THREE.BufferGeometry {
  const base = new THREE.OctahedronGeometry(radius, 0);
  const nonIndexed = base.toNonIndexed();
  nonIndexed.computeVertexNormals();
  return nonIndexed;
}

/**
 * Generates instanced crystalline knowledge prisms and their multi-state morph coordinates.
 */
export function createInstancedCrystals(count: number, seed: number = 0x4b7a91): InstancedCrystalData {
  const prng = createMulberry32(seed);
  const geometry = createBaseCrystalGeometry(0.042);

  const sourcePositions = new Float32Array(count * 3);
  const convergePositions = new Float32Array(count * 3);
  const brainPositions = new Float32Array(count * 3);
  const rotationAxes = new Float32Array(count * 3);
  const rotationSpeeds = new Float32Array(count);
  const regions = new Float32Array(count);
  const phases = new Float32Array(count);
  const scales = new Float32Array(count);

  const dxHalfGap = 0.10; // Longitudinal cerebral fissure half-gap

  for (let i = 0; i < count; i++) {
    const idx = i * 3;

    // --- 1. State 1: Fragmented Shards (Turbulent 3D Cloud) ---
    const fragTheta = prng() * 2.0 * Math.PI;
    const fragPhi = Math.acos(2.0 * prng() - 1.0);
    const fragRadius = 1.8 + Math.cbrt(prng()) * 3.2;

    sourcePositions[idx] = fragRadius * Math.sin(fragPhi) * Math.cos(fragTheta);
    sourcePositions[idx + 1] = fragRadius * Math.sin(fragPhi) * Math.sin(fragTheta) * 0.85;
    sourcePositions[idx + 2] = fragRadius * Math.cos(fragPhi) * 1.15;

    // --- 2. State 2: Converging Vortex Streamlines ---
    const tNorm = i / count;
    const spiralAngle = tNorm * Math.PI * 18.0 + prng() * 0.6;
    const spiralRadius = 0.6 + Math.sqrt(prng()) * 2.4;
    const spiralHeight = (prng() - 0.5) * 3.4;

    convergePositions[idx] = spiralRadius * Math.cos(spiralAngle);
    convergePositions[idx + 1] = spiralHeight + Math.sin(spiralAngle * 0.4) * 0.35;
    convergePositions[idx + 2] = spiralRadius * Math.sin(spiralAngle);

    // --- 3. State 3: Anatomical Dual-Hemisphere Crystalline Brain ---
    // Deterministic hemisphere assignment: Left (-1) or Right (+1)
    const hemisphereSign = i % 2 === 0 ? 1 : -1;

    // Equal-area polar angle sampling to eliminate polar clustering
    const uTheta = prng();
    const theta = Math.acos(1.0 - 2.0 * uTheta); // [0, PI]
    const uPhi = prng();
    const phi = uPhi * Math.PI; // [0, PI]

    // Multi-harmonic gyri and sulci convolutions
    const primaryGyrus = 0.11 * Math.sin(3.0 * theta) * Math.cos(4.0 * phi);
    const secondaryGyrus = 0.085 * Math.sin(7.0 * theta + 1.6 * Math.cos(5.0 * phi)) * Math.cos(6.0 * phi);
    const tertiarySulcus = 0.045 * Math.sin(12.0 * phi) * Math.cos(10.0 * theta);

    // Medial inward curving along longitudinal fissure
    const medialProximity = Math.sin(phi);
    const medialFissureDip = medialProximity < 0.30 ? -0.14 * (1.0 - medialProximity / 0.30) : 0.0;

    const baseRadius = 1.0 + primaryGyrus + secondaryGyrus + tertiarySulcus + medialFissureDip;

    // Anatomical ellipsoidal radii (x=lateral, y=superior-inferior, z=anterior-posterior)
    const rx = 1.05;
    const ry = 0.90;
    const rz = 1.25;

    // Brain coordinate parameterization
    const localX = baseRadius * rx * Math.sin(theta) * Math.sin(phi);
    let localY = baseRadius * ry * Math.cos(theta);
    let localZ = baseRadius * rz * Math.sin(theta) * Math.cos(phi);

    // Anatomical lobar sculpting:
    // Frontal pole (superior-anterior): fuller curvature
    if (localZ > 0 && localY > 0) {
      localY *= 1.08;
      localZ *= 1.06;
    }
    // Temporal lobe swell (lateral-inferior-middle)
    if (Math.abs(localX) > 0.45 && localY < -0.15 && Math.abs(localZ) < 0.6) {
      localY -= 0.12;
    }
    // Occipital lobe taper (posterior-inferior)
    if (localZ < -0.5 && localY < 0.1) {
      localZ *= 1.08;
    }

    // Apply strict longitudinal fissure separation along X axis
    const finalBrainX = (localX + dxHalfGap) * hemisphereSign;
    const finalBrainY = localY;
    const finalBrainZ = localZ;

    brainPositions[idx] = finalBrainX;
    brainPositions[idx + 1] = finalBrainY;
    brainPositions[idx + 2] = finalBrainZ;

    // --- 4. Per-Instance Tumbling Dynamic Attributes ---
    // Random 3D rotation unit axis
    const rotTheta = prng() * 2.0 * Math.PI;
    const rotZ = 2.0 * prng() - 1.0;
    const rotR = Math.sqrt(Math.max(0, 1.0 - rotZ * rotZ));
    rotationAxes[idx] = rotR * Math.cos(rotTheta);
    rotationAxes[idx + 1] = rotR * Math.sin(rotTheta);
    rotationAxes[idx + 2] = rotZ;

    // Tumbling angular speed (0.4 to 1.6 rad/s)
    rotationSpeeds[i] = 0.4 + prng() * 1.2;

    // Structural region classification
    let region = 0; // 0: Gyri crests (Electric Blue / Cyan)
    if (medialFissureDip < -0.04 || tertiarySulcus < -0.02) {
      region = 1; // 1: Sulci crevices & longitudinal fissure (Deep Violet / Purple)
    } else if (Math.abs(localX) > 0.55 && localY < 0.0) {
      region = 2; // 2: Temporal lateral lobes (Teal / Jade)
    } else if (prng() < 0.18) {
      region = 3; // 3: Synaptic hotspots / action hubs (Hyper-Magenta / Cyan)
    } else if (localY < -0.55 && localZ < -0.4) {
      region = 4; // 4: Cerebellum / brainstem (Violet / Steel)
    }
    regions[i] = region;

    // Neural pulse wave phase [0, 2PI]
    phases[i] = prng() * Math.PI * 2.0;

    // Per-instance crystal scale variation
    scales[i] = 0.65 + prng() * 0.70;
  }

  return {
    geometry,
    count,
    sourcePositions,
    convergePositions,
    brainPositions,
    rotationAxes,
    rotationSpeeds,
    regions,
    phases,
    scales,
  };
}

/**
 * Generates near-field foreground bokeh shards.
 * These are delicate, luminous crystalline flakes floating close to the camera lens (Z: 3.5 to 4.8),
 * framed along the outer perimeter to add optical depth without interfering with typography.
 */
export function createForegroundBokehCrystals(count: number = 18, seed: number = 0x9e3779): InstancedCrystalData {
  const prng = createMulberry32(seed);
  const geometry = createBaseCrystalGeometry(0.065); // Delicate crystal flakes (not oversized boulders)

  const sourcePositions = new Float32Array(count * 3);
  const convergePositions = new Float32Array(count * 3);
  const brainPositions = new Float32Array(count * 3);
  const rotationAxes = new Float32Array(count * 3);
  const rotationSpeeds = new Float32Array(count);
  const regions = new Float32Array(count);
  const phases = new Float32Array(count);
  const scales = new Float32Array(count);

  for (let i = 0; i < count; i++) {
    const idx = i * 3;

    // Distribute along the perimeter (top, bottom, and right edges) avoiding the central reading zone
    const side = prng();
    let posX = 0;
    let posY = 0;

    if (side < 0.45) {
      // Right hemisphere perimeter (behind/around the 3D nucleus)
      posX = 1.4 + prng() * 1.8;
      posY = (prng() - 0.5) * 3.2;
    } else if (side < 0.75) {
      // Top or bottom margin
      posX = (prng() - 0.5) * 4.0;
      posY = prng() < 0.5 ? 1.4 + prng() * 0.8 : -1.4 - prng() * 0.8;
    } else {
      // Far left exterior boundary
      posX = -2.2 - prng() * 1.2;
      posY = (prng() - 0.5) * 3.0;
    }

    const posZ = 3.6 + prng() * 1.2; // Near-field floating

    sourcePositions[idx] = posX;
    sourcePositions[idx + 1] = posY;
    sourcePositions[idx + 2] = posZ;

    convergePositions[idx] = posX * 0.9;
    convergePositions[idx + 1] = posY * 0.9;
    convergePositions[idx + 2] = posZ;

    brainPositions[idx] = posX;
    brainPositions[idx + 1] = posY;
    brainPositions[idx + 2] = posZ;

    const rotTheta = prng() * 2.0 * Math.PI;
    const rotZ = 2.0 * prng() - 1.0;
    const rotR = Math.sqrt(Math.max(0, 1.0 - rotZ * rotZ));
    rotationAxes[idx] = rotR * Math.cos(rotTheta);
    rotationAxes[idx + 1] = rotR * Math.sin(rotTheta);
    rotationAxes[idx + 2] = rotZ;

    rotationSpeeds[i] = 0.25 + prng() * 0.45; // Slow, organic tumbling drift
    regions[i] = 0; // Silver-cyan crystal sheen
    phases[i] = prng() * Math.PI * 2.0;
    scales[i] = 0.7 + prng() * 0.6;
  }

  return {
    geometry,
    count,
    sourcePositions,
    convergePositions,
    brainPositions,
    rotationAxes,
    rotationSpeeds,
    regions,
    phases,
    scales,
  };
}
