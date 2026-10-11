/**
 * Procedural neuron-field geometry for the site background (pure module):
 * three depth layers of soma outlines, tapering dendrites, synapse dots and
 * pulse tracks, generated in unit space and scaled to the viewport when the
 * artwork is pre-rendered offscreen.
 *
 * The field is built in CLUSTERS (4-7 on desktop, fewer on phones) whose
 * centres sit slightly outside unit space, so near-layer somas can be cropped
 * by the viewport edges like in the reference image. Each soma also exports
 * one of its dendrites as a `somaPath` so the engine can fire a pulse from it
 * when the user hovers a primary button.
 */

export interface Stroke {
  /** flat [x0, y0, x1, y1, …] in unit space */
  pts: number[];
  w: number;
}

export interface SomaShape extends Stroke {
  cx: number;
  cy: number;
  r: number;
}

export interface Dot {
  x: number;
  y: number;
  r: number;
}

export interface PulseTrack {
  pts: number[];
  /** cumulative lengths per point */
  cum: number[];
  total: number;
}

export interface NeuronLayer {
  soma: SomaShape[];
  dendrites: Stroke[];
  dots: Dot[];
  pulses: PulseTrack[];
  /** one dendrite per soma (starts at the soma edge) — CTA-hover pulses */
  somaPaths: PulseTrack[];
}

export interface NeuronField {
  far: NeuronLayer;
  mid: NeuronLayer;
  near: NeuronLayer;
  /** synapse dots that travel into the legal elements on transition */
  travelers: Array<{ x: number; y: number }>;
}

const TAU = Math.PI * 2;

/** Small deterministic PRNG (mulberry32) — same seed → same geometry. */
export function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/* Module-local generator, reseeded by buildNeuronField so every load of the
   site renders the identical field (reproducible evidence, stable art). */
let rnd: () => number = Math.random;

function somaStroke(cx: number, cy: number, r: number, w: number): SomaShape {
  const pts: number[] = [];
  const n = 14;
  for (let i = 0; i <= n; i++) {
    const a = (i / n) * TAU;
    const rr = r * (0.82 + rnd() * 0.36);
    pts.push(cx + Math.cos(a) * rr, cy + Math.sin(a) * rr * 0.92);
  }
  return { pts, w, cx, cy, r };
}

function branch(
  x: number,
  y: number,
  ang: number,
  steps: number,
  step: number,
  w: number,
  out: Stroke[],
  dots: Dot[],
  depth: number,
  maxDepth: number,
): number[] {
  const pts = [x, y];
  let cx = x;
  let cy = y;
  let a = ang;
  for (let i = 0; i < steps; i++) {
    a += (rnd() - 0.5) * 0.9;
    cx += Math.cos(a) * step;
    cy += Math.sin(a) * step;
    pts.push(cx, cy);
    /* deeper recursive branching (depth 3), slightly denser forking */
    if (depth < maxDepth && i > 1 && rnd() < 0.28) {
      const dir = rnd() < 0.5 ? -1 : 1;
      branch(cx, cy, a + dir * (0.5 + rnd() * 0.7), steps - 2, step * 0.72, w * 0.66, out, dots, depth + 1, maxDepth);
      dots.push({ x: cx, y: cy, r: 0.7 + rnd() * 0.7 });
    }
  }
  out.push({ pts, w });
  dots.push({ x: cx, y: cy, r: 0.8 + rnd() * 0.9 });
  return pts;
}

function trackOf(pts: number[], wobble: number): PulseTrack {
  const out: number[] = [];
  for (let i = 0; i < pts.length; i += 2) {
    out.push(pts[i] + (rnd() - 0.5) * wobble, pts[i + 1] + (rnd() - 0.5) * wobble);
  }
  const cum = [0];
  let total = 0;
  for (let i = 2; i < out.length; i += 2) {
    total += Math.hypot(out[i] - out[i - 2], out[i + 1] - out[i - 1]);
    cum.push(total);
  }
  return { pts: out, cum, total: Math.max(total, 1e-4) };
}

