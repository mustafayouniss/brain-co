/**
 * Brain-Co Cinematic Redesign — Modular Department Target Geometries
 * Generates the 5 high-fidelity 3D target shapes for the scroll-driven morphing sequence:
 * 1. Legal / Compliance: Brass Balance Scale on Marble Base
 * 2. Human Resources: 3 Stylized Human Figures & Organizational Network
 * 3. Sales: Volumetric Growth Bars & Golden Ascending Arrow
 * 4. Finance: Tilted Coin Ring & Central Reserve Stack
 * 5. Operations: 3 Connected Translucent Layer Disks & Vertical Flow Pipelines
 *
 * Implements surface-area-weighted sampling (CDF) to generate exact target attributes
 * (position, size, normal, colorCode) for unified GPU facet population morphing.
 * Reference: Organizational Brain Refrence (1).html
 */

import * as THREE from "three";

// Color Palette Constants matching Dala-Grade Corporate Identity
export const PALETTE_COLORS: [number, number, number][] = [
  [1.0, 0.957, 0.863],   // 0: Warm white / platinum
  [0.918, 0.851, 0.627], // 1: Champagne gold
  [0.804, 0.706, 0.416], // 2: Deep amber gold
  [0.769, 0.71, 0.941],  // 3: Soft lavender
  [0.663, 0.549, 0.902], // 4: Royal purple
  [0.494, 0.357, 0.769], // 5: Deep violet
  [0.357, 0.243, 0.62],  // 6: Midnight indigo
  [0.604, 0.863, 0.922], // 7: Icy cyan
  [0.373, 0.722, 0.8],   // 8: Deep turquoise
  [0.91, 0.663, 0.816],  // 9: Coral pink
  [0.851, 0.541, 0.722], // 10: Rose quartz
  [0.847, 0.824, 0.925], // 11: Silver sheen
  [0.561, 0.659, 0.91],  // 12: Electric blue
  [0.949, 0.933, 0.973], // 13: Pure pearl
  [0.878, 0.722, 0.471], // 14: Polished bronze
  [0.718, 0.604, 0.816], // 15: Muted mauve
];

export interface DepartmentTargetBuffers {
  targetPositions: Float32Array; // N * 4 (x, y, z, size)
  targetNormals: Float32Array;   // N * 4 (nx, ny, nz, colorCode)
}

export interface PrepGeometryData {
  positions: number[];
  normals: number[];
  colors: number[];
  glowFlags: number[];
  cumulativeAreas: number[];
  totalArea: number;
}

function getLuminance(r: number, g: number, b: number): number {
  return 0.299 * r + 0.587 * g + 0.114 * b;
}

export function encodeColorCode(r: number, g: number, b: number): number {
  let bestIdx = 0;
  let bestDist = 999;
  for (let i = 0; i < PALETTE_COLORS.length; i++) {
    const c = PALETTE_COLORS[i];
    const dist = (c[0] - r) ** 2 + (c[1] - g) ** 2 + (c[2] - b) ** 2;
    if (dist < bestDist) {
      bestDist = dist;
      bestIdx = i;
    }
  }
  const c = PALETTE_COLORS[bestIdx];
  const lumRatio = getLuminance(r, g, b) / (getLuminance(c[0], c[1], c[2]) || 1.0);
  const brightnessOffset = Math.min(0.99, Math.max(0, (lumRatio - 0.45) / 0.95));
  return bestIdx + brightnessOffset;
}

function createRod(
  parent: THREE.Group,
  start: THREE.Vector3,
  end: THREE.Vector3,
  radius: number,
  color: number,
  emissive = false
): THREE.Mesh {
  const dir = new THREE.Vector3().subVectors(end, start);
  const len = dir.length();
  const geom = new THREE.CylinderGeometry(radius, radius, len, 8);
  const mat = new THREE.MeshStandardMaterial({
    color,
    metalness: emissive ? 0.2 : 0.85,
    roughness: emissive ? 0.3 : 0.25,
    emissive: emissive ? color : 0x000000,
    emissiveIntensity: emissive ? 1.8 : 0,
  });
  const mesh = new THREE.Mesh(geom, mat);
  mesh.position.copy(start).addScaledVector(dir, 0.5);
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.normalize());
  parent.add(mesh);
  return mesh;
}

