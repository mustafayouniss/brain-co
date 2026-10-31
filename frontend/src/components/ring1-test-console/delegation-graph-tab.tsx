"use client";

import * as React from "react";
import { CheckCircle2, AlertTriangle, ShieldAlert, Loader2, Sparkles, Database, Layers, Search, Brain, Eye } from "lucide-react";
import { DelegationEdge, TestRunEvent } from "./types";

interface DelegationGraphTabProps {
  events: TestRunEvent[];
  delegationEdges: DelegationEdge[];
  invokedEngines: string[];
}

interface EngineNodeConfig {
  id: string;
  name: string;
  role: string;
  icon: React.ComponentType<{ className?: string }>;
  x: number; // percentage in SVG viewport
  y: number;
}

const ENGINES: EngineNodeConfig[] = [
  { id: "perception", name: "Perception", role: "Input Structuring & Parsing", icon: Eye, x: 18, y: 22 },
  { id: "observation", name: "Observation", role: "Event Capture & Idempotency", icon: Sparkles, x: 50, y: 22 },
  { id: "context", name: "Context", role: "Case Boundary Resolution", icon: Layers, x: 82, y: 22 },
  { id: "memory", name: "Basic Memory", role: "Scoped PostgreSQL Storage", icon: Database, x: 18, y: 78 },
  { id: "retrieval", name: "Basic Retrieval", role: "Case-Scoped Search & Isolation", icon: Search, x: 50, y: 78 },
  { id: "planning", name: "Planning", role: "Multi-Step & Replan Lifecycle", icon: Brain, x: 82, y: 78 },
];

export function DelegationGraphTab({ events, delegationEdges, invokedEngines }: DelegationGraphTabProps) {
  // Compute real status per engine based on actual recorded events
  const engineStatuses = React.useMemo(() => {
    const statuses: Record<string, "idle" | "running" | "completed" | "failed" | "denied"> = {};
    for (const eng of ENGINES) {
      if (!invokedEngines.includes(eng.id)) {
        statuses[eng.id] = "idle";
        continue;
      }
      // Check latest event targeting this engine
      const relevant = events.filter((e) => e.destination_engine === eng.id);
      if (relevant.length === 0) {
        statuses[eng.id] = "idle";
        continue;
      }
      const last = relevant[relevant.length - 1];
      statuses[eng.id] = last.status as any;
    }
    return statuses;
  }, [events, invokedEngines]);

  return (
    <div className="flex flex-col h-full space-y-3">
      {/* Top Banner & Status Legend */}
      <div className="flex items-center justify-between px-3 py-2 rounded-xl bg-surface/80 border border-border/70 text-xs">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-white">Peer-to-Peer Mesh Graph</span>
          <span className="text-[11px] text-[#8a94a8]">
            ({delegationEdges.length} active delegation edges observed)
          </span>
        </div>
        <div className="flex items-center gap-3 text-[10px]">
          <span className="flex items-center gap-1 text-emerald-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400" /> Completed
          </span>
          <span className="flex items-center gap-1 text-violet">
            <span className="w-2 h-2 rounded-full bg-brand animate-pulse" /> Running
          </span>
          <span className="flex items-center gap-1 text-amber-300">
            <span className="w-2 h-2 rounded-full bg-amber-400" /> Denied
          </span>
          <span className="flex items-center gap-1 text-red-300">
            <span className="w-2 h-2 rounded-full bg-red-400" /> Failed
          </span>
          <span className="flex items-center gap-1 text-[#8a94a8]">
            <span className="w-2 h-2 rounded-full bg-border" /> Not Invoked
          </span>
        </div>
      </div>

      {/* Interactive Visual Graph Canvas */}
      <div className="relative flex-1 min-h-[340px] rounded-2xl border border-border/80 bg-[#050b1a]/90 backdrop-blur-md overflow-hidden p-4">
        {/* SVG Drawing Layer for Real Edges */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <marker
              id="arrow-success"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#8adabc" />
            </marker>
            <marker
              id="arrow-brand"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#946eff" />
            </marker>
            <linearGradient id="edge-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#8052ff" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#8adabc" stopOpacity="0.8" />
            </linearGradient>
          </defs>

          {/* Render Actual Recorded Delegation Edges */}
          {delegationEdges.map((edge, idx) => {
            const srcNode = ENGINES.find((e) => e.id === edge.source);
            const tgtNode = ENGINES.find((e) => e.id === edge.target);
            if (!srcNode || !tgtNode) return null;

            return (
              <g key={`${edge.source}-${edge.target}-${idx}`}>
                <line
                  x1={`${srcNode.x}%`}
                  y1={`${srcNode.y}%`}
                  x2={`${tgtNode.x}%`}
                  y2={`${tgtNode.y}%`}
                  stroke="url(#edge-gradient)"
                  strokeWidth="2.5"
                  strokeDasharray="4 3"
                  markerEnd="url(#arrow-success)"
                  className="animate-pulse"
                />
              </g>
            );
          })}
        </svg>

        {/* Nodes Layer */}
        <div className="relative w-full h-full">
          {ENGINES.map((eng) => {
            const status = engineStatuses[eng.id] || "idle";
            const isInvoked = invokedEngines.includes(eng.id);
            const Icon = eng.icon;

            const getBorderAndBg = () => {
              switch (status) {
                case "completed":
                  return "border-emerald-500/80 bg-emerald-950/40 shadow-lg shadow-emerald-500/10 text-white";
                case "running":
                  return "border-brand bg-brand/20 shadow-lg shadow-brand/20 ring-2 ring-brand/40 animate-pulse text-white";
                case "failed":
                  return "border-red-500/80 bg-red-950/40 shadow-lg shadow-red-500/10 text-white";
                case "denied":
                  return "border-amber-500/80 bg-amber-950/40 shadow-lg shadow-amber-500/10 text-white";
                default:
                  return "border-border/60 bg-surface/40 text-[#8a94a8] opacity-60";
              }
            };

            const getStatusIcon = () => {
              switch (status) {
                case "completed":
                  return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />;
                case "running":
                  return <Loader2 className="w-3.5 h-3.5 text-violet animate-spin" />;
                case "failed":
                  return <AlertTriangle className="w-3.5 h-3.5 text-red-400" />;
                case "denied":
                  return <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />;
                default:
                  return <span className="w-2 h-2 rounded-full bg-border" />;
              }
            };

            return (
              <div
                key={eng.id}
                style={{
                  left: `${eng.x}%`,
                  top: `${eng.y}%`,
                  transform: "translate(-50%, -50%)",
                }}
                className={`absolute z-10 flex flex-col items-center justify-center p-3 rounded-2xl border transition-all duration-300 w-36 sm:w-44 text-center ${getBorderAndBg()}`}
              >
                <div className="flex items-center justify-between w-full mb-1">
                  <div className="p-1 rounded-lg bg-surface/80 border border-border/60">
                    <Icon className="w-4 h-4 text-brand-hover" />
                  </div>
                  <div className="flex items-center gap-1 font-mono text-[9px] uppercase tracking-wider font-semibold">
                    {getStatusIcon()}
                    <span>{status}</span>
                  </div>
                </div>

                <div className="text-xs font-bold truncate w-full text-white">
                  {eng.name}
                </div>
                <div className="text-[10px] text-[#9ba5b9] line-clamp-1 mt-0.5">
                  {eng.role}
                </div>

                <div className="mt-1.5 pt-1 border-t border-border/40 w-full flex items-center justify-center gap-1 text-[9px] text-[#8a94a8]">
                  <span>{isInvoked ? "Invoked" : "Skipped"}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
