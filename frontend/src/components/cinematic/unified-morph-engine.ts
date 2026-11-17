/**
 * Brain-Co Cinematic Redesign — Unified Multi-Target Morphing Engine
 * Executes continuous, scroll-driven GPU morphing of a single unified population
 * of faceted crystalline shards across 7 narrative stages:
 *
 * 0. Hero: Authenticated Gross-Anatomical Human Brain (models/original/brain.glb)
 * 1. Legal / Compliance: Brass Balance Scale on Marble Base
 * 2. Human Resources: 3 Stylized Human Figures & Organizational Network
 * 3. Sales: Volumetric 3D Growth Bars & Golden Ascending Arrow
 * 4. Finance: Tilted Orbital Coin Ring & Central Treasury Stack
 * 5. Operations: 3 Connected Translucent Layer Disks & Flow Conduits
 * 6. Final: Return to Unified System / Coalesced Brain
 *
 * Reference: Organizational Brain Refrence (1).html
 */

import * as THREE from "three";
import {
  createLegalShape,
  createHRShape,
  createSalesShape,
  createFinanceShape,
  createOperationsShape,
  prepGeometryGroup,
  sampleDepartmentShards,
  PALETTE_COLORS,
} from "./department-geometries";
import { BRAIN_COORDS_B64, decodeBase64Float32 } from "./brain-reference-data";

export interface UnifiedEngineConfig {
  shardCount?: number;
  spinSpeed?: number;
  morphSpeed?: number;
}

