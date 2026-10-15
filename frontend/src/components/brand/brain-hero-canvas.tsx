"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { buildShapeBuffers, type ShapeBuffers, type ShapeKey } from "./brain-shapes";
import { brainPhaseStore, TIMELINE } from "./brain-phase";

/**
 * The hero centerpiece: a morphing particle brain on a plain 2D <canvas>,
 * ported faithfully from the reference IIFE in
 * docs/reference/brain-co_V2.html — same shapes, same motion (spring catch-up
 * per particle, random wake delay, travelling shimmer, perspective, vertex
 * dots). Only the colours change: every palette is built from the site's CSS
 * tokens at runtime.
 *
 * Panel-free + theme-aware (hero fix pass):
 *  - the canvas is TRANSPARENT (clearRect, no fill) and edge-masked by the
 *    wrapper — particles sit directly on the page background;
 *  - dark theme keeps additive ('lighter') glow;
 *  - light theme uses normal blending with deeper, more saturated purple
 *    tints (deeper amber for the Legal scales), higher alpha and slightly
 *    larger particles, so the brain reads crisply on the light page;
 *  - particles start AT the brain targets (already formed, no fly-in) and the
 *    wrapper crossfades the server-rendered placeholder out once onReady fires.
 *
 * All work happens inside useEffect (SSR-safe): engine start is deferred to
 * requestIdleCallback so it never delays first paint/LCP, rendering pauses
 * while off-screen or tab-hidden, resize rebuilds are debounced, DPR is
 * capped at 2, and per-frame fill styles are bucket-quantised into a string
 * cache (the reference allocates one rgba() string per particle per frame).
 */

type RGB = [number, number, number];

const TOKEN_FALLBACKS = { brand: "#8052ff", hover: "#946eff", gold: "#f3ca78" } as const;

function cssVar(name: string, fallback: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback;
}
function hexToRgb(hex: string): RGB {
  const h = hex.trim();
  return [
    parseInt(h.slice(1, 3), 16),
    parseInt(h.slice(3, 5), 16),
    parseInt(h.slice(5, 7), 16),
  ];
}
function mix(a: RGB, b: RGB, t: number): RGB {
  return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
}
function lighten(c: RGB, t: number): RGB {
  return mix(c, [255, 255, 255], t);
}
function darken(c: RGB, t: number): RGB {
  return mix(c, [0, 0, 0], t);
}

interface Palette {
  brain: RGB[];
  legal: RGB[];
  sales: RGB[];
  hr: RGB[];
  dot1: RGB; // V=1 bright vertex dot (light purple tint)
  dot2: RGB; // V=2 hub dot (near-white purple tint)
}

/**
 * Site-token palettes: BRAIN = purple family; LEGAL = purple + the existing
 * --gold accent; SALES/HR = purple family with slight lightness variation.
 * (The reference's cyan/blue/pink palettes are deliberately not used.)
 * Light theme: deeper, more saturated tints — additive glow would be invisible
 * on the light page, so these are drawn with source-over instead.
 */
function buildPalettes(light: boolean): Palette {
  const brand = hexToRgb(cssVar("--brand", TOKEN_FALLBACKS.brand));
  const hover = hexToRgb(cssVar("--brand-hover", TOKEN_FALLBACKS.hover));
  const gold = hexToRgb(cssVar("--gold", TOKEN_FALLBACKS.gold));
  if (!light) {
    return {
      brain: [
        brand,
        hover,
        lighten(brand, 0.2),
        lighten(brand, 0.4),
        lighten(brand, 0.58),
        darken(brand, 0.25),
        darken(brand, 0.45),
        mix(brand, hover, 0.5),
        lighten(hover, 0.3),
        mix(brand, [255, 255, 255], 0.75),
      ],
      legal: [gold, lighten(gold, 0.28), lighten(gold, 0.5), brand, lighten(brand, 0.25)],
      sales: [brand, hover, lighten(brand, 0.22), darken(brand, 0.3)],
      hr: [brand, mix(brand, hover, 0.5), lighten(brand, 0.18), darken(brand, 0.35)],
      dot1: lighten(brand, 0.55),
      dot2: lighten(brand, 0.82),
    };
  }
  const satDeep: RGB = [96, 38, 224]; // deeper, saturated brand purple
  return {
    brain: [
      brand,
      hover,
      darken(brand, 0.14),
      darken(brand, 0.28),
      mix(brand, satDeep, 0.5),
      darken(hover, 0.1),
      darken(brand, 0.4),
      mix(brand, hover, 0.5),
      darken(brand, 0.22),
      mix(brand, satDeep, 0.32),
    ],
    legal: [gold, darken(gold, 0.16), mix(gold, brand, 0.3), brand, darken(brand, 0.22)],
    sales: [brand, hover, darken(brand, 0.18), darken(brand, 0.34)],
    hr: [brand, mix(brand, hover, 0.5), darken(brand, 0.1), darken(brand, 0.38)],
    dot1: mix(brand, hover, 0.45),
    dot2: hover,
  };
}

