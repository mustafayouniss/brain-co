"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface TabItem {
  id: string;
  label: string;
}

interface TabsProps {
  items: TabItem[];
  activeId: string;
  onChange: (id: string) => void;
  className?: string;
  ariaLabel: string;
}

/** WAI-ARIA tabs with roving tabindex + arrow-key navigation. */
export function Tabs({ items, activeId, onChange, className, ariaLabel }: TabsProps) {
  const refs = React.useRef<Record<string, HTMLButtonElement | null>>({});

  const onKeyDown = (event: React.KeyboardEvent) => {
    const index = items.findIndex((item) => item.id === activeId);
    let next = index;
    if (event.key === "ArrowRight") next = (index + 1) % items.length;
    else if (event.key === "ArrowLeft") next = (index - 1 + items.length) % items.length;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = items.length - 1;
    else return;
    event.preventDefault();
    const target = items[next];
    onChange(target.id);
    refs.current[target.id]?.focus();
  };

  return (
    <div
      role="tablist"
      aria-label={ariaLabel}
      onKeyDown={onKeyDown}
      className={cn(
        "flex gap-1 overflow-x-auto border-b border-border [scrollbar-width:none] [&::-webkit-scrollbar]:hidden",
        className,
      )}
    >
      {items.map((item) => {
        const active = item.id === activeId;
        return (
          <button
            key={item.id}
            ref={(el) => {
              refs.current[item.id] = el;
            }}
            type="button"
            role="tab"
            id={`tab-${item.id}`}
            aria-selected={active}
            aria-controls={`panel-${item.id}`}
            tabIndex={active ? 0 : -1}
            onClick={() => onChange(item.id)}
            className={cn(
              "relative -mb-px flex-none whitespace-nowrap border-b-2 px-1 py-3.5 text-sm transition-colors",
              active
                ? "border-gold text-foreground"
                : "border-transparent text-muted hover:text-foreground",
            )}
          >
            {item.label}
          </button>
        );
      })}
    </div>
  );
}

export function TabPanel({
  id,
  active,
  children,
  className,
}: {
  id: string;
  active: boolean;
  children: React.ReactNode;
  className?: string;
}) {
  if (!active) return null;
  return (
    <div
      role="tabpanel"
      id={`panel-${id}`}
      aria-labelledby={`tab-${id}`}
      tabIndex={0}
      className={cn("focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-ring", className)}
    >
      {children}
    </div>
  );
}