const UNIFIED_VERTEX_SHADER = /* glsl */ `
attribute vec4 aO, t1, t2, t3, t4, t5, aR, n1, n2, n3, n4, n5;
uniform float uA, uB, uMix, uT, uStr, uF, uBr;
uniform vec3 uRo, uRd, uPal[16];
varying vec3 vC, vBc;
varying float vA;

vec4 getTargetPos(float k) {
  vec4 r = vec4(position, 0.0);
  r = mix(r, t1, step(0.5, k));
  r = mix(r, t2, step(1.5, k));
  r = mix(r, t3, step(2.5, k));
  r = mix(r, t4, step(3.5, k));
  r = mix(r, t5, step(4.5, k));
  return r;
}

vec4 getTargetNorm(float k) {
  vec4 r = n1;
  r = mix(r, n2, step(1.5, k));
  r = mix(r, n3, step(2.5, k));
  r = mix(r, n4, step(3.5, k));
  r = mix(r, n5, step(4.5, k));
  return r;
}

vec3 getFacetOffset(float k, float angle, out vec3 outNormal) {
  vec3 n = k < 0.5 ? aO.xyz : getTargetNorm(k).xyz;
  float sz = k < 0.5 ? uBr * (0.75 + 0.55 * aR.w) : getTargetPos(k).w;
  
  // Deterministic individual tilt per facet
  vec3 tilt = fract(aR.zxw * 91.7 + aR.yzx * 13.1) - 0.5;
  n = normalize(n + tilt * (k < 0.5 ? 1.4 : 0.8));
  outNormal = n;

  vec3 a = normalize(cross(n, abs(n.y) < 0.9 ? vec3(0.0, 1.0, 0.0) : vec3(1.0, 0.0, 0.0)));
  vec3 b = cross(n, a);
  float cornerAngle = angle + floor((aO.w + 0.001) / 16.0) * 2.094395;
  return (a * cos(cornerAngle) + b * sin(cornerAngle)) * sz;
}

float getTargetColorCode(float k) {
  float r = aO.w - floor((aO.w + 0.001) / 16.0) * 16.0;
  return k < 0.5 ? r : getTargetNorm(k).w;
}

vec3 decodePalette(float c) {
  float i = floor(c);
  int idx = int(clamp(i, 0.0, 15.0));
  return uPal[idx] * (0.62 + 0.5 * (c - i));
}

void main() {
  // Hermite smoothstep with random per-shard timing jitter
  float m = clamp((uMix - aR.x * 0.45) / 0.55, 0.0, 1.0);
  m = m * m * (3.0 - 2.0 * m);
  float dispersion = sin(m * 3.14159265);

  vec3 nA, nB;
  vec3 center = mix(getTargetPos(uA).xyz, getTargetPos(uB).xyz, m);
  vec3 offset = mix(getFacetOffset(uA, aR.z * 6.28318, nA), getFacetOffset(uB, aR.z * 6.28318, nB), m);
  vec3 normal = normalize(mix(nA, nB, m));

  // Subtle flight turbulence & respiration drift
  float pre = smoothstep(0.0, 0.06, uMix) * (1.0 - smoothstep(0.0, 0.25, m));
  center += pre * 0.012 * vec3(sin(uT * 37.0 + aR.x * 60.0), sin(uT * 41.0 + aR.y * 60.0), sin(uT * 33.0 + aR.z * 60.0));
  center += 0.008 * vec3(sin(uT * 0.7 + aR.x * 50.0), sin(uT * 0.6 + aR.y * 50.0), sin(uT * 0.8 + aR.z * 50.0));

  // 3D Harmonic Swirl during flight
  vec3 turbulence = vec3(
    sin(center.y * 1.7 + aR.z * 6.0 + uT * 0.5),
    sin(center.z * 1.9 + aR.w * 6.0 + uT * 0.4),
    sin(center.x * 1.8 + aR.y * 6.0 + uT * 0.6)
  );
  center += (turbulence * 0.8 + normalize(aR.yzw - 0.5 + 1e-4) * 0.7) * dispersion;

  float swirlAngle = dispersion * (aR.y - 0.5) * 2.2;
  float cs = cos(swirlAngle), sn = sin(swirlAngle);
  center.xz = mat2(cs, -sn, sn, cs) * center.xz;

  // Tumbling rotation around random 3D unit axis (Rodrigues Formula)
  vec3 tumbleAxis = normalize(aR.wxy - 0.5 + 1e-4);
  float tumbleAngle = dispersion * (aR.w - 0.5) * 10.0 + uT * (aR.x - 0.5) * 0.6;
  offset = offset * cos(tumbleAngle) + cross(tumbleAxis, offset) * sin(tumbleAngle) + tumbleAxis * dot(tumbleAxis, offset) * (1.0 - cos(tumbleAngle));
  offset *= (1.0 + dispersion * 0.5);

  // World and View transform
  vec3 worldPos = (modelMatrix * vec4(center, 1.0)).xyz;

  // Interactive pointer repulsion field
  vec3 q = worldPos - uRo;
  vec3 dv = worldPos - (uRo + uRd * dot(q, uRd));
  worldPos += normalize(dv + 1e-4) * exp(-dot(dv, dv) / 0.35) * uStr * uF;

  // Fresnel silhouette rim glow
  float isBrain = (1.0 - step(0.5, uA)) * (1.0 - m) + (1.0 - step(0.5, uB)) * m;
  float rim = pow(1.0 - abs(dot(normalize(mat3(modelMatrix) * normal), normalize(cameraPosition - worldPos))), 1.6);

  worldPos += mat3(modelMatrix) * offset;
  vec4 mvPosition = viewMatrix * vec4(worldPos, 1.0);
  gl_Position = projectionMatrix * mvPosition;

  // Barycentric corner flag
  float cornerIdx = floor((aO.w + 0.001) / 16.0);
  vBc = vec3(cornerIdx < 0.5 ? 1.0 : 0.0, abs(cornerIdx - 1.0) < 0.5 ? 1.0 : 0.0, cornerIdx > 1.5 ? 1.0 : 0.0);

  // Shard coloring
  vec3 baseColor = mix(decodePalette(getTargetColorCode(uA)), decodePalette(getTargetColorCode(uB)), m);
  float specularSpark = step(0.93, aR.y);
  vC = mix(baseColor, vec3(1.0, 0.95, 0.88), clamp(rim * isBrain * 0.45 + specularSpark * 0.55, 0.0, 0.75));

  // Depth fade
  vA = clamp(1.6 - (-mvPosition.z) * 0.065, 0.4, 1.0) * (0.7 + 0.35 * aR.y) * (1.0 + 0.3 * specularSpark);
}
`;

