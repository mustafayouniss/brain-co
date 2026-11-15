"use client";

import * as React from "react";
import {
  Brain,
  Play,
  RefreshCw,
  ListTree,
  Network,
  GitBranch,
  FileCode,
  CheckCircle,
  AlertTriangle,
  Loader2,
  Send,
  FileText,
  Upload,
  Database,
  Building,
  Briefcase,
  BookOpen,
  Copy,
  Check,
} from "lucide-react";

import { LiveTraceTab } from "./live-trace-tab";
import { DelegationGraphTab } from "./delegation-graph-tab";
import { PlanVersionsTab } from "./plan-versions-tab";
import { EventDetailsTab } from "./event-details-tab";
import { TestSummaryTab } from "./test-summary-tab";
import { ExtractedKnowledgeTab } from "./extracted-knowledge-tab";
import {
  TestRunEvent,
  TestRunSummary,
  DelegationEdge,
  PlanModel,
  ReplanDetails,
  SavedKnowledgeRecord,
} from "./types";

type TabType = "trace" | "graph" | "plans" | "knowledge" | "details" | "summary";

export interface MeshTestConsoleProps {
  organizationId: string;
  caseId: string;
  caseNumber?: string;
  caseTitle?: string;
  className?: string;
}

function createSampleContractPdfBlob(): Blob {
  const content = `%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 5 0 R /Resources << /Font << /F1 7 0 R >> >> >>
endobj
4 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 6 0 R /Resources << /Font << /F1 7 0 R >> >> >>
endobj
5 0 obj
<< /Length 260 >>
stream
BT
/F1 14 Tf
72 720 Td
(COMMERCIAL CONSULTING AGREEMENT) Tj
0 -30 Td
(Dated: 2026-10-15) Tj
0 -30 Td
(Party A: Apex Global Holdings LLC) Tj
0 -30 Td
(Party B: Cairo Legal Consultants SAE) Tj
0 -30 Td
(Article 147: The contract makes the law of the parties.) Tj
ET
endstream
endobj
6 0 obj
<< /Length 280 >>
stream
BT
/F1 14 Tf
72 720 Td
(FINANCIAL TERMS AND CONFIDENTIALITY) Tj
0 -30 Td
(Retainer Fee: USD 50,000 payable upon signing.) Tj
0 -30 Td
(Payment Date: Due on 2026-11-01.) Tj
0 -30 Td
(Governing Law: Egyptian Civil Code Article 147 and related statutes.) Tj
ET
endstream
endobj
7 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 8
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000121 00000 n 
0000000234 00000 n 
0000000347 00000 n 
0000000659 00000 n 
0000000991 00000 n 
trailer
<< /Size 8 /Root 1 0 R >>
startxref
1062
%%EOF`;
  return new Blob([content], { type: "application/pdf" });
}

