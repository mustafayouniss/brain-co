/**
 * Minimal line-art legal elements for the site background (pure module).
 * Icon strokes live in local unit coords [-1, 1]; the scales' beam + pans are
 * a separate group so the balance can sway while the pillar stays upright.
 * Colours are applied by the engine (--gold only on the scales).
 */

import { mulberry32, type Stroke } from "./neurons";

export type IconType = "scales" | "gavel" | "column" | "scroll" | "section" | "book";

export interface IconArt {
  /** static part of the icon */
  body: Stroke[];
  /** scales only: beam + chains + pans, rotates about (0, beamPivotY) */
  beam: Stroke[];
}

export interface LegalIcon {
  type: IconType;
  art: IconArt;
  /** centre in unit space */
  x: number;
  y: number;
  /** half-size in unit space */
  s: number;
  /** per-icon phase so sways/staggers never sync */
  phase: number;
}

export interface LegalScene {
  icons: LegalIcon[];
  /** faint connection lines between nearby icons (network idea) */
  links: Array<[number, number]>;
}

/** Beam pivot in local coords (top of the pillar). */
export const BEAM_PIVOT_Y = -0.72;

const line = (x0: number, y0: number, x1: number, y1: number, w = 1): Stroke => ({
  pts: [x0, y0, x1, y1],
  w,
});

const arc = (cx: number, cy: number, r: number, a0: number, a1: number, w = 1): Stroke => {
  const pts: number[] = [];
  const n = 9;
  for (let i = 0; i <= n; i++) {
    const a = a0 + (a1 - a0) * (i / n);
    pts.push(cx + Math.cos(a) * r, cy + Math.sin(a) * r);
  }
  return { pts, w };
};

const rect = (x0: number, y0: number, x1: number, y1: number, w = 1): Stroke[] => [
  line(x0, y0, x1, y0, w),
  line(x1, y0, x1, y1, w),
  line(x1, y1, x0, y1, w),
  line(x0, y1, x0, y0, w),
];

function iconBody(type: IconType): Stroke[] {
  switch (type) {
    case "scales":
      return [
        line(-0.55, 0.95, 0.55, 0.95, 1.1),
        line(-0.32, 0.85, 0.32, 0.85),
        line(0, 0.85, 0, BEAM_PIVOT_Y + 0.04, 1.1),
        arc(0, BEAM_PIVOT_Y, 0.06, 0, TAU_HALF),
      ];
    case "gavel":
      return [
        /* head: rotated barrel */
        line(-0.72, -0.62, -0.28, -0.9, 1.1),
        line(-0.28, -0.9, 0.0, -0.72, 1.1),
        line(0.0, -0.72, -0.44, -0.44, 1.1),
        line(-0.44, -0.44, -0.72, -0.62, 1.1),
        line(-0.72, -0.62, -0.44, -0.44),
        /* handle */
        line(-0.4, -0.48, 0.62, 0.28, 1.2),
        /* sounding block */
        line(-0.5, 0.62, 0.18, 0.62, 1.1),
        line(-0.42, 0.62, -0.34, 0.92),
        line(0.1, 0.62, 0.02, 0.92),
        line(-0.34, 0.92, 0.02, 0.92),
      ];
    case "column":
      return [
        line(-0.7, -0.8, 0.7, -0.8, 1.1),
        line(-0.58, -0.8, -0.58, -0.66),
        line(0.58, -0.8, 0.58, -0.66),
        line(-0.4, -0.66, -0.4, 0.66, 1.1),
        line(0.4, -0.66, 0.4, 0.66, 1.1),
        line(-0.13, -0.6, -0.13, 0.6),
        line(0.13, -0.6, 0.13, 0.6),
        line(-0.6, 0.66, 0.6, 0.66, 1.1),
        line(-0.72, 0.92, 0.72, 0.92, 1.1),
        line(-0.6, 0.66, -0.68, 0.92),
        line(0.6, 0.66, 0.68, 0.92),
      ];
    case "scroll":
      return [
        arc(-0.62, -0.72, 0.18, -Math.PI * 0.5, Math.PI * 0.6),
        arc(0.62, 0.72, 0.18, Math.PI * 0.5, Math.PI * 1.6),
        line(-0.74, -0.66, -0.74, 0.6),
        line(0.74, 0.66, 0.74, -0.6),
        line(-0.5, -0.36, 0.5, -0.36),
        line(-0.5, -0.08, 0.42, -0.08),
        line(-0.5, 0.2, 0.5, 0.2),
      ];
    case "section":
      return [
        /* § approximated with two mirrored curves + spine */
        arc(0.08, -0.42, 0.42, Math.PI * 0.85, Math.PI * 1.95, 1.1),
        arc(-0.08, 0.42, 0.42, -Math.PI * 0.05, Math.PI * 1.1, 1.1),
        line(0.16, -0.78, -0.04, -0.62),
        line(-0.16, 0.78, 0.04, 0.62),
      ];
    case "book":
      return [
        ...rect(-0.66, -0.85, 0.66, 0.85, 1.1),
        line(-0.44, -0.85, -0.44, 0.85),
        line(-0.38, -0.85, -0.38, 0.85),
        line(-0.2, -0.45, 0.5, -0.45),
        line(-0.2, -0.17, 0.5, -0.17),
        line(-0.2, 0.11, 0.34, 0.11),
      ];
  }
}

function iconBeam(): Stroke[] {
  return [
    line(-0.8, BEAM_PIVOT_Y, 0.8, BEAM_PIVOT_Y, 1.2),
    line(-0.8, BEAM_PIVOT_Y, -0.62, -0.34),
    line(0.8, BEAM_PIVOT_Y, 0.62, -0.34),
    arc(-0.62, -0.34, 0.3, Math.PI * 0.08, Math.PI * 0.92, 1.1),
    arc(0.62, -0.34, 0.3, Math.PI * 0.08, Math.PI * 0.92, 1.1),
  ];
}