function createBall(
  parent: THREE.Group,
  pos: THREE.Vector3,
  radius: number,
  color: number,
  emissive = false
): THREE.Mesh {
  const geom = new THREE.SphereGeometry(radius, 20, 14);
  const mat = new THREE.MeshStandardMaterial({
    color,
    metalness: emissive ? 0.1 : 0.7,
    roughness: emissive ? 0.2 : 0.3,
    emissive: emissive ? color : 0x000000,
    emissiveIntensity: emissive ? 2.2 : 0,
  });
  const mesh = new THREE.Mesh(geom, mat);
  mesh.position.copy(pos);
  parent.add(mesh);
  return mesh;
}

/**
 * Shape 1: Legal / Compliance — Brass Balance Scale on Marble Base
 */
export function createLegalShape(): THREE.Group {
  const G = new THREE.Group();
  const gold = 0xd4af37;
  const marble = 0xe9e4f2;
  const matGold = new THREE.MeshStandardMaterial({ color: gold, metalness: 0.92, roughness: 0.22 });
  const matMarble = new THREE.MeshStandardMaterial({ color: marble, metalness: 0.08, roughness: 0.28 });

  // Marble tiered plinth base
  const b1 = new THREE.Mesh(new THREE.CylinderGeometry(1.25, 1.4, 0.22, 48), matMarble);
  b1.position.y = -2.05;
  G.add(b1);

  const b2 = new THREE.Mesh(new THREE.CylinderGeometry(0.95, 1.05, 0.16, 48), matGold);
  b2.position.y = -1.86;
  G.add(b2);

  // Central column
  const col = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.13, 3.5, 24), matGold);
  col.position.y = -0.1;
  G.add(col);

  // Fulcrum pivot sphere
  createBall(G, new THREE.Vector3(0, 1.78, 0), 0.17, gold);

  // Balance crossbeam tilted at gentle dynamic angle
  createRod(G, new THREE.Vector3(-1.9, 1.62, 0), new THREE.Vector3(1.9, 1.62, 0), 0.065, gold);

  // Dual scale pans suspended via triangular rods
  [-1, 1].forEach((side) => {
    const cx = side * 1.9;
    createBall(G, new THREE.Vector3(cx, 1.62, 0), 0.1, gold);

    for (let k = 0; k < 3; k++) {
      const a = k * 2.0944 + 0.5;
      createRod(
        G,
        new THREE.Vector3(cx, 1.62, 0),
        new THREE.Vector3(cx + 0.78 * Math.cos(a), 0.3, 0.78 * Math.sin(a)),
        0.014,
        0xdde3ee
      );
    }

    // Hemisphere pan bowl
    const panGeom = new THREE.SphereGeometry(0.82, 36, 18, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2);
    const panMesh = new THREE.Mesh(
      panGeom,
      new THREE.MeshStandardMaterial({ color: 0xe6c35c, metalness: 0.95, roughness: 0.2, side: THREE.DoubleSide })
    );
    panMesh.scale.y = 0.5;
    panMesh.position.set(cx, 0.28, 0);
    G.add(panMesh);

    // Pan rim torus
    const rimGeom = new THREE.TorusGeometry(0.82, 0.03, 10, 48);
    const rimMesh = new THREE.Mesh(rimGeom, matGold);
    rimMesh.rotation.x = Math.PI / 2;
    rimMesh.position.set(cx, 0.28, 0);
    G.add(rimMesh);

    // Glowing core weight
    const weightCol = side < 0 ? 0x22d3ee : 0xffb829;
    createBall(G, new THREE.Vector3(cx, 0.2, 0), 0.17, weightCol, true);
  });

  return G;
}

/**
 * Shape 2: Human Resources — 3 Stylized Human Figures & Organizational Network
 */
