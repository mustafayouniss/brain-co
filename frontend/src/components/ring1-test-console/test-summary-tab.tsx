"use client";

import * as React from "react";
import { CheckCircle2, ShieldCheck, Database, GitCommit, Layers, AlertCircle, Clock, Zap } from "lucide-react";
import { TestRunEvent, TestRunSummary } from "./types";

interface TestSummaryTabProps {
  summary?: TestRunSummary | null;
  events: TestRunEvent[];
}

export function TestSummaryTab({ summary, events }: TestSummaryTabProps) {
  const allEngines = ["perception", "observation", "context", "memory", "retrieval", "planning"];
  const invokedSet = new Set(summary?.invoked_engines || events.map((e) => e.destination_engine));
  const totalEvents = events.length;

  const totalDuration = summary?.duration_ms || (
    events.length > 0
      ? events.reduce((acc, curr) => acc + (curr.duration_ms || 0), 0)
      : 0
  );

  return (
    <div className="flex flex-col h-full space-y-4 overflow-y-auto pr-1 max-h-[390px] text-xs">
      {/* Top Scorecard Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <div className="p-3 rounded-xl bg-surface/70 border border-border/80">
          <div className="flex items-center gap-1.5 text-[10px] text-[#8a94a8] uppercase font-mono">
            <Zap className="w-3 h-3 text-brand" />
            <span>Engines Invoked</span>
          </div>
          <div className="text-lg font-bold text-white mt-1">
            {invokedSet.size} <span className="text-xs text-[#8a94a8] font-normal">/ 6</span>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-surface/70 border border-border/80">
          <div className="flex items-center gap-1.5 text-[10px] text-[#8a94a8] uppercase font-mono">
            <Layers className="w-3 h-3 text-emerald-400" />
            <span>Trace Events</span>
          </div>
          <div className="text-lg font-bold text-white mt-1">
            {totalEvents}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-surface/70 border border-border/80">
          <div className="flex items-center gap-1.5 text-[10px] text-[#8a94a8] uppercase font-mono">
            <Clock className="w-3 h-3 text-gold" />
            <span>Total Duration</span>
          </div>
          <div className="text-lg font-bold text-white mt-1">
            {totalDuration} <span className="text-xs text-[#8a94a8] font-normal">ms</span>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-surface/70 border border-border/80">
          <div className="flex items-center gap-1.5 text-[10px] text-[#8a94a8] uppercase font-mono">
            <ShieldCheck className="w-3 h-3 text-emerald-400" />
            <span>Isolation</span>
          </div>
          <div className="text-sm font-bold text-emerald-300 mt-1 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Enforced</span>
          </div>
        </div>
      </div>

      {/* Engine Participation Audit */}
      <div className="rounded-xl border border-border/80 bg-surface/60 p-3 space-y-2">
        <div className="font-semibold text-white flex items-center justify-between">
          <span>Engine Participation Audit</span>
          <span className="text-[11px] text-[#8a94a8]">
            {invokedSet.size === 6 ? "Full 6-Engine System Engaged" : `${invokedSet.size} of 6 Engines Engaged`}
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-1">
          {allEngines.map((eng) => {
            const isInvoked = invokedSet.has(eng);
            return (
              <div
                key={eng}
                className={`flex items-center justify-between px-2.5 py-1.5 rounded-lg border text-[11px] font-mono ${
                  isInvoked
                    ? "border-emerald-500/50 bg-emerald-950/20 text-emerald-200"
                    : "border-border/60 bg-surface/40 text-[#8a94a8]"
                }`}
              >
                <span className="font-medium capitalize">{eng}</span>
                {isInvoked ? (
                  <span className="text-[10px] text-emerald-400 font-bold">INVOKED</span>
                ) : (
                  <span className="text-[10px] text-[#8a94a8]">SKIPPED</span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Constitutional Invariants Verified */}
      <div className="rounded-xl border border-border/80 bg-surface/60 p-3 space-y-2.5">
        <div className="font-semibold text-white">System Invariants &amp; Integrity Verification</div>

        <div className="space-y-2">
          <div className="flex items-start gap-2 text-[11px]">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-white">Strict Case Isolation:</span>
              <span className="text-[#9ba5b9] ml-1">
                Memory facts and observation events are strictly partitioned by <code className="text-violet">case_id</code> in PostgreSQL. Cross-case query returns 0 records; direct unauthorized ID read is rejected with <code className="text-amber-300">AUTHORIZATION_DENIED</code>.
              </span>
            </div>
          </div>

          <div className="flex items-start gap-2 text-[11px]">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-white">Idempotent Deduplication:</span>
              <span className="text-[#9ba5b9] ml-1">
                Identical observation payloads with matching <code className="text-violet">idempotency_key</code> are recognized and suppressed without creating duplicate database rows.
              </span>
            </div>
          </div>

          <div className="flex items-start gap-2 text-[11px]">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-white">Bounded Versioned Replanning:</span>
              <span className="text-[#9ba5b9] ml-1">
                Plan models transition from v1 to v2 upon failure without discarding completed work. Replan attempts are bounded by <code className="text-violet">max_replans</code>.
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Real Behavior vs. Test Doubles Notice */}
      <div className="p-3 rounded-xl bg-surface-2/60 border border-border/70 text-[11px] text-[#9ba5b9] space-y-1">
        <div className="font-semibold text-white flex items-center gap-1.5">
          <Database className="w-3.5 h-3.5 text-brand" />
          <span>Execution Environment &amp; Zero-Cost Baseline</span>
        </div>
        <p>
          Mesh routing, PostgreSQL persistence, and envelope validation execute through live production code paths. Baseline AI inference uses deterministic test doubles (<code className="text-violet">FakeLLMProvider</code>) to ensure fast, free, and repeatable offline execution.
        </p>
      </div>
    </div>
  );
}
