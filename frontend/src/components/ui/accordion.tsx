"use client";

import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "@/lib/utils";

export interface AccordionItemData {
  q: string;
  a: string;
}

/** Accessible FAQ accordion: buttons with aria-expanded, animated panels. */
export function Accordion({
  items,
  className,
}: {
  items: readonly AccordionItemData[];
  className?: string;
}) {
  const [open, setOpen] = React.useState<number | null>(0);

  return (
    <div className={cn("divide-y divide-border border-y border-border", className)}>
      {items.map((item, index) => {
        const expanded = open === index;
        const panelId = `faq-panel-${index}`;
        const buttonId = `faq-button-${index}`;
        return (
          <div key={item.q}>
            <h3>
              <button
                type="button"
                id={buttonId}
                aria-expanded={expanded}
                aria-controls={panelId}
                onClick={() => setOpen(expanded ? null : index)}
                className="flex w-full items-start justify-between gap-6 py-5 text-left text-base font-medium text-foreground transition-colors hover:text-[var(--ring)]"
              >
                <span>{item.q}</span>
                <span
                  aria-hidden="true"
                  className={cn(
                    "mt-1 grid h-6 w-6 flex-none place-items-center rounded-full border border-border-strong text-sm transition-transform duration-300",
                    expanded && "rotate-45 border-gold text-gold",
                  )}
                >
                  +
                </span>
              </button>
            </h3>
            <AnimatePresence initial={false}>
              {expanded && (
                <motion.div
                  id={panelId}
                  role="region"
                  aria-labelledby={buttonId}
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: [0.2, 0.8, 0.2, 1] }}
                  className="overflow-hidden"
                >
                  <p className="pb-6 pr-10 text-sm leading-relaxed text-muted">
                    {item.a}
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}
    </div>
  );
}
