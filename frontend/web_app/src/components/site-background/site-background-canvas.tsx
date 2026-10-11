"use client";

import { useEffect, useRef } from "react";
import {
  buildNeuronField,
  mulberry32,
  pointOnTrack,
  type NeuronField,
  type NeuronLayer,
  type PulseTrack,
  type Stroke,
} from "./neurons";
import { BEAM_PIVOT_Y, buildLegalScene, contentBox, type LegalScene } from "./legal-icons";

/**
 * 2D-canvas engine for the site background: line-art only (no washes, no
 * page-wide gradients). Static artwork is pre-rendered once per layer
 * offscreen — soma glow included — and only blitted with slow drift +
 * mouse/scroll parallax; light pulses, the scales sway, the cursor boost and
 * the neuron→legal transition are the only per-frame vector work.
 *
 * Strength + readability (both at once):
 *  - Gutters render at FULL pre-rendered strength (large somas, tapered
 *    dendrites, glow, synapses — the shapes carry the look).
 *  - Text columns are dimmed in SCREEN space: each layer is composited
 *    through a reusable temp canvas and a soft horizontal erase gradient, so
 *    the brightness transition is gradual (no visible panel/strip edges) and
 *    the column alphas stay exactly at the AA-certified values.
 *  - Colours come from the dedicated --bg-cell-* / --bg-legal-* tokens.
 *
 * Transition (~1.75 s, not a crossfade): dendrites fade → synapse dots travel
 * along arcs and settle into the legal elements → the legal drawings stroke
 * in one by one. Sales/HR keep the neural field. The workspace runs a quieter
 * variant (lower opacity, slower motion) that still reads clearly.
 */

type RGB = [number, number, number];

const TOKEN_FALLBACKS = { brand: "#8052ff", hover: "#946eff", gold: "#f3ca78" } as const;
const CELL_FALLBACKS = {
  soma: "#efeaff",
  dend: "#9a76ff",
  dendHi: "#b9a3ff",
  glow: "#cfc4ff",
  synapse: "#d8d0ff",
  core: "#0b0726",
  ink: "#9a76ff",
} as const;
const TRANS_SECONDS = 1.75;
const PAD = 90;

function cssVar(name: string, fallback: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback;
}

