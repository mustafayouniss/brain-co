"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { BrandMark } from "@/components/brand/icons";
import { useSession } from "@/hooks/use-session";
import { useObservationWs } from "@/hooks/use-observation-ws";
import { MeshTestConsole } from "@/components/ring1-test-console/mesh-test-console";
import {
  ArrowLeft,
  Bot,
  Brain,
  CheckCircle,
  Clock,
  Database,
  FileText,
  Radio,
  Send,
  ShieldCheck,
  Sparkles,
  Upload,
} from "lucide-react";

interface CaseDetails {
  id: string;
  case_number: string;
  title: string;
  description?: string | null;
  status?: string;
  organization_id: string;
  created_at?: string;
  updated_at?: string;
}

interface CaseDocument {
  id: string;
  original_filename: string;
  size_bytes?: number;
  content_type?: string;
  status?: string;
  created_at?: string;
}

interface CaseKnowledgeRecord {
  record_id: string;
  record_type: string;
  status: string;
  created_at?: string;
  payload?: any;
  provenance?: any;
}

export function CaseWorkspaceClient({ caseId }: { caseId: string }) {
  const router = useRouter();
  const { user, loading: sessionLoading } = useSession();

  const [caseData, setCaseData] = React.useState<CaseDetails | null>(null);
  const [loadingCase, setLoadingCase] = React.useState(true);
  const [caseError, setCaseError] = React.useState<string | null>(null);
  const [activeTab, setActiveTab] = React.useState<
    "overview" | "documents" | "knowledge" | "console" | "mesh" | "ai"
  >("overview");

  // Load Case Details
  const loadCase = React.useCallback(async () => {
    setLoadingCase(true);
    setCaseError(null);
    try {
      const res = await fetch(`/api/cases/${caseId}`);
      if (res.ok) {
        const data = await res.json();
        setCaseData(data);
      } else if (res.status === 404) {
        setCaseError("Case not found or access denied under organization policy");
      } else {
        setCaseError("Failed to load case details");
      }
    } catch {
      setCaseError("Network error fetching case details");
    } finally {
      setLoadingCase(false);
    }
  }, [caseId]);

  React.useEffect(() => {
    loadCase();
  }, [loadCase]);

  // Real-time WebSocket hook for this case scope
  const { isConnected, connectionStatus, events, clearEvents } = useObservationWs({
    caseId,
    enabled: true,
  });

  const meshStatus = React.useMemo(() => {
    switch (connectionStatus) {
      case "connected":
        return {
          label: "Mesh Live",
          color: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
          dot: "bg-emerald-400 animate-pulse",
        };
      case "connecting":
        return {
          label: "Connecting...",
          color: "bg-blue-500/10 text-blue-400 border-blue-500/30",
          dot: "bg-blue-400 animate-pulse",
        };
      case "reconnecting":
        return {
          label: "Reconnecting...",
          color: "bg-amber-500/10 text-amber-300 border-amber-500/30",
          dot: "bg-amber-400 animate-pulse",
        };
      case "error":
        return {
          label: "Connection Error",
          color: "bg-red-500/10 text-red-400 border-red-500/30",
          dot: "bg-red-400",
        };
      case "disconnected":
      default:
        return {
          label: "Mesh Standby",
          color: "bg-zinc-500/10 text-zinc-400 border-zinc-500/30",
          dot: "bg-zinc-400",
        };
    }
  }, [connectionStatus]);

  if (sessionLoading || loadingCase) {
    return (
      <div className="dark min-h-dvh flex items-center justify-center screen-base text-white">
        <div className="flex items-center gap-3 text-sm text-[#8a94a8]">
          <span className="h-2 w-2 rounded-full bg-[#946eff] animate-ping" />
          Loading case workspace...
        </div>
      </div>
    );
  }

  if (caseError || !caseData) {
    return (
      <div className="dark min-h-dvh flex items-center justify-center screen-base text-white p-4">
        <div className="max-w-md w-full rounded-2xl border border-red-500/30 bg-[#0b1425] p-6 text-center space-y-4">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-500/10 text-red-400">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <h2 className="text-base font-semibold text-white">Access Refused / Not Found</h2>
          <p className="text-xs text-[#a7b0c1]">{caseError || "Case does not exist."}</p>
          <Link
            href="/workspace"
            className="inline-flex items-center gap-2 rounded-full border border-[#34405a] px-4 py-2 text-xs font-semibold text-white hover:border-[#946eff]"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Organization Workspace
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="dark min-h-dvh screen-base text-white">
      {/* Header */}
      <header className="sticky top-0 z-30 border-b border-[#202a3e] bg-[#050b1a]/85 backdrop-blur-xl">
        <div className="mx-auto flex h-14 w-full max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <Link
              href="/workspace"
              className="flex items-center gap-1.5 text-xs text-[#8a94a8] hover:text-white transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Workspace</span>
            </Link>
            <span className="text-[#34405a]">/</span>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-semibold text-[#946eff]">
                {caseData.case_number}
              </span>
              <span className="text-xs font-medium text-white truncate max-w-[200px] sm:max-w-md">
                {caseData.title}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`flex items-center gap-1.5 text-[11px] font-mono px-2.5 py-1 rounded-full border ${meshStatus.color}`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${meshStatus.dot}`} />
              {meshStatus.label}
            </span>
            <span className="tag text-[10px] capitalize">{caseData.status || "open"}</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 space-y-6">
        {/* Case Meta Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#202a3e] pb-4">
          <div className="space-y-1">
            <h1 className="text-xl font-bold tracking-tight text-white">{caseData.title}</h1>
            <div className="flex flex-wrap items-center gap-2 text-xs text-[#8a94a8]">
              <span className="font-mono text-white font-semibold">Reference: {caseData.case_number}</span>
              <span>•</span>
              <span className="font-mono text-[11px]" title={`Tenant ID: ${caseData.organization_id}`}>
                Org: {caseData.organization_id.slice(0, 8)}...
              </span>
              <span>•</span>
              <span className="font-mono text-[11px]" title={`Case UUID: ${caseData.id}`}>
                UUID: {caseData.id.slice(0, 8)}...
              </span>
              {caseData.created_at && (
                <>
                  <span>•</span>
                  <span>Registered: {new Date(caseData.created_at).toLocaleDateString()}</span>
                </>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="tag border-white/20 text-[#8a94a8] text-[10px]">
              CACS Boundary Protected
            </span>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-[#202a3e] gap-1 overflow-x-auto text-xs">
          {[
            { id: "overview", label: "Overview", icon: FileText },
            { id: "documents", label: "Documents", icon: Upload },
            { id: "knowledge", label: "Extracted Knowledge", icon: Database },
            { id: "console", label: "Mesh Test Console", icon: Brain },
            { id: "mesh", label: `Live Mesh Activity (${events.length})`, icon: Radio },
            { id: "ai", label: "Case AI Employee", icon: Bot },
          ].map((tab) => {
            const Icon = tab.icon;
            const isTabActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-2.5 font-medium border-b-2 transition-colors whitespace-nowrap ${
                  isTabActive
                    ? "border-[#946eff] text-white"
                    : "border-transparent text-[#8a94a8] hover:text-[#a7b0c1]"
                }`}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab Content Panels */}
        {activeTab === "overview" && <OverviewTab caseData={caseData} />}
        {activeTab === "documents" && <DocumentsTab caseId={caseId} />}
        {activeTab === "knowledge" && <KnowledgeTab caseId={caseId} />}
        {activeTab === "console" && (
          <MeshTestConsole
            organizationId={caseData.organization_id}
            caseId={caseData.id}
            caseNumber={caseData.case_number}
            caseTitle={caseData.title}
          />
        )}
        {activeTab === "mesh" && (
          <MeshTab
            caseId={caseId}
            events={events}
            isConnected={isConnected}
            clearEvents={clearEvents}
          />
        )}
        {activeTab === "ai" && <AIEmployeeTab caseData={caseData} />}
      </main>
    </div>
  );
}

