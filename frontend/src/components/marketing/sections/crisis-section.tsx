"use client";

import React from "react";
import { Reveal } from "./reveal";

const CRISIS_POINTS = [
  {
    num: "01",
    title: "Trapped in Silos",
    tagline: "Unindexed drives and disconnected departments",
    body: "Critical agreements, partner amendments, and regulatory memorandums sit in private email threads and local downloads. No single team member has access to the full institutional record.",
    stat: "74%",
    statLabel: "of enterprise knowledge is duplicated or inaccessible",
  },
  {
    num: "02",
    title: "The Context Cliff",
    tagline: "Precedent walks out the door on departure day",
    body: "When partners or key specialists resign, their unwritten rationale, negotiation context, and client heuristics evaporate. New teams start from scratch, repeating historical mistakes.",
    stat: "18 Mo",
    statLabel: "average time to rebuild lost domain expertise",
  },
  {
    num: "03",
    title: "Silent Compliance Drift",
    tagline: "Outdated templates masking severe legal exposure",
    body: "Agreements written five years ago continue to be duplicated across active deals without accounting for recent statutory updates, conflicting notice clauses, or indemnification caps.",
    stat: "3.4x",
    statLabel: "higher dispute rate from unreviewed boilerplate",
  },
];

export function CrisisSection() {
  return (
    <section className="relative py-28 px-4 sm:px-6 lg:px-8 border-t border-white/[0.06] bg-transparent">
      <div className="max-w-6xl mx-auto">
        {/* Section Header */}
        <div className="max-w-3xl">
          <Reveal>
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-cyan-400">
              The Fragmentation Crisis
            </div>
            <h2 className="cinematic-title text-3xl sm:text-4xl md:text-5xl font-normal tracking-tight text-white text-balance leading-tight mt-4">
              Organizations lose 80% of what their people learn.
            </h2>
            <p className="mt-5 text-base sm:text-lg text-zinc-400 font-light leading-relaxed">
              Every day, brilliant decisions, negotiated compromises, and hard-won legal interpretations
              are made inside your organization. And every day, they vanish into unindexed email threads and personal memory.
            </p>
          </Reveal>
        </div>

        {/* 3 Editorial Cards */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6">
          {CRISIS_POINTS.map((point, index) => (
            <Reveal key={point.num} delay={index * 0.1}>
              <div className="h-full flex flex-col justify-between p-8 rounded-2xl border border-white/[0.08] bg-black/40 transition-all duration-300 hover:border-white/20 hover:bg-black/60">
                <div>
                  <div className="flex items-center justify-between pb-6 border-b border-white/[0.06]">
                    <span className="text-xs font-mono font-medium text-cyan-400 tracking-wider">
                      {point.num}
                    </span>
                    <span className="text-[11px] font-mono uppercase text-zinc-400 tracking-widest">
                      Vulnerability
                    </span>
                  </div>

                  <h3 className="mt-6 text-xl font-medium tracking-tight text-white">
                    {point.title}
                  </h3>
                  <p className="mt-1 text-xs font-mono text-zinc-300">
                    {point.tagline}
                  </p>

                  <p className="mt-4 text-sm font-light text-zinc-400 leading-relaxed">
                    {point.body}
                  </p>
                </div>

                <div className="mt-8 pt-6 border-t border-white/[0.06]">
                  <div className="text-2xl font-mono font-medium text-white tracking-tight">
                    {point.stat}
                  </div>
                  <div className="text-[11px] font-mono text-zinc-400 mt-0.5">
                    {point.statLabel}
                  </div>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