function hexToRgb(hex: string): RGB {
  const h = hex.trim();
  return [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
}

function rgba(c: RGB, a: number): string {
  return `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`;
}

function mix(a: RGB, b: RGB, t: number): RGB {
  return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
}

const clamp01 = (v: number) => Math.max(0, Math.min(1, v));
const smooth = (t: number) => t * t * (3 - 2 * t);
const easeOut = (t: number) => 1 - (1 - t) * (1 - t);

interface Palette {
  brand: RGB;
  hover: RGB;
  gold: RGB;
  soma: RGB;
  dend: RGB;
  dendHi: RGB;
  glow: RGB;
  synapse: RGB;
  core: RGB;
  ink: RGB;
  light: boolean;
}

function readPalette(): Palette {
  return {
    brand: hexToRgb(cssVar("--brand", TOKEN_FALLBACKS.brand)),
    hover: hexToRgb(cssVar("--brand-hover", TOKEN_FALLBACKS.hover)),
    gold: hexToRgb(cssVar("--bg-legal-gold", TOKEN_FALLBACKS.gold)),
    soma: hexToRgb(cssVar("--bg-cell-soma", CELL_FALLBACKS.soma)),
    dend: hexToRgb(cssVar("--bg-cell-dendrite", CELL_FALLBACKS.dend)),
    dendHi: hexToRgb(cssVar("--bg-cell-dendrite-hi", CELL_FALLBACKS.dendHi)),
    glow: hexToRgb(cssVar("--bg-cell-glow", CELL_FALLBACKS.glow)),
    synapse: hexToRgb(cssVar("--bg-cell-synapse", CELL_FALLBACKS.synapse)),
    core: hexToRgb(cssVar("--bg-cell-core", CELL_FALLBACKS.core)),
    ink: hexToRgb(cssVar("--bg-legal-stroke", CELL_FALLBACKS.ink)),
    light: document.documentElement.classList.contains("light"),
  };
}

interface Sprite {
  c: HTMLCanvasElement;
  side: number;
  pivotPx: number;
}

type IconSprites = { body: Sprite; beam: Sprite | null };

interface Offscreens {
  far: HTMLCanvasElement;
  mid: HTMLCanvasElement;
  near: HTMLCanvasElement;
  links: HTMLCanvasElement;
  sprites: Map<object, IconSprites>;
}

export function SiteBackgroundCanvas({
  legal,
  quiet,
  reduced,
  zone,
}: {
  legal: boolean;
  quiet: boolean;
  reduced: boolean;
  zone: "wide" | "prose";
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const legalRef = useRef(legal);
  const quietRef = useRef(quiet);
  const zoneRef = useRef(zone);
  const applyRef = useRef<((v: boolean) => void) | null>(null);
  const rezoneRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    legalRef.current = legal;
    applyRef.current?.(legal);
  }, [legal]);

  useEffect(() => {
    quietRef.current = quiet;
  }, [quiet]);

  useEffect(() => {
    zoneRef.current = zone;
    rezoneRef.current?.();
  }, [zone]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return; // canvas unavailable → render nothing
    const context: CanvasRenderingContext2D = ctx;
    const surface: HTMLCanvasElement = canvas;

    let W = 0;
    let H = 0;
    let dpr = 1;
    let S = 1;
    let contentL = 0; // px edge of the text column (worst-case route container)
    let pal = readPalette();

    const field: NeuronField = buildNeuronField(0x5eed, {
      compact: typeof window !== "undefined" && window.innerWidth < 768,
    });
    /* scene is viewport-dependent (icons live in the gutters outside the text
       column) — built/rebuilt in rebuild() once the canvas is measured */
    let scene: LegalScene = buildLegalScene({ W: 0, H: 0, S: 1, zone: "wide" });
    let travelers: Array<{ x0: number; y0: number; x1: number; y1: number }> = [];
    let somaPathList: PulseTrack[] = [];

    /* stable pairing: each synapse dot settles near an icon centre (seeded,
       so the flight targets are deterministic like the scene itself) */
    function pairTravelers(): void {
      const trnd = mulberry32(0x7a31);
      travelers = field.travelers.map((p, i) => {
        const icon = scene.icons[i % scene.icons.length];
        return {
          x0: p.x,
          y0: p.y,
          x1: icon.x + (trnd() - 0.5) * icon.s,
          y1: icon.y + (trnd() - 0.5) * icon.s,
        };
      });
    }

    let mode: "neural" | "legal" = legalRef.current ? "legal" : "neural";
    let target = mode;
    let transFrom = mode;
    let transStart = -1;

    let rafId = 0;
    let running = false;
    let last = 0;
    let time = 0;
    /* ambient art drifts slowly — capping the loop at 30fps is visually
       indistinguishable but stops the canvas painting on every compositor
       BeginFrame (which matters for screenshot-style full-page captures). */
    const FRAME_MS = 1000 / 30;
    let lastDraw = 0;

    let mx = 0;
    let my = 0;
    let mtx = 0;
    let mty = 0;
    let mousePxX = -1e4;
    let mousePxY = -1e4;
    let scroll = 0;
    let mScroll = 0;

    let offs: Offscreens | null = null;
    /* erase strips (small cached horizontal-gradient tiles) are rebuilt on
       resize; each erase strength gets one, blitted with destination-out */
    let eraseStrips = new Map<number, HTMLCanvasElement>();
    /* cached pulse-dot tiles (crisp core + soft halo), rebuilt on resize or
       theme change — stand in for per-frame shadowBlur passes */
    let pulseTiles: { core: HTMLCanvasElement; halo: HTMLCanvasElement } | null = null;
    const layerOffsets: Array<[number, number]> = [
      [0, 0],
      [0, 0],
      [0, 0],
    ];

    /* one-off soma pulse fired by hovering a primary button/CTA */
    let hoverPulse: { tr: PulseTrack; t0: number } | null = null;
    let lastHover = -10;

    const px = (x: number) => W / 2 + (x - 0.5) * S;
    const py = (y: number) => H / 2 + (y - 0.5) * S;

    function strokePath(g: CanvasRenderingContext2D, s: Stroke): void {
      g.beginPath();
      g.moveTo(px(s.pts[0]), py(s.pts[1]));
      for (let i = 2; i < s.pts.length; i += 2) g.lineTo(px(s.pts[i]), py(s.pts[i + 1]));
    }

    /** Pre-rendered (gutter) stroke strength — the strong base of the art. */
    function fullAlpha(depth: number): number {
      const base = depth === 0 ? 0.5 : depth === 1 ? 0.64 : 0.8;
      return base * (pal.light ? 0.55 : 1);
    }

    /**
     * Effective stroke alpha inside the text columns. These track the exact
     * values the AA probe certified under glyphs (dark ×1.15 over v6 after the
     * bands went translucent; light unchanged — it was the tighter margin),
     * so stronger gutters can never leak behind body text.
     */
    function colAlpha(depth: number): number {
      const dark = depth === 0 ? 0.0518 : depth === 1 ? 0.088 : 0.1346;
      return pal.light ? dark * 0.4348 : dark;
    }

    function prerenderLayer(layer: NeuronLayer, depth: number): HTMLCanvasElement {
      const c = document.createElement("canvas");
      c.width = (W + PAD * 2) * dpr;
      c.height = (H + PAD * 2) * dpr;
      const g = c.getContext("2d")!;
      g.setTransform(dpr, 0, 0, dpr, 0, 0);
      g.translate(PAD, PAD);
      g.lineJoin = "round";
      g.lineCap = "round";
      const a = fullAlpha(depth);

      /* 1) soft pre-rendered radial glow + faint cool core tint (dark).
         The glow shape is rasterized ONCE into a small tile and blitted per
         soma — a cached bitmap blit instead of a fresh radial gradient per
         soma, keeping the one-time layer prerender off the long-task budget.
         The tile's gradient stops are exactly the previous per-soma ones, so
         the output is visually identical. */
      let maxGr = 0;
      for (const s of layer.soma) maxGr = Math.max(maxGr, Math.max(9, s.r * S * (2.3 + depth * 0.35)));
      let glowTile: HTMLCanvasElement | null = null;
      if (maxGr > 0) {
        const side = Math.min(1024, Math.max(32, Math.ceil(maxGr * 2 * dpr)));
        glowTile = document.createElement("canvas");
        glowTile.width = side;
        glowTile.height = side;
        const tg = glowTile.getContext("2d")!;
        const r = side / 2;
        const grad = tg.createRadialGradient(r, r, 0, r, r, r);
        grad.addColorStop(0, rgba(pal.glow, Math.min(1, a * 1.05)));
        grad.addColorStop(0.3, rgba(pal.glow, a * 0.5));
        grad.addColorStop(0.62, rgba(pal.glow, a * 0.15));
        grad.addColorStop(1, rgba(pal.glow, 0));
        tg.fillStyle = grad;
        tg.fillRect(0, 0, side, side);
      }
      for (const s of layer.soma) {
        const gx = px(s.cx);
        const gy = py(s.cy);
        const gr = Math.max(9, s.r * S * (2.3 + depth * 0.35));
        if (glowTile) g.drawImage(glowTile, gx - gr, gy - gr, gr * 2, gr * 2);
        if (!pal.light) {
          g.fillStyle = rgba(pal.core, a * 0.45);
          g.beginPath();
          g.arc(gx, gy, Math.max(3, s.r * S * 0.55), 0, Math.PI * 2);
          g.fill();
        }
      }

      /* 2) soma outlines */
      g.strokeStyle = rgba(pal.soma, Math.min(1, a * 1.6));
      for (const s of layer.soma) {
        g.lineWidth = Math.max(1.1, s.w);
        strokePath(g, s);
        g.stroke();
      }

      /* 3) tapering dendrites: near = brand purple, far = lighter violet */
      const dendCol = mix(pal.dend, pal.dendHi, depth === 0 ? 0.65 : depth === 1 ? 0.3 : 0);
      g.strokeStyle = rgba(dendCol, a);
      for (const d of layer.dendrites) {
        g.lineWidth = Math.max(0.6, d.w);
        strokePath(g, d);
        g.stroke();
      }

      /* 4) synapse dots */
      g.fillStyle = rgba(pal.synapse, Math.min(1, a * 2));
      const dotScale = Math.max(0.9, S / 850);
      for (const d of layer.dots) {
        g.beginPath();
        g.arc(px(d.x), py(d.y), d.r * dotScale * 1.3, 0, Math.PI * 2);
        g.fill();
      }
      return c;
    }

    function prerenderLinks(): HTMLCanvasElement {
      const c = document.createElement("canvas");
      c.width = (W + PAD * 2) * dpr;
      c.height = (H + PAD * 2) * dpr;
      const g = c.getContext("2d")!;
      g.setTransform(dpr, 0, 0, dpr, 0, 0);
      g.translate(PAD, PAD);
      g.strokeStyle = rgba(pal.dend, fullAlpha(1) * 0.4);
      g.lineWidth = 0.7;
      for (const [i, j] of scene.links) {
        g.beginPath();
        g.moveTo(px(scene.icons[i].x), py(scene.icons[i].y));
        g.lineTo(px(scene.icons[j].x), py(scene.icons[j].y));
        g.stroke();
      }
      return c;
    }

    function prerenderIcon(icon: LegalScene["icons"][number]): { body: Sprite; beam: Sprite | null } {
      const gold = icon.type === "scales";
      const colour = gold ? pal.gold : pal.ink;
      const make = (strokes: Stroke[]): Sprite => {
        const side = Math.ceil(2.4 * icon.s * S);
        const c = document.createElement("canvas");
        c.width = side * dpr;
        c.height = side * dpr;
        const g = c.getContext("2d")!;
        g.setTransform(dpr, 0, 0, dpr, 0, 0);
        g.lineJoin = "round";
        g.lineCap = "round";
        g.strokeStyle = rgba(colour, 1);
        const k = icon.s * S;
        const cxp = side / 2;
        const cyp = side / 2;
        for (const s of strokes) {
          g.beginPath();
          g.moveTo(cxp + s.pts[0] * k, cyp + s.pts[1] * k);
          for (let i = 2; i < s.pts.length; i += 2) g.lineTo(cxp + s.pts[i] * k, cyp + s.pts[i + 1] * k);
          /* crisp line-art: ~1.5px+ strokes at every icon size */
          g.lineWidth = Math.max(1.5, s.w * (k / 120));
          g.stroke();
        }
        return { c, side, pivotPx: BEAM_PIVOT_Y * k };
      };
      return {
        body: make(icon.art.body),
        beam: icon.art.beam.length ? make(icon.art.beam) : null,
      };
    }

    function rebuild(): void {
      if (!W || !H) return;
      scene = buildLegalScene({ W, H, S, zone: zoneRef.current });
      pairTravelers();
      somaPathList = [
        ...field.far.somaPaths,
        ...field.mid.somaPaths,
        ...field.near.somaPaths,
      ];
      offs = {
        far: prerenderLayer(field.far, 0),
        mid: prerenderLayer(field.mid, 1),
        near: prerenderLayer(field.near, 2),
        links: prerenderLinks(),
        sprites: new Map<object, IconSprites>(
          scene.icons.map((icon) => [icon as object, prerenderIcon(icon)]),
        ),
      };
    }

    function measure(): void {
      const rect = surface.getBoundingClientRect();
      W = Math.max(320, Math.round(rect.width));
      H = Math.max(320, Math.round(rect.height));
      dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      surface.width = Math.round(W * dpr);
      surface.height = Math.round(H * dpr);
      surface.style.width = `${W}px`;
      surface.style.height = `${H}px`;
      context.setTransform(dpr, 0, 0, dpr, 0, 0);
      S = Math.max(W, H);
      contentL = contentBox(W, zoneRef.current).left;
      eraseStrips = new Map();
      pulseTiles = null;
    }

    /**
     * Cached erase strip (screen space): a small 512×1 tile holding the soft
     * horizontal erase profile — alpha 0 over the gutters, e across the text
     * columns, finishing just inside the glyph clearance, so brightness
     * transitions are gradual and there is no visible strip edge. Blitting
     * this bitmap with destination-out is markedly cheaper per frame than
     * re-evaluating a full-viewport gradient fill under software raster.
     */
    function eraseStrip(e: number): HTMLCanvasElement | null {
      const key = Math.round(e * 1000);
      let strip = eraseStrips.get(key);
      if (strip) return strip;
      const narrow = W < 640;
      const x0 = Math.max(0, contentL - (narrow ? 16 : 44));
      const x1 = Math.min(W, W - contentL + (narrow ? 16 : 44));
      const span = x1 - x0;
      if (span <= 0) return null;
      /* remap the in-column stops onto the strip's [0,1] span — outside the
         strip the gradient is alpha 0 either way, so the profile is identical */
      const t1 = (Math.min(W, contentL + (narrow ? 2 : 12)) - x0) / span;
      const t2 = (Math.max(0, W - contentL - (narrow ? 2 : 12)) - x0) / span;
      const N = 512;
      strip = document.createElement("canvas");
      strip.width = N;
      strip.height = 1;
      const sg = strip.getContext("2d")!;
      const g = sg.createLinearGradient(0, 0, N, 0);
      g.addColorStop(0, "rgba(0,0,0,0)");
      g.addColorStop(Math.max(0, Math.min(1, t1)), `rgba(0,0,0,${e})`);
      g.addColorStop(Math.max(0, Math.min(1, t2)), `rgba(0,0,0,${e})`);
      g.addColorStop(1, "rgba(0,0,0,0)");
      sg.fillStyle = g;
      sg.fillRect(0, 0, N, 1);
      eraseStrips.set(key, strip);
      return strip;
    }

    /** Blit one pre-rendered layer at full gutter strength. The column erase
     *  runs once afterwards over the whole composite (eraseColumns). */
    function blitLayer(c: HTMLCanvasElement, ox: number, oy: number, neuralA: number, qf: number): void {
      context.globalAlpha = neuralA * qf;
      context.drawImage(c, -PAD + ox, -PAD + oy, W + PAD * 2, H + PAD * 2);
      context.globalAlpha = 1;
    }

    /**
     * Soft horizontal erase (screen space) applied ONCE to the composited
     * neural layers: alpha 0 over the gutters, e across the text columns,
     * finishing just inside the glyph clearance — brightness transitions are
     * gradual, so there is no visible strip edge. `e` uses the strictest of
     * the three per-layer ratios (set by the far layer), so no layer can ever
     * exceed its AA-certified column alpha; near/mid sit deeper than their
     * individual targets, which only increases text contrast. This replaces
     * the per-layer temp-canvas round trip (9 full-viewport composites per
     * frame → 4), keeping the animation loop well inside the long-task budget
     * under CPU throttling.
     */
    function columnErase(): number {
      const q = quietRef.current;
      const minRatio = Math.min(
        colAlpha(0) / fullAlpha(0),
        colAlpha(1) / fullAlpha(1),
        colAlpha(2) / fullAlpha(2),
      );
      return clamp01(1 - (minRatio * (q ? 0.55 : 1)) / (q ? 0.75 : 1));
    }

    function eraseColumns(e: number): void {
      if (e <= 0.01) return;
      const narrow = W < 640;
      const x0 = Math.max(0, contentL - (narrow ? 16 : 44));
      const x1 = Math.min(W, W - contentL + (narrow ? 16 : 44));
      if (x1 <= x0) return;
      const strip = eraseStrip(e);
      if (!strip) return;
      context.globalCompositeOperation = "destination-out";
      context.drawImage(strip, 0, 0, strip.width, 1, x0, 0, x1 - x0, H);
      context.globalCompositeOperation = "source-over";
    }

    /** Motion dots (pulses, flying travellers) fade while they pass behind
     *  the text column so a moving dot can never dip body-text contrast. */
    function colDim(xPx: number, deep = false): number {
      const ramp = 44;
      const inL = clamp01((xPx - (contentL - ramp)) / ramp);
      const inR = 1 - clamp01((xPx - (W - contentL)) / ramp);
      return 1 - (deep ? 0.88 : 0.8) * Math.min(inL, inR);
    }

    /* --- transition state --------------------------------------------- */

    function setTarget(legalOn: boolean): void {
      target = legalOn ? "legal" : "neural";
      if (target !== mode && transStart < 0) {
        transFrom = mode;
        transStart = time;
      }
    }
    applyRef.current = setTarget;

    interface Parts {
      neuralA: number;
      legalP: number;
      travelP: number;
      linksP: number;
      iconP: (i: number) => number;
    }

    function partsAt(p: number, from: "neural" | "legal"): Parts {
      if (from === "neural") {
        return {
          neuralA: 1 - smooth(clamp01(p / 0.42)),
          travelP: easeOut(clamp01((p - 0.12) / 0.55)),
          legalP: easeOut(clamp01((p - 0.45) / 0.5)),
          linksP: easeOut(clamp01((p - 0.75) / 0.25)),
          iconP: (i) => easeOut(clamp01((p - 0.42 - i * 0.0125) / 0.4)),
        };
      }
      return {
        legalP: 1 - easeOut(clamp01(p / 0.5)),
        linksP: 1 - clamp01(p / 0.25),
        travelP: 1 - easeOut(clamp01((p - 0.3) / 0.55)),
        neuralA: smooth(clamp01((p - 0.4) / 0.55)),
        iconP: (i) => 1 - easeOut(clamp01((p - i * 0.03) / 0.45)),
      };
    }

    /* --- drawing ------------------------------------------------------- */

    function drawTravelers(travelP: number, alpha: number): void {
      if (travelP <= 0) return;
      const r = Math.max(1, S / 800);
      for (const t of travelers) {
        const e = travelP;
        const mxp = (t.x0 + t.x1) / 2 + (t.y1 - t.y0) * 0.18;
        const myp = (t.y0 + t.y1) / 2 - (t.x1 - t.x0) * 0.18;
        const x = (1 - e) * (1 - e) * t.x0 + 2 * (1 - e) * e * mxp + e * e * t.x1;
        const y = (1 - e) * (1 - e) * t.y0 + 2 * (1 - e) * e * myp + e * e * t.y1;
        context.fillStyle = rgba(pal.synapse, alpha * colDim(px(x)));
        context.beginPath();
        context.arc(px(x), py(y), r, 0, Math.PI * 2);
        context.fill();
      }
    }

    function drawIconVector(i: number, progress: number, alpha: number): void {
      if (progress <= 0) return;
      const icon = scene.icons[i];
      const gold = icon.type === "scales";
      const colour = gold ? pal.gold : pal.ink;
      const k = icon.s * S;
      const cxp = px(icon.x);
      const cyp = py(icon.y);
      context.lineJoin = "round";
      context.lineCap = "round";
      context.strokeStyle = rgba(colour, alpha);
      const all = icon.art.beam.length ? [...icon.art.body, ...icon.art.beam] : icon.art.body;
      let totalLen = 0;
      const lens: number[] = [];
      for (const s of all) {
        let l = 0;
        for (let j = 2; j < s.pts.length; j += 2) {
          l += Math.hypot((s.pts[j] - s.pts[j - 2]) * k, (s.pts[j + 1] - s.pts[j - 1]) * k);
        }
        lens.push(l);
        totalLen += l;
      }
      let budget = totalLen * progress;
      for (let si = 0; si < all.length; si++) {
        const s = all[si];
        if (budget <= 0) break;
        const take = Math.min(1, budget / (lens[si] || 1));
        budget -= lens[si];
        context.lineWidth = Math.max(1.5, s.w * (k / 120));
        context.beginPath();
        context.moveTo(cxp + s.pts[0] * k, cyp + s.pts[1] * k);
        const segCount = s.pts.length / 2 - 1;
        const at = segCount * take;
        const full = Math.floor(at);
        for (let j = 1; j <= full; j++) {
          context.lineTo(cxp + s.pts[j * 2] * k, cyp + s.pts[j * 2 + 1] * k);
        }
        const frac = at - full;
        if (frac > 0 && full < segCount) {
          const jx = s.pts[full * 2];
          const jy = s.pts[full * 2 + 1];
          context.lineTo(
            cxp + (jx + (s.pts[full * 2 + 2] - jx) * frac) * k,
            cyp + (jy + (s.pts[full * 2 + 3] - jy) * frac) * k,
          );
        }
        context.stroke();
      }
    }

    function drawIconSprite(i: number, alpha: number): void {
      const icon = scene.icons[i];
      const sprite = offs?.sprites.get(icon);
      if (!sprite) return;
      const cxp = px(icon.x);
      const cyp = py(icon.y);
      context.globalAlpha = alpha;
      context.drawImage(sprite.body.c, cxp - sprite.body.side / 2, cyp - sprite.body.side / 2, sprite.body.side, sprite.body.side);
      if (sprite.beam) {
        const angle = Math.sin(time * 0.5 + icon.phase) * 0.055;
        context.save();
        context.translate(cxp, cyp + sprite.beam.pivotPx);
        context.rotate(angle);
        context.drawImage(
          sprite.beam.c,
          -sprite.beam.side / 2,
          -(sprite.beam.side / 2 + sprite.beam.pivotPx),
          sprite.beam.side,
          sprite.beam.side,
        );
        context.restore();
      }
      context.globalAlpha = 1;
    }

    /** Bright, clearly visible pulses travelling along the dendrites; deeply
     *  dimmed (not hidden) while they cross the text columns. */
    /** Cached pulse-dot tiles (dark theme): a crisp core dot plus a soft
     *  halo, drawn as bitmap blits. The previous shadowBlur halo ran ~90
     *  blur passes per frame — shadowed fills are by far the most expensive
     *  canvas operation under software rasterization (they dominated the
     *  Lighthouse long-task budget); the tiles reproduce the same glowing
     *  look for a fraction of the cost. Light theme never used shadows. */
    function getPulseTiles(): { core: HTMLCanvasElement; halo: HTMLCanvasElement } | null {
      if (pal.light) return null;
      if (pulseTiles) return pulseTiles;
      const T = 64;
      const r = T / 2;
      const core = document.createElement("canvas");
      core.width = T;
      core.height = T;
      const cg = core.getContext("2d")!;
      const cGrad = cg.createRadialGradient(r, r, 0, r, r, r);
      cGrad.addColorStop(0, rgba(pal.glow, 1));
      cGrad.addColorStop(0.62, rgba(pal.glow, 1));
      cGrad.addColorStop(0.8, rgba(pal.glow, 0.55));
      cGrad.addColorStop(1, rgba(pal.glow, 0));
      cg.fillStyle = cGrad;
      cg.fillRect(0, 0, T, T);
      const halo = document.createElement("canvas");
      halo.width = T;
      halo.height = T;
      const hg = halo.getContext("2d")!;
      const hGrad = hg.createRadialGradient(r, r, 0, r, r, r);
      hGrad.addColorStop(0, rgba(pal.glow, 0.62));
      hGrad.addColorStop(0.3, rgba(pal.glow, 0.4));
      hGrad.addColorStop(0.6, rgba(pal.glow, 0.14));
      hGrad.addColorStop(1, rgba(pal.glow, 0));
      hg.fillStyle = hGrad;
      hg.fillRect(0, 0, T, T);
      pulseTiles = { core, halo };
      return pulseTiles;
    }

    function drawPulses(neuralA: number): void {
      if (reduced || neuralA < 0.35) return;
      const layers: NeuronLayer[] = [field.far, field.mid, field.near];
      const tiles = getPulseTiles();
      const dot = (x: number, y: number, rc: number, alpha: number, dim: number): void => {
        if (tiles) {
          if (dim > 0.98) {
            const rh = rc + 6.4; // soft halo, gutters only — no glow over text
            context.globalAlpha = 0.85;
            context.drawImage(tiles.halo, x - rh, y - rh, rh * 2, rh * 2);
          }
          const rr = rc * 1.61; // core tile's solid span is 0.62 of its radius
          context.globalAlpha = Math.min(1, alpha);
          context.drawImage(tiles.core, x - rr, y - rr, rr * 2, rr * 2);
          context.globalAlpha = 1;
          return;
        }
        context.fillStyle = rgba(pal.glow, Math.max(0.05, alpha));
        context.beginPath();
        context.arc(x, y, rc, 0, Math.PI * 2);
        context.fill();
      };
      for (let li = 0; li < layers.length; li++) {
        const tracks = layers[li].pulses.slice(0, 6);
        for (let pi = 0; pi < tracks.length; pi++) {
          const f = (time * 0.12 * (0.7 + li * 0.2) + pi * 0.37 + li * 0.13) % 1;
          const [x, y] = pointOnTrack(tracks[pi], f);
          const base = neuralA * (pal.light ? 0.55 : 0.85) * (0.6 + 0.4 * Math.sin(time + pi));
          const dim = colDim(px(x), true);
          dot(px(x), py(y), 2 + li * 0.5, Math.max(0.05, base * dim), dim);
          /* short fading tail along the track */
          for (let t = 1; t <= 4; t++) {
            const ft = f - t * 0.02;
            if (ft < 0) break;
            const [tx, ty] = pointOnTrack(tracks[pi], ft);
            const tDim = colDim(px(tx), true);
            dot(px(tx), py(ty), 1.6 + li * 0.4, Math.max(0.03, base * (0.55 - t * 0.12) * tDim), tDim);
          }
        }
      }
    }

    /** Dendrites/soma near the cursor brighten slightly — gutters only, so
     *  art behind the text columns is never boosted. Three soft rings fake a
     *  falloff without any per-frame blur cost. */
    function drawCursorBoost(neuralA: number): void {
      if (reduced || mode !== "neural" || neuralA < 0.35 || !offs) return;
      const x = mousePxX;
      const y = mousePxY;
      if (x < 0 || x > W || y < 0 || y > H) return;
      if (x > contentL - 40 && x < W - contentL + 40) return; // over/near text
      const rings: Array<[number, number]> = [
        [150, 0.05],
        [104, 0.07],
        [62, 0.1],
      ];
      const layers: Array<[HTMLCanvasElement, number]> = [
        [offs.mid, 1],
        [offs.near, 2],
      ];
      for (const [c, d] of layers) {
        const [ox, oy] = layerOffsets[d];
        for (const [r, a] of rings) {
          context.save();
          context.beginPath();
          context.rect(0, 0, contentL, H);
          context.rect(W - contentL, 0, contentL, H);
          context.clip();
          context.beginPath();
          context.arc(x, y, r, 0, Math.PI * 2);
          context.clip();
          context.globalAlpha = a * neuralA;
          context.drawImage(c, -PAD + ox, -PAD + oy, W + PAD * 2, H + PAD * 2);
          context.restore();
        }
      }
      context.globalAlpha = 1;
    }

    /** One pulse from the soma nearest a hovered primary button/CTA. */
    function drawHoverPulse(neuralA: number): void {
      if (!hoverPulse) return;
      const f = (time - hoverPulse.t0) / 1.1;
      if (f >= 1) {
        hoverPulse = null;
        return;
      }
      const e = easeOut(f);
      const [x, y] = pointOnTrack(hoverPulse.tr, e);
      const dim = colDim(px(x), true);
      const a = Math.sin(Math.PI * f) * 0.95 * neuralA;
      if (!pal.light && dim > 0.98) {
        context.shadowColor = rgba(pal.glow, 0.9);
        context.shadowBlur = 7;
      }
      context.fillStyle = rgba(pal.synapse, Math.max(0.04, a * dim));
      context.beginPath();
      context.arc(px(x), py(y), 3.4, 0, Math.PI * 2);
      context.fill();
      for (let t = 1; t <= 2; t++) {
        const ft = e - t * 0.05;
        if (ft < 0) break;
        const [tx, ty] = pointOnTrack(hoverPulse.tr, ft);
        const tDim = colDim(px(tx), true);
        context.shadowBlur = !pal.light && tDim > 0.98 ? 7 : 0;
        context.fillStyle = rgba(pal.synapse, Math.max(0.03, a * (0.5 - t * 0.16) * tDim));
        context.beginPath();
        context.arc(px(tx), py(ty), 2.6 - t * 0.5, 0, Math.PI * 2);
        context.fill();
      }
      context.shadowBlur = 0;
    }

    function composite(steady: boolean): void {
      if (!offs) return;
      context.clearRect(0, 0, W, H);

      let neuralA = mode === "neural" ? 1 : 0;
      let legalP = mode === "legal" ? 1 : 0;
      let travelP = mode === "legal" ? 1 : 0;
      let linksP = mode === "legal" ? 1 : 0;
      let iconP: (i: number) => number = () => (mode === "legal" ? 1 : 0);

      if (transStart >= 0 && !steady) {
        const p = clamp01((time - transStart) / TRANS_SECONDS);
        const parts = partsAt(p, transFrom);
        neuralA = parts.neuralA;
        legalP = parts.legalP;
        travelP = parts.travelP;
        linksP = parts.linksP;
        iconP = parts.iconP;
        if ((time - transStart) >= TRANS_SECONDS) {
          transStart = -1;
          mode = target;
          if (target !== mode) {
            transFrom = mode;
            transStart = time;
          }
        }
      } else if (transStart >= 0 && steady) {
        transStart = -1;
        mode = target;
      }

      if (neuralA > 0.002) {
        const damp = quietRef.current ? 0.6 : 1;
        const qf = quietRef.current ? 0.75 : 1;
        const driftA = [8, 14, 22];
        const driftW = [0.021, 0.029, 0.038];
        const parX = [1.2, 3, 5.5];
        const parY = [0.7, 1.8, 3.2];
        const scrollF = [0.02, 0.05, 0.09];
        const layers: Array<[HTMLCanvasElement, number]> = [
          [offs.far, 0],
          [offs.mid, 1],
          [offs.near, 2],
        ];
        for (const [c, d] of layers) {
          const ox = Math.sin(time * driftW[d] + d * 2.1) * driftA[d] * damp + mx * parX[d];
          const oy =
            Math.cos(time * driftW[d] * 0.8 + d * 1.3) * driftA[d] * 0.6 * damp +
            my * parY[d] -
            Math.min(36, scroll * scrollF[d]);
          layerOffsets[d] = [ox, oy];
          blitLayer(c, ox, oy, neuralA, qf);
        }
        eraseColumns(columnErase());
        drawCursorBoost(neuralA);
        drawPulses(neuralA);
        drawHoverPulse(neuralA);
        drawTravelers(travelP, mode === "legal" && travelP >= 1 ? 0.22 : 0.5);
      } else if (travelP > 0) {
        drawTravelers(travelP, mode === "legal" && travelP >= 1 ? 0.22 : 0.5);
      }

      if (legalP > 0 || linksP > 0 || travelP > 0) {
        const qAlpha = quietRef.current ? 0.55 : 1;
        if (linksP > 0.002) {
          context.globalAlpha = linksP * qAlpha;
          context.drawImage(offs.links, -PAD, -PAD, W + PAD * 2, H + PAD * 2);
          context.globalAlpha = 1;
        }
        for (let i = 0; i < scene.icons.length; i++) {
          const p = iconP(i);
          const gold = scene.icons[i].type === "scales";
          const iconAlpha =
            qAlpha *
            (gold
              ? pal.light
                ? 0.42
                : 0.6
              : pal.light
                ? 0.45
                : 0.62);
          if (p >= 0.999) drawIconSprite(i, iconAlpha);
          else if (p > 0.002) drawIconVector(i, p, iconAlpha);
        }
      }
    }

    /* --- lifecycle ------------------------------------------------------ */

    function frame(ms: number): void {
      rafId = requestAnimationFrame(frame);
      if (ms - lastDraw < FRAME_MS) return;
      const dt = Math.min(0.05, (ms - last) / 1000 || 0);
      last = ms;
      lastDraw = ms;
      time += dt * (quietRef.current ? 0.6 : 1);
      mx += (mtx - mx) * 0.05;
      my += (mty - my) * 0.05;
      scroll += (mScroll - scroll) * 0.06;
      composite(false);
    }

    function setRunning(run: boolean): void {
      if (run === running) return;
      running = run;
      if (run) {
        last = performance.now();
        lastDraw = 0; // draw the first frame immediately on resume
        if (!rafId) rafId = requestAnimationFrame(frame);
      } else if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = 0;
      }
    }

    const onVisibility = (): void => setRunning(!document.hidden && !reduced);
    document.addEventListener("visibilitychange", onVisibility);

    const onMouse = (e: MouseEvent): void => {
      mtx = (e.clientX / Math.max(1, W) - 0.5) * 2;
      mty = (e.clientY / Math.max(1, H) - 0.5) * 2;
      mousePxX = e.clientX;
      mousePxY = e.clientY;
    };
    const onScroll = (): void => {
      mScroll = window.scrollY;
    };
    window.addEventListener("mousemove", onMouse, { passive: true });
    window.addEventListener("scroll", onScroll, { passive: true });

    /* primary button / CTA hover → pulse from the nearest soma */
    const onPointerOver = (e: PointerEvent): void => {
      if (reduced || mode !== "neural" || time - lastHover < 0.9) return;
      const el = e.target instanceof Element ? e.target.closest("a, button") : null;
      if (!el || !el.classList.contains("bg-brand")) return;
      const r = el.getBoundingClientRect();
      const ux = (r.left + r.width / 2 - W / 2) / S + 0.5;
      const uy = (r.top + r.height / 2 - H / 2) / S + 0.5;
      let best: PulseTrack | null = null;
      let bd = Infinity;
      for (const p of somaPathList) {
        const dx = p.pts[0] - ux;
        const dy = p.pts[1] - uy;
        const d = dx * dx + dy * dy;
        if (d < bd) {
          bd = d;
          best = p;
        }
      }
      if (best) {
        hoverPulse = { tr: best, t0: time };
        lastHover = time;
      }
    };
    document.addEventListener("pointerover", onPointerOver, { passive: true });

    let rebuildTimer = 0;
    const scheduleRebuild = (): void => {
      window.clearTimeout(rebuildTimer);
      rebuildTimer = window.setTimeout(() => {
        pal = readPalette();
        measure();
        rebuild();
        if (reduced) composite(true);
      }, 220);
    };
    const onResize = (): void => scheduleRebuild();
    window.addEventListener("resize", onResize);
    rezoneRef.current = scheduleRebuild; // route-zone change → re-measure + re-scene
    const themeObserver = new MutationObserver(scheduleRebuild);
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });

    /* start after first paint so it never delays LCP */
    interface IdleWindowish {
      requestIdleCallback?(cb: () => void): number;
      cancelIdleCallback?(id: number): void;
    }
    const idleWindow = window as unknown as IdleWindowish;
    let idleId = 0;
    const start = (): void => {
      measure();
      rebuild();
      setTarget(legalRef.current);
      if (reduced) composite(true);
      else setRunning(!document.hidden);
    };
    if (typeof idleWindow.requestIdleCallback === "function") {
      idleId = idleWindow.requestIdleCallback(start);
    } else {
      idleId = window.setTimeout(start, 220);
    }

    return (): void => {
      if (typeof idleWindow.cancelIdleCallback === "function") idleWindow.cancelIdleCallback(idleId);
      else window.clearTimeout(idleId);
      applyRef.current = null;
      rezoneRef.current = null;
      setRunning(false);
      if (rafId) cancelAnimationFrame(rafId);
      window.clearTimeout(rebuildTimer);
      window.removeEventListener("resize", onResize);
      window.removeEventListener("mousemove", onMouse);
      window.removeEventListener("scroll", onScroll);
      document.removeEventListener("visibilitychange", onVisibility);
      document.removeEventListener("pointerover", onPointerOver);
      themeObserver.disconnect();
    };
  }, [reduced]);

  return <canvas ref={canvasRef} className="site-background" aria-hidden="true" />;
}
