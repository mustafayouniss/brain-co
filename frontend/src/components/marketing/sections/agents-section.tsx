"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowIcon } from "@/components/brand/icons";
import { buttonClasses } from "@/components/ui/button";
import { Badge } from "@/components/ui/card";
import { Reveal } from "./reveal";
import { cn } from "@/lib/utils";

interface AgentProfile {
  id: string;
  name: string;
  domain: string;
  status: "active" | "roadmap";
  statusText: string;
  tagline: string;
  description: string;
  capabilities: string[];
  executionSample: {
    input: string;
    output: string;
    latency: string;
    verificationHash: string;
  };
}

const AGENTS: AgentProfile[] = [
  {
    id: "legal",
    name: "Egyptian Legal Intelligence Agent",
    domain: "Corporate & Commercial Law",
    status: "active",
    statusText: "Active in Production (V1)",
    tagline: "Deterministic contract auditing anchored in the Egyptian Civil Code",
    description:
      "Trained on hundreds of judicial precedents and Egyptian commercial statutory frameworks. Dispatches 6 deterministic verification sub-engines to identify indemnity exposure, conflicting notice covenants, and jurisdictional liabilities.",
    capabilities: [
      "Egyptian Civil Code Articles 147 & 148 compliance verification",
      "Multi-document indemnification cap & cross-liability audit",
      "Notice timeline mismatch and procedural anomaly detection",
      "Verbatim statutory and precedent citations with page grounding",
    ],
    executionSample: {
      input: "Review 84-page Master Supply & EPC Construction Agreement (Cairo Metro Expansion)",
      output:
        "Flagged Article 19.3: Notice period (14 days) conflicts with Addendum C (30 days). Detected unilateral penalty clause violating Civil Code Art. 224; recommended revision draft attached.",
      latency: "3.8s execution time",
      verificationHash: "sha256:7f4c9a...e31b80",
    },
  },
  {
    id: "sales",
    name: "Enterprise Deal Intelligence Agent",
    domain: "Sales & Strategic Procurement",
    status: "roadmap",
    statusText: "Architectural Roadmap",
    tagline: "Enduring memory of complex multi-year procurement negotiations",
    description:
      "Synthesizes historical discount tolerances, competitive objection battlecards, and multi-stakeholder procurement histories across long deal cycles.",
    capabilities: [
      "Historical margin & concession threshold tracking",
      "Stakeholder objection matrix with historical win patterns",
      "RFP response drafting with source-grounded case studies",
      "Executive summary synthesis for revenue leadership",
    ],
    executionSample: {
      input: "Generate RFP competitive objection briefing for Global Banking RFP",
      output:
        "Retrieved 14 historical enterprise concessions from 2024-2025. Recommended maximum SLA discount of 4.5% based on previous Procurement Officer history.",
      latency: "2.4s execution time",
      verificationHash: "sha256:1a8d02...f099c2",
    },
  },
  {
    id: "operations",
    name: "Organizational Governance & SOP Agent",
    domain: "Operations & HR Compliance",
    status: "roadmap",
    statusText: "Architectural Roadmap",
    tagline: "Continuous audit readiness and organizational policy continuity",
    description:
      "Maintains the complete institutional repository of internal handbooks, ISO compliance standards, and operating procedures, ensuring zero institutional drift.",
    capabilities: [
      "Internal policy conflict and contradiction detection",
      "Automated standard operating procedure (SOP) versioning",
      "Zero-retention employee query resolution",
      "Audited escalation pathways for executive sign-off",
    ],
    executionSample: {
      input: "Audit revised remote-work policy against local labor regulations",
      output:
        "Detected section 4 ambiguity regarding overtime calculation during public holidays under Egyptian Labor Law No. 12/2003.",
      latency: "1.9s execution time",
      verificationHash: "sha256:c941e1...83ad09",
    },
  },
];

