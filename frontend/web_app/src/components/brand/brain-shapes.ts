/**
 * Faithful 2D port of the reference particle shapes from
 * docs/reference/brain-co_V2.html (IIFE sections SHAPE PRIMITIVES / BRAIN /
 * OTHER SHAPES): a side-view neural BRAIN wireframe plus the LEGAL scales,
 * SALES chart and HR team. The reference's Support and Finance shapes are
 * intentionally omitted (V1 has Legal, Sales and HR only).
 *
 * Pure module — Math.random at build time, no React/DOM/3D imports.
 */

export type ShapeKey = "brain" | "legal" | "sales" | "hr";

export const SHAPE_KEYS: readonly ShapeKey[] = ["brain", "legal", "sales", "hr"];

export interface ShapeBuffers {
  X: Float32Array;
  Y: Float32Array;
  Z: Float32Array;
  /** 0 = regular square particle, 1 = bright vertex dot, 2 = hub dot. */
  V: Uint8Array;
}

interface Sampler {
  readonly p?: number;
  readonly v?: number;
  f(): [number, number, number];
}
type Weighted = readonly [number, Sampler];

const R = Math.random;
const TAU = Math.PI * 2;
const PI = Math.PI;

/* ===== SHAPE PRIMITIVES (verbatim from the reference) ===== */

const gj = (): number => (R() - 0.5) * 0.012;
const dir = (): [number, number, number] => {
  const a = R() + R() + R() + R() - 2;
  const b = R() + R() + R() + R() - 2;
  const c = R() + R() + R() + R() - 2;
  const l = Math.hypot(a, b, c) || 1;
  return [a / l, b / l, c / l];
};
const line = (a: readonly number[], b: readonly number[], p = 0): Sampler => ({
  p,
  f: () => {
    const t = R();
    return [
      a[0] + (b[0] - a[0]) * t + gj(),
      a[1] + (b[1] - a[1]) * t + gj(),
      (a[2] || 0) + ((b[2] || 0) - (a[2] || 0)) * t + gj() * 4,
    ];
  },
});
const disc = (x: number, y: number, r: number, p = 0): Sampler => ({
  p,
  f: () => {
    const a = R() * TAU;
    const d = Math.sqrt(R()) * r;
    return [x + Math.cos(a) * d, y + Math.sin(a) * d, (R() - 0.5) * 0.05];
  },
});
const box = (x0: number, y0: number, x1: number, y1: number, p = 0): Sampler => ({
  p,
  f: () => [x0 + (x1 - x0) * R(), y0 + (y1 - y0) * R(), (R() - 0.5) * 0.14],
});
const ball = (x: number, y: number, r: number, p = 0): Sampler => ({
  p,
  f: () => {
    const d = dir();
    const k = r * (0.8 + 0.2 * R());
    return [x + d[0] * k, y + d[1] * k, d[2] * k];
  },
});
const flat = (x: number, y: number, r: number, p = 0): Sampler => ({
  p,
  f: () => {
    const a = R() * TAU;
    const d = Math.sqrt(R()) * r;
    return [x + Math.cos(a) * d, y + (R() - 0.5) * 0.04, Math.sin(a) * d];
  },
});
const bowl = (x: number, y: number, r: number, dp: number, p?: number): Sampler => ({
  p,
  f: () => {
    const a = R() * TAU;
    const u = (R() * PI) / 2;
    return [x + Math.cos(a) * r * Math.cos(u), y - dp * Math.sin(u), Math.sin(a) * r * Math.cos(u)];
  },
});
const rimR = (x: number, y: number, r: number, p?: number): Sampler => ({
  p,
  f: () => {
    const a = R() * TAU;
    return [x + Math.cos(a) * r, y, Math.sin(a) * r];
  },
});
const rect = (
  x0: number,
  y0: number,
  x1: number,
  y1: number,
  w = 0.05,
): Array<readonly [number, Sampler]> => [
  [w, line([x0, y0], [x1, y0])],
  [w, line([x1, y0], [x1, y1])],
  [w, line([x1, y1], [x0, y1])],
  [w, line([x0, y1], [x0, y0])],
];

/** Kept for parity with the reference; only the omitted Support shape uses it. */
export const REFERENCE_PRIMITIVES = { rect };

/* ===== BRAIN: side-view neural wireframe (rim, mesh, sulci, cerebellum, drips) ===== */

const bulge = (c: number): number => 1 + 0.35 * Math.exp(-(((c - 0.15) / 0.4) ** 2));
const rimPt = (t: number): [number, number] => {
  const s = Math.sin(t);
  const c = Math.cos(t);
  return [0.92 * c, 0.18 + (s > 0 ? 0.58 * s : 0.3 * bulge(c) * s)];
};
const inB = (x: number, y: number, k: number): boolean => {
  const c = x / 0.92;
  const yy = y - 0.18;
  const h = yy > 0 ? 0.58 : 0.3 * bulge(c);
  return c * c + (yy / h) * (yy / h) < k * k;
};