export function createHRShape(): THREE.Group {
  const G = new THREE.Group();
  const matFig = (col: number) =>
    new THREE.MeshStandardMaterial({ color: col, metalness: 0.25, roughness: 0.35 });

  function addFigure(x: number, y: number, z: number, s: number, col: number) {
    const figGroup = new THREE.Group();
    figGroup.position.set(x, y, z);
    figGroup.scale.setScalar(s);
    G.add(figGroup);

    // Head
    createBall(figGroup, new THREE.Vector3(0, 1.25, 0), 0.3, col);

    // Neck
    const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.12, 0.2, 12), matFig(col));
    neck.position.y = 0.95;
    figGroup.add(neck);

    // Torso
    const torso = new THREE.Mesh(new THREE.SphereGeometry(1, 24, 18), matFig(col));
    torso.scale.set(0.52, 0.78, 0.32);
    torso.position.y = 0.3;
    figGroup.add(torso);

    // Limbs
    [-1, 1].forEach((k) => {
      createRod(figGroup, new THREE.Vector3(k * 0.5, 0.8, 0), new THREE.Vector3(k * 0.68, -0.2, 0.05), 0.1, col);
      createBall(figGroup, new THREE.Vector3(k * 0.68, -0.28, 0.05), 0.1, col);
      createRod(figGroup, new THREE.Vector3(k * 0.2, -0.35, 0), new THREE.Vector3(k * 0.24, -1.5, 0), 0.14, col);
    });
  }

  // 3 Central Figures
  addFigure(0, -0.2, 0, 1.05, 0xe4dcff);
  addFigure(-1.8, -0.5, -0.7, 0.75, 0x5ec9ff);
  addFigure(1.8, -0.5, -0.7, 0.75, 0x6ee7c8);

  // Network Orbit Nodes
  const headCenters = [
    new THREE.Vector3(0, 1.15, 0),
    new THREE.Vector3(-1.8, 0.4, -0.7),
    new THREE.Vector3(1.8, 0.4, -0.7),
  ];
  const networkNodes: THREE.Vector3[] = [];

  for (let i = 0; i < 10; i++) {
    const a = i * 0.6283 + 0.15;
    const p = new THREE.Vector3(Math.cos(a) * 2.3, (i % 3) * 0.8 - 0.8, Math.sin(a) * 1.2 - 0.3);
    networkNodes.push(p);
    createBall(G, p, 0.085, i % 2 === 0 ? 0xffb829 : 0x22d3ee, true);
  }

  networkNodes.forEach((p, i) => {
    createRod(G, p, networkNodes[(i + 1) % 10], 0.012, 0x22d3ee, true);
    if (i % 3 === 0) {
      createRod(G, p, headCenters[i % 3], 0.012, 0x8b5cf6, true);
    }
  });

  return G;
}

/**
 * Shape 3: Sales — Volumetric 3D Growth Bars & Ascending Golden Arrow
 */
export function createSalesShape(): THREE.Group {
  const G = new THREE.Group();
  const barHeights = [0.8, 1.2, 1.0, 1.7, 1.5, 2.3, 2.8];

  // Exponential growth bars
  barHeights.forEach((h, i) => {
    const col = new THREE.Color(0x7c3aed).lerp(new THREE.Color(0x22d3ee), h / 2.8).getHex();
    const barGeom = new THREE.BoxGeometry(0.44, h, 0.44);
    const barMat = new THREE.MeshStandardMaterial({
      color: col,
      metalness: 0.35,
      roughness: 0.25,
      emissive: col,
      emissiveIntensity: 0.3,
    });
    const bar = new THREE.Mesh(barGeom, barMat);
    bar.position.set(-1.8 + i * 0.6, -1.7 + h / 2, i % 2 ? 0.35 : -0.35);
    G.add(bar);
  });

  // Base glass floor plinth
  const floorGeom = new THREE.BoxGeometry(4.5, 0.08, 1.9);
  const floorMat = new THREE.MeshStandardMaterial({
    color: 0x241a52,
    metalness: 0.6,
    roughness: 0.15,
    transparent: true,
    opacity: 0.6,
  });
  const floor = new THREE.Mesh(floorGeom, floorMat);
  floor.position.y = -1.78;
  G.add(floor);

  // Background grid guidelines
  for (let k = 0; k < 4; k++) {
    const gridBar = new THREE.Mesh(
      new THREE.BoxGeometry(4.2, 0.015, 0.015),
      new THREE.MeshStandardMaterial({ color: 0x6d6aa8, emissive: 0x6d6aa8, emissiveIntensity: 0.8 })
    );
    gridBar.position.set(0, -0.9 + k * 0.9, -0.95);
    G.add(gridBar);
  }

  // Golden ascending growth arrow
  const a = new THREE.Vector3(-2.0, -0.9, 1.05);
  const b = new THREE.Vector3(1.6, 1.7, 1.05);
  const arrowDir = b.clone().sub(a).normalize();
  createRod(G, a, b, 0.07, 0xffcf4d, true);

  const coneGeom = new THREE.ConeGeometry(0.22, 0.55, 24);
  const coneMat = new THREE.MeshStandardMaterial({
    color: 0xffcf4d,
    metalness: 0.5,
    roughness: 0.25,
    emissive: 0xffb020,
    emissiveIntensity: 1.5,
  });
  const cone = new THREE.Mesh(coneGeom, coneMat);
  cone.position.copy(b).addScaledVector(arrowDir, 0.2);
  cone.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), arrowDir);
  G.add(cone);

  return G;
}

