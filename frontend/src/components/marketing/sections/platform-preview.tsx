"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowIcon } from "@/components/brand/icons";
import { buttonClasses } from "@/components/ui/button";
import { Reveal } from "./reveal";
import { cn } from "@/lib/utils";

type PreviewTab = "overview" | "clauses" | "conflicts" | "audit";

export function PlatformPreview() {
  const [activeTab, setActiveTab] = useState<PreviewTab>("overview");

  return (
    <section className="relative py-28 px-4 sm:px-6 lg:px-8 border-t border-white/[0.06] bg-transparent">
      <div className="max-w-6xl mx-auto">
        <div className="max-w-3xl">
          <Reveal>
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-cyan-400">
              Interactive Product Experience
            </div>
            <h2 className="cinematic-title text-3xl sm:text-4xl md:text-5xl font-normal tracking-tight text-white text-balance leading-tight mt-4">
              The Production Workspace.
            </h2>
            <p className="mt-5 text-base sm:text-lg text-zinc-400 font-light leading-relaxed">
              Experience the live inspection console used by leading legal counsels and operations directors.
              Inspect live synthetic extractions, conflict flags, and cryptographic audit proofs below.
            </p>
          </Reveal>
        </div>

        {/* Workspace Console Shell */}
        <Reveal delay={0.12} className="mt-12">
          <div className="rounded-2xl border border-white/[0.12] bg-[#030611] shadow-[0_20px_60px_rgba(0,0,0,0.8)] overflow-hidden">
            {/* Console Window Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 sm:px-6 border-b border-white/[0.08] bg-white/[0.02]">
              <div className="flex items-center gap-3">
                <div className="flex gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-red-500/80" />
                  <span className="w-3 h-3 rounded-full bg-yellow-500/80" />
                  <span className="w-3 h-3 rounded-full bg-emerald-500/80" />
                </div>
                <span className="h-4 w-px bg-white/10" />
                <span className="font-mono text-xs font-medium text-white">
                  SAMPLE-CASE-EGY-2026-08
                </span>
                <span className="hidden sm:inline-block px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-950/60 text-cyan-300 border border-cyan-500/30">
                  Tripartite Concession & EPC
                </span>
              </div>

              {/* Console Navigation Tabs */}
              <div className="flex items-center gap-1 bg-black/60 p-1 rounded-xl border border-white/[0.06]">
                <button
                  type="button"
                  onClick={() => setActiveTab("overview")}
                  className={cn(
                    "px-3 py-1.5 rounded-lg text-xs font-mono transition-all cursor-pointer",
                    activeTab === "overview"
                      ? "bg-white text-black font-semibold"
                      : "text-zinc-400 hover:text-white"
                  )}
                >
                  Overview
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab("clauses")}
                  className={cn(
                    "px-3 py-1.5 rounded-lg text-xs font-mono transition-all cursor-pointer",
                    activeTab === "clauses"
                      ? "bg-white text-black font-semibold"
                      : "text-zinc-400 hover:text-white"
                  )}
                >
                  Clauses (42)
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab("conflicts")}
                  className={cn(
                    "px-3 py-1.5 rounded-lg text-xs font-mono transition-all cursor-pointer flex items-center gap-1.5",
                    activeTab === "conflicts"
                      ? "bg-white text-black font-semibold"
                      : "text-zinc-400 hover:text-white"
                  )}
                >
                  <span>Conflicts</span>
                  <span className="px-1.5 py-0.2 rounded-full text-[9px] bg-amber-500/30 text-amber-300 font-bold">
                    1
                  </span>
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab("audit")}
                  className={cn(
                    "px-3 py-1.5 rounded-lg text-xs font-mono transition-all cursor-pointer",
                    activeTab === "audit"
                      ? "bg-white text-black font-semibold"
                      : "text-zinc-400 hover:text-white"
                  )}
                >
                  Audit Trail
                </button>
              </div>
            </div>

            {/* Console Tab Content */}
            <div className="p-6 sm:p-8 min-h-[380px]">
              {activeTab === "overview" && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="p-5 rounded-xl border border-white/[0.06] bg-white/[0.01]">
                    <span className="text-[11px] font-mono uppercase text-zinc-400">
                      Jurisdiction & Legal Framework
                    </span>
                    <div className="mt-2 text-lg font-medium text-white">
                      Egyptian Civil Code (Law No. 131/1948)
                    </div>
                    <p className="mt-2 text-xs text-zinc-400 leading-relaxed font-light">
                      Governing commercial concessions, public utility exemptions, and mandatory statutory indemnification rules.
                    </p>
                  </div>

                  <div className="p-5 rounded-xl border border-white/[0.06] bg-white/[0.01]">
                    <span className="text-[11px] font-mono uppercase text-zinc-400">
                      Dispatched Ring-1 Engines
                    </span>
                    <div className="mt-2 text-lg font-medium text-cyan-400 font-mono">
                      6 / 6 Operational
                    </div>
                    <p className="mt-2 text-xs text-zinc-400 leading-relaxed font-light">
                      Synthesizing indemnity, force majeure, dispute forums, arbitration jurisdiction, and payment schedules.
                    </p>
                  </div>

                  <div className="p-5 rounded-xl border border-white/[0.06] bg-white/[0.01]">
                    <span className="text-[11px] font-mono uppercase text-zinc-400">
                      Deterministic Risk Index
                    </span>
                    <div className="mt-2 text-lg font-medium text-emerald-400 font-mono">
                      12% (Low Risk)
                    </div>
                    <p className="mt-2 text-xs text-zinc-400 leading-relaxed font-light">
                      1 resolved covenant ambiguity; zero ungrounded clauses; 100% human partner verification complete.
                    </p>
                  </div>
                </div>
              )}

              {activeTab === "clauses" && (
                <div className="overflow-x-auto">
                  <table className="w-full text-left font-mono text-xs">
                    <thead>
                      <tr className="border-b border-white/[0.08] text-zinc-400">
                        <th className="pb-3 font-normal uppercase tracking-wider">Clause ID</th>
                        <th className="pb-3 font-normal uppercase tracking-wider">Statutory Grounding</th>
                        <th className="pb-3 font-normal uppercase tracking-wider">Summary Term</th>
                        <th className="pb-3 font-normal uppercase tracking-wider">Deterministic Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/[0.04]">
                      <tr>
                        <td className="py-3 text-cyan-400">Art. 14.2</td>
                        <td className="py-3 text-zinc-300">ECC Art. 147 (Pacta Sunt Servanda)</td>
                        <td className="py-3 text-zinc-400">Force Majeure & Exceptional Unforeseen Hardship</td>
                        <td className="py-3 text-emerald-400">VERIFIED</td>
                      </tr>
                      <tr>
                        <td className="py-3 text-cyan-400">Art. 18.5</td>
                        <td className="py-3 text-zinc-300">ECC Art. 215 (Contractual Liability)</td>
                        <td className="py-3 text-zinc-400">Aggregate Indemnification Cap ($12,500,000 max)</td>
                        <td className="py-3 text-emerald-400">VERIFIED</td>
                      </tr>
                      <tr>
                        <td className="py-3 text-cyan-400">Art. 22.1</td>
                        <td className="py-3 text-zinc-300">ECC Art. 224 (Liquidated Damages)</td>
                        <td className="py-3 text-zinc-400">Pre-estimated delay compensation per calendar day</td>
                        <td className="py-3 text-emerald-400">VERIFIED</td>
                      </tr>
                      <tr>
                        <td className="py-3 text-cyan-400">Art. 29.4</td>
                        <td className="py-3 text-zinc-300">CRCICA Rules 2024</td>
                        <td className="py-3 text-zinc-400">Cairo Regional Centre for Int. Commercial Arbitration</td>
                        <td className="py-3 text-emerald-400">VERIFIED</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}

              {activeTab === "conflicts" && (
                <div className="p-6 rounded-xl border border-amber-500/30 bg-amber-950/15">
                  <div className="flex items-center gap-2 text-amber-400 font-mono text-xs font-semibold">
                    <span>FLAG #EGY-01: Discrepancy in Default Cure Period</span>
                  </div>
                  <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                    <div className="p-3 rounded-lg bg-black/60 border border-white/[0.06]">
                      <span className="text-zinc-400 uppercase text-[10px]">Master Agreement Sec 14.1:</span>
                      <p className="mt-1 text-white font-medium">30 calendar days written notice</p>
                    </div>
                    <div className="p-3 rounded-lg bg-black/60 border border-white/[0.06]">
                      <span className="text-zinc-400 uppercase text-[10px]">Schedule C (Subcontractor Terms):</span>
                      <p className="mt-1 text-white font-medium">60 calendar days written notice</p>
                    </div>
                  </div>
                  <div className="mt-4 pt-3 border-t border-amber-500/20 flex items-center justify-between text-xs font-mono">
                    <span className="text-zinc-300">Human Resolution: Partner approved override aligning Schedule C to 30 days.</span>
                    <span className="text-emerald-400 font-semibold">RESOLVED & AUDITED</span>
                  </div>
                </div>
              )}

              {activeTab === "audit" && (
                <div className="space-y-3 font-mono text-xs">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                    <div className="flex items-center gap-3">
                      <span className="text-emerald-400">[RING-1 RUN]</span>
                      <span className="text-white">Document Ingestion & Chunking Complete</span>
                    </div>
                    <span className="text-zinc-400 text-[11px]">2026-11-16 14:22:04 UTC &middot; hash: 9a4f2e</span>
                  </div>
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                    <div className="flex items-center gap-3">
                      <span className="text-cyan-400">[ASSERTION]</span>
                      <span className="text-white">ECC Statutory Harmonization Passed</span>
                    </div>
                    <span className="text-zinc-400 text-[11px]">2026-11-16 14:22:07 UTC &middot; hash: cb8120</span>
                  </div>
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                    <div className="flex items-center gap-3">
                      <span className="text-purple-400">[HUMAN SIGN]</span>
                      <span className="text-white">Managing Partner Sign-off (CACS Token: user-712)</span>
                    </div>
                    <span className="text-zinc-400 text-[11px]">2026-11-16 14:24:19 UTC &middot; hash: ef0031</span>
                  </div>
                </div>
              )}
            </div>

            {/* Console Footer */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 sm:px-6 border-t border-white/[0.08] bg-black/60">
              <span className="text-xs font-mono text-zinc-400">
                Live sandbox &middot; All mock data isolated from production tenants
              </span>
              <Link
                href="/onboarding"
                className={cn(buttonClasses("pill-white", "sm"), "text-xs font-semibold px-4")}
              >
                <span>Launch Your Custom Workspace</span>
                <ArrowIcon />
              </Link>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