const brainP: Weighted[] = [];
/* 1. bright glowing rim */
brainP.push([
  1.0,
  {
    p: 0,
    f: () => {
      const q = rimPt(R() * TAU);
      const o = 1 + (R() - 0.5) * 0.035;
      return [q[0] * o + gj(), (q[1] - 0.18) * o + 0.18 + gj(), 0.3];
    },
  },
]);
/* 2. sparse interior haze */
brainP.push([
  0.35,
  {
    p: 0,
    f: () => {
      let x = 0;
      let y = 0;
      let n = 0;
      do {
        x = (R() * 2 - 1) * 0.9;
        y = 0.18 + (R() * 2 - 1) * 0.58;
        n++;
      } while (n < 20 && !inB(x, y, 0.95));
      return [x, y, (R() - 0.5) * 0.12];
    },
  },
]);
/* 3. vertex mesh: glowing vertices joined into a triangulated-style wireframe */
const verts: Array<[number, number, number]> = [];
for (let t = 0; t < 44; t++) {
  const q = rimPt((t / 44) * TAU);
  verts.push([q[0], q[1], 0.3]);
}
for (let tries = 0; verts.length < 190 && tries < 8000; tries++) {
  const x = (R() * 2 - 1) * 0.9;
  const y = 0.18 + (R() * 2 - 1) * 0.58;
  if (!inB(x, y, 0.9) || verts.some((v) => Math.hypot(v[0] - x, v[1] - y) < 0.082)) continue;
  const r = Math.min(1, (x / 0.92) ** 2 + ((y - 0.18) / 0.58) ** 2);
  verts.push([x, y, 0.05 + 0.3 * Math.sqrt(1 - r)]);
}
const seen = new Set<string>();
verts.forEach((a, i) => {
  verts
    .map((b, j) => [Math.hypot(a[0] - b[0], a[1] - b[1]), j] as const)
    .filter((e) => e[1] !== i)
    .sort((u, v) => u[0] - v[0])
    .slice(0, 4)
    .forEach(([d, j]) => {
      const key = i < j ? `${i}-${j}` : `${j}-${i}`;
      if (d < 0.2 && !seen.has(key)) {
        seen.add(key);
        brainP.push([0.006 + d * 0.03, line(a, verts[j])]);
      }
    });
  brainP.push([
    0.008,
    {
      p: 0,
      v: 1,
      f: () => {
        const d = dir();
        const k = 0.01 * R();
        return [a[0] + d[0] * k, a[1] + d[1] * k, a[2] + d[2] * k];
      },
    },
  ]);
});
/* hub vertices: brighter, larger */
for (let h = 0; h < 14; h++) {
  const a = verts[44 + ((R() * (verts.length - 44)) | 0)];
  brainP.push([
    0.02,
    {
      p: 0,
      v: 2,
      f: () => {
        const d = dir();
        const k = 0.014 * R();
        return [a[0] + d[0] * k, a[1] + d[1] * k, a[2] + d[2] * k];
      },
    },
  ]);
}
/* 4. winding sulci: random walks starting from the rim */
for (let k = 0; k < 13; k++) {
  const q = rimPt(R() * TAU);
  let x = q[0] * 0.96;
  let y = (q[1] - 0.18) * 0.96 + 0.18;
  let a = Math.atan2(0.18 - y, -x) + (R() - 0.5);
  for (let s = 0; s < 10; s++) {
    const nx = x + Math.cos(a) * 0.085;
    const ny = y + Math.sin(a) * 0.085;
    if (!inB(nx, ny, 0.93)) break;
    brainP.push([0.005, line([x, y, 0.12], [nx, ny, 0.12])]);
    x = nx;
    y = ny;
    a += (R() - 0.5) * 1.4;
  }
}
/* 5. cerebellum: outline plus fine striations */
const ccx = -0.42;
const ccy = -0.1;
brainP.push([
  0.16,
  {
    p: 0,
    f: () => {
      const a = R() * TAU;
      return [ccx + 0.3 * Math.cos(a), ccy + 0.16 * Math.sin(a), 0.25];
    },
  },
]);
for (let i = 0; i < 10; i++) {
  const y = ccy + (i - 4.5) * 0.031;
  const hw = 0.3 * Math.sqrt(Math.max(0, 1 - ((y - ccy) / 0.165) ** 2));
  brainP.push([0.03, line([ccx - hw, y, 0.2], [ccx + hw, y - 0.035, 0.2])]);
}
/* 6. brainstem */
brainP.push(
  [0.05, line([-0.06, -0.05, 0.1], [-0.15, -0.42, 0.1])],
  [0.05, line([0.05, -0.1, 0.1], [-0.05, -0.42, 0.1])],
  [0.02, line([-0.15, -0.42, 0.1], [-0.05, -0.42, 0.1])],
);
/* 7. data drips falling from the brain */
for (let i = 0; i < 17; i++) {
  const x = -0.4 + 0.95 * R();
  const y0 = -0.05 - R() * 0.15;
  const y1 = -0.3 - R() * 0.25;
  brainP.push([0.04, line([x, y0, 0], [x, y1, 0])], [0.008, ball(x, y1, 0.02)]);
}

