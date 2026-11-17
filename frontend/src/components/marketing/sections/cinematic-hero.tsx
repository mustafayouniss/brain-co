"use client";

import React from "react";
import Link from "next/link";
import { ArrowIcon } from "@/components/brand/icons";
import { buttonClasses } from "@/components/ui/button";
import { Reveal } from "./reveal";
import { cn } from "@/lib/utils";

export function CinematicHero() {
  return (
    <section className="relative min-h-[94vh] flex items-center px-4 sm:px-6 lg:px-12 pt-24 pb-16 overflow-hidden">
      <div className="w-full max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">
        {/* Left Editorial Narrative Column */}
        <div className="lg:col-span-7 xl:col-span-7 flex flex-col items-start text-left z-10">
          {/* Dala-Grade Eyebrow Badge (Amber/Gold Signal) */}
          <Reveal>
            <div className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full border border-[#ffb829]/25 bg-[#ffb829]/[0.08] mb-8">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#ffb829] opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#ffb829]" />
              </span>
              <span className="text-[11px] font-mono uppercase tracking-[0.22em] text-[#ffb829] font-medium">
                Autonomous Neural Architecture &middot; Ring-1 Active
              </span>
            </div>
          </Reveal>

          {/* Dala-Grade Display Headline (3 deliberate editorial breaks, tight tracking) */}
          <Reveal delay={0.06}>
            <h1 className="cinematic-display text-5xl sm:text-7xl md:text-8xl lg:text-[5.5rem] xl:text-[6.25rem] font-medium tracking-[-0.038em] text-white max-w-3xl leading-[0.92]">
              Your organization <br />
              has a brain. <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-b from-white via-zinc-200 to-zinc-400">
                Put it to work.
              </span>
            </h1>
          </Reveal>

          {/* Editorial Subtitle */}
          <Reveal delay={0.12}>
            <p className="mt-8 max-w-xl text-base sm:text-lg text-zinc-400 font-light leading-[1.65] text-balance">
              A unified cognitive layer that aggregates fragmented organizational memory,
              verifies domain logic with deterministic rigor, and prevents decades of institutional precedent from walking out the door.
            </p>
          </Reveal>

          {/* Action CTAs (Vivid Purple Primary Pill + Glass Secondary Pill) */}
          <Reveal delay={0.18} className="mt-10 flex flex-wrap items-center gap-4">
            <Link
              href="/onboarding"
              className={cn(
                buttonClasses("primary", "lg"),
                "group px-8 text-sm rounded-full bg-[#6d35ff] hover:bg-[#5b28e6] text-white shadow-[0_0_30px_rgba(109,53,255,0.5)] border-0 transition-all duration-300 hover:shadow-[0_0_40px_rgba(109,53,255,0.7)]"
              )}
            >
              <span>Deploy Your Brain</span>
              <ArrowIcon className="transition-transform duration-200 group-hover:translate-x-1" />
            </Link>
            <Link
              href="/modules"
              className={cn(
                buttonClasses("pill-glass", "lg"),
                "px-8 text-sm hover:border-white/30 transition-colors"
              )}
            >
              <span>Explore Intelligence Modules</span>
            </Link>
          </Reveal>

          {/* Telemetry pill bar */}
          <Reveal delay={0.24}>
            <div className="mt-16 grid grid-cols-2 sm:grid-cols-4 gap-4 sm:gap-6 pt-8 border-t border-white/[0.08] w-full max-w-2xl">
              <div className="flex flex-col">
                <span className="text-xl sm:text-2xl font-mono font-medium text-white tracking-tight">
                  V1 Active
                </span>
                <span className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider mt-1">
                  Egyptian Civil Code
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-xl sm:text-2xl font-mono font-medium text-white tracking-tight">
                  4 Layers
                </span>
                <span className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider mt-1">
                  Cognitive Pipeline
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-xl sm:text-2xl font-mono font-medium text-cyan-400 tracking-tight">
                  100%
                </span>
                <span className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider mt-1">
                  Human-Validated
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-xl sm:text-2xl font-mono font-medium text-white tracking-tight">
                  0 Silos
                </span>
                <span className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider mt-1">
                  Immutable Ledger
                </span>
              </div>
            </div>
          </Reveal>
        </div>

        {/* Right Spatial Aperture — Unobstructed View of 3D Reference Brain */}
        <div className="lg:col-span-5 xl:col-span-5 relative h-full flex flex-col justify-end items-end pointer-events-none pb-8 hidden lg:flex">
          <Reveal delay={0.32}>
            <div className="flex items-center gap-3 px-3.5 py-1.5 rounded-full border border-white/[0.08] bg-black/60">
              <span className="w-1.5 h-1.5 rounded-full bg-[#ffb829] animate-pulse" />
              <span className="text-[10px] font-mono uppercase tracking-widest text-zinc-400">
                Neural Lattice &middot; 3D Anatomical Architecture
              </span>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