/**
 * Shape 4: Finance — Tilted Orbital Coin Ring & Central Reserve Stack
 */
export function createFinanceShape(): THREE.Group {
  const G = new THREE.Group();
  const gold = 0xd4af37;
  const matGold = new THREE.MeshStandardMaterial({ color: gold, metalness: 0.95, roughness: 0.2 });

  // Tilted orbital ring
  const ring = new THREE.Group();
  ring.rotation.x = 0.5;
  G.add(ring);

  const torusMesh = new THREE.Mesh(new THREE.TorusGeometry(1.9, 0.045, 12, 64), matGold);
  torusMesh.rotation.x = Math.PI / 2;
  ring.add(torusMesh);

  // Orbital perimeter coins
  const orbitalPositions: THREE.Vector3[] = [];
  for (let k = 0; k < 6; k++) {
    const angle = k * 1.0472;
    const p = new THREE.Vector3(Math.cos(angle) * 1.9, 0, Math.sin(angle) * 1.9);
    orbitalPositions.push(p);

    const coin = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 0.1, 32), matGold);
    coin.position.copy(p);
    ring.add(coin);

    createBall(ring, p.clone().setY(0.14), 0.07, 0x22d3ee, true);

    const q = new THREE.Vector3(Math.cos(angle + 0.5236) * 1.9, 0, Math.sin(angle + 0.5236) * 1.9);
    createBall(ring, q, 0.06, 0xffb829, true);
  }

  // Transaction flow links
  orbitalPositions.forEach((p, k) => {
    createRod(ring, p, new THREE.Vector3(0, 0, 0), 0.012, 0x22d3ee, true);
    createRod(ring, p, orbitalPositions[(k + 2) % 6], 0.008, 0x8b5cf6, true);
  });

  // Central Treasury coin pillar (7 stacked coins)
  for (let i = 0; i < 7; i++) {
    const coinCol = i % 2 === 0 ? 0xe6c35c : gold;
    const stackCoin = new THREE.Mesh(
      new THREE.CylinderGeometry(0.62, 0.62, 0.13, 48),
      new THREE.MeshStandardMaterial({ color: coinCol, metalness: 0.92, roughness: 0.22 })
    );
    stackCoin.position.y = -1.0 + i * 0.16;
    G.add(stackCoin);
  }

  // Top halo ring
  const halo = new THREE.Mesh(
    new THREE.TorusGeometry(0.42, 0.025, 8, 36),
    new THREE.MeshStandardMaterial({ color: 0xdde3ee, metalness: 0.9, roughness: 0.2 })
  );
  halo.rotation.x = Math.PI / 2;
  halo.position.y = 0.2;
  G.add(halo);

  return G;
}

/**
 * Shape 5: Operations — 3 Connected Translucent Layer Disks & Vertical Flow Pipelines
 */
