/**
 * Brain-Co Cinematic Engine — Unified Multi-Target Visual Controller
 * Recreates the complete 7-stage experience from Organizational Brain Refrence (1).html:
 * 0. Hero: Authenticated Gross-Anatomical Human Brain (16k Shards from models/original/brain.glb)
 * 1. Legal / Compliance: Brass Balance Scale on Marble Base
 * 2. Human Resources: 3 Connected Human Figures & Organizational Network
 * 3. Sales: Volumetric 3D Growth Bars & Ascending Golden Arrow
 * 4. Finance: Tilted Orbital Coin Ring & Central Reserve Stack
 * 5. Operations: 3 Connected Translucent Layer Disks & Flow Pipelines
 * 6. Final: Return to Unified System / Coalesced Brain
 *
 * Synchronous idempotent React 19 lifecycle, full context loss recovery, and performance telemetry.
 */

import * as THREE from "three";
import { DeviceTier, PARTICLE_BUDGETS, type BrainEngineOptions, type ParticleBudget } from "./types";
import { UnifiedMorphEngine } from "./unified-morph-engine";

export interface PerformanceMetrics {
  fps: number;
  frameTimeMs: number;
  drawCalls: number;
  triangles: number;
  tier: DeviceTier;
}

export class ThreeBrainEngine {
  private canvas: HTMLCanvasElement;
  private options: BrainEngineOptions;
  private budget: ParticleBudget;

  private renderer: THREE.WebGLRenderer | null = null;
  private camera: THREE.PerspectiveCamera | null = null;
  private scene: THREE.Scene | null = null;

  // Primary Unified Multi-Target Morphing Engine
  private unifiedEngine: UnifiedMorphEngine | null = null;

  private rafId: number | null = null;
  private lastTime: number = 0;
  private targetProgress: number = 0; // [0.0, 6.0]

  // Performance telemetry
  private frameTimes: number[] = [];
  private currentFps: number = 60;
  private avgFrameTimeMs: number = 16.6;

  public isContextLost: boolean = false;
  public isRendering: boolean = false;

  private resizeObserver: ResizeObserver | null = null;

  // Bound event handlers
  private boundHandleResize: () => void;
  private boundHandleVisibilityChange: () => void;
  private boundHandlePointerMove: (e: MouseEvent) => void;
  private boundHandleContextLost: (e: Event) => void;
  private boundHandleContextRestored: () => void;
  private boundTick: (time: number) => void;

  constructor(canvas: HTMLCanvasElement, options: BrainEngineOptions = {}) {
    this.canvas = canvas;
    this.options = options;
    const tier = options.tier || DeviceTier.Tier2_DesktopStandard;
    this.budget = PARTICLE_BUDGETS[tier] || PARTICLE_BUDGETS[DeviceTier.Tier2_DesktopStandard];

    this.boundHandleResize = this.handleResize.bind(this);
    this.boundHandleVisibilityChange = this.handleVisibilityChange.bind(this);
    this.boundHandlePointerMove = this.handlePointerMove.bind(this);
    this.boundHandleContextLost = this.handleContextLost.bind(this);
    this.boundHandleContextRestored = this.handleContextRestored.bind(this);
    this.boundTick = this.tick.bind(this);

    this.init();
  }

