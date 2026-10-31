"use client";

import * as React from "react";
import { Check, Copy, Code, FileText, ArrowRight, ShieldCheck, AlertCircle } from "lucide-react";
import { TestRunEvent } from "./types";

interface EventDetailsTabProps {
  event: TestRunEvent | null;
}

export function EventDetailsTab({ event }: EventDetailsTabProps) {
  const [copiedSection, setCopiedSection] = React.useState<string | null>(null);

  const handleCopy = async (section: string, data: any) => {
    try {
      const text = JSON.stringify(data, null, 2);
      await navigator.clipboard.writeText(text);
      setCopiedSection(section);
      setTimeout(() => setCopiedSection(null), 1500);
    } catch {
      // Fallback
    }
  };

  if (!event) {
    return (
      <div className="flex flex-col items-center justify-center h-64 rounded-xl border border-dashed border-border/60 text-center p-6">
        <Code className="w-10 h-10 text-[#8a94a8] mb-2 stroke-[1.5]" />
        <h3 className="text-sm font-semibold text-white">No Event Selected</h3>
        <p className="text-xs text-[#8a94a8] max-w-sm mt-1">
          Click on any row in the &quot;Live Trace&quot; tab to inspect its full MeshRequest and MeshResponse envelopes, error codes, and sanitized contracts.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full space-y-3 overflow-y-auto pr-1 max-h-[390px] text-xs">
      {/* Event Header Banner */}
      <div className="flex items-center justify-between p-3 rounded-xl bg-surface/80 border border-border/80">
        <div className="flex items-center gap-2">
          <span className="font-mono px-2 py-0.5 rounded bg-surface-2 text-violet font-bold border border-border">
            Seq #{event.sequence}
          </span>
          <span className="font-semibold text-white">
            {event.event_type.replace(/_/g, " ").toUpperCase()}
          </span>
        </div>

        <div className="flex items-center gap-2 font-mono text-[11px]">
          <span className="text-[#8a94a8]">Status:</span>
          <span
            className={`font-semibold uppercase ${
              event.status === "completed"
                ? "text-emerald-400"
                : event.status === "failed"
                ? "text-red-400"
                : event.status === "denied"
                ? "text-amber-400"
                : "text-violet"
            }`}
          >
            {event.status}
          </span>
          {event.duration_ms && (
            <span className="text-[#8a94a8]">({event.duration_ms} ms)</span>
          )}
        </div>
      </div>

      {/* Identifiers Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
        <div className="p-2.5 rounded-xl bg-surface/60 border border-border/60">
          <div className="text-[10px] text-[#8a94a8] uppercase font-mono">Run ID</div>
          <div className="font-mono text-white text-[11px] truncate mt-0.5">{event.run_id}</div>
        </div>

        <div className="p-2.5 rounded-xl bg-surface/60 border border-border/60">
          <div className="text-[10px] text-[#8a94a8] uppercase font-mono">Sender Engine</div>
          <div className="font-semibold text-violet text-[11px] truncate mt-0.5">{event.source_engine}</div>
        </div>

        <div className="p-2.5 rounded-xl bg-surface/60 border border-border/60">
          <div className="text-[10px] text-[#8a94a8] uppercase font-mono">Recipient Capability</div>
          <div className="font-mono text-emerald-300 text-[11px] truncate mt-0.5">{event.capability}</div>
        </div>
      </div>

      {/* MeshRequest Envelope */}
      {event.request_envelope && (
        <div className="rounded-xl border border-border/80 bg-surface/70 overflow-hidden">
          <div className="flex items-center justify-between px-3 py-2 bg-surface-2/60 border-b border-border/60">
            <span className="font-mono text-[11px] font-semibold text-white flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-violet" />
              MeshRequest Envelope
            </span>
            <button
              type="button"
              onClick={() => handleCopy("request", event.request_envelope)}
              className="flex items-center gap-1 text-[10px] text-[#8a94a8] hover:text-white transition-colors"
            >
              {copiedSection === "request" ? (
                <>
                  <Check className="w-3 h-3 text-emerald-400" />
                  <span className="text-emerald-400">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3" />
                  <span>Copy JSON</span>
                </>
              )}
            </button>
          </div>
          <pre className="p-3 font-mono text-[10px] text-[#c9c2ff] overflow-x-auto max-h-48 leading-relaxed">
            {JSON.stringify(event.request_envelope, null, 2)}
          </pre>
        </div>
      )}

      {/* MeshResponse Envelope */}
      {event.response_envelope && (
        <div className="rounded-xl border border-border/80 bg-surface/70 overflow-hidden">
          <div className="flex items-center justify-between px-3 py-2 bg-surface-2/60 border-b border-border/60">
            <span className="font-mono text-[11px] font-semibold text-white flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              MeshResponse Envelope
            </span>
            <button
              type="button"
              onClick={() => handleCopy("response", event.response_envelope)}
              className="flex items-center gap-1 text-[10px] text-[#8a94a8] hover:text-white transition-colors"
            >
              {copiedSection === "response" ? (
                <>
                  <Check className="w-3 h-3 text-emerald-400" />
                  <span className="text-emerald-400">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3" />
                  <span>Copy JSON</span>
                </>
              )}
            </button>
          </div>
          <pre className="p-3 font-mono text-[10px] text-[#8adabc] overflow-x-auto max-h-48 leading-relaxed">
            {JSON.stringify(event.response_envelope, null, 2)}
          </pre>
        </div>
      )}

      {/* Raw Details / Failure Evidence */}
      {event.details && Object.keys(event.details).length > 0 && !event.request_envelope && !event.response_envelope && (
        <div className="rounded-xl border border-border/80 bg-surface/70 overflow-hidden">
          <div className="flex items-center justify-between px-3 py-2 bg-surface-2/60 border-b border-border/60">
            <span className="font-mono text-[11px] font-semibold text-white flex items-center gap-1.5">
              <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
              Event Structured Details
            </span>
            <button
              type="button"
              onClick={() => handleCopy("details", event.details)}
              className="flex items-center gap-1 text-[10px] text-[#8a94a8] hover:text-white transition-colors"
            >
              {copiedSection === "details" ? (
                <>
                  <Check className="w-3 h-3 text-emerald-400" />
                  <span className="text-emerald-400">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3" />
                  <span>Copy JSON</span>
                </>
              )}
            </button>
          </div>
          <pre className="p-3 font-mono text-[10px] text-[#f3ca78] overflow-x-auto max-h-48 leading-relaxed">
            {JSON.stringify(event.details, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