export function createOperationsShape(): THREE.Group {
  const G = new THREE.Group();
  const layerY = [-1.5, 0, 1.5];
  const layerCols = [0x8b5cf6, 0x3b82f6, 0x22d3ee];
  const layerNodes: THREE.Vector3[][] = [];

  layerY.forEach((y, li) => {
    const col = layerCols[li];
    const diskGeom = new THREE.CylinderGeometry(2.5, 2.5, 0.04, 48);
    const diskMat = new THREE.MeshStandardMaterial({
      color: col,
      metalness: 0.1,
      roughness: 0.2,
      transparent: true,
      opacity: 0.22,
      side: THREE.DoubleSide,
      emissive: col,
      emissiveIntensity: 0.3,
    });
    const disk = new THREE.Mesh(diskGeom, diskMat);
    disk.position.y = y;
    G.add(disk);

    // Glowing disk rim
    const rim = new THREE.Mesh(
      new THREE.TorusGeometry(2.5, 0.02, 8, 64),
      new THREE.MeshStandardMaterial({ color: col, emissive: col, emissiveIntensity: 2.0 })
    );
    rim.rotation.x = Math.PI / 2;
    rim.position.y = y;
    G.add(rim);

    // Surface data nodes
    const nodes: THREE.Vector3[] = [];
    for (let i = 0; i < 6; i++) {
      const angle = i * 1.0472 + (li * 0.3);
      const r = 1.1 + (i % 3) * 0.45;
      const p = new THREE.Vector3(Math.cos(angle) * r * 1.05, y, Math.sin(angle) * r);
      nodes.push(p);
      createBall(G, p, 0.15, 0xe9e4f2);
      createBall(G, p, 0.07, col, true);
    }
    layerNodes.push(nodes);

    // Intralayer horizontal connections
    nodes.forEach((p, i) => {
      createRod(G, p, nodes[(i + 1) % 6], 0.012, col, true);
      if (i % 2 === 0) {
        createRod(G, p, nodes[(i + 3) % 6], 0.008, col, true);
      }
    });
  });

  // Vertical Inter-Layer pipeline conduits
  for (let l = 0; l < 2; l++) {
    layerNodes[l].forEach((p, i) => {
      const topP = layerNodes[l + 1][i];
      const linkCol = i % 2 === 0 ? 0xffb829 : 0x22d3ee;
      createRod(G, p, topP, 0.022, linkCol, true);
    });
  }

  return G;
}

/**
 * Surface-Area Weighted Geometry Preprocessor (`prep`)
 * Extracts all triangle faces, computes exact area weights, and builds cumulative distribution function.
 */
export function prepGeometryGroup(group: THREE.Group): PrepGeometryData {
  group.updateMatrixWorld(true);

  const positions: number[] = [];
  const normals: number[] = [];
  const colors: number[] = [];
  const glowFlags: number[] = [];
  const cumulativeAreas: number[] = [];
  let totalArea = 0;

  const a = new THREE.Vector3();
  const b = new THREE.Vector3();
  const c = new THREE.Vector3();
  const nv = new THREE.Vector3();
  const normalMatrix = new THREE.Matrix3();

  group.traverse((obj) => {
    if (!(obj instanceof THREE.Mesh) || !obj.geometry) return;

    const geom = obj.geometry;
    const posAttr = geom.attributes.position;
    const normAttr = geom.attributes.normal;
    const colAttr = geom.attributes.color;
    const indexAttr = geom.index;
    const mat = obj.material as THREE.MeshStandardMaterial;

    normalMatrix.getNormalMatrix(obj.matrixWorld);

    let baseColor = [1.0, 1.0, 1.0];
    let areaWeight = 1.0;
    let isGlowing = 0;

    if (!colAttr && mat) {
      const hasEmissive = (mat.emissiveIntensity || 0) >= 1.0 && mat.emissive && mat.emissive.getHex() !== 0;
      const refColor = hasEmissive ? mat.emissive : mat.color;
      if (refColor) {
        baseColor = [refColor.r, refColor.g, refColor.b];
      }
      if (hasEmissive) {
        areaWeight = 8.0;
        isGlowing = 1;
      } else if (mat.transparent && mat.opacity < 0.3) {
        areaWeight = 0.35;
      }
    }

    const triCount = indexAttr ? indexAttr.count / 3 : posAttr.count / 3;

    for (let t = 0; t < triCount; t++) {
      const i0 = indexAttr ? indexAttr.getX(t * 3) : t * 3;
      const i1 = indexAttr ? indexAttr.getX(t * 3 + 1) : t * 3 + 1;
      const i2 = indexAttr ? indexAttr.getX(t * 3 + 2) : t * 3 + 2;

      a.fromBufferAttribute(posAttr, i0).applyMatrix4(obj.matrixWorld);
      b.fromBufferAttribute(posAttr, i1).applyMatrix4(obj.matrixWorld);
      c.fromBufferAttribute(posAttr, i2).applyMatrix4(obj.matrixWorld);

      const ux = b.x - a.x, uy = b.y - a.y, uz = b.z - a.z;
      const vx = c.x - a.x, vy = c.y - a.y, vz = c.z - a.z;
      const cx = uy * vz - uz * vy;
      const cy = uz * vx - ux * vz;
      const cz = ux * vy - uy * vx;
      const triArea = 0.5 * Math.sqrt(cx * cx + cy * cy + cz * cz) * areaWeight;

      totalArea += triArea;
      cumulativeAreas.push(totalArea);
      glowFlags.push(isGlowing);
      positions.push(a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z);

      const vertIndices = [i0, i1, i2];
      for (let k = 0; k < 3; k++) {
        if (normAttr) {
          nv.fromBufferAttribute(normAttr, vertIndices[k]).applyMatrix3(normalMatrix).normalize();
          normals.push(nv.x, nv.y, nv.z);
        } else {
          normals.push(0, 1, 0);
        }

        if (colAttr) {
          colors.push(
            Math.pow(colAttr.getX(vertIndices[k]), 0.4545),
            Math.pow(colAttr.getY(vertIndices[k]), 0.4545),
            Math.pow(colAttr.getZ(vertIndices[k]), 0.4545)
          );
        } else {
          colors.push(baseColor[0], baseColor[1], baseColor[2]);
        }
      }
    }
  });

  return {
    positions,
    normals,
    colors,
    glowFlags,
    cumulativeAreas,
    totalArea,
  };
}

