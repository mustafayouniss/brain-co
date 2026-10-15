/**
 * Faithful 2D port of the reference particle shapes from
 * docs/reference/brain-co_V2.html (IIFE sections SHAPE PRIMITIVES / BRAIN /
 * OTHER SHAPES): a side-view neural BRAIN wireframe plus the LEGAL scales,
 * SALES chart and HR team. The reference's Support and Finance shapes are
 * intentionally omitted (V1 has Legal, Sales and HR only).
 *
 * Pure module — no React/DOM/3D imports. The layout is built once at module
 * load from a FIXED seed: the server and the client must produce identical
 * particle positions, or the server-rendered placeholder SVG in
 * brain-hero.tsx would mismatch at hydration (React: "A tree hydrated but
 * some attributes of the server rendered HTML didn't match").
 */

export type ShapeKey = "brain" | "legal" | "sales" | "hr";

export const SHAPE_KEYS: readonly ShapeKey[] = ["brain", "legal", "sales", "hr"];

export interface ShapeBuffers {
  X: Float32Array;
  Y: Float32Array;
  Z: Float32Array;
  /** 0 = regular square particle, 1 = bright vertex dot, 2 = hub dot,
      3 = crisp outline/fissure particle (brain only; drawn smaller + sharper). */
  V: Uint8Array;
}

interface Sampler {
  readonly p?: number;
  readonly v?: number;
  f(): [number, number, number];
}
type Weighted = readonly [number, Sampler];

/** Deterministic PRNG (mulberry32) — same seed, same sequence on server and client. */
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const R = mulberry32(0x9e3779b9);
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

/* ===== BRAIN: side-view anatomical silhouette (facing right) =====
   Redesigned for readable anatomy: length:height ≈ 1.46 — rounded frontal
   lobe (right), parietal dome, tapered occipital pole (left), temporal lobe
   bulging below the lateral (Sylvian) fissure, cerebellum tucked under the
   occipital behind a visible notch, narrower brainstem descending at an
   angle. The outer contour and the three major fissures are dense,
   tight-jittered V=3 "sharp" particles; the fine winding gyri stay at lower
   density so they never blur the main structure. Same bounding box
   (x ±0.92, y +0.70/−0.56) and centre as before. Brain randomness uses its
   own seeded stream so the other shapes' build is independent of it. */

const RB = mulberry32(0x51ed270b);
const bj = (): number => (RB() - 0.5) * 0.003; // tight jitter for sharp lines

const BRAIN_KEYS: ReadonlyArray<readonly [number, number]> = [
  [0.92, 0.06], // frontal pole
  [0.86, 0.3],
  [0.66, 0.54],
  [0.38, 0.66],
  [0.06, 0.7], // parietal high point
  [-0.26, 0.67],
  [-0.52, 0.58],
  [-0.74, 0.42],
  [-0.9, 0.2],
  [-0.92, 0.0], // occipital pole
  [-0.84, -0.14],
  [-0.66, -0.14], // flat underside shelf above the cerebellum
  [-0.46, -0.08],
  [-0.3, -0.06], // Sylvian notch — posterior end of the lateral fissure
  [-0.1, -0.38], // temporal lobe drops
  [0.1, -0.46], // temporal bottom (deepest cerebrum point)
  [0.28, -0.42],
  [0.4, -0.28], // temporal pole
  [0.52, -0.26], // frontal underside — flatter slope
  [0.68, -0.22],
  [0.82, -0.12],
];