  private init(): void {
    if (this.budget.shardCount === 0) {
      return; // Tier 5 Fallback
    }

    const width = this.canvas.clientWidth || (typeof window !== "undefined" ? window.innerWidth : 1280);
    const height = this.canvas.clientHeight || (typeof window !== "undefined" ? window.innerHeight : 800);

    // Renderer configuration
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
      depth: false,
    });

    const dpr = Math.min(typeof window !== "undefined" ? window.devicePixelRatio : 1, this.budget.dprCap);
    this.renderer.setPixelRatio(dpr);
    this.renderer.setSize(width, height, false);
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.05;

    // Camera setup with perspective matching Dala & Reference
    this.camera = new THREE.PerspectiveCamera(38, width / height, 0.1, 100);
    this.camera.position.set(0.0, 0.0, 7.4);

    this.scene = new THREE.Scene();

    // Studio lighting matching reference HTML
    const key = new THREE.DirectionalLight(0xfff0e2, 2.4);
    key.position.set(4, 5, 6);
    this.scene.add(key);

    const rim = new THREE.DirectionalLight(0x38d6ff, 2.6);
    rim.position.set(-5, 2, -5);
    this.scene.add(rim);

    const rim2 = new THREE.DirectionalLight(0xc04bff, 1.4);
    rim2.position.set(5, -2, -4);
    this.scene.add(rim2);

    this.scene.add(new THREE.HemisphereLight(0x8aa4ff, 0x2a1245, 0.55));

    // Initialize Unified Morph Engine
    this.unifiedEngine = new UnifiedMorphEngine(this.scene, {
      shardCount: this.budget.shardCount,
      morphSpeed: 0.08,
      spinSpeed: 0.15,
    });

    this.setupListeners();
  }

  private setupListeners(): void {
    if (typeof window !== "undefined") {
      window.addEventListener("resize", this.boundHandleResize, { passive: true });
      window.addEventListener("mousemove", this.boundHandlePointerMove, { passive: true });
      document.addEventListener("visibilitychange", this.boundHandleVisibilityChange);
    }

    this.canvas.addEventListener("webglcontextlost", this.boundHandleContextLost);
    this.canvas.addEventListener("webglcontextrestored", this.boundHandleContextRestored);

    if (typeof ResizeObserver !== "undefined") {
      this.resizeObserver = new ResizeObserver(() => {
        this.handleResize();
      });
      this.resizeObserver.observe(this.canvas);
    }
  }

  public start(): void {
    if (this.isRendering || this.isContextLost) return;
    this.isRendering = true;
    this.lastTime = performance.now();
    this.rafId = requestAnimationFrame(this.boundTick);
  }

  public stop(): void {
    this.isRendering = false;
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
  }

  public setTargetScroll(progress: number): void {
    this.targetProgress = Math.max(0.0, Math.min(6.0, progress));
    this.unifiedEngine?.setScrollProgress(this.targetProgress);
  }

  public setMorphProgress(progress: number): void {
    this.setTargetScroll(progress);
  }

  private handlePointerMove(e: MouseEvent): void {
    if (typeof window === "undefined") return;
    const x = (e.clientX / window.innerWidth) * 2.0 - 1.0;
    const y = -((e.clientY / window.innerHeight) * 2.0 - 1.0);
    this.unifiedEngine?.setPointer(x, y, 1.0);
  }

  private tick(time: number): void {
    if (!this.isRendering || this.isContextLost) return;

    const delta = Math.min((time - this.lastTime) * 0.001, 0.05);
    this.lastTime = time;

    // Track frame metrics
    const frameMs = delta * 1000.0;
    this.frameTimes.push(frameMs);
    if (this.frameTimes.length > 60) this.frameTimes.shift();

    const sumMs = this.frameTimes.reduce((acc, val) => acc + val, 0);
    this.avgFrameTimeMs = sumMs / this.frameTimes.length;
    this.currentFps = Math.round(1000.0 / (this.avgFrameTimeMs || 16.6));

    const width = this.canvas.clientWidth || (typeof window !== "undefined" ? window.innerWidth : 1280);
    const height = this.canvas.clientHeight || (typeof window !== "undefined" ? window.innerHeight : 800);

    // Update Unified Morph Engine
    if (this.unifiedEngine && this.camera) {
      this.unifiedEngine.update(time, this.camera, width, height);
    }

    if (this.renderer && this.scene && this.camera) {
      this.renderer.render(this.scene, this.camera);
    }

    this.rafId = requestAnimationFrame(this.boundTick);
  }

  private handleResize(): void {
    if (!this.renderer || !this.camera || !this.canvas) return;

    const width = this.canvas.clientWidth || (typeof window !== "undefined" ? window.innerWidth : 1280);
    const height = this.canvas.clientHeight || (typeof window !== "undefined" ? window.innerHeight : 800);

    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();

    const dpr = Math.min(typeof window !== "undefined" ? window.devicePixelRatio : 1, this.budget.dprCap);
    this.renderer.setPixelRatio(dpr);
    this.renderer.setSize(width, height, false);
  }

  private handleVisibilityChange(): void {
    if (document.hidden) {
      this.stop();
    } else if (!this.isContextLost) {
      this.start();
    }
  }

  private handleContextLost(e: Event): void {
    e.preventDefault();
    this.isContextLost = true;
    this.stop();
    this.options.onContextLost?.();
  }

  private handleContextRestored(): void {
    if (!this.renderer) return;

    this.isContextLost = false;
    this.unifiedEngine?.dispose();
    this.unifiedEngine = null;

    if (this.scene) {
      this.unifiedEngine = new UnifiedMorphEngine(this.scene, {
        shardCount: this.budget.shardCount,
        morphSpeed: 0.08,
        spinSpeed: 0.15,
      });
      this.unifiedEngine.setScrollProgress(this.targetProgress);
    }

    this.options.onContextRestored?.();
    this.start();
  }

  public getRenderer(): THREE.WebGLRenderer | null {
    return this.renderer;
  }

  public getPerformanceMetrics(): PerformanceMetrics {
    const drawCalls = this.renderer?.info.render.calls || 0;
    const triangles = this.renderer?.info.render.triangles || 0;
    return {
      fps: this.currentFps,
      frameTimeMs: parseFloat(this.avgFrameTimeMs.toFixed(2)),
      drawCalls,
      triangles,
      tier: this.options.tier || DeviceTier.Tier2_DesktopStandard,
    };
  }

  public dispose(): void {
    this.stop();

    if (typeof window !== "undefined") {
      window.removeEventListener("resize", this.boundHandleResize);
      window.removeEventListener("mousemove", this.boundHandlePointerMove);
      document.removeEventListener("visibilitychange", this.boundHandleVisibilityChange);
    }

    this.canvas.removeEventListener("webglcontextlost", this.boundHandleContextLost);
    this.canvas.removeEventListener("webglcontextrestored", this.boundHandleContextRestored);

    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
      this.resizeObserver = null;
    }

    if (this.unifiedEngine) {
      this.unifiedEngine.dispose();
      this.unifiedEngine = null;
    }

    if (this.renderer) {
      this.renderer.dispose();
      this.renderer = null;
    }

    this.scene = null;
    this.camera = null;
  }
}
