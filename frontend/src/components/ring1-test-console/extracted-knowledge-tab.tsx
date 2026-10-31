"use client";

import * as React from "react";
import {
  FileText,
  CheckCircle2,
  AlertTriangle,
  Scale,
  Calendar,
  Users,
  BookOpen,
  Database,
  Search,
  Layers,
  ShieldCheck,
  ChevronRight,
  Sparkles,
} from "lucide-react";

import {
  DocumentStructuredKnowledge,
  PDFPageContent,
  ScorecardModel,
  SavedKnowledgeRecord,
  ExtractedFact,
} from "./types";

interface ExtractedKnowledgeTabProps {
  knowledge?: DocumentStructuredKnowledge | null;
  pages?: PDFPageContent[] | null;
  scorecard?: ScorecardModel | null;
  savedRecords?: SavedKnowledgeRecord[] | null;
  onRefreshSavedRecords?: () => void;
  isLoadingSaved?: boolean;
}

export function ExtractedKnowledgeTab({
  knowledge,
  pages,
  scorecard,
  savedRecords,
  onRefreshSavedRecords,
  isLoadingSaved,
}: ExtractedKnowledgeTabProps) {
  const [activeSubTab, setActiveSubTab] = React.useState<"facts" | "entities" | "pages" | "saved">("facts");
  const [selectedPageIndex, setSelectedPageIndex] = React.useState(0);
  const [factFilter, setFactFilter] = React.useState("");

  if (!knowledge && (!pages || pages.length === 0)) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-8 bg-surface/30 rounded-xl border border-dashed border-border/60">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-surface-2 text-[#8a94a8] mb-3 border border-border">
          <BookOpen className="h-6 w-6 text-brand" />
        </div>
        <h4 className="text-sm font-semibold text-white">No PDF Knowledge Ingested Yet</h4>
        <p className="text-xs text-[#8a94a8] mt-1 max-w-sm">
          Select or drag-and-drop a real PDF in the header, or run the live pipeline to extract text,
          Egyptian legal articles, facts, and persist them into PostgreSQL.
        </p>
      </div>
    );
  }

  const filteredFacts = (knowledge?.facts || []).filter((f: ExtractedFact) => {
    if (!factFilter) return true;
    const term = factFilter.toLowerCase();
    return (
      f.statement.toLowerCase().includes(term) ||
      f.category.toLowerCase().includes(term) ||
      f.source_excerpt.toLowerCase().includes(term)
    );
  });

  return (
    <div className="flex flex-col h-full gap-3 overflow-hidden">
      {/* Top Knowledge Scorecard Card */}
      <div className="p-3 rounded-xl bg-surface-2/60 border border-border-strong/70 shrink-0">
        <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-border/50">
          <div className="flex items-center gap-2 min-w-0">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand/20 text-brand shrink-0">
              <FileText className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <h4 className="text-xs font-bold text-white truncate">
                {knowledge?.title || "Ingested Document"}
              </h4>
              <p className="text-[10px] text-[#8a94a8] capitalize truncate">
                Type: {knowledge?.document_type.replace(/_/g, " ")} | Mode: {knowledge?.extraction_mode}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5 flex-wrap">
            {scorecard && (
              <span
                className={`text-[10px] font-mono px-2 py-0.5 rounded-full border font-semibold ${
                  scorecard.processing_outcome === "SUCCESS"
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                    : scorecard.processing_outcome === "RECOVERED"
                    ? "bg-amber-500/10 text-amber-300 border-amber-500/30"
                    : "bg-rose-500/10 text-rose-400 border-rose-500/30"
                }`}
              >
                {scorecard.processing_outcome}
              </span>
            )}

            {scorecard?.isolation_verified && (
              <span className="flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-full bg-violet/10 text-violet border border-violet/30 font-medium">
                <ShieldCheck className="w-3 h-3 text-violet" />
                Case Isolated
              </span>
            )}
          </div>
        </div>

        {/* Quick KPI Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 text-center font-mono">
          <div className="p-1.5 rounded-lg bg-surface/50 border border-border/40">
            <div className="text-[10px] text-[#8a94a8]">Pages</div>
            <div className="text-xs font-bold text-white">{pages?.length || scorecard?.pages_processed || 0}</div>
          </div>
          <div className="p-1.5 rounded-lg bg-surface/50 border border-border/40">
            <div className="text-[10px] text-[#8a94a8]">Candidate Facts</div>
            <div className="text-xs font-bold text-brand">{knowledge?.facts.length || 0}</div>
          </div>
          <div className="p-1.5 rounded-lg bg-surface/50 border border-border/40">
            <div className="text-[10px] text-[#8a94a8]">Persisted in DB</div>
            <div className="text-xs font-bold text-emerald-400">
              {scorecard?.persisted_facts ?? (knowledge?.facts.length || 0)}
            </div>
          </div>
          <div className="p-1.5 rounded-lg bg-surface/50 border border-border/40">
            <div className="text-[10px] text-[#8a94a8]">Verified Retrieval</div>
            <div className="text-xs font-bold text-violet">
              {scorecard?.retrieved_facts ?? (savedRecords ? savedRecords.length : 1)}
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex items-center justify-between gap-2 border-b border-border/60 pb-1.5 shrink-0">
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => setActiveSubTab("facts")}
            className={`px-2.5 py-1 text-xs font-medium rounded-md transition-all ${
              activeSubTab === "facts"
                ? "bg-brand text-white shadow-sm"
                : "text-[#8a94a8] hover:text-white hover:bg-surface-2"
            }`}
          >
            Facts ({knowledge?.facts.length || 0})
          </button>
          <button
            type="button"
            onClick={() => setActiveSubTab("entities")}
            className={`px-2.5 py-1 text-xs font-medium rounded-md transition-all ${
              activeSubTab === "entities"
                ? "bg-brand text-white shadow-sm"
                : "text-[#8a94a8] hover:text-white hover:bg-surface-2"
            }`}
          >
            Entities &amp; Obligations ({knowledge?.entities.length || 0})
          </button>
          <button
            type="button"
            onClick={() => setActiveSubTab("pages")}
            className={`px-2.5 py-1 text-xs font-medium rounded-md transition-all ${
              activeSubTab === "pages"
                ? "bg-brand text-white shadow-sm"
                : "text-[#8a94a8] hover:text-white hover:bg-surface-2"
            }`}
          >
            Raw Pages ({pages?.length || 0})
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveSubTab("saved");
              onRefreshSavedRecords?.();
            }}
            className={`px-2.5 py-1 text-xs font-medium rounded-md transition-all flex items-center gap-1 ${
              activeSubTab === "saved"
                ? "bg-brand text-white shadow-sm"
                : "text-[#8a94a8] hover:text-white hover:bg-surface-2"
            }`}
          >
            <Database className="w-3 h-3" />
            <span>PostgreSQL Memory</span>
            {savedRecords && savedRecords.length > 0 && (
              <span className="font-mono text-[9px] px-1.5 py-0.2 rounded-full bg-black/40">
                {savedRecords.length}
              </span>
            )}
          </button>
        </div>

        {activeSubTab === "facts" && (
          <div className="relative">
            <Search className="w-3 h-3 text-[#8a94a8] absolute left-2 top-2" />
            <input
              type="text"
              placeholder="Search facts..."
              value={factFilter}
              onChange={(e) => setFactFilter(e.target.value)}
              className="text-[11px] py-1 pl-6 pr-2 rounded-md bg-surface/80 border border-border/60 text-white placeholder-[#8a94a8] focus:outline-none focus:border-brand w-32 sm:w-44"
            />
          </div>
        )}
      </div>

      {/* Sub-Tab Contents */}
      <div className="flex-1 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
        {/* FACTS TAB */}
        {activeSubTab === "facts" && (
          <div className="space-y-2">
            {filteredFacts.length === 0 ? (
              <div className="text-center py-6 text-xs text-[#8a94a8]">No matching facts found.</div>
            ) : (
              filteredFacts.map((fact: ExtractedFact, idx: number) => (
                <div
                  key={fact.fact_id || idx}
                  className="p-2.5 rounded-lg bg-surface/60 border border-border/70 hover:border-brand/40 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="font-mono text-[9px] px-1.5 py-0.2 rounded bg-surface-2 text-[#8a94a8] border border-border/50">
                        Page {fact.page_number}
                      </span>
                      <span className="font-mono text-[9px] px-1.5 py-0.2 rounded uppercase bg-brand/10 text-brand border border-brand/20">
                        {fact.category}
                      </span>
                      {fact.is_validated && (
                        <span className="flex items-center gap-0.5 font-mono text-[9px] text-emerald-400">
                          <CheckCircle2 className="w-2.5 h-2.5" />
                          Validated
                        </span>
                      )}
                    </div>
                    <span className="font-mono text-[9px] text-[#8a94a8]">
                      {(fact.confidence * 100).toFixed(0)}% conf
                    </span>
                  </div>

                  <p className="text-xs text-white mt-1.5 leading-relaxed font-medium">
                    {fact.statement}
                  </p>

                  {fact.source_excerpt && (
                    <blockquote className="mt-1.5 pl-2 border-l-2 border-brand/50 text-[11px] text-[#8a94a8] italic bg-surface-2/30 py-0.5 rounded-r">
                      &ldquo;{fact.source_excerpt}&rdquo;
                    </blockquote>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {/* ENTITIES & OBLIGATIONS TAB */}
        {activeSubTab === "entities" && (
          <div className="space-y-3">
            {/* Entities Section */}
            <div>
              <h5 className="text-[11px] font-bold text-[#8a94a8] uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                <Users className="w-3 h-3 text-brand" />
                <span>Named Entities ({knowledge?.entities.length || 0})</span>
              </h5>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {(knowledge?.entities || []).map((ent, idx) => (
                  <div
                    key={idx}
                    className="p-2 rounded-lg bg-surface/50 border border-border/60 flex items-center justify-between text-xs"
                  >
                    <div className="min-w-0 pr-2">
                      <div className="font-semibold text-white truncate">{ent.name}</div>
                      <div className="text-[10px] text-[#8a94a8] capitalize">
                        {ent.entity_type} | Page {ent.page_number}
                      </div>
                    </div>
                    <span className="font-mono text-[10px] text-brand shrink-0">
                      {(ent.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Obligations Section */}
            {knowledge?.obligations && knowledge.obligations.length > 0 && (
              <div>
                <h5 className="text-[11px] font-bold text-[#8a94a8] uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                  <Scale className="w-3 h-3 text-amber-400" />
                  <span>Contractual Obligations ({knowledge.obligations.length})</span>
                </h5>
                <div className="space-y-1.5">
                  {knowledge.obligations.map((oblg, idx) => (
                    <div key={idx} className="p-2 rounded-lg bg-surface/50 border border-amber-500/30 text-xs">
                      <div className="flex items-center justify-between text-[10px] text-amber-300 font-mono mb-1">
                        <span>Page {oblg.page_number}</span>
                        {oblg.deadline && <span>Deadline: {oblg.deadline}</span>}
                      </div>
                      <p className="text-white text-xs">{oblg.description}</p>
                      {oblg.responsible_party && (
                        <div className="text-[10px] text-[#8a94a8] mt-1">
                          Party: <span className="text-white">{oblg.responsible_party}</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* RAW PAGES VIEWER TAB */}
        {activeSubTab === "pages" && pages && pages.length > 0 && (
          <div className="flex flex-col h-full gap-2">
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 shrink-0">
              {pages.map((p, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setSelectedPageIndex(idx)}
                  className={`px-2.5 py-1 text-xs font-mono rounded-md border transition-all shrink-0 ${
                    selectedPageIndex === idx
                      ? "bg-brand text-white border-brand shadow-sm font-bold"
                      : "bg-surface text-[#8a94a8] border-border/60 hover:text-white"
                  }`}
                >
                  Page {p.page_number} ({p.char_count} chars)
                </button>
              ))}
            </div>

            <div className="flex-1 p-3 rounded-lg bg-[#040813] border border-border-strong font-mono text-xs text-[#cbd5e1] whitespace-pre-wrap overflow-y-auto leading-relaxed select-text">
              {pages[selectedPageIndex]?.text || "(Empty page content)"}
            </div>
          </div>
        )}

        {/* SAVED KNOWLEDGE IN POSTGRESQL */}
        {activeSubTab === "saved" && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs text-[#8a94a8] pb-1">
              <span>Durably persisted rows in ring1_memory_records:</span>
              <button
                type="button"
                onClick={() => onRefreshSavedRecords?.()}
                disabled={isLoadingSaved}
                className="text-brand hover:underline font-medium text-[11px]"
              >
                {isLoadingSaved ? "Querying..." : "Refresh Database"}
              </button>
            </div>

            {!savedRecords || savedRecords.length === 0 ? (
              <div className="text-center py-8 text-xs text-[#8a94a8] bg-surface/30 rounded-lg border border-border/50">
                No saved records found for this case in PostgreSQL yet.
              </div>
            ) : (
              savedRecords.map((rec) => (
                <div
                  key={rec.record_id}
                  className="p-2.5 rounded-lg bg-surface/60 border border-border/70 font-mono text-xs space-y-1.5"
                >
                  <div className="flex items-center justify-between text-[10px] text-[#8a94a8]">
                    <span className="text-brand font-semibold">{rec.record_type}</span>
                    <span>{rec.created_at || "now"}</span>
                  </div>
                  <div className="text-[10px] text-[#8a94a8] truncate">
                    Record ID: <span className="text-white">{rec.record_id}</span>
                  </div>
                  <div className="text-[10px] text-[#8a94a8] truncate">
                    Case Scope: <span className="text-white">{rec.case_id}</span> | Org:{" "}
                    <span className="text-white">{rec.organization_id}</span>
                  </div>
                  <details className="mt-1">
                    <summary className="text-[10px] text-violet cursor-pointer hover:underline select-none">
                      Inspect Stored Payload JSON
                    </summary>
                    <pre className="mt-1 p-2 rounded bg-[#040813] text-[10px] text-[#cbd5e1] overflow-x-auto whitespace-pre-wrap">
                      {JSON.stringify(rec.payload, null, 2)}
                    </pre>
                  </details>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