/** Closed (contour) or open (fissure) Catmull–Rom spline through keypoints. */
function catmull(
  pts: ReadonlyArray<readonly [number, number]>,
  samples: number,
  closed: boolean,
): Array<[number, number]> {
  const out: Array<[number, number]> = [];
  const n = pts.length;
  const at = (i: number): readonly [number, number] =>
    closed ? pts[((i % n) + n) % n] : pts[Math.max(0, Math.min(n - 1, i))];
  const steps = closed ? samples : samples - 1;
  for (let i = 0; i < samples; i++) {
    const t = (i / steps) * (closed ? n : n - 1);
    const i1 = Math.floor(t);
    const f = t - i1;
    const p0 = at(i1 - 1);
    const p1 = at(i1);
    const p2 = at(i1 + 1);
    const p3 = at(i1 + 2);
    const f2 = f * f;
    const f3 = f2 * f;
    out.push([
      0.5 *
        (2 * p1[0] +
          (-p0[0] + p2[0]) * f +
          (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * f2 +
          (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * f3),
      0.5 *
        (2 * p1[1] +
          (-p0[1] + p2[1]) * f +
          (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * f2 +
          (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * f3),
    ]);
  }
  return out;
}

const RIM = catmull(BRAIN_KEYS, 720, true);
const RIMPOLY = RIM.filter((_, i) => i % 3 === 0); // 240-pt polygon for containment
const rimPt = (t: number): [number, number] => {
  const u = ((((t % TAU) + TAU) % TAU) / TAU) * RIM.length;
  const i = Math.floor(u) % RIM.length;
  const j = (i + 1) % RIM.length;
  const f = u - Math.floor(u);
  return [RIM[i][0] + (RIM[j][0] - RIM[i][0]) * f, RIM[i][1] + (RIM[j][1] - RIM[i][1]) * f];
};
const pip = (x: number, y: number): boolean => {
  let inside = false;
  for (let i = 0, j = RIMPOLY.length - 1; i < RIMPOLY.length; j = i++) {
    const [xi, yi] = RIMPOLY[i];
    const [xj, yj] = RIMPOLY[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
};
const edgeDist = (x: number, y: number): number => {
  let best = 1e9;
  for (let i = 0, j = RIMPOLY.length - 1; i < RIMPOLY.length; j = i++) {
    const [xi, yi] = RIMPOLY[i];
    const [xj, yj] = RIMPOLY[j];
    const dx = xj - xi;
    const dy = yj - yi;
    const len2 = dx * dx + dy * dy || 1e-9;
    const t = Math.max(0, Math.min(1, ((x - xi) * dx + (y - yi) * dy) / len2));
    const d = Math.hypot(x - (xi + dx * t), y - (yi + dy * t));
    if (d < best) best = d;
  }
  return best;
};
/** Inside the silhouette, at least (1-k)·0.6 units from its edge. */
const inB = (x: number, y: number, k: number): boolean => pip(x, y) && edgeDist(x, y) >= (1 - k) * 0.6;

const brainP: Weighted[] = [];
/* 1. crisp outer contour — dense V=3 sharp particles, very low jitter */
brainP.push([
  1.0,
  {
    p: 0,
    v: 3,
    f: () => {
      const q = rimPt(RB() * TAU);
      const o = 1 + (RB() - 0.5) * 0.016;
      return [q[0] * o + bj(), q[1] * o + bj(), 0.3];
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
        x = (RB() * 2 - 1) * 0.92;
        y = (RB() * 2 - 1) * 0.7;
        n++;
      } while (n < 20 && !inB(x, y, 0.95));
      return [x, y, (RB() - 0.5) * 0.12];
    },
  },
]);
/* 3. major fissures — continuous dense sharp lines that read at a glance */
const sharpPath = (
  pts: ReadonlyArray<readonly [number, number]>,
  samples: number,
  p: number,
): Weighted => {
  const poly = catmull(pts, samples, false);
  return [
    p,
    {
      p: 0,
      v: 3,
      f: () => {
        const t = RB() * (poly.length - 1);
        const i = t | 0;
        const f = t - i;
        const a = poly[i];
        const b = poly[Math.min(i + 1, poly.length - 1)];
        return [a[0] + (b[0] - a[0]) * f + bj(), a[1] + (b[1] - a[1]) * f + bj(), 0.24];
      },
    },
  ];
};
brainP.push(
  // lateral (Sylvian) fissure — separates the temporal lobe below
  sharpPath([[-0.3, -0.06], [-0.06, -0.14], [0.16, -0.2], [0.32, -0.22], [0.4, -0.14], [0.42, -0.06]], 72, 0.2),
  // central sulcus — frontal/parietal boundary from the top down
  sharpPath([[0.1, 0.69], [0.18, 0.44], [0.26, 0.2], [0.32, -0.02]], 52, 0.15),
  // parieto-occipital line — short upper-back groove
  sharpPath([[-0.4, 0.63], [-0.44, 0.44], [-0.46, 0.24], [-0.5, 0.1]], 40, 0.1),
);
/* 4. vertex mesh: glowing vertices joined into a triangulated-style wireframe,
      constrained to the new silhouette (chords crossing a fissure notch are
      dropped so the notch stays crisp) */
const verts: Array<[number, number, number]> = [];
for (let t = 0; t < 60; t++) {
  const q = rimPt((t / 60) * TAU);
  verts.push([q[0], q[1], 0.3]);
}
for (let tries = 0; verts.length < 185 && tries < 9000; tries++) {
  const x = (RB() * 2 - 1) * 0.9;
  const y = (RB() * 2 - 1) * 0.7;
  if (!inB(x, y, 0.9) || verts.some((v) => Math.hypot(v[0] - x, v[1] - y) < 0.078)) continue;
  const r = Math.min(1, (x / 0.92) ** 2 + ((y - 0.08) / 0.72) ** 2);
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
      const b = verts[j];
      if (d < 0.2 && !seen.has(key) && inB((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 0.97)) {
        seen.add(key);
        brainP.push([0.006 + d * 0.03, line(a, b)]);
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
  const a = verts[60 + ((R() * (verts.length - 60)) | 0)];
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
/* 5. finer winding gyri — lower density so they never blur the main structure */
for (let k = 0; k < 9; k++) {
  const q = rimPt(RB() * TAU);
  let x = q[0] * 0.94;
  let y = q[1] * 0.94;
  let a = Math.atan2(0.08 - y, -x) + (RB() - 0.5) * 0.8;
  for (let s = 0; s < 8; s++) {
    const nx = x + Math.cos(a) * 0.07;
    const ny = y + Math.sin(a) * 0.07;
    if (!inB(nx, ny, 0.9)) break;
    brainP.push([0.004, line([x, y, 0.12], [nx, ny, 0.12])]);
    x = nx;
    y = ny;
    a += (RB() - 0.5) * 1.1;
  }
}
/* 6. cerebellum: smaller finely striated lobe under the occipital pole,
      separated from the cerebrum by a visible notch */
const ccx = -0.62;
const ccy = -0.36;
const crx = 0.24;
const cry = 0.14;
brainP.push([
  0.14,
  {
    p: 0,
    v: 3,
    f: () => {
      const a = RB() * TAU;
      const o = 1 + (RB() - 0.5) * 0.02;
      return [ccx + crx * Math.cos(a) * o + bj(), ccy + cry * Math.sin(a) * o + bj(), 0.26];
    },
  },
]);
for (let i = 0; i < 9; i++) {
  const y = ccy + (i - 4) * 0.03;
  const hw = crx * Math.sqrt(Math.max(0, 1 - ((y - ccy) / cry) ** 2));
  brainP.push([
    0.016,
    {
      p: 0,
      f: () => {
        const t = RB();
        return [ccx + (t * 2 - 1) * hw, y - 0.03 * Math.sin(PI * t) - 0.02 * t + bj() * 2, 0.22];
      },
    },
  ]);
}
/* 7. brainstem: narrower than the cerebellum, descending at a clear forward
      angle below it — the only place drips are allowed */
const bs0: readonly [number, number] = [-0.26, -0.22];
const bsVec: readonly [number, number] = [-0.09 - bs0[0], -0.55 - bs0[1]];
const bsLen = Math.hypot(bsVec[0], bsVec[1]);
const bsN: readonly [number, number] = [-bsVec[1] / bsLen, bsVec[0] / bsLen];
const stemAt = (t: number, s: number): [number, number] => {
  const hw = 0.065 - 0.02 * t;
  return [bs0[0] + bsVec[0] * t + bsN[0] * s * hw, bs0[1] + bsVec[1] * t + bsN[1] * s * hw];
};
const stemEdge = (s: number): Weighted => [
  0.045,
  {
    p: 0,
    v: 3,
    f: () => {
      const q = stemAt(RB(), s);
      return [q[0] + bj(), q[1] + bj(), 0.16];
    },
  },
];
brainP.push(
  stemEdge(1),
  stemEdge(-1),
  [
    0.03,
    {
      p: 0,
      f: () => {
        const q = stemAt(RB(), RB() * 2 - 1);
        return [q[0], q[1], 0.12];
      },
    },
  ],
);
/* a few short drips from the brainstem tip only */
const drips: ReadonlyArray<readonly [number, number, number, number]> = [
  [-0.05, -0.54, -0.04, -0.63],
  [-0.09, -0.56, -0.08, -0.67],
  [-0.13, -0.58, -0.12, -0.7],
];
for (const [x0, y0, x1, y1] of drips) {
  brainP.push([0.012, line([x0, y0, 0.05], [x1, y1, 0.05])], [0.004, ball(x1, y1, 0.012)]);
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

function build(pr: Weighted[], n: number): ShapeBuffers {
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
  return { X, Y: Yy, Z, V };
}

/** Builds every shape's per-particle buffers for a fixed particle count. */
export function buildShapeBuffers(n: number): Record<ShapeKey, ShapeBuffers> {
  return {
    brain: build(PROMS.brain, n),
    legal: build(PROMS.legal, n),
    sales: build(PROMS.sales, n),
    hr: build(PROMS.hr, n),
  };
}
