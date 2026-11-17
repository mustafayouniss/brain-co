"use client";

import React from "react";
import { Reveal } from "./reveal";

const SECURITY_PILLARS = [
  {
    title: "CACS Tenant Isolation",
    badge: "Hardware & Logical Partition",
    description:
      "Context-Aware Access Control (CACS) guarantees data is isolated at the tenant and case level. Even within the same firm, cross-matter walls are enforced mathematically.",
  },
  {
    title: "Zero Model Training",
    badge: "Strict Data Confidentiality",
    description:
      "Your documents, precedent memorandums, and organizational insights are yours alone. Enterprise data is never exposed or used to train public foundational models.",
  },
  {
    title: "Cryptographic WebSocket Auth",
    badge: "Ephemeral Token Streaming",
    description:
      "Live observation feeds and Ring-1 execution progress use single-use, cryptographically signed session tickets with sub-minute expiration windows.",
  },
  {
    title: "Immutable Event Ledger",
    badge: "SOC-2 Ready Auditability",
    description:
      "Every document ingestion, fact extraction, assertion check, and human approval is stamped with a SHA-256 verification hash and persistent timestamp.",
  },
];

export function SecuritySection() {
  return (
    <section className="relative py-28 px-4 sm:px-6 lg:px-8 border-t border-white/[0.06] bg-transparent">
      <div className="max-w-6xl mx-auto">
        <div className="max-w-3xl">
          <Reveal>
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-cyan-400">
              Verifiable Trust & Security
            </div>
            <h2 className="cinematic-title text-3xl sm:text-4xl md:text-5xl font-normal tracking-tight text-white text-balance leading-tight mt-4">
              Enterprise-grade defense. <br />
              <span className="font-light text-zinc-400">Engineered for regulated institutions.</span>
            </h2>
            <p className="mt-5 text-base sm:text-lg text-zinc-400 font-light leading-relaxed">
              We design for organizations where client confidentiality and legal privilege are sacred.
              Security is not an afterthought or an add-on; it is the fundamental architectural constraint.
            </p>
          </Reveal>
        </div>

        <div className="mt-16 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {SECURITY_PILLARS.map((p, index) => (
            <Reveal key={p.title} delay={index * 0.08}>
              <div className="h-full flex flex-col justify-between p-6 rounded-2xl border border-white/[0.08] bg-black/40 transition-all duration-300 hover:border-white/20 hover:bg-black/60">
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400">
                    {p.badge}
                  </span>
                  <h3 className="mt-3 text-lg font-medium text-white tracking-tight">
                    {p.title}
                  </h3>
                  <p className="mt-3 text-xs font-light text-zinc-400 leading-relaxed">
                    {p.description}
                  </p>
                </div>

                <div className="mt-6 pt-4 border-t border-white/[0.06] flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  <span className="text-[11px] font-mono text-zinc-400">Verified Enforced</span>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