interface LayerOpts {
  /** neuron groups — 4-7 on desktop, fewer on phones */
  clusters: number;
  /** base dendrite width (px, tapered per recursion depth) */
  w: number;
  /** soma outline width (px) */
  somaW: number;
}

function buildLayer(count: number, scale: number, wander: number, o: LayerOpts): NeuronLayer {
  const soma: SomaShape[] = [];
  const dendrites: Stroke[] = [];
  const dots: Dot[] = [];
  const pulses: PulseTrack[] = [];
  const somaPaths: PulseTrack[] = [];

  /* Cluster centres spread across and slightly BEYOND unit space so some
     near-layer somas land cropped by the viewport edges (reference style). */
  const cc: Array<[number, number]> = [];
  for (let i = 0; i < o.clusters; i++) cc.push([-0.1 + rnd() * 1.2, -0.08 + rnd() * 1.16]);

  for (let i = 0; i < count; i++) {
    const c = cc[i % cc.length];
    const cx = c[0] + (rnd() - 0.5) * 0.34;
    const cy = c[1] + (rnd() - 0.5) * 0.34;
    const r = scale * (0.55 + rnd() * 0.8);
    soma.push(somaStroke(cx, cy, r, o.somaW));
    const k = 4 + ((rnd() * 4) | 0);
    let firstPath: number[] | null = null;
    for (let b = 0; b < k; b++) {
      const a = (b / k) * TAU + rnd() * 1.2;
      const before = dendrites.length;
      const root = branch(
        cx + Math.cos(a) * r,
        cy + Math.sin(a) * r,
        a,
        7 + ((rnd() * 4) | 0),
        scale * (1.1 + rnd()),
        o.w,
        dendrites,
        dots,
        0,
        3,
      );
      if (!firstPath) firstPath = root;
      if (rnd() < 0.5 && dendrites.length > before) {
        const t = dendrites[before + ((rnd() * (dendrites.length - before)) | 0)];
        pulses.push(trackOf(t.pts, wander));
      }
    }
    if (firstPath) somaPaths.push(trackOf(firstPath, 0));
  }
  return { soma, dendrites, dots, pulses, somaPaths };
}

/** Builds the three-depth neuron field (unit space). Seeded — deterministic. */
export function buildNeuronField(seed = 0x5eed, opts?: { compact?: boolean }): NeuronField {
  rnd = mulberry32(seed);
  const c = opts?.compact
    ? { far: 3, mid: 2, near: 2, scale: 0.82, count: 0.75 }
    : { far: 6, mid: 5, near: 4, scale: 1, count: 1 };
  const far = buildLayer(Math.round(22 * c.count), 0.014 * c.scale, 0.004, {
    clusters: c.far,
    w: 0.85,
    somaW: 1.3,
  });
  const mid = buildLayer(Math.round(15 * c.count), 0.021 * c.scale, 0.006, {
    clusters: c.mid,
    w: 1.3,
    somaW: 1.7,
  });
  const near = buildLayer(Math.round(9 * c.count), 0.034 * c.scale, 0.008, {
    clusters: c.near,
    w: 1.9,
    somaW: 2.2,
  });
  const travelers = [...far.dots, ...mid.dots, ...near.dots]
    .filter(() => rnd() < 0.5)
    .slice(0, 120)
    .map((d) => ({ x: d.x, y: d.y }));
  return { far, mid, near, travelers };
}

/** Point at fraction f along a pulse track (for the travelling light pulses). */
export function pointOnTrack(track: PulseTrack, f: number): [number, number] {
  const d = f * track.total;
  let lo = 0;
  let hi = track.cum.length - 1;
  while (lo < hi - 1) {
    const m = (lo + hi) >> 1;
    if (track.cum[m] <= d) lo = m;
    else hi = m;
  }
  const seg = track.cum[hi] - track.cum[lo] || 1;
  const t = (d - track.cum[lo]) / seg;
  const x = track.pts[lo * 2] + (track.pts[hi * 2] - track.pts[lo * 2]) * t;
  const y = track.pts[lo * 2 + 1] + (track.pts[hi * 2 + 1] - track.pts[lo * 2 + 1]) * t;
  return [x, y];
}