const UNIFIED_FRAGMENT_SHADER = /* glsl */ `
varying vec3 vC, vBc;
varying float vA;

void main() {
  float minBary = min(min(vBc.x, vBc.y), vBc.z);
  float edgeRing = 1.0 - smoothstep(0.10, 0.22, minBary);

  vec3 finalColor = vC * (0.82 + 0.35 * edgeRing);
  float finalAlpha = (0.24 + 0.55 * edgeRing) * vA;

  // Subtle analog film grain dither to prevent banding
  float noise = fract(sin(dot(gl_FragCoord.xy, vec2(12.9898, 78.233))) * 43758.5453);
  finalColor += (vec3(noise) - 0.5) * 0.018;

  gl_FragColor = vec4(finalColor, finalAlpha);
}
`;

export class UnifiedMorphEngine {
  public worldGroup: THREE.Group;
  public ptsMesh: THREE.Mesh | null = null;
  public uniforms: Record<string, { value: any }>;

  private shardCount: number;
  private morphSpeed: number;
  private spinSpeed: number;

  private targetU: number = 0;
  private currentU: number = 0;
  private rotY: number = 0;
  private lastTime: number = performance.now();

  // Mouse / Pointer Parallax Spring
  private pointerSpring = { x: 0, y: 0, vx: 0, vy: 0, strength: 0, vStrength: 0 };
  private targetPointer = { x: 0, y: 0, on: 0 };
  private raycaster = new THREE.Raycaster();
  private pointerCoords = new THREE.Vector2();

  constructor(scene: THREE.Scene, config: UnifiedEngineConfig = {}) {
    this.worldGroup = new THREE.Group();
    scene.add(this.worldGroup);

    this.shardCount = config.shardCount || 16000;
    this.morphSpeed = config.morphSpeed || 0.08;
    this.spinSpeed = config.spinSpeed || 0.15;

    this.uniforms = {
      uA: { value: 0.0 },
      uB: { value: 1.0 },
      uMix: { value: 0.0 },
      uT: { value: 0.0 },
      uStr: { value: 0.0 },
      uBr: { value: 0.028 },
      uRo: { value: new THREE.Vector3(0, 0, 0) },
      uRd: { value: new THREE.Vector3(0, 0, -1) },
      uF: { value: 0.1 },
      uPal: {
        value: PALETTE_COLORS.map((c) => new THREE.Vector3(c[0], c[1], c[2])),
      },
    };

    this.initFacetPopulation();
  }

