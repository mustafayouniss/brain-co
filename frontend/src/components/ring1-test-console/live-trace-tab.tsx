"use client";

import * as React from "react";
import { ArrowRight, CheckCircle2, Clock, AlertTriangle, ShieldAlert, Loader2, Search } from "lucide-react";
import { TestRunEvent } from "./types";

interface LiveTraceTabProps {
  events: TestRunEvent[];
  selectedEvent: TestRunEvent | null;
  onSelectEvent: (event: TestRunEvent) => void;
}

export function LiveTraceTab({ events, selectedEvent, onSelectEvent }: LiveTraceTabProps) {
  const [filterText, setFilterText] = React.useState("");
  const [filterEngine, setFilterEngine] = React.useState<string>("all");

  const filteredEvents = React.useMemo(() => {
    return events.filter((evt) => {
      if (filterEngine !== "all") {
        if (evt.destination_engine !== filterEngine && evt.source_engine !== filterEngine) {
          return false;
        }
      }
      if (filterText) {
        const query = filterText.toLowerCase();
        const str = `${evt.capability} ${evt.event_type} ${evt.source_engine} ${evt.destination_engine} ${JSON.stringify(evt.details || {})}`.toLowerCase();
        if (!str.includes(query)) return false;
      }
      return true;
    });
  }, [events, filterText, filterEngine]);

  const getStatusBadge = (status: TestRunEvent["status"]) => {
    switch (status) {
      case "completed":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
            <CheckCircle2 className="w-3 h-3" />
            COMPLETED
          </span>
        );
      case "running":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-brand/20 text-violet border border-brand/40 animate-pulse">
            <Loader2 className="w-3 h-3 animate-spin" />
            RUNNING
          </span>
        );
      case "failed":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-red-500/15 text-red-300 border border-red-500/30">
            <AlertTriangle className="w-3 h-3" />
            FAILED
          </span>
        );
      case "denied":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">
            <ShieldAlert className="w-3 h-3" />
            DENIED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-surface-2 text-[#9ba5b9] border border-border">
            {status.toUpperCase()}
          </span>
        );
    }
  };

  const formatTimestamp = (iso: string) => {
    try {
      const d = new Date(iso);
      return d.toLocaleTimeString([], { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" }) +
        "." + String(d.getMilliseconds()).padStart(3, "0");
    } catch {
      return iso;
    }
  };

  return (
    <div className="flex flex-col h-full space-y-3">
      {/* Search and Filters */}
      <div className="flex items-center gap-2 pt-1">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#8a94a8]" />
          <input
            type="text"
            placeholder="Filter events, capabilities, or payloads..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 text-xs rounded-lg border border-border/80 bg-surface/80 text-white placeholder-[#8a94a8] focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
          />
        </div>
        <select
          value={filterEngine}
          onChange={(e) => setFilterEngine(e.target.value)}
          className="text-xs py-1.5 px-2.5 rounded-lg border border-border/80 bg-surface/80 text-white focus:border-brand focus:outline-none"
        >
          <option value="all">All Engines</option>
          <option value="perception">Perception</option>
          <option value="observation">Observation</option>
          <option value="context">Context</option>
          <option value="memory">Memory</option>
          <option value="retrieval">Retrieval</option>
          <option value="planning">Planning</option>
        </select>
      </div>

      {/* Events List */}
      <div className="flex-1 overflow-y-auto pr-1 space-y-2 max-h-[380px]">
        {filteredEvents.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 rounded-xl border border-dashed border-border/60 text-center p-4">
            <Clock className="w-8 h-8 text-[#8a94a8] mb-2 stroke-[1.5]" />
            <p className="text-xs font-medium text-white">No execution events found</p>
            <p className="text-[11px] text-[#8a94a8] mt-1">
              Click &quot;Run Integration Test&quot; or &quot;Force Failure &amp; Replan&quot; to begin a live run.
            </p>
          </div>
        ) : (
          filteredEvents.map((evt) => {
            const isSelected = selectedEvent?.sequence === evt.sequence;
            return (
              <div
                key={evt.sequence}
                onClick={() => onSelectEvent(evt)}
                className={`group relative flex flex-col gap-1.5 p-2.5 rounded-xl border text-xs cursor-pointer transition-all ${
                  isSelected
                    ? "border-brand bg-brand/10 shadow-md shadow-brand/10"
                    : "border-border/70 bg-surface/60 hover:border-brand/50 hover:bg-surface-2"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="flex items-center justify-center px-1.5 py-0.5 rounded font-mono text-[10px] font-bold bg-surface-2 text-[#9ba5b9] border border-border">
                      #{evt.sequence}
                    </span>
                    <span className="font-mono text-[10px] text-[#8a94a8]">
                      {formatTimestamp(evt.timestamp)}
                    </span>
                    <span className="font-semibold text-white">
                      {evt.event_type.replace(/_/g, " ").toUpperCase()}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    {evt.duration_ms !== undefined && evt.duration_ms !== null && (
                      <span className="font-mono text-[10px] text-[#8a94a8]">
                        {evt.duration_ms} ms
                      </span>
                    )}
                    {getStatusBadge(evt.status)}
                  </div>
                </div>

                {/* Routing & Capability path */}
                <div className="flex items-center gap-1.5 text-[11px] text-[#9ba5b9]">
                  <span className="px-1.5 py-0.5 rounded bg-surface border border-border/60 text-white font-medium">
                    {evt.source_engine}
                  </span>
                  <ArrowRight className="w-3 h-3 text-[#8a94a8] shrink-0" />
                  <span className="px-1.5 py-0.5 rounded bg-surface border border-border/60 text-violet font-mono font-medium">
                    {evt.capability}
                  </span>
                  {evt.plan_version && (
                    <span className="ml-auto px-1.5 py-0.5 rounded bg-surface border border-border/60 text-gold font-mono text-[10px]">
                      v{evt.plan_version}
                    </span>
                  )}
                </div>

                {/* Details snippet */}
                {evt.details && Object.keys(evt.details).length > 0 && (
                  <div className="truncate text-[10px] font-mono text-[#8a94a8] bg-surface/50 rounded px-1.5 py-0.5 border border-border/40">
                    {JSON.stringify(evt.details)}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