/* ===== OTHER SHAPES (verbatim from the reference) ===== */

const A = 0.75;
const Y = 0.62;
const pan = (s: number, p?: number): Weighted[] => {
  const ax = s * A;
  const o: Weighted[] = [];
  for (let i = 0; i < 3; i++) {
    const t = (i * TAU) / 3;
    o.push([0.035, line([ax, Y, 0], [ax + 0.34 * Math.cos(t), 0, 0.34 * Math.sin(t)], p)]);
  }
  o.push([0.03, rimR(ax, 0, 0.34, p)]);
  o.push([0.09, bowl(ax, 0, 0.34, 0.12, p)]);
  o.push([0.04, ball(ax, 0.09, s < 0 ? 0.1 : 0.14, p)]);
  return o;
};
const legalP: Weighted[] = [
  [0.07, flat(0, -0.86, 0.36)],
  [0.03, flat(0, -0.8, 0.16)],
  [0.1, line([0, -0.82], [0, 0.6])],
  [0.02, ball(0, 0.68, 0.07)],
  [0.1, line([-A, Y], [A, Y], 1)],
  [0.02, ball(-A, Y, 0.045, 1)],
  [0.02, ball(A, Y, 0.045, 1)],
  ...pan(-1, 2),
  ...pan(1, 3),
];

const salesP: Weighted[] = [];
for (let i = 0; i < 5; i++) {
  salesP.push([0.11, box(-0.75 + i * 0.3, -0.65, -0.55 + i * 0.3, -0.43 + 0.2 * i)]);
}
salesP.push(
  [0.06, line([-0.75, 0.05], [-0.15, 0.35])],
  [0.06, line([-0.15, 0.35], [0.15, 0.2])],
  [0.06, line([0.15, 0.2], [0.75, 0.85])],
  [0.03, line([0.75, 0.85], [0.55, 0.83])],
  [0.03, line([0.75, 0.85], [0.72, 0.65])],
);

const person = (x: number, y: number, s: number): Weighted[] => [
  [0.06, disc(x, y + 0.32 * s, 0.11 * s)],
  [
    0.1,
    {
      p: 0,
      f: () => {
        const a = R() * PI;
        const d = Math.sqrt(R());
        return [
          x + Math.cos(a) * 0.27 * s * d,
          y - 0.2 * s + Math.sin(a) * 0.32 * s * d,
          (R() - 0.5) * 0.05,
        ];
      },
    },
  ],
];
const hrP: Weighted[] = [
  ...person(0, -0.05, 1.15),
  ...person(-0.65, -0.2, 0.85),
  ...person(0.65, -0.2, 0.85),
  [0.03, line([-0.65, 0.07], [0, 0.32])],
  [0.03, line([0, 0.32], [0.65, 0.07])],
];

/* ===== build (reference build(): weight-proportional fill + Fisher–Yates) ===== */

const PROMS: Record<ShapeKey, Weighted[]> = {
  brain: brainP,
  legal: legalP,
  sales: salesP,
  hr: hrP,
};

function build(pr: Weighted[], n: number, recentreBrain = false): ShapeBuffers {
  const tot = pr.reduce((a, b) => a + b[0], 0);
  const X = new Float32Array(n);
  const Yy = new Float32Array(n);
  const Z = new Float32Array(n);
  const V = new Uint8Array(n);
  let i = 0;
  pr.forEach(([w, q], k) => {
    const c = k === pr.length - 1 ? n - i : Math.round((n * w) / tot);
    for (let j = 0; j < c && i < n; j++, i++) {
      const v = q.f();
      X[i] = v[0];
      Yy[i] = v[1];
      Z[i] = v[2];
      V[i] = q.v || 0;
    }
  });
  for (; i < n; i++) {
    const v = pr[0][1].f();
    X[i] = v[0];
    Yy[i] = v[1];
    Z[i] = v[2];
  }
  for (let k = n - 1; k > 0; k--) {
    const j = (R() * (k + 1)) | 0;
    [X[k], X[j]] = [X[j], X[k]];
    [Yy[k], Yy[j]] = [Yy[j], Yy[k]];
    [Z[k], Z[j]] = [Z[j], Z[k]];
    [V[k], V[j]] = [V[j], V[k]];
  }
  // Reference init(): the side-view brain sits high, so centre it vertically.
  if (recentreBrain) for (let k = 0; k < n; k++) Yy[k] -= 0.27;
  return { X, Y: Yy, Z, V };
}

/** Builds every shape's per-particle buffers for a fixed particle count. */
export function buildShapeBuffers(n: number): Record<ShapeKey, ShapeBuffers> {
  return {
    brain: build(PROMS.brain, n, true),
    legal: build(PROMS.legal, n),
    sales: build(PROMS.sales, n),
    hr: build(PROMS.hr, n),
  };
}
