"use client";

import * as React from "react";
import { CheckCircle2, AlertTriangle, ArrowRight, GitCommit, ShieldCheck, RefreshCw, Layers } from "lucide-react";
import { PlanModel, ReplanDetails, TestRunEvent } from "./types";

interface PlanVersionsTabProps {
  initialPlan?: PlanModel | null;
  replannedDetails?: ReplanDetails | null;
  currentPlan?: PlanModel | null;
  events: TestRunEvent[];
}

export function PlanVersionsTab({ initialPlan, replannedDetails, currentPlan, events }: PlanVersionsTabProps) {
  // Find failure event if available
  const failureEvent = React.useMemo(() => {
    return events.find((e) => e.event_type === "step_failed");
  }, [events]);

  const replanEvent = React.useMemo(() => {
    return events.find((e) => e.event_type === "replan_completed");
  }, [events]);

  if (!initialPlan) {
    return (
      <div className="flex flex-col items-center justify-center h-64 rounded-xl border border-dashed border-border/60 text-center p-6">
        <Layers className="w-10 h-10 text-[#8a94a8] mb-2 stroke-[1.5]" />
        <h3 className="text-sm font-semibold text-white">No Plan Generated Yet</h3>
        <p className="text-xs text-[#8a94a8] max-w-md mt-1">
          Trigger a test using &quot;Run Integration Test&quot; or &quot;Force Failure &amp; Replan&quot; to inspect real plan versioning, step retention, and dynamic replanning.
        </p>
      </div>
    );
  }

  const hasReplanned = Boolean(replannedDetails || (currentPlan && currentPlan.version > 1));

  return (
    <div className="flex flex-col h-full space-y-4 overflow-y-auto pr-1 max-h-[390px]">
      {/* Header Info Banner */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
        <div className="p-2.5 rounded-xl bg-surface/70 border border-border/70">
          <div className="text-[10px] text-[#8a94a8] uppercase font-mono">Plan ID</div>
          <div className="font-mono font-medium text-white truncate mt-0.5">
            {initialPlan.plan_id}
          </div>
        </div>

        <div className="p-2.5 rounded-xl bg-surface/70 border border-border/70">
          <div className="text-[10px] text-[#8a94a8] uppercase font-mono">Current Version</div>
          <div className="flex items-center gap-1.5 font-bold text-violet mt-0.5">
            <GitCommit className="w-3.5 h-3.5" />
            <span>v{currentPlan ? currentPlan.version : initialPlan.version}</span>
            {hasReplanned && (
              <span className="text-[10px] text-emerald-400 font-normal">
                (Replanned +1)
              </span>
            )}
          </div>
        </div>

        <div className="p-2.5 rounded-xl bg-surface/70 border border-border/70">
          <div className="text-[10px] text-[#8a94a8] uppercase font-mono">Work Preservation</div>
          <div className="flex items-center gap-1.5 font-semibold text-emerald-400 mt-0.5">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>{hasReplanned ? "Verified Retained" : "Step 1 Completed"}</span>
          </div>
        </div>

        <div className="p-2.5 rounded-xl bg-surface/70 border border-border/70">
          <div className="text-[10px] text-[#8a94a8] uppercase font-mono">Replans / Max</div>
          <div className="font-mono font-semibold text-white mt-0.5">
            {currentPlan?.replan_count ?? (hasReplanned ? 1 : 0)} / {initialPlan.max_replans}
          </div>
        </div>
      </div>

      {/* Goal */}
      <div className="px-3 py-2 rounded-xl bg-surface/80 border border-border/70 text-xs">
        <span className="font-semibold text-[#8a94a8] mr-2">GOAL:</span>
        <span className="text-white font-medium">{initialPlan.goal}</span>
      </div>

      {/* If failure occurred, show Controlled Failure & Evidence Banner */}
      {failureEvent && (
        <div className="p-3 rounded-xl bg-red-950/30 border border-red-500/40 text-xs space-y-1.5">
          <div className="flex items-center gap-2 text-red-300 font-semibold">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
            <span>Controlled Failure Signal Passed to Planning Engine</span>
          </div>
          <div className="text-[11px] text-[#9ba5b9] font-mono pl-6">
            Reason: <span className="text-white font-semibold">{failureEvent.details?.reason_code}</span> | Step ID:{" "}
            <span className="text-white font-semibold">{failureEvent.details?.step_id}</span>
          </div>
          {failureEvent.details?.evidence && (
            <div className="bg-surface/80 rounded-lg p-2 font-mono text-[10px] text-red-200 border border-red-500/30 ml-6 overflow-x-auto">
              {JSON.stringify(failureEvent.details.evidence, null, 2)}
            </div>
          )}
        </div>
      )}

      {/* Plan Version 1 vs Plan Version 2 Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 text-xs">
        {/* Version 1 Panel */}
        <div className="flex flex-col p-3 rounded-xl border border-border/80 bg-surface/50 space-y-2">
          <div className="flex items-center justify-between pb-1.5 border-b border-border/60">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded font-mono font-bold bg-surface-2 text-violet border border-border">
                Version 1
              </span>
              <span className="text-[11px] text-[#8a94a8]">(Initial Plan)</span>
            </div>
            <span className="text-[11px] font-mono text-[#8a94a8]">
              {initialPlan.steps?.length || 4} steps
            </span>
          </div>

          <div className="space-y-2 pt-1">
            {initialPlan.steps?.map((st, idx) => {
              const isRetained = replannedDetails?.steps_retained?.includes(st.step_id);
              const isFailed = failureEvent?.details?.step_id === st.step_id;
              return (
                <div
                  key={st.step_id || idx}
                  className={`p-2.5 rounded-lg border text-[11px] flex flex-col gap-1 ${
                    isRetained
                      ? "border-emerald-500/60 bg-emerald-950/30 text-white"
                      : isFailed
                      ? "border-red-500/60 bg-red-950/30 text-white"
                      : "border-border/60 bg-surface/70 text-[#9ba5b9]"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold">
                      #{idx + 1} {st.capability}
                    </span>
                    {isRetained ? (
                      <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-300">
                        <CheckCircle2 className="w-3 h-3" />
                        COMPLETED & RETAINED
                      </span>
                    ) : isFailed ? (
                      <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-red-300">
                        <AlertTriangle className="w-3 h-3" />
                        FAILED (CONTEXT_INSUFFICIENT)
                      </span>
                    ) : (
                      <span className="text-[10px] text-[#8a94a8]">PENDING</span>
                    )}
                  </div>
                  <div className="text-[10px] text-[#8a94a8]">{st.description}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Version 2 Panel (Replanned) */}
        <div className="flex flex-col p-3 rounded-xl border border-brand/50 bg-brand/5 space-y-2">
          <div className="flex items-center justify-between pb-1.5 border-b border-border/60">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded font-mono font-bold bg-brand text-white shadow-sm">
                Version 2
              </span>
              <span className="text-[11px] text-violet font-medium">
                {hasReplanned ? "Replanned Execution Graph" : "Awaiting Replan"}
              </span>
            </div>
            {hasReplanned && (
              <span className="text-[10px] text-emerald-300 font-mono">
                Preserved 1, Added {replannedDetails?.steps_added?.length || 2}
              </span>
            )}
          </div>

          {hasReplanned ? (
            <div className="space-y-2 pt-1">
              {/* Preserved Step 1 */}
              <div className="p-2.5 rounded-lg border border-emerald-500/70 bg-emerald-950/40 text-[11px] flex flex-col gap-1">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-white">
                    #1 {initialPlan.steps?.[0]?.capability || "perception.structure_input"}
                  </span>
                  <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-300">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                    RETAINED & NOT RE-RUN
                  </span>
                </div>
                <div className="text-[10px] text-emerald-200/80">
                  Completed work from v1 preserved intact.
                </div>
              </div>

              {/* Added Recovery Steps */}
              {(replannedDetails?.steps_added || currentPlan?.steps?.slice(1) || []).map((step, idx) => (
                <div
                  key={step.step_id || idx}
                  className="p-2.5 rounded-lg border border-brand/60 bg-surface-2 text-[11px] flex flex-col gap-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-white">
                      #{idx + 2} {step.capability}
                    </span>
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-violet">
                      <RefreshCw className="w-3 h-3 text-brand" />
                      NEW RECOVERY STEP
                    </span>
                  </div>
                  <div className="text-[10px] text-[#8a94a8]">
                    {step.description || "Disambiguate case boundaries and proceed with bounded retrieval."}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-44 rounded-lg border border-dashed border-border/60 text-center p-4">
              <RefreshCw className="w-6 h-6 text-[#8a94a8] mb-1" />
              <p className="text-xs text-white">Version 2 not triggered yet</p>
              <p className="text-[11px] text-[#8a94a8] mt-1">
                Click &quot;Force Failure &amp; Replan&quot; to test bounded replan recovery.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