/**
 * Surface Sampler (`draw`)
 * Draws N uniform points across the preprocessed geometry using binary search over cumulative areas.
 */
export function sampleDepartmentShards(
  prep: PrepGeometryData,
  count: number,
  baseRadius: number,
  seed = 0x5a1e5
): DepartmentTargetBuffers {
  const targetPositions = new Float32Array(count * 4); // x, y, z, size
  const targetNormals = new Float32Array(count * 4);   // nx, ny, nz, colorCode

  function mulberry32(a: number) {
    return function () {
      let t = (a += 0x6d2b79f5);
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  const prng = mulberry32(seed);

  const { positions, normals, colors, glowFlags, cumulativeAreas, totalArea } = prep;
  const triCount = cumulativeAreas.length;

  for (let i = 0; i < count; i++) {
    const r = prng() * totalArea;

    // Binary search in CDF
    let lo = 0;
    let hi = triCount - 1;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (cumulativeAreas[mid] < r) {
        lo = mid + 1;
      } else {
        hi = mid;
      }
    }

    // Barycentric random coordinates
    let u = prng();
    let v = prng();
    if (u + v > 1) {
      u = 1 - u;
      v = 1 - v;
    }
    const w = 1 - u - v;

    const t = lo * 9;
    const px = positions[t] * w + positions[t + 3] * u + positions[t + 6] * v;
    const py = positions[t + 1] * w + positions[t + 4] * u + positions[t + 7] * v;
    const pz = positions[t + 2] * w + positions[t + 5] * u + positions[t + 8] * v;

    const nx = normals[t] * w + normals[t + 3] * u + normals[t + 6] * v;
    const ny = normals[t + 1] * w + normals[t + 4] * u + normals[t + 7] * v;
    const nz = normals[t + 2] * w + normals[t + 5] * u + normals[t + 8] * v;
    const nLen = Math.sqrt(nx * nx + ny * ny + nz * nz) || 1;

    const cr = colors[t] * w + colors[t + 3] * u + colors[t + 6] * v;
    const cg = colors[t + 1] * w + colors[t + 4] * u + colors[t + 7] * v;
    const cb = colors[t + 2] * w + colors[t + 5] * u + colors[t + 8] * v;

    const colorCode = encodeColorCode(cr, cg, cb);
    const isGlowing = glowFlags[lo];
    const shardSize = baseRadius * (isGlowing ? 0.65 : 1.0);

    const idx4 = i * 4;
    targetPositions[idx4] = px;
    targetPositions[idx4 + 1] = py;
    targetPositions[idx4 + 2] = pz;
    targetPositions[idx4 + 3] = shardSize;

    targetNormals[idx4] = nx / nLen;
    targetNormals[idx4 + 1] = ny / nLen;
    targetNormals[idx4 + 2] = nz / nLen;
    targetNormals[idx4 + 3] = colorCode;
  }

  return { targetPositions, targetNormals };
}