function OverviewTab({ caseData }: { caseData: CaseDetails }) {
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      <div className="sm:col-span-2 rounded-2xl border border-[#202a3e] bg-[#0b1425] p-5 space-y-4">
        <div>
          <h3 className="text-sm font-semibold text-white">Case Summary &amp; Scope</h3>
          <p className="mt-2 text-xs text-[#a7b0c1] leading-relaxed">
            {caseData.description || "No detailed description supplied for this matter."}
          </p>
        </div>
        <div className="border-t border-[#202a3e] pt-4 grid grid-cols-2 gap-4 text-xs">
          <div>
            <p className="text-[#8a94a8]">Case Number</p>
            <p className="font-mono font-medium text-white mt-1">{caseData.case_number}</p>
          </div>
          <div>
            <p className="text-[#8a94a8]">Current Status</p>
            <p className="capitalize text-emerald-400 font-medium mt-1">
              {caseData.status || "Active"}
            </p>
          </div>
          <div>
            <p className="text-[#8a94a8]">Organization Identifier</p>
            <p className="font-mono text-white mt-1">{caseData.organization_id}</p>
          </div>
          <div>
            <p className="text-[#8a94a8]">Internal UUID</p>
            <p className="font-mono text-[#8a94a8] text-[11px] mt-1">{caseData.id}</p>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-[#202a3e] bg-[#0b1425] p-5 space-y-4">
        <h3 className="text-sm font-semibold text-white">Cognitive Governance</h3>
        <ul className="space-y-3 text-xs text-[#a7b0c1]">
          <li className="flex items-start gap-2">
            <ShieldCheck className="h-4 w-4 text-[#946eff] shrink-0 mt-0.5" />
            <span>Dual-boundary isolation enforced across all document ingestion and retrieval.</span>
          </li>
          <li className="flex items-start gap-2">
            <Brain className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
            <span>Extracted facts validated against Egyptian Civil Code articles.</span>
          </li>
          <li className="flex items-start gap-2">
            <Radio className="h-4 w-4 text-blue-400 shrink-0 mt-0.5" />
            <span>Live Mesh execution streams to authorized case subscribers only.</span>
          </li>
        </ul>
      </div>
    </div>
  );
}