interface IdleWindow {
  requestIdleCallback(cb: () => void): number;
  cancelIdleCallback(id: number): void;
}

export function BrainHeroCanvas({
  ready,
  onReady,
}: {
  ready?: boolean;
  onReady?: () => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const onReadyRef = useRef(onReady);
  useEffect(() => {
    onReadyRef.current = onReady;
  });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const surface: HTMLCanvasElement = canvas;
    const ctx = surface.getContext("2d");
    if (!ctx) return;
    const context: CanvasRenderingContext2D = ctx;
    const container = surface.parentElement ?? canvas;

    const R = Math.random;
    const TAU = Math.PI * 2;
    const cl = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));
    const DPR = () => Math.min(window.devicePixelRatio || 1, 2);

    let W = 0;
    let H = 0;
    let S = 0;
    let cx = 0;
    let cy = 0;
    let N = 0;
    let shapes: Record<ShapeKey, ShapeBuffers> | null = null;
    let px = new Float32Array(0);
    let py = new Float32Array(0);
    let pz = new Float32Array(0);
    let ci = new Uint8Array(0);
    let cr = new Float32Array(0);
    let cg = new Float32Array(0);
    let cb = new Float32Array(0);
    let sp = new Float32Array(0);
    let ph = new Float32Array(0);
    let wake = new Float32Array(0);
    let light = document.documentElement.classList.contains("light");
    let pal = buildPalettes(light);
    let curPhase = 0;
    let phaseStart = 0;
    let paused = false;
    let manualPauseUntil = 0;
    let started = false;
    let readyFired = false;
    let running = false;
    let rafId = 0;
    let last = 0;
    let ioVisible = true;
    /* Per-mount token: false once THIS effect run has been cleaned up. Every
       frame checks it first, so a stale callback can never touch engine state
       after unmount — and state is closure-local, so one mount's cleanup can
       never null another mount's engine. */
    let alive = true;
    /* Set only at the end of init(), once shapes and buffers are fully built.
       The rAF loop may start exclusively after this (see setRunning). */
    let engineReady = false;

    /* fillStyle bucket cache: quantised rgb (8-step) + alpha (1/40) — the
       look is identical to per-particle rgba() but allocation-free. */
    const styleCache = new Map<number, string>();
    function styleFor(r: number, g: number, b: number, a: number): string {
      const qa = Math.min(52, Math.round(a * 40));
      const key = ((r >> 3) << 15) | ((g >> 3) << 10) | ((b >> 3) << 5) | qa;
      let s = styleCache.get(key);
      if (s === undefined) {
        s = `rgba(${(r >> 3) << 3},${(g >> 3) << 3},${(b >> 3) << 3},${(qa / 40).toFixed(3)})`;
        styleCache.set(key, s);
      }
      return s;
    }

    /**
     * Sizes + (when the particle count changes) buffers are built into LOCALS
     * first and swapped in one synchronous step at the end — `shapes` is never
     * assigned null, and a running loop can only ever observe a complete state
     * (frame callbacks run between tasks, never inside this function).
     */
    function init(): void {
      const rect = container.getBoundingClientRect();
      const w = Math.max(200, Math.round(rect.width));
      const h = Math.max(200, Math.round(rect.height));
      const n = window.innerWidth < 768 ? 4200 : 7000;
      const rebuild = n !== N || !shapes;

      let nextShapes = shapes;
      let nextPx = px;
      let nextPy = py;
      let nextPz = pz;
      let nextCi = ci;
      let nextCr = cr;
      let nextCg = cg;
      let nextCb = cb;
      let nextSp = sp;
      let nextPh = ph;
      let nextWake = wake;
      if (rebuild) {
        const built = buildShapeBuffers(n);
        nextShapes = built;
        nextPx = Float32Array.from(built.brain.X);
        nextPy = Float32Array.from(built.brain.Y);
        nextPz = Float32Array.from(built.brain.Z);
        nextCi = new Uint8Array(n);
        nextCr = new Float32Array(n);
        nextCg = new Float32Array(n);
        nextCb = new Float32Array(n);
        nextSp = new Float32Array(n);
        nextPh = new Float32Array(n);
        nextWake = new Float32Array(n);
        for (let i = 0; i < n; i++) {
          nextCi[i] = (R() * 32) | 0;
          const c = pal.brain[nextCi[i] % pal.brain.length];
          nextCr[i] = c[0];
          nextCg[i] = c[1];
          nextCb[i] = c[2];
          nextSp[i] = 0.65 + R() * 0.65;
          nextPh[i] = R() * TAU;
        }
      }

      // Atomic swap of geometry + buffers.
      const dpr = DPR();
      surface.width = Math.round(w * dpr);
      surface.height = Math.round(h * dpr);
      surface.style.width = `${w}px`;
      surface.style.height = `${h}px`;
      context.setTransform(dpr, 0, 0, dpr, 0, 0);
      W = w;
      H = h;
      S = Math.min(W * 0.52, H * 0.56);
      cx = W * 0.5;
      cy = H * 0.5;
      if (rebuild) {
        N = n;
        shapes = nextShapes;
        px = nextPx;
        py = nextPy;
        pz = nextPz;
        ci = nextCi;
        cr = nextCr;
        cg = nextCg;
        cb = nextCb;
        sp = nextSp;
        ph = nextPh;
        wake = nextWake;
        styleCache.clear();
      }
      // Shapes are fully built now — starting the rAF loop is allowed.
      engineReady = true;
    }

    function advanceShape(manual: boolean): void {
      curPhase = (curPhase + 1) % TIMELINE.length;
      const now = performance.now() / 1000;
      phaseStart = now;
      if (manual) manualPauseUntil = now + 5;
      for (let k = 0; k < N; k++) wake[k] = now + R() * 0.35;
      brainPhaseStore.set({ live: true, shape: TIMELINE[curPhase].shape, index: curPhase });
    }

    function frame(ms: number): void {
      // 1. Per-mount token first: after cleanup this frame must do nothing
      //    and must NOT re-arm — the loop dies with the mount.
      if (!alive) return;
      rafId = requestAnimationFrame(frame);
      const now = ms / 1000;
      // 2. Timeline guard: never index TIMELINE out of range.
      const entry = TIMELINE[curPhase];
      if (!entry) return;
      if (!started) {
        started = true;
        last = now;
        phaseStart = now;
        for (let k = 0; k < N; k++) wake[k] = now + R() * 0.4;
        const first = TIMELINE[0];
        if (first) brainPhaseStore.set({ live: true, shape: first.shape, index: 0 });
      }
      const dt = Math.min(0.05, now - last);
      last = now;
      if (!paused && now > manualPauseUntil && now - phaseStart > entry.hold) {
        advanceShape(false);
      }

      // 3. Engine-state guards: skip the draw (loop stays armed) if shapes,
      //    the canvas geometry or the target phase is not available.
      if (!shapes) return;
      if (!W || !H || surface.width === 0 || surface.height === 0) return;
      const shapeKey = TIMELINE[curPhase]?.shape;
      if (!shapeKey) return;
      const sh = shapes[shapeKey];
      const palFor = pal[shapeKey];
      if (!sh || !palFor) return;
      /* Transparent panel: clear only — particles sit on the page background.
         Dark theme keeps the reference's additive glow, light theme draws
         opaque-ish tints with normal compositing (additive is invisible on
         light backgrounds). */
      context.globalCompositeOperation = "source-over";
      context.clearRect(0, 0, W, H);
      context.globalCompositeOperation = light ? "source-over" : "lighter";

      const base = S / 190;
      for (let i = 0; i < N; i++) {
        if (now >= wake[i]) {
          const k = 1 - Math.exp(-dt * sp[i]);
          px[i] += (sh.X[i] - px[i]) * k;
          py[i] += (sh.Y[i] - py[i]) * k;
          pz[i] += (sh.Z[i] - pz[i]) * k;
        }
        const c = palFor[ci[i] % palFor.length];
        cr[i] += (c[0] - cr[i]) * 0.022;
        cg[i] += (c[1] - cg[i]) * 0.022;
        cb[i] += (c[2] - cb[i]) * 0.022;

        const z = pz[i];
        const f = 3.2 / (3.2 - z);
        const sx = cx + px[i] * S * f;
        const sy = cy - py[i] * S * f;

        /* travelling shimmer, positions stay fixed */
        let sw = Math.max(0, Math.sin(px[i] * 3.5 - py[i] * 2 - now * 1.1));
        sw = sw * sw * sw * sw;
        const a = cl(0.8 + 0.14 * Math.sin(now * 0.7 + ph[i]) + sw * 0.5, 0.55, 1) * cl(0.7 + 0.6 * z, 0.7, 1.3);
        const sz = (base + sw * 1.3) * f * (light ? 1.5 : 1.25);
        let r: number;
        let g: number;
        let b: number;
        let al: number;
        if (light) {
          /* deeper colours kept as-is (no whitening), higher alpha */
          r = cr[i] | 0;
          g = cg[i] | 0;
          b = cb[i] | 0;
          al = cl(a * 1.15, 0.72, 1);
        } else {
          r = Math.min(255, cr[i] * 1.25) | 0;
          g = Math.min(255, cg[i] * 1.25) | 0;
          b = Math.min(255, cb[i] * 1.25) | 0;
          al = a;
        }
        const vt = sh.V[i];
        if (vt === 3) {
          /* Sharp outline/fissure particle (brain only): ~38% smaller with a
             bump of alpha — crisp contours, no additive-glow bloom spilling
             past the silhouette. Other shapes never emit V=3. */
          const ssz = sz * 0.62;
          const a3 = light ? cl(al * 1.2, 0, 0.96) : cl(al * 1.08, 0, 0.85);
          context.fillStyle = styleFor(r, g, b, a3);
          context.fillRect(sx - ssz / 2, sy - ssz / 2, ssz, ssz);
          continue;
        }
        if (vt === 1) {
          r = pal.dot1[0] | 0;
          g = pal.dot1[1] | 0;
          b = pal.dot1[2] | 0;
          al = 1;
          context.fillStyle = styleFor(r, g, b, al);
          context.fillRect(sx - sz * 1.2, sy - sz * 1.2, sz * 2.4, sz * 2.4);
          continue;
        }
        if (vt === 2) {
          r = pal.dot2[0] | 0;
          g = pal.dot2[1] | 0;
          b = pal.dot2[2] | 0;
          al = 1;
          context.fillStyle = styleFor(r, g, b, al);
          context.fillRect(sx - sz * 1.8, sy - sz * 1.8, sz * 3.6, sz * 3.6);
          continue;
        }
        context.fillStyle = styleFor(r, g, b, al);
        context.fillRect(sx - sz / 2, sy - sz / 2, sz, sz);
      }
      context.globalCompositeOperation = "source-over";
      if (!readyFired) {
        readyFired = true; // first frame drawn → wrapper crossfades the placeholder
        onReadyRef.current?.();
      }
    }

    function setRunning(run: boolean): void {
      if (run === running) return;
      // The loop may only start once init() has fully built shapes/buffers —
      // this is what previously let an IntersectionObserver/visibilitychange
      // callback start frame() before requestIdleCallback had run init().
      if (run && (!engineReady || !shapes)) return;
      running = run;
      if (run) {
        last = performance.now() / 1000;
        phaseStart = last;
        if (!rafId) rafId = requestAnimationFrame(frame);
      } else if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = 0;
      }
    }

    /* --- lifecycle ------------------------------------------------- */

    const applyTheme = (): void => {
      light = document.documentElement.classList.contains("light");
      pal = buildPalettes(light);
      styleCache.clear();
    };
    applyTheme();
    const themeObserver = new MutationObserver(applyTheme);
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });

    const update = (): void => setRunning(ioVisible && !document.hidden);
    const intersectionObserver = new IntersectionObserver(
      (entries) => {
        ioVisible = entries.some((entry) => entry.isIntersecting);
        update();
      },
      { threshold: 0 },
    );
    intersectionObserver.observe(canvas);
    document.addEventListener("visibilitychange", update);

    const onEnter = (): void => {
      paused = true;
    };
    const onLeave = (): void => {
      paused = false;
    };
    const onClick = (): void => advanceShape(true);
    container.addEventListener("mouseenter", onEnter);
    container.addEventListener("mouseleave", onLeave);
    container.addEventListener("click", onClick);

    let resizeTimer = 0;
    const onResize = (): void => {
      window.clearTimeout(resizeTimer);
      resizeTimer = window.setTimeout(init, 150);
    };
    window.addEventListener("resize", onResize);

    // Start after first paint so the engine never delays LCP.
    let idleId = 0;
    const idleWindow = window as unknown as IdleWindow;
    const start = (): void => {
      init();
      update();
    };
    if (typeof idleWindow.requestIdleCallback === "function") {
      idleId = idleWindow.requestIdleCallback(start);
    } else {
      idleId = window.setTimeout(start, 200);
    }

    return (): void => {
      // Per-mount teardown: block every future frame first, then cancel the
      // pending id and all observers/listeners.
      alive = false;
      if (typeof idleWindow.cancelIdleCallback === "function") idleWindow.cancelIdleCallback(idleId);
      else window.clearTimeout(idleId);
      setRunning(false);
      if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = 0;
      }
      window.clearTimeout(resizeTimer);
      window.removeEventListener("resize", onResize);
      document.removeEventListener("visibilitychange", update);
      intersectionObserver.disconnect();
      themeObserver.disconnect();
      container.removeEventListener("mouseenter", onEnter);
      container.removeEventListener("mouseleave", onLeave);
      container.removeEventListener("click", onClick);
    };
  }, []);

  return <canvas ref={canvasRef} className={cn("brain-canvas", ready && "is-on")} aria-hidden="true" />;
}
