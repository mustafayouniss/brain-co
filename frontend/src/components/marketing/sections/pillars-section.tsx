"use client";

import React from "react";
import { Reveal } from "./reveal";

const PILLARS = [
  {
    num: "01",
    title: "Immutable Ground-Truth Memory",
    tagline: "Cryptographically partitioned vector & document store",
    description:
      "All ingested agreements, policies, and judicial filings are indexed into isolated tenant partitions. Vector representations maintain exact bidirectional mappings to their origin source lines, ensuring zero hallucinatory drift.",
    metrics: "Sub-millisecond retrieval across 100k+ enterprise filings",
  },
  {
    num: "02",
    title: "Semantic Graph Reasoning",
    tagline: "Multi-hop relational traversal across precedent",
    description:
      "The Brain constructs dynamic knowledge graphs connecting legal entities, cross-guarantees, statutory citations, and historical amendment chains. Complex queries trace full dependency lineages automatically.",
    metrics: "Bidirectional clause lineage & entity mapping",
  },
  {
    num: "03",
    title: "Deterministic Verification",
    tagline: "Mathematical assertion layers overriding LLM output",
    description:
      "Probabilistic AI is never allowed to invent legal facts. Every assertion runs through deterministic logic gates that verify statutory articles, calculation bounds, and procedural deadlines before output is shown.",
    metrics: "100% citation grounding with page & paragraph coordinates",
  },
  {
    num: "04",
    title: "Human Validation Protocol",
    tagline: "Zero unchecked autonomous learning",
    description:
      "Nothing enters permanent institutional memory without explicit partner approval. The Brain proposes interpretations; senior humans validate or correct them, creating an audited, compounding intelligence moat.",
    metrics: "Cryptographically signed audit logs for every approval",
  },
];

export function PillarsSection() {
  return (
    <section className="relative py-28 px-4 sm:px-6 lg:px-8 border-t border-white/[0.06] bg-transparent">
      <div className="max-w-6xl mx-auto">
        <div className="max-w-3xl">
          <Reveal>
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-cyan-400">
              The Organizational Brain Core
            </div>
            <h2 className="cinematic-title text-3xl sm:text-4xl md:text-5xl font-normal tracking-tight text-white text-balance leading-tight mt-4">
              The four foundations of <br />
              <span className="font-light text-zinc-400">deterministic intelligence.</span>
            </h2>
            <p className="mt-5 text-base sm:text-lg text-zinc-400 font-light leading-relaxed">
              Why enterprise legal and operations leaders trust Brain-co: a rigorous architecture
              where mathematics, provenance, and human verification supersede probabilistic guesswork.
            </p>
          </Reveal>
        </div>

        <div className="mt-16 grid grid-cols-1 md:grid-cols-2 gap-6">
          {PILLARS.map((pillar, index) => (
            <Reveal key={pillar.num} delay={index * 0.08}>
              <div className="h-full flex flex-col justify-between p-8 rounded-2xl border border-white/[0.08] bg-black/40 transition-all duration-300 hover:border-white/20 hover:bg-black/60">
                <div>
                  <div className="flex items-center justify-between pb-4 border-b border-white/[0.06]">
                    <span className="text-xs font-mono font-medium text-cyan-400">
                      PILLAR {pillar.num}
                    </span>
                    <span className="text-[11px] font-mono text-zinc-400">
                      Architectural Layer
                    </span>
                  </div>

                  <h3 className="mt-6 text-xl font-medium tracking-tight text-white">
                    {pillar.title}
                  </h3>
                  <p className="mt-1 text-xs font-mono text-cyan-400">
                    {pillar.tagline}
                  </p>

                  <p className="mt-4 text-sm font-light text-zinc-300 leading-relaxed">
                    {pillar.description}
                  </p>
                </div>

                <div className="mt-8 pt-4 border-t border-white/[0.06] flex items-center justify-between text-xs font-mono text-zinc-400">
                  <span>Standard:</span>
                  <span className="text-zinc-200">{pillar.metrics}</span>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
