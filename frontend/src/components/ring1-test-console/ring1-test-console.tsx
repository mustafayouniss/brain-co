"use client";

import * as React from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  Brain,
  Play,
  RefreshCw,
  X,
  ListTree,
  Network,
  GitBranch,
  FileCode,
  CheckCircle,
  AlertTriangle,
  Loader2,
  Send,
  Sparkles,
  FileUp,
  BookOpen,
  FileText,
  Upload,
  Database,
  Building,
  Briefcase,
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

export function Ring1TestConsole() {
  const [isOpen, setIsOpen] = React.useState(false);
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
  const [statusMessage, setStatusMessage] = React.useState<string>("Idle");

  // PDF Ingestion & Context State
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [organizationId, setOrganizationId] = React.useState("org-default");
  const [caseId, setCaseId] = React.useState("case-legal-101");
  const [savedRecords, setSavedRecords] = React.useState<SavedKnowledgeRecord[] | null>(null);
  const [isLoadingSaved, setIsLoadingSaved] = React.useState(false);

  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const shouldReduceMotion = useReducedMotion();

  const fetchSavedRecords = React.useCallback(async (org = organizationId, cId = caseId) => {
    if (!org.trim() || !cId.trim()) return;
    setIsLoadingSaved(true);
    try {
      const res = await fetch(`/api/ring1/knowledge?organization_id=${encodeURIComponent(org)}&case_id=${encodeURIComponent(cId)}`);
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

  const runPdfPipeline = async (mode: "normal" | "failure_recovery") => {
    if (isRunning) return;

    setIsRunning(true);
    setStatusMessage(
      mode === "failure_recovery"
        ? "Injecting Context Failure & Demonstrating Bounded Recovery..."
        : "Executing Real PDF Ingestion & Persistent Knowledge Mesh..."
    );
    setEvents([]);
    setSelectedEvent(null);
    setDelegationEdges([]);
    setInvokedEngines([]);
    setInitialPlan(null);
    setReplannedDetails(null);
    setCurrentPlan(null);
    setSummary(null);

    // Switch to trace tab on start
    setActiveTab(mode === "failure_recovery" ? "plans" : "trace");

    try {
      const formData = new FormData();
      if (selectedFile) {
        formData.append("file", selectedFile);
      } else {
        const sampleBlob = createSampleContractPdfBlob();
        formData.append("file", sampleBlob, "commercial_consulting_agreement.pdf");
      }
      formData.append("organization_id", organizationId.trim() || "org-default");
      formData.append("case_id", caseId.trim() || "case-legal-101");
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
              setStatusMessage(
                runSummary.scorecard?.processing_outcome === "RECOVERED"
                  ? "Completed (Recovered via Replan)"
                  : "Completed (Verified Knowledge Stored)"
              );
              // Refresh persisted records from PostgreSQL
              void fetchSavedRecords(organizationId, caseId);
              // Switch to knowledge inspector tab
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

  const runTestScenario = async (mode: "e2e" | "force_failure" | "custom_prompt", customPromptText?: string) => {
    if (isRunning) return;

    setIsRunning(true);
    setStatusMessage(
      mode === "force_failure"
        ? "Simulating Failure & Bounded Replan..."
        : mode === "custom_prompt"
        ? "Processing Custom Scenario..."
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

    setActiveTab(mode === "force_failure" ? "plans" : "trace");

    try {
      const response = await fetch("/api/ring1/test-run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode,
          custom_prompt: customPromptText,
          stream: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
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
              setSummary(evt.details as TestRunSummary);
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
    <aside
      aria-label="Ring 1 Live Integration Test Console"
      className="fixed bottom-4 left-4 sm:bottom-6 sm:left-6 z-50 flex flex-col items-start pointer-events-auto"
    >
      {/* Expanded Live Test Console Modal */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            key="ring1-console-window"
            initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.95, y: 16 }}
            animate={shouldReduceMotion ? { opacity: 1 } : { opacity: 1, scale: 1, y: 0 }}
            exit={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.95, y: 16 }}
            transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
            className="mb-3 flex flex-col overflow-hidden w-[calc(100vw-2rem)] sm:w-[720px] lg:w-[820px] h-[680px] max-h-[calc(100vh-5rem)] rounded-2xl border border-border-strong/80 bg-[#070d1d]/95 backdrop-blur-xl shadow-2xl shadow-black/80"
            role="dialog"
            aria-modal="false"
            aria-labelledby="ring1-console-title"
          >
            {/* Header with Title, Actions & Controls */}
            <header className="flex flex-col border-b border-border-strong/70 bg-surface/90 px-4 py-3 shrink-0 gap-2.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-brand to-violet text-white shadow-md">
                    <Brain className="h-4 w-4" />
                  </div>
                  <div>
                    <h2 id="ring1-console-title" className="text-sm font-bold text-white flex items-center gap-2">
                      Ring 1 Mesh Live Test Console
                      <span className="font-mono text-[10px] px-2 py-0.2 rounded-full bg-brand/20 text-violet border border-brand/40">
                        PDF Pipeline Active
                      </span>
                    </h2>
                    <p className="text-[11px] text-[#8a94a8]">
                      Real PDF Ingestion &bull; Knowledge Extraction &bull; PostgreSQL Memory Persistence
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono border border-border/80 bg-surface-2/80">
                    {isRunning ? (
                      <>
                        <Loader2 className="w-3 h-3 text-violet animate-spin" />
                        <span className="text-violet font-semibold">Processing</span>
                      </>
                    ) : summary?.status === "completed" ? (
                      <>
                        <CheckCircle className="w-3 h-3 text-emerald-400" />
                        <span className="text-emerald-300 font-semibold">Verified</span>
                      </>
                    ) : (
                      <>
                        <span className="w-2 h-2 rounded-full bg-border" />
                        <span className="text-[#8a94a8]">Idle</span>
                      </>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={() => setIsOpen(false)}
                    className="flex h-7 w-7 items-center justify-center rounded-lg text-[#8a94a8] transition-colors hover:bg-surface-2 hover:text-white"
                    aria-label="Close test console"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {/* REAL PDF INGESTION TOOLBAR */}
              <div className="p-2 rounded-xl bg-surface-2/40 border border-border/60 flex flex-col gap-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  {/* File Upload Selector */}
                  <div className="flex items-center gap-2 min-w-0">
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
                      className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-2 hover:bg-surface text-white border border-border/80 transition-all disabled:opacity-50"
                    >
                      <Upload className="w-3 h-3 text-brand" />
                      <span>{selectedFile ? "Change PDF" : "Choose PDF"}</span>
                    </button>

                    <div className="text-xs text-[#cbd5e1] truncate max-w-[220px]">
                      {selectedFile ? (
                        <span className="font-semibold text-white flex items-center gap-1">
                          <FileText className="w-3 h-3 text-brand inline" />
                          {selectedFile.name} ({(selectedFile.size / 1024).toFixed(0)} KB)
                        </span>
                      ) : (
                        <span className="text-[#8a94a8] italic text-[11px]">
                          Sample: Egyptian Commercial Agreement
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Context Scope Inputs */}
                  <div className="flex items-center gap-1.5 text-xs font-mono">
                    <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-surface border border-border/60 text-[#8a94a8]">
                      <Building className="w-3 h-3 text-violet" />
                      <input
                        type="text"
                        value={organizationId}
                        onChange={(e) => setOrganizationId(e.target.value)}
                        placeholder="Org ID"
                        className="bg-transparent text-white w-20 focus:outline-none text-[11px]"
                      />
                    </div>
                    <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-surface border border-border/60 text-[#8a94a8]">
                      <Briefcase className="w-3 h-3 text-brand" />
                      <input
                        type="text"
                        value={caseId}
                        onChange={(e) => setCaseId(e.target.value)}
                        placeholder="Case ID"
                        className="bg-transparent text-white w-24 focus:outline-none text-[11px]"
                      />
                    </div>
                  </div>
                </div>

                {/* PDF Primary Execution Buttons */}
                <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-border/40">
                  <button
                    type="button"
                    onClick={() => runPdfPipeline("normal")}
                    disabled={isRunning}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-900/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Run Real PDF Pipeline</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => runPdfPipeline("failure_recovery")}
                    disabled={isRunning}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-surface-2 hover:bg-surface text-amber-300 border border-amber-500/40 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Test Failure &amp; Bounded Recovery</span>
                  </button>

                  <div className="h-4 w-px bg-border/60 mx-1 hidden sm:block" />

                  {/* Core Mesh Tests */}
                  <button
                    type="button"
                    onClick={() => runTestScenario("e2e")}
                    disabled={isRunning}
                    className="text-xs text-[#8a94a8] hover:text-white transition-colors disabled:opacity-50"
                  >
                    Mesh E2E
                  </button>

                  {events.length > 0 && (
                    <span className="ml-auto text-[11px] font-mono text-[#8a94a8] hidden sm:inline">
                      {events.length} events | {invokedEngines.length} engines
                    </span>
                  )}
                </div>
              </div>
            </header>

            {/* Quick Prompt Composer */}
            <form
              onSubmit={handleCustomPromptSubmit}
              className="flex items-center gap-2 px-4 py-1.5 border-b border-border/60 bg-surface/40 shrink-0"
            >
              <input
                type="text"
                placeholder="Or test custom legal instructions via Perception &amp; Planning..."
                value={promptInput}
                onChange={(e) => setPromptInput(e.target.value)}
                disabled={isRunning}
                className="flex-1 text-xs py-1 px-3 rounded-lg border border-border/80 bg-surface/80 text-white placeholder-[#8a94a8] focus:border-brand focus:outline-none"
              />
              <button
                type="submit"
                disabled={isRunning || !promptInput.trim()}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-2 hover:bg-surface text-white border border-border/80 disabled:opacity-40 transition-all"
              >
                <Send className="w-3 h-3" />
                <span>Test</span>
              </button>
            </form>

            {/* Navigation Tabs */}
            <nav className="flex items-center gap-1 px-4 py-2 border-b border-border/60 bg-surface/60 shrink-0 overflow-x-auto">
              <button
                type="button"
                onClick={() => setActiveTab("knowledge")}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                  activeTab === "knowledge"
                    ? "bg-brand text-white shadow-sm font-semibold"
                    : "text-[#8a94a8] hover:text-white hover:bg-surface-2"
                }`}
              >
                <BookOpen className="w-3.5 h-3.5 text-brand" />
                <span>Extracted Knowledge</span>
                {summary?.structured_knowledge && (
                  <span className="font-mono text-[10px] px-1.5 py-0.2 rounded-full bg-black/30 text-brand">
                    {summary.structured_knowledge.facts.length}
                  </span>
                )}
              </button>

              <button
                type="button"
                onClick={() => setActiveTab("trace")}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                  activeTab === "trace"
                    ? "bg-brand text-white shadow-sm font-semibold"
                    : "text-[#8a94a8] hover:text-white hover:bg-surface-2"
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
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                  activeTab === "graph"
                    ? "bg-brand text-white shadow-sm font-semibold"
                    : "text-[#8a94a8] hover:text-white hover:bg-surface-2"
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
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                  activeTab === "plans"
                    ? "bg-brand text-white shadow-sm font-semibold"
                    : "text-[#8a94a8] hover:text-white hover:bg-surface-2"
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
                onClick={() => setActiveTab("details")}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                  activeTab === "details"
                    ? "bg-brand text-white shadow-sm font-semibold"
                    : "text-[#8a94a8] hover:text-white hover:bg-surface-2"
                }`}
              >
                <FileCode className="w-3.5 h-3.5" />
                <span>Event Details</span>
                {selectedEvent && <span className="w-2 h-2 rounded-full bg-emerald-400" />}
              </button>

              <button
                type="button"
                onClick={() => setActiveTab("summary")}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                  activeTab === "summary"
                    ? "bg-brand text-white shadow-sm font-semibold"
                    : "text-[#8a94a8] hover:text-white hover:bg-surface-2"
                }`}
              >
                <CheckCircle className="w-3.5 h-3.5" />
                <span>Test Summary</span>
              </button>
            </nav>

            {/* Active Tab Viewport */}
            <main className="flex-1 p-3 overflow-hidden bg-surface/30">
              {activeTab === "knowledge" && (
                <ExtractedKnowledgeTab
                  knowledge={summary?.structured_knowledge}
                  pages={summary?.pages}
                  scorecard={summary?.scorecard}
                  savedRecords={savedRecords}
                  onRefreshSavedRecords={() => void fetchSavedRecords(organizationId, caseId)}
                  isLoadingSaved={isLoadingSaved}
                />
              )}

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

              {activeTab === "details" && <EventDetailsTab event={selectedEvent} />}

              {activeTab === "summary" && <TestSummaryTab summary={summary} events={events} />}
            </main>

            {/* Footer with Operational Info */}
            <footer className="flex items-center justify-between px-4 py-2 border-t border-border-strong/70 bg-surface/90 text-[10px] text-[#8a94a8] shrink-0 font-mono">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                <span>PostgreSQL Persistent</span>
                <span className="text-border">|</span>
                <span>Context Isolation Enforced</span>
              </div>
              <div>
                <span>{statusMessage}</span>
              </div>
            </footer>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Floating Launcher Button */}
      <motion.button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        whileHover={shouldReduceMotion ? {} : { scale: 1.05 }}
        whileTap={shouldReduceMotion ? {} : { scale: 0.94 }}
        className="group relative flex items-center gap-2 px-3.5 py-2.5 rounded-full bg-gradient-to-r from-surface to-surface-2 border border-border-strong text-white shadow-xl shadow-black/50 transition-all hover:border-brand/70 hover:shadow-brand/20 focus-visible:outline-2 focus-visible:outline-brand"
        aria-expanded={isOpen}
        aria-label={isOpen ? "Close Ring 1 Live Test Console" : "Open Ring 1 Live Test Console"}
      >
        <span className="relative flex h-2.5 w-2.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand opacity-75" />
          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-brand" />
        </span>
        <Brain className="h-4 w-4 text-violet group-hover:text-brand-hover transition-colors" />
        <span className="text-xs font-semibold tracking-wide">Ring 1 Live Console</span>
      </motion.button>
    </aside>
  );
}