export function AgentsSection() {
  const [selectedAgent, setSelectedAgent] = useState<string>("legal");
  const agent = AGENTS.find((a) => a.id === selectedAgent) || AGENTS[0];

  return (
    <section className="relative py-28 px-4 sm:px-6 lg:px-8 border-t border-white/[0.06] bg-transparent">
      <div className="max-w-6xl mx-auto">
        {/* Section Header */}
        <div className="max-w-3xl">
          <Reveal>
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-cyan-400">
              AI Employees
            </div>
            <h2 className="cinematic-title text-3xl sm:text-4xl md:text-5xl font-normal tracking-tight text-white text-balance leading-tight mt-4">
              Autonomous domain specialists, <br />
              <span className="font-light text-zinc-400">anchored in verifiable ground truth.</span>
            </h2>
            <p className="mt-5 text-base sm:text-lg text-zinc-400 font-light leading-relaxed">
              Generalist chatbots hallucinate when questioned on specialized domains.
              Brain-co deploys domain-dedicated agents with immutable memory, mathematical logic gates, and deterministic legal validation.
            </p>
          </Reveal>
        </div>

        {/* Agent Switcher Tabs */}
        <Reveal delay={0.1} className="mt-12 flex flex-wrap gap-2 pb-6 border-b border-white/[0.08]">
          {AGENTS.map((a) => {
            const isSelected = a.id === selectedAgent;
            return (
              <button
                key={a.id}
                type="button"
                onClick={() => setSelectedAgent(a.id)}
                className={cn(
                  "flex items-center gap-2.5 px-4 py-2.5 rounded-xl text-xs font-mono tracking-tight transition-all duration-200 cursor-pointer",
                  isSelected
                    ? "bg-white text-black font-semibold shadow-[0_4px_20px_rgba(255,255,255,0.15)]"
                    : "bg-white/[0.03] text-zinc-400 hover:text-white hover:bg-white/[0.06] border border-white/[0.06]"
                )}
              >
                <span
                  className={cn(
                    "w-2 h-2 rounded-full",
                    a.status === "active" ? "bg-cyan-400 animate-pulse" : "bg-zinc-500"
                  )}
                />
                <span>{a.name}</span>
                <span className="text-[10px] opacity-75">
                  ({a.status === "active" ? "V1 Ready" : "Roadmap"})
                </span>
              </button>
            );
          })}
        </Reveal>

        {/* Selected Agent Showcase */}
        <Reveal delay={0.15} className="mt-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 p-8 sm:p-10 rounded-2xl border border-white/[0.08] bg-black/40">
            {/* Left 7 Columns: Capabilities & Description */}
            <div className="lg:col-span-7 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-3">
                  <Badge variant={agent.status === "active" ? "cyan" : "violet"}>
                    {agent.statusText}
                  </Badge>
                  <span className="text-xs font-mono text-zinc-400">
                    Domain: {agent.domain}
                  </span>
                </div>

                <h3 className="mt-5 text-2xl sm:text-3xl font-medium tracking-tight text-white">
                  {agent.name}
                </h3>
                <p className="mt-2 text-sm font-mono text-cyan-400">
                  {agent.tagline}
                </p>

                <p className="mt-5 text-sm sm:text-base font-light text-zinc-300 leading-relaxed">
                  {agent.description}
                </p>

                <div className="mt-8">
                  <h4 className="text-xs font-mono uppercase tracking-widest text-zinc-400 mb-4">
                    Architectural Capabilities
                  </h4>
                  <ul className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {agent.capabilities.map((cap) => (
                      <li key={cap} className="flex items-start gap-2.5 text-xs text-zinc-300">
                        <span className="mt-1 h-1.5 w-1.5 rounded-full bg-cyan-400 flex-none" />
                        <span className="leading-normal">{cap}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="mt-8 pt-6 border-t border-white/[0.08] flex items-center gap-4">
                <Link
                  href={agent.status === "active" ? "/onboarding" : "/contact"}
                  className={cn(buttonClasses("pill-white", "sm"), "text-xs font-semibold px-5")}
                >
                  <span>{agent.status === "active" ? "Deploy This Agent" : "Join Waitlist"}</span>
                  <ArrowIcon />
                </Link>
                <Link
                  href="/modules"
                  className={cn(buttonClasses("pill-glass", "sm"), "text-xs px-5")}
                >
                  <span>View All Modules</span>
                </Link>
              </div>
            </div>

            {/* Right 5 Columns: Live Synthetic Execution Telemetry */}
            <div className="lg:col-span-5 flex flex-col justify-between p-6 rounded-xl border border-white/[0.08] bg-black/80">
              <div>
                <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
                  <span className="text-[11px] font-mono uppercase text-zinc-400 tracking-wider">
                    Execution Telemetry
                  </span>
                  <span className="text-[11px] font-mono text-emerald-400">
                    Live Sample
                  </span>
                </div>

                <div className="mt-4">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">
                    Corpus Input
                  </span>
                  <div className="mt-1.5 p-3 rounded-lg bg-white/[0.03] border border-white/[0.06] font-mono text-xs text-zinc-300 leading-relaxed">
                    {agent.executionSample.input}
                  </div>
                </div>

                <div className="mt-4">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400">
                    Audited Output
                  </span>
                  <div className="mt-1.5 p-3 rounded-lg bg-cyan-950/20 border border-cyan-500/30 font-mono text-xs text-cyan-100 leading-relaxed">
                    {agent.executionSample.output}
                  </div>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-white/[0.08] flex items-center justify-between text-[11px] font-mono text-zinc-400">
                <span>{agent.executionSample.latency}</span>
                <span className="truncate max-w-[160px] text-zinc-400">
                  {agent.executionSample.verificationHash}
                </span>
              </div>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