  private initFacetPopulation() {
    const N = this.shardCount;
    const V3 = N * 3;

    // 1. Target 0: Authenticated Gross-Anatomical Brain
    const brainCoords = decodeBase64Float32(BRAIN_COORDS_B64);
    const availableBrainShards = brainCoords.length / 3;

    const baseRadius = 0.028;
    this.uniforms.uBr.value = baseRadius;

    const posArray = new Float32Array(V3 * 3);
    const aOArray = new Float32Array(V3 * 4);
    const aRArray = new Float32Array(V3 * 4);

    function mulberry32(a: number) {
      return function () {
        let t = (a += 0x6d2b79f5);
        t = Math.imul(t ^ (t >>> 15), t | 1);
        t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
      };
    }
    const prng = mulberry32(0xda1a7c);

    // Pick Dala color ramp for brain
    const RAMP = [6, 5, 4, 3, 7, 1, 2];
    const pickColorCode = (x: number, y: number, z: number) => {
      const grad = Math.min(1, Math.max(0, 0.5 + 0.3 * (z / 2.16) + 0.18 * (y / 1.4)));
      let idx = Math.min(6, Math.max(0, Math.round(grad * 6 + (prng() - 0.5) * 1.4)));
      const q = prng();
      if (q < 0.12) return prng() < 0.5 ? 9 : 10;
      if (q < 0.20) return prng() < 0.5 ? 0 : 13;
      if (q < 0.26) return prng() < 0.5 ? 8 : 7;
      return RAMP[idx];
    };

    for (let i = 0; i < N; i++) {
      const bIdx = (i % availableBrainShards) * 3;
      const bx = brainCoords[bIdx];
      const by = brainCoords[bIdx + 1];
      const bz = brainCoords[bIdx + 2];

      const len = Math.sqrt(bx * bx + by * by + bz * bz) || 1.0;
      const nx = bx / len;
      const ny = by / len;
      const nz = bz / len;

      const r = [prng(), prng(), prng(), prng()];
      const cd0 = pickColorCode(bx, by, bz) + 0.4 + prng() * 0.55;
      const shift = (prng() - 0.5) * 0.025;

      for (let k = 0; k < 3; k++) {
        const v = i * 3 + k;
        posArray.set([bx + nx * shift, by + ny * shift, bz + nz * shift], v * 3);
        aOArray.set([nx, ny, nz, k * 16.0 + cd0], v * 4);
        aRArray.set(r, v * 4);
      }
    }

    // 2. Generate and sample department shapes 1 through 5
    const shapeBuilders = [
      createLegalShape,
      createHRShape,
      createSalesShape,
      createFinanceShape,
      createOperationsShape,
    ];

    const targetPosBuffers: Float32Array[] = [];
    const targetNormBuffers: Float32Array[] = [];

    shapeBuilders.forEach((builder, sIdx) => {
      const shapeGroup = builder();
      this.worldGroup.add(shapeGroup);
      shapeGroup.visible = false; // Solid template hidden; facets sampled

      const prepData = prepGeometryGroup(shapeGroup);
      const sampled = sampleDepartmentShards(prepData, N, baseRadius, 0x1000 + sIdx * 0x333);

      const tp = new Float32Array(V3 * 4);
      const tn = new Float32Array(V3 * 4);

      for (let i = 0; i < N; i++) {
        const spIdx = i * 4;
        const px = sampled.targetPositions[spIdx];
        const py = sampled.targetPositions[spIdx + 1];
        const pz = sampled.targetPositions[spIdx + 2];
        const sz = sampled.targetPositions[spIdx + 3];

        const nx = sampled.targetNormals[spIdx];
        const ny = sampled.targetNormals[spIdx + 1];
        const nz = sampled.targetNormals[spIdx + 2];
        const cc = sampled.targetNormals[spIdx + 3];

        for (let j = 0; j < 3; j++) {
          const v = i * 3 + j;
          tp.set([px, py, pz, sz], v * 4);
          tn.set([nx, ny, nz, cc], v * 4);
        }
      }

      targetPosBuffers.push(tp);
      targetNormBuffers.push(tn);
    });

    // 3. Assemble single BufferGeometry
    const geom = new THREE.BufferGeometry();
    geom.setAttribute("position", new THREE.BufferAttribute(posArray, 3));
    geom.setAttribute("aO", new THREE.BufferAttribute(aOArray, 4));
    geom.setAttribute("aR", new THREE.BufferAttribute(aRArray, 4));

    for (let k = 0; k < 5; k++) {
      geom.setAttribute(`t${k + 1}`, new THREE.BufferAttribute(targetPosBuffers[k], 4));
      geom.setAttribute(`n${k + 1}`, new THREE.BufferAttribute(targetNormBuffers[k], 4));
    }

    const mat = new THREE.ShaderMaterial({
      uniforms: this.uniforms,
      vertexShader: UNIFIED_VERTEX_SHADER,
      fragmentShader: UNIFIED_FRAGMENT_SHADER,
      side: THREE.DoubleSide,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });

    this.ptsMesh = new THREE.Mesh(geom, mat);
    this.ptsMesh.frustumCulled = false;
    this.worldGroup.add(this.ptsMesh);
  }

  public setScrollProgress(uVal: number) {
    this.targetU = Math.max(0.0, Math.min(6.0, uVal));
  }

  public setPointer(x: number, y: number, on: number) {
    this.targetPointer.x = x;
    this.targetPointer.y = y;
    this.targetPointer.on = on;
  }