function DocumentsTab({ caseId }: { caseId: string }) {
  const [docs, setDocs] = React.useState<CaseDocument[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [uploading, setUploading] = React.useState(false);
  const [uploadMsg, setUploadMsg] = React.useState<{ text: string; error: boolean } | null>(null);
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);

  const fetchDocs = React.useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/cases/${caseId}/documents`);
      if (res.ok) {
        const data = await res.json();
        setDocs(Array.isArray(data) ? data : []);
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  React.useEffect(() => {
    fetchDocs();
  }, [fetchDocs]);

  const handleUpload = async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setUploadMsg({ text: "Only PDF documents are supported.", error: true });
      return;
    }

    setUploading(true);
    setUploadMsg(null);
    const fd = new FormData();
    fd.append("file", file);

    try {
      const res = await fetch(`/api/cases/${caseId}/documents`, {
        method: "POST",
        body: fd,
      });
      if (res.ok) {
        setUploadMsg({
          text: `Document '${file.name}' accepted for ingestion and task dispatched.`,
          error: false,
        });
        fetchDocs();
      } else {
        const err = await res.json().catch(() => ({}));
        setUploadMsg({
          text: err.detail?.message || err.error || "Upload failed",
          error: true,
        });
      }
    } catch {
      setUploadMsg({ text: "Network error during upload", error: true });
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div className="space-y-4">
      {/* Upload Zone */}
      <div
        onClick={() => fileInputRef.current?.click()}
        className="rounded-2xl border-2 border-dashed border-[#202a3e] bg-[#0b1425]/50 hover:bg-[#0b1425] hover:border-[#946eff]/60 transition-all p-8 text-center cursor-pointer"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleUpload(f);
          }}
        />
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[#946eff]/10 text-[#946eff] mb-3">
          <Upload className="h-6 w-6" />
        </div>
        <p className="text-sm font-semibold text-white">
          {uploading ? "Ingesting PDF..." : "Upload Legal PDF Document"}
        </p>
        <p className="text-xs text-[#8a94a8] mt-1">
          Contracts, court filings, legal notices, or correspondence (up to 20MB).
        </p>
      </div>

      {uploadMsg && (
        <div
          className={`p-3 rounded-lg text-xs border ${
            uploadMsg.error
              ? "bg-red-500/10 border-red-500/30 text-red-400"
              : "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
          }`}
        >
          {uploadMsg.text}
        </div>
      )}

      {/* Document List */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-white">Case Source Documents</h3>
        {loading ? (
          <p className="text-xs text-[#8a94a8] py-4">Loading documents...</p>
        ) : docs.length === 0 ? (
          <div className="rounded-2xl border border-[#202a3e] bg-[#0b1425] p-6 text-center text-xs text-[#8a94a8]">
            No source documents uploaded for this case yet.
          </div>
        ) : (
          <div className="divide-y divide-[#202a3e] rounded-2xl border border-[#202a3e] bg-[#0b1425] overflow-hidden">
            {docs.map((doc) => (
              <div key={doc.id} className="p-4 flex items-center justify-between gap-4 text-xs">
                <div className="flex items-center gap-3">
                  <FileText className="h-5 w-5 text-[#946eff]" />
                  <div>
                    <p className="font-medium text-white">{doc.original_filename}</p>
                    <p className="text-[11px] text-[#8a94a8]">
                      {doc.size_bytes ? `${Math.round(doc.size_bytes / 1024)} KB` : "Document"} •{" "}
                      {doc.created_at ? new Date(doc.created_at).toLocaleString() : ""}
                    </p>
                  </div>
                </div>
                <span className="tag text-[10px] capitalize text-emerald-400 border-emerald-500/30">
                  {doc.status || "ready"}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function KnowledgeTab({ caseId }: { caseId: string }) {
  const [records, setRecords] = React.useState<CaseKnowledgeRecord[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [query, setQuery] = React.useState("");

  const fetchKnowledge = React.useCallback(async () => {
    setLoading(true);
    try {
      const url = new URL(`/api/cases/${caseId}/knowledge`, window.location.origin);
      if (query.trim()) url.searchParams.set("query", query.trim());
      const res = await fetch(url.toString());
      if (res.ok) {
        const data = await res.json();
        setRecords(Array.isArray(data.records) ? data.records : []);
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [caseId, query]);

  React.useEffect(() => {
    fetchKnowledge();
  }, [fetchKnowledge]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-white">Extracted Legal Knowledge</h3>
          <p className="text-xs text-[#a7b0c1]">
            Facts, contractual clauses, and statutory obligations grounded in Egyptian Civil Law.
          </p>
        </div>
        <input
          type="text"
          placeholder="Filter knowledge..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="rounded-lg bg-[#0b1425] border border-[#202a3e] px-3 py-1.5 text-xs text-white placeholder-[#8a94a8] focus:border-[#946eff] focus:outline-none w-64"
        />
      </div>

      {loading ? (
        <p className="text-xs text-[#8a94a8] py-4">Querying case memory...</p>
      ) : records.length === 0 ? (
        <div className="rounded-2xl border border-[#202a3e] bg-[#0b1425] p-6 text-center text-xs text-[#8a94a8]">
          No knowledge records found. Upload a PDF document to begin automated extraction.
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {records.map((r) => {
            const payload = r.payload || {};
            const facts = payload.facts || [];
            const obligations = payload.obligations || [];
            return (
              <div key={r.record_id} className="rounded-2xl border border-[#202a3e] bg-[#0b1425] p-5 space-y-3 text-xs">
                <div className="flex items-center justify-between">
                  <span className="tag text-[10px] text-[#946eff] font-mono">{r.record_type}</span>
                  <span className="tag text-[10px] capitalize text-emerald-400 border-emerald-500/30">
                    {r.status}
                  </span>
                </div>
                {payload.title && (
                  <p className="font-semibold text-sm text-white">{payload.title}</p>
                )}
                {payload.summary && (
                  <p className="text-[#a7b0c1] text-xs leading-relaxed">{payload.summary}</p>
                )}
                {facts.length > 0 && (
                  <div className="space-y-1">
                    <p className="text-[11px] font-semibold text-[#8a94a8]">Extracted Facts:</p>
                    <ul className="list-disc list-inside text-[11px] text-[#a7b0c1] space-y-0.5">
                      {facts.slice(0, 3).map((f: any, idx: number) => (
                        <li key={idx}>{f.statement || f.fact_text || (typeof f === "string" ? f : JSON.stringify(f))}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {obligations.length > 0 && (
                  <div className="space-y-1">
                    <p className="text-[11px] font-semibold text-[#8a94a8]">Legal Obligations:</p>
                    <ul className="list-disc list-inside text-[11px] text-amber-300/80 space-y-0.5">
                      {obligations.slice(0, 2).map((o: any, idx: number) => (
                        <li key={idx}>
                          {o.responsible_party ? `[${o.responsible_party}] ` : ""}
                          {o.description || o}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                <div className="pt-2 border-t border-[#202a3e] text-[10px] text-[#8a94a8] flex justify-between">
                  <span>ID: {r.record_id.slice(0, 8)}...</span>
                  <span>{r.created_at ? new Date(r.created_at).toLocaleDateString() : ""}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function MeshTab({
  caseId,
  events,
  isConnected,
  clearEvents,
}: {
  caseId: string;
  events: any[];
  isConnected: boolean;
  clearEvents: () => void;
}) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-white">Live Capability Mesh Telemetry</h3>
          <p className="text-xs text-[#a7b0c1]">
            Real-time peer-to-peer event stream scoped strictly to case {caseId}.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={clearEvents}
            className="rounded-lg border border-[#34405a] px-3 py-1 text-xs text-[#8a94a8] hover:text-white"
          >
            Clear Stream
          </button>
        </div>
      </div>

      <div className="rounded-2xl border border-[#202a3e] bg-[#0b1425] p-4 font-mono text-xs max-h-[500px] overflow-y-auto space-y-2">
        {events.length === 0 ? (
          <p className="text-center text-[#8a94a8] py-8">
            Listening for live mesh execution events... Trigger an action or upload a document to observe real-time telemetry.
          </p>
        ) : (
          events.map((evt, idx) => (
            <div
              key={idx}
              className="flex items-start gap-3 p-2 rounded-lg bg-[#050b1a]/60 border border-[#202a3e]/50 hover:border-[#946eff]/40 transition-colors"
            >
              <span className="text-[#8a94a8] text-[10px]">
                {evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : "--:--:--"}
              </span>
              <span className="text-[#946eff] font-semibold">{evt.event_type}</span>
              <span className="text-white truncate max-w-[200px]">
                {evt.capability || evt.source_engine || "mesh"}
              </span>
              <span
                className={`ml-auto text-[10px] px-2 py-0.5 rounded ${
                  evt.status === "completed" || evt.status === "success"
                    ? "bg-emerald-500/10 text-emerald-400"
                    : evt.status === "failed"
                    ? "bg-red-500/10 text-red-400"
                    : "bg-blue-500/10 text-blue-300"
                }`}
              >
                {evt.status || "ok"}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function AIEmployeeTab({ caseData }: { caseData: CaseDetails }) {
  const [messages, setMessages] = React.useState<Array<{ role: string; content: string }>>([
    {
      role: "assistant",
      content: `Hello! I am your AI Legal Assistant grounded on case "${caseData.title}" (${caseData.case_number}). Ask me about Egyptian Civil Code obligations, contractual terms, or case strategy.`,
    },
  ]);
  const [input, setInput] = React.useState("");
  const [loading, setLoading] = React.useState(false);

  const sendMessage = async (promptText: string) => {
    if (!promptText.trim() || loading) return;
    const userMsg = { role: "user", content: promptText };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/ai/prompt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: promptText,
          context: "legal",
          case_id: caseData.case_number,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: data.response || "No response received." },
        ]);
      } else {
        const err = await res.json().catch(() => ({}));
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `Error: ${err.error || err.detail || "Failed to contact AI Employee"}`,
          },
        ]);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Network error communicating with AI Employee." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-2xl border border-[#202a3e] bg-[#0b1425] p-5 space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-white">Case-Grounded Cognitive Assistant</h3>
        <p className="text-xs text-[#a7b0c1]">
          Responses are strictly grounded in this case&apos;s verified memory records and Egyptian Civil Law.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {[
          "Summarize key legal obligations in this case",
          "What Egyptian Civil Code articles apply?",
          "Assess liability risks for Party B",
        ].map((suggestion, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => sendMessage(suggestion)}
            className="rounded-full border border-[#202a3e] bg-[#050b1a] px-3 py-1 text-[11px] text-[#a7b0c1] hover:text-white hover:border-[#946eff]/40 transition-colors"
          >
            {suggestion}
          </button>
        ))}
      </div>

      <div className="space-y-3 max-h-[350px] overflow-y-auto p-3 rounded-xl bg-[#050b1a]/50 border border-[#202a3e]">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`flex items-start gap-2.5 text-xs ${
              m.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            {m.role === "assistant" && (
              <div className="h-6 w-6 rounded-full bg-[#946eff]/20 flex items-center justify-center text-[#946eff] shrink-0 mt-0.5">
                <Sparkles className="h-3.5 w-3.5" />
              </div>
            )}
            <div
              className={`p-3 rounded-2xl max-w-[80%] leading-relaxed ${
                m.role === "user"
                  ? "bg-[#946eff] text-white"
                  : "bg-[#0b1425] border border-[#202a3e] text-[#e1e7f0]"
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-xs text-[#8a94a8]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#946eff] animate-pulse" />
            <span>AI Employee is reasoning over case knowledge...</span>
          </div>
        )}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          sendMessage(input);
        }}
        className="flex gap-2"
      >
        <input
          type="text"
          placeholder="Ask a question about this case..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 rounded-xl bg-[#050b1a] border border-[#202a3e] px-4 py-2 text-xs text-white placeholder-[#8a94a8] focus:border-[#946eff] focus:outline-none"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="rounded-xl bg-[#946eff] px-4 py-2 text-xs font-semibold text-white hover:bg-[#7c3aed] disabled:opacity-50 transition-colors flex items-center gap-1.5"
        >
          <Send className="h-3.5 w-3.5" />
          <span>Send</span>
        </button>
      </form>
    </div>
  );
}
