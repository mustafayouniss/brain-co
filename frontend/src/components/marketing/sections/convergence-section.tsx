"use client";

import React from "react";
import { Reveal } from "./reveal";

export function ConvergenceSection() {
  return (
    <section className="relative min-h-[75vh] flex flex-col justify-center items-center py-28 px-4 sm:px-6 lg:px-8 border-t border-white/[0.06] overflow-hidden">
      <div className="max-w-4xl mx-auto text-center">
        <Reveal>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-cyan-500/30 bg-cyan-950/20 text-cyan-400 mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
            <span className="text-[11px] font-mono uppercase tracking-[0.18em]">
              The Generative State Transition
            </span>
          </div>

          <h2 className="cinematic-title text-3xl sm:text-5xl md:text-6xl font-light tracking-tight text-white max-w-3xl mx-auto text-balance leading-tight mt-4">
            Order from chaos. <br />
            <span className="font-medium text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 via-blue-400 to-indigo-300">
              The Convergence.
            </span>
          </h2>

          <p className="mt-8 max-w-2xl mx-auto text-base sm:text-lg text-zinc-300 font-light leading-relaxed">
            When disparate contracts, operational directives, and judicial rulings are mapped into high-dimensional semantic space,
            turbulence collapses. Shards of disconnected data assemble along intentional synaptic pathways.
          </p>
        </Reveal>

        <Reveal delay={0.15}>
          <div className="mt-14 max-w-2xl mx-auto p-8 rounded-2xl border border-white/[0.08] bg-black/75 text-left">
            <div className="flex items-center gap-3 pb-4 border-b border-white/[0.08]">
              <div className="flex gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
                <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/80" />
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
              </div>
              <span className="text-[11px] font-mono text-zinc-400 uppercase tracking-widest">
                Topology Alignment Engine
              </span>
            </div>

            <div className="mt-4 font-mono text-xs leading-relaxed text-zinc-300 space-y-2">
              <p className="text-zinc-400">
                // Coalescing isolated corpora into unified dual-hemisphere memory...
              </p>
              <p className="text-cyan-400">
                &gt; Ingesting 1,420 legal precedent files... [OK]
              </p>
              <p className="text-blue-400">
                &gt; Aligning cross-jurisdictional statutory citations... [OK]
              </p>
              <p className="text-emerald-400">
                &gt; Synaptic lattice stabilized. Zero hallucinations detected.
              </p>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