  public update(time: number, camera: THREE.PerspectiveCamera, innerWidth: number, innerHeight: number) {
    const dt = Math.min((time - this.lastTime) / 1000.0, 0.05);
    this.lastTime = time;
    this.uniforms.uT.value = time / 1000.0;

    // Smooth scroll interpolation
    this.currentU += (this.targetU - this.currentU) * this.morphSpeed;
    const u = this.currentU;

    // Sequence mapping: [0 (Brain), 1 (Legal), 2 (HR), 3 (Sales), 4 (Finance), 5 (Ops), 0 (Brain)]
    const SEQ = [0, 1, 2, 3, 4, 5, 0];
    const i = Math.min(Math.floor(u), 5);
    const f = u - i;

    // Hermite curve for section morph window
    const mx = Math.max(0.0, Math.min(1.0, (f - 0.30) / (0.85 - 0.30)));
    const smoothMx = mx * mx * (3.0 - 2.0 * mx);

    const shapeA = SEQ[i];
    const shapeB = SEQ[i + 1];

    this.uniforms.uA.value = shapeA;
    this.uniforms.uB.value = shapeB;
    this.uniforms.uMix.value = smoothMx;

    // Camera & World Spatial Choreography
    const home = 1.0 - (Math.max(0, Math.min(1, (u - 0.2) / 0.7))) * (1.0 - Math.max(0, Math.min(1, (u - 5.1) / 0.7)));
    const camz = 7.4 + 1.9 * (1.0 - home);
    const halfWidth = Math.tan(0.349) * camz * (innerWidth / innerHeight);
    const isWide = innerWidth > 900;

    // On Hero / Final: Centered or balanced; on Departments: Glides to LEFT
    const targetWorldX = isWide ? -halfWidth * 0.48 * (1.0 - home) + (1.45 * home) : 0.0;
    this.worldGroup.position.x += (targetWorldX - this.worldGroup.position.x) * 0.08;
    this.worldGroup.position.y = isWide ? 0.35 * home : 0.85 * (1.0 - home) + 0.25 * home;

    const scale = (isWide ? 1.0 : 0.82) * (1.25 * home + 1.15 * (1.0 - home));
    this.worldGroup.scale.setScalar(scale);

    // Damped Spring for Pointer Parallax
    const spring = this.pointerSpring;
    spring.vx += (this.targetPointer.x - spring.x) * 0.08;
    spring.vx *= 0.82;
    spring.x += spring.vx;

    spring.vy += (this.targetPointer.y - spring.y) * 0.08;
    spring.vy *= 0.82;
    spring.y += spring.vy;

    spring.vStrength += (this.targetPointer.on - spring.strength) * 0.06;
    spring.vStrength *= 0.82;
    spring.strength += spring.vStrength;

    // Continuous Rotation
    this.rotY += dt * this.spinSpeed;
    this.worldGroup.rotation.y =
      (0.7 + 0.9 * Math.sin(this.rotY * 0.5)) * home +
      0.25 * (1.0 - home) +
      Math.sin(this.rotY) * 0.35 * (1.0 - home) +
      spring.x * 0.25;
    this.worldGroup.rotation.x = -spring.y * 0.12;

    camera.position.set(
      Math.sin(u * 0.9) * 0.4,
      0.3 + Math.sin(u * 1.1) * 0.25,
      camz + Math.sin(u * 0.8) * 0.4 + (innerWidth < 700 ? 2.2 : 0.0)
    );
    camera.lookAt(0, 0, 0);

    // Update Pointer Raycasting
    this.pointerCoords.set(spring.x, spring.y);
    this.raycaster.setFromCamera(this.pointerCoords, camera);
    this.uniforms.uRo.value.copy(this.raycaster.ray.origin);
    this.uniforms.uRd.value.copy(this.raycaster.ray.direction);
    this.uniforms.uStr.value = Math.max(spring.strength, 0.0);
  }

  public dispose() {
    if (this.ptsMesh) {
      this.ptsMesh.geometry.dispose();
      (this.ptsMesh.material as THREE.Material).dispose();
      this.worldGroup.remove(this.ptsMesh);
      this.ptsMesh = null;
    }
    while (this.worldGroup.children.length > 0) {
      const child = this.worldGroup.children[0];
      this.worldGroup.remove(child);
      if (child instanceof THREE.Mesh) {
        child.geometry?.dispose();
        if (Array.isArray(child.material)) child.material.forEach((m) => m.dispose());
        else child.material?.dispose();
      }
    }
  }
}