const TAU_HALF = Math.PI;

const ART: Record<IconType, IconArt> = {
  scales: { body: iconBody("scales"), beam: iconBeam() },
  gavel: { body: iconBody("gavel"), beam: [] },
  column: { body: iconBody("column"), beam: [] },
  scroll: { body: iconBody("scroll"), beam: [] },
  section: { body: iconBody("section"), beam: [] },
  book: { body: iconBody("book"), beam: [] },
};

/**
 * Text-column bound for the route family (viewport px). Two families:
 *  - "prose"  : /terms /privacy /login — max-w-3xl documents, roomy gutters
 *  - "wide"   : everything else — landing/about/modules/contact use
 *               container-page (max-w-6xl) and workspace/onboarding use
 *               max-w-5xl; the smaller of the two is the worst case.
 * Return value = left edge of text on any route of that family, so the icons
 * can never land behind body text *on a given route*.
 */
export type ZoneKind = "wide" | "prose";

export function contentBox(W: number, kind: ZoneKind = "wide"): { left: number; right: number } {
  const padM = W < 640 ? 20 : 32; // container-page (max-w-6xl, px-5/sm:px-8)
  const padW = W < 640 ? 16 : 24; // workspace/onboarding (max-w-5xl, px-4/sm:px-6)
  const mkt = (W - Math.min(1152, W)) / 2 + padM;
  const wsp = (W - Math.min(1024, W)) / 2 + padW;
  const prose = (W - Math.min(768, W)) / 2 + padM;
  const left =
    kind === "prose"
      ? prose
      : Math.min(mkt, wsp);
  /* clearance: 12px on desktop (comfortably outside any glyph), 5px on phones
     where the gutter itself is only the page padding */
  const margin = W < 640 ? 5 : 12;
  const safe = Math.max(4, left - margin);
  return { left: safe, right: W - safe };
}

export interface SceneViewport {
  W: number;
  H: number;
  S: number;
  zone: ZoneKind;
}

/**
 * Places the legal elements deterministically (seeded PRNG) inside the two
 * side gutters *outside* the text column, so a scale can never land behind
 * body text on any route at any width. Sizes are planned in px (capped by the
 * gutter width — on phones the motifs become small edge-cropped slivers);
 * y is stratified so the two columns never pile up. Connection lines only
 * link icons within the same gutter, so no line crosses the text column.
 */
export function buildLegalScene(vp: SceneViewport): LegalScene {
  const { W, S, zone } = vp;
  const rnd = mulberry32(0x1e6a);
  const edge = contentBox(W, zone).left; // icons stay outside this edge

  /* planned half-sizes in px (grew ~12% for the "strong legal world" pass;
     still capped by the gutter width below) */
  const plan: Array<{ type: IconType; sMin: number; sMax: number }> = [
    { type: "scales", sMin: 0.052 * S, sMax: 0.088 * S },
    { type: "scales", sMin: 0.043 * S, sMax: 0.074 * S },
    { type: "scales", sMin: 0.041 * S, sMax: 0.07 * S },
    { type: "scales", sMin: 0.038 * S, sMax: 0.064 * S },
    { type: "scales", sMin: 0.036 * S, sMax: 0.06 * S },
    { type: "scales", sMin: 0.034 * S, sMax: 0.056 * S },
    { type: "gavel", sMin: 0.041 * S, sMax: 0.063 * S },
    { type: "column", sMin: 0.039 * S, sMax: 0.06 * S },
    { type: "column", sMin: 0.034 * S, sMax: 0.053 * S },
    { type: "scroll", sMin: 0.039 * S, sMax: 0.06 * S },
    { type: "scroll", sMin: 0.032 * S, sMax: 0.051 * S },
    { type: "section", sMin: 0.036 * S, sMax: 0.055 * S },
    { type: "book", sMin: 0.036 * S, sMax: 0.055 * S },
  ];

  const bands: Array<{ side: "L" | "R"; members: typeof plan }> = [
    { side: "L", members: [] },
    { side: "R", members: [] },
  ];
  plan.forEach((p, i) => bands[i % 2].members.push(p));

  const icons: LegalIcon[] = [];
  const bandOf: number[] = [];
  bands.forEach((band, bandIdx) => {
    const n = band.members.length;
    const slot = 0.82 / n;
    band.members.forEach((p, k) => {
      const sPx = Math.max(4, Math.min(p.sMin + rnd() * (p.sMax - p.sMin), edge * 0.62));
      const s = sPx / S;
      /* gutter x: inner edge pinned, jittered outward — never crosses `edge`,
         may be cropped by the viewport (that keeps icons off text on phones) */
      const inner = edge - sPx - rnd() * Math.max(0, (edge - sPx) * 0.5);
      const x = (band.side === "L" ? inner : W - inner) / S + 0.5 - W / (2 * S);
      const y = 0.09 + (k + 0.5 + (rnd() - 0.5) * 0.45) * slot;
      icons.push({
        type: p.type,
        art: ART[p.type],
        x,
        y,
        s,
        phase: rnd() * Math.PI * 2,
      });
      bandOf.push(bandIdx);
    });
  });

  /* link icons only within the same gutter (never across the text column) */
  const links: Array<[number, number]> = [];
  for (let i = 0; i < icons.length; i++) {
    for (let j = i + 1; j < icons.length; j++) {
      if (bandOf[i] !== bandOf[j]) continue;
      const d = Math.hypot(icons[i].x - icons[j].x, icons[i].y - icons[j].y);
      if (d < 0.3) links.push([i, j]);
    }
  }
  return { icons, links };
}