export function MeshTestConsole({
  organizationId,
  caseId,
  caseNumber,
  caseTitle,
  className = "",
}: MeshTestConsoleProps) {
  const [activeTab, setActiveTab] = React.useState<TabType>("trace");
  const [isRunning, setIsRunning] = React.useState(false);
  const [promptInput, setPromptInput] = React.useState("");
  const [events, setEvents] = React.useState<TestRunEvent[]>([]);
  const [selectedEvent, setSelectedEvent] = React.useState<TestRunEvent | null>(null);
  const [delegationEdges, setDelegationEdges] = React.useState<DelegationEdge[]>([]);
  const [invokedEngines, setInvokedEngines] = React.useState<string[]>([]);
  const [initialPlan, setInitialPlan] = React.useState<PlanModel | null>(null);
  const [replannedDetails, setReplannedDetails] = React.useState<ReplanDetails | null>(null);
  const [currentPlan, setCurrentPlan] = React.useState<PlanModel | null>(null);
  const [summary, setSummary] = React.useState<TestRunSummary | null>(null);
  const [statusMessage, setStatusMessage] = React.useState<string>("Ready");
  const [activeRunId, setActiveRunId] = React.useState<string | null>(null);
  const [copiedRunId, setCopiedRunId] = React.useState(false);

  // PDF Ingestion & Saved Knowledge State
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [savedRecords, setSavedRecords] = React.useState<SavedKnowledgeRecord[] | null>(null);
  const [isLoadingSaved, setIsLoadingSaved] = React.useState(false);

  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const fetchSavedRecords = React.useCallback(async () => {
    if (!organizationId?.trim() || !caseId?.trim()) return;
    setIsLoadingSaved(true);
    try {
      const res = await fetch(
        `/api/ring1/knowledge?organization_id=${encodeURIComponent(
          organizationId
        )}&case_id=${encodeURIComponent(caseId)}`
      );
      if (res.ok) {
        const data = await res.json();
        setSavedRecords(data.records || []);
      }
    } catch {
      // Ignored
    } finally {
      setIsLoadingSaved(false);
    }
  }, [organizationId, caseId]);

  React.useEffect(() => {
    fetchSavedRecords();
  }, [fetchSavedRecords]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        alert("Please upload a valid PDF document.");
        return;
      }
      setSelectedFile(file);
    }
  };

  const copyRunId = () => {
    if (!activeRunId) return;
    navigator.clipboard.writeText(activeRunId);
    setCopiedRunId(true);
    setTimeout(() => setCopiedRunId(false), 2000);
  };

  const runPdfPipeline = async (mode: "normal" | "failure_recovery") => {
    if (isRunning) return;

    setIsRunning(true);
    setStatusMessage(
      mode === "failure_recovery"
        ? "Injecting Context Boundary Failure & Testing Bounded Replan..."
        : "Executing Real PDF Ingestion & PostgreSQL Knowledge Mesh..."
    );
    setEvents([]);
    setSelectedEvent(null);
    setDelegationEdges([]);
    setInvokedEngines([]);
    setInitialPlan(null);
    setReplannedDetails(null);
    setCurrentPlan(null);
    setSummary(null);
    setActiveRunId(null);

    setActiveTab(mode === "failure_recovery" ? "plans" : "trace");

    try {
      const formData = new FormData();
      if (selectedFile) {
        formData.append("file", selectedFile);
      } else {
        const sampleBlob = createSampleContractPdfBlob();
        formData.append("file", sampleBlob, "commercial_consulting_agreement.pdf");
      }
      formData.append("organization_id", organizationId);
      formData.append("case_id", caseId);
      formData.append("mode", mode);
      formData.append("stream", "true");

      const response = await fetch("/api/ring1/upload-pdf", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || errJson.error?.message || `HTTP ${response.status}`);
      }

      if (!response.body) {
        throw new Error("No response body stream received");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data:")) continue;

          const jsonStr = trimmed.replace(/^data:\s*/, "");
          try {
            const evt: TestRunEvent = JSON.parse(jsonStr);

            if (evt.run_id && !activeRunId) {
              setActiveRunId(evt.run_id);
            }

            setEvents((prev) => [...prev, evt]);

            if (evt.destination_engine) {
              setInvokedEngines((prev) =>
                prev.includes(evt.destination_engine) ? prev : [...prev, evt.destination_engine]
              );
            }

            if (
              evt.source_engine &&
              evt.source_engine !== "client" &&
              evt.source_engine !== "operator" &&
              evt.source_engine !== "system"
            ) {
              setDelegationEdges((prev) => {
                const exists = prev.some(
                  (e) => e.source === evt.source_engine && e.target === evt.destination_engine
                );
                return exists
                  ? prev
                  : [...prev, { source: evt.source_engine, target: evt.destination_engine }];
              });
            }

            if (evt.event_type === "plan_created" && evt.response_envelope?.payload) {
              setInitialPlan(evt.response_envelope.payload as PlanModel);
            }

            if (evt.event_type === "replan_completed" && evt.details) {
              setReplannedDetails(evt.details as ReplanDetails);
            }

            if (evt.event_type === "plan_status_verified" && evt.details) {
              setCurrentPlan(evt.details as PlanModel);
            }

            if (evt.event_type === "run_completed" && evt.details) {
              const runSummary = evt.details as TestRunSummary;
              setSummary(runSummary);
              if (runSummary.run_id) {
                setActiveRunId(runSummary.run_id);
              }
              setStatusMessage(
                runSummary.scorecard?.processing_outcome === "RECOVERED"
                  ? "Completed (Recovered via Replan)"
                  : "Completed (Verified Knowledge Stored)"
              );
              void fetchSavedRecords();
              setActiveTab("knowledge");
            }
          } catch {
            // Ignore parse errors on keep-alives
          }
        }
      }
    } catch (err) {
      setStatusMessage(`Error: ${String(err)}`);
    } finally {
      setIsRunning(false);
    }
  };

  const runTestScenario = async (
    mode: "e2e" | "force_failure" | "custom_prompt",
    customPromptText?: string
  ) => {
    if (isRunning) return;

    setIsRunning(true);
    setStatusMessage(
      mode === "force_failure"
        ? "Simulating Failure & Testing Bounded Replan..."
        : mode === "custom_prompt"
        ? "Processing Custom Mesh Task..."
        : "Executing 6-Engine Mesh Integration..."
    );
    setEvents([]);
    setSelectedEvent(null);
    setDelegationEdges([]);
    setInvokedEngines([]);
    setInitialPlan(null);
    setReplannedDetails(null);
    setCurrentPlan(null);
    setSummary(null);
    setActiveRunId(null);

    setActiveTab(mode === "force_failure" ? "plans" : "trace");

    try {
      const response = await fetch("/api/ring1/test-run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode,
          custom_prompt: customPromptText,
          case_id: caseId,
          organization_id: organizationId,
          stream: true,
        }),
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || errJson.error?.message || `HTTP ${response.status}`);
      }

      if (!response.body) {
        throw new Error("No response body stream received");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data:")) continue;

          const jsonStr = trimmed.replace(/^data:\s*/, "");
          try {
            const evt: TestRunEvent = JSON.parse(jsonStr);

            if (evt.run_id && !activeRunId) {
              setActiveRunId(evt.run_id);
            }

            setEvents((prev) => [...prev, evt]);

            if (evt.destination_engine) {
              setInvokedEngines((prev) =>
                prev.includes(evt.destination_engine) ? prev : [...prev, evt.destination_engine]
              );
            }

            if (
              evt.source_engine &&
              evt.source_engine !== "client" &&
              evt.source_engine !== "operator" &&
              evt.source_engine !== "system"
            ) {
              setDelegationEdges((prev) => {
                const exists = prev.some(
                  (e) => e.source === evt.source_engine && e.target === evt.destination_engine
                );
                return exists
                  ? prev
                  : [...prev, { source: evt.source_engine, target: evt.destination_engine }];
              });
            }

            if (evt.event_type === "plan_created" && evt.response_envelope?.payload) {
              setInitialPlan(evt.response_envelope.payload as PlanModel);
            }

            if (evt.event_type === "replan_completed" && evt.details) {
              setReplannedDetails(evt.details as ReplanDetails);
            }

            if (evt.event_type === "plan_status_verified" && evt.details) {
              setCurrentPlan(evt.details as PlanModel);
            }

            if (evt.event_type === "run_completed" && evt.details) {
              const runSummary = evt.details as TestRunSummary;
              setSummary(runSummary);
              if (runSummary.run_id) {
                setActiveRunId(runSummary.run_id);
              }
              setStatusMessage("Completed");
            }
          } catch {
            // Ignore parse errors on keep-alives
          }
        }
      }
    } catch (err) {
      setStatusMessage(`Error: ${String(err)}`);
    } finally {
      setIsRunning(false);
    }
  };

  const handleCustomPromptSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!promptInput.trim()) return;
    const text = promptInput.trim();
    setPromptInput("");
    void runTestScenario("custom_prompt", text);
  };

  return (
    <div
      className={`flex flex-col rounded-2xl border border-[#202a3e] bg-[#070d1d]/95 backdrop-blur-xl shadow-2xl overflow-hidden min-h-[680px] ${className}`}
    >
      {/* Console Top Header */}
      <header className="flex flex-col border-b border-[#202a3e] bg-[#0c1529]/90 px-4 py-3 shrink-0 gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-[#946eff] to-[#8052ff] text-white shadow-lg shadow-[#946eff]/20">
              <Brain className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-white tracking-tight">
                  Mesh Test Console
                </h2>
                <span className="font-mono text-[10px] px-2 py-0.5 rounded-full bg-[#946eff]/20 text-[#cbb5ff] border border-[#946eff]/40">
                  Case Execution Pipeline
                </span>
              </div>
              <p className="text-[11px] text-[#8a94a8]">
                Real Multi-Agent Cognitive Mesh &bull; Plan Execution &bull; CACS Context Bound
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Run ID Pill */}
            {activeRunId && (
              <button
                type="button"
                onClick={copyRunId}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono bg-[#162036] hover:bg-[#1e2c4a] text-[#cbb5ff] border border-[#344465] transition-colors"
                title="Click to copy Run ID"
              >
                <span>Run: {activeRunId}</span>
                {copiedRunId ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 opacity-60" />}
              </button>
            )}

            {/* Status Pill */}
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono border border-[#202a3e] bg-[#0c1529]">
              {isRunning ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 text-[#946eff] animate-spin" />
                  <span className="text-[#cbb5ff] font-semibold">Running</span>
                </>
              ) : summary?.status === "completed" ? (
                <>
                  <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-emerald-300 font-semibold">Verified</span>
                </>
              ) : (
                <>
                  <span className="w-2 h-2 rounded-full bg-[#34405a]" />
                  <span className="text-[#8a94a8]">Idle</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Bound Scope & Actions Control Bar */}
        <div className="p-2.5 rounded-xl bg-[#091024]/80 border border-[#202a3e] flex flex-col gap-2.5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            {/* Authenticated Tenant and Case Context (Read-Only) */}
            <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
              <span className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[#111c33] border border-[#202a3e] text-[#8a94a8]">
                <Building className="w-3.5 h-3.5 text-[#946eff]" />
                <span className="text-[#cbd5e1] font-medium">{organizationId}</span>
              </span>
              <span className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[#111c33] border border-[#202a3e] text-[#8a94a8]">
                <Briefcase className="w-3.5 h-3.5 text-[#8adabc]" />
                <span className="text-[#cbd5e1] font-medium">{caseNumber || caseId}</span>
              </span>
              {caseTitle && (
                <span className="text-[#8a94a8] text-[11px] truncate max-w-[200px] sm:max-w-xs font-sans">
                  {caseTitle}
                </span>
              )}
            </div>

            {/* PDF File Picker */}
            <div className="flex items-center gap-2">
              <input
                ref={fileInputRef}
                type="file"
                accept="application/pdf"
                onChange={handleFileChange}
                className="hidden"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={isRunning}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-[#162036] hover:bg-[#1e2c4a] text-white border border-[#344465] transition-all disabled:opacity-50"
              >
                <Upload className="w-3 h-3 text-[#946eff]" />
                <span>{selectedFile ? "Change PDF" : "Choose PDF"}</span>
              </button>
              <div className="text-xs text-[#8a94a8] truncate max-w-[180px]">
                {selectedFile ? (
                  <span className="text-[#cbd5e1] font-medium">{selectedFile.name}</span>
                ) : (
                  <span className="italic text-[11px]">Using sample contract</span>
                )}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-[#1c273e]">
            <button
              type="button"
              onClick={() => runPdfPipeline("normal")}
              disabled={isRunning}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-950/40 transition-all disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Run Real PDF Pipeline</span>
            </button>

            <button
              type="button"
              onClick={() => runPdfPipeline("failure_recovery")}
              disabled={isRunning}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#162036] hover:bg-[#1e2c4a] text-amber-300 border border-amber-500/40 transition-all disabled:opacity-50"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Test Failure &amp; Bounded Recovery</span>
            </button>

            <button
              type="button"
              onClick={() => runTestScenario("e2e")}
              disabled={isRunning}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[#162036] hover:bg-[#1e2c4a] text-white border border-[#344465] transition-all disabled:opacity-50"
            >
              <span>Execute 6-Engine Mesh (E2E)</span>
            </button>

            {events.length > 0 && (
              <span className="ml-auto text-[11px] font-mono text-[#8a94a8]">
                {events.length} events | {invokedEngines.length} engines active
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Quick Custom Task Prompt Input */}
      <form
        onSubmit={handleCustomPromptSubmit}
        className="flex items-center gap-2 px-4 py-2 border-b border-[#202a3e] bg-[#0c1529]/60 shrink-0"
      >
        <input
          type="text"
          placeholder="Enter legal task or prompt (e.g. 'Investigate NDA breach and verify trade secret disclosure', 'Extract governing law and obligations')..."
          value={promptInput}
          onChange={(e) => setPromptInput(e.target.value)}
          disabled={isRunning}
          className="flex-1 text-xs py-1.5 px-3 rounded-lg border border-[#2a3854] bg-[#070d1d] text-white placeholder-[#62718e] focus:border-[#946eff] focus:outline-none"
        />
        <button
          type="submit"
          disabled={isRunning || !promptInput.trim()}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#946eff] hover:bg-[#8052ff] text-white disabled:opacity-40 transition-all shadow-md shadow-[#946eff]/20"
        >
          <Send className="w-3.5 h-3.5" />
          <span>Run Custom Mesh Task</span>
        </button>
      </form>

      {/* Sub-Tab Navigation Bar */}
      <nav className="flex items-center gap-1 px-4 py-2 border-b border-[#202a3e] bg-[#080f21] shrink-0 overflow-x-auto text-xs">
        <button
          type="button"
          onClick={() => setActiveTab("trace")}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition-all ${
            activeTab === "trace"
              ? "bg-[#946eff] text-white shadow-sm font-semibold"
              : "text-[#8a94a8] hover:text-white hover:bg-[#162036]"
          }`}
        >
          <ListTree className="w-3.5 h-3.5" />
          <span>Live Trace</span>
          {events.length > 0 && (
            <span className="font-mono text-[10px] px-1.5 py-0.2 rounded-full bg-black/30">
              {events.length}
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("graph")}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition-all ${
            activeTab === "graph"
              ? "bg-[#946eff] text-white shadow-sm font-semibold"
              : "text-[#8a94a8] hover:text-white hover:bg-[#162036]"
          }`}
        >
          <Network className="w-3.5 h-3.5" />
          <span>Delegation Graph</span>
          {delegationEdges.length > 0 && (
            <span className="font-mono text-[10px] px-1.5 py-0.2 rounded-full bg-black/30">
              {delegationEdges.length}
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("plans")}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition-all ${
            activeTab === "plans"
              ? "bg-[#946eff] text-white shadow-sm font-semibold"
              : "text-[#8a94a8] hover:text-white hover:bg-[#162036]"
          }`}
        >
          <GitBranch className="w-3.5 h-3.5" />
          <span>Plan Versions</span>
          {initialPlan && (
            <span className="font-mono text-[10px] px-1.5 py-0.2 rounded-full bg-black/30">
              v{currentPlan ? currentPlan.version : initialPlan.version}
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("knowledge")}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition-all ${
            activeTab === "knowledge"
              ? "bg-[#946eff] text-white shadow-sm font-semibold"
              : "text-[#8a94a8] hover:text-white hover:bg-[#162036]"
          }`}
        >
          <BookOpen className="w-3.5 h-3.5" />
          <span>Extracted Knowledge</span>
          {summary?.structured_knowledge && (
            <span className="font-mono text-[10px] px-1.5 py-0.2 rounded-full bg-black/30">
              {summary.structured_knowledge.facts.length}
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("details")}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition-all ${
            activeTab === "details"
              ? "bg-[#946eff] text-white shadow-sm font-semibold"
              : "text-[#8a94a8] hover:text-white hover:bg-[#162036]"
          }`}
        >
          <FileCode className="w-3.5 h-3.5" />
          <span>Event Details</span>
          {selectedEvent && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />}
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("summary")}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition-all ${
            activeTab === "summary"
              ? "bg-[#946eff] text-white shadow-sm font-semibold"
              : "text-[#8a94a8] hover:text-white hover:bg-[#162036]"
          }`}
        >
          <CheckCircle className="w-3.5 h-3.5" />
          <span>Test Summary</span>
        </button>
      </nav>

      {/* Main Tab Viewport */}
      <main className="flex-1 p-4 overflow-auto bg-[#050b1a]/60">
        {activeTab === "trace" && (
          <LiveTraceTab
            events={events}
            selectedEvent={selectedEvent}
            onSelectEvent={(evt) => {
              setSelectedEvent(evt);
              setActiveTab("details");
            }}
          />
        )}

        {activeTab === "graph" && (
          <DelegationGraphTab
            events={events}
            delegationEdges={delegationEdges}
            invokedEngines={invokedEngines}
          />
        )}

        {activeTab === "plans" && (
          <PlanVersionsTab
            initialPlan={initialPlan}
            replannedDetails={replannedDetails}
            currentPlan={currentPlan}
            events={events}
          />
        )}

        {activeTab === "knowledge" && (
          <ExtractedKnowledgeTab
            knowledge={summary?.structured_knowledge}
            pages={summary?.pages}
            scorecard={summary?.scorecard}
            savedRecords={savedRecords}
            onRefreshSavedRecords={() => void fetchSavedRecords()}
            isLoadingSaved={isLoadingSaved}
          />
        )}

        {activeTab === "details" && <EventDetailsTab event={selectedEvent} />}

        {activeTab === "summary" && <TestSummaryTab summary={summary} events={events} />}
      </main>

      {/* Operational Footer */}
      <footer className="flex flex-wrap items-center justify-between px-4 py-2.5 border-t border-[#202a3e] bg-[#0c1529]/90 text-[11px] text-[#8a94a8] shrink-0 font-mono">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400" />
          <span className="text-[#cbd5e1]">PostgreSQL Persistent</span>
          <span className="text-[#34405a]">|</span>
          <span>Scope: {caseNumber || caseId}</span>
          <span className="text-[#34405a]">|</span>
          <span>Mesh Events: {events.length}</span>
        </div>
        <div>
          <span>{statusMessage}</span>
        </div>
      </footer>
    </div>
  );
}
