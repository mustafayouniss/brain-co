"use client";

import * as React from "react";
import { createPortal } from "react-dom";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { useMounted } from "@/lib/use-mounted";

interface DialogProps {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
  /** Element id of the visible title (aria-labelledby). */
  labelledBy?: string;
  /** Bottom sheet on small screens, centered card on desktop (default). */
  variant?: "sheet" | "center";
  className?: string;
}

/**
 * Accessible modal dialog: Escape to close, click-outside to close, focus trap,
 * focus restore and scroll lock. Bottom-sheet presentation on mobile mirrors the
 * source app's DiscoverSheet.
 */
export function Dialog({
  open,
  onClose,
  children,
  labelledBy,
  variant = "center",
  className,
}: DialogProps) {
  const panelRef = React.useRef<HTMLDivElement>(null);
  const previousFocus = React.useRef<HTMLElement | null>(null);
  // createPortal needs `document`, which doesn't exist during static
  // prerendering (SSR). Only portal to the body once mounted on the client.
  const mounted = useMounted();

  React.useEffect(() => {
    if (!open) return;
    previousFocus.current = document.activeElement as HTMLElement | null;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const handleKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
        return;
      }
      if (event.key !== "Tab" || !panelRef.current) return;
      const focusables = panelRef.current.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), input, textarea, select, [tabindex]:not([tabindex="-1"])',
      );
      if (focusables.length === 0) return;
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener("keydown", handleKey);
    const focusTimer = window.setTimeout(() => {
      panelRef.current
        ?.querySelector<HTMLElement>("button, a, input, [tabindex]:not([tabindex='-1'])")
        ?.focus();
    }, 30);

    return () => {
      document.removeEventListener("keydown", handleKey);
      document.body.style.overflow = overflow;
      window.clearTimeout(focusTimer);
      previousFocus.current?.focus?.();
    };
  }, [open, onClose]);

  if (!mounted) return null;

  return createPortal(
    <AnimatePresence>
      {open && (
        <motion.div
          className={cn(
            "fixed inset-0 z-50 flex bg-black/75 backdrop-blur-[7px]",
            variant === "sheet" ? "items-end justify-center" : "items-center justify-center p-4",
          )}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.22 }}
          onMouseDown={onClose}
        >
          <motion.div
            ref={panelRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby={labelledBy}
            className={cn(
              "relative max-h-[91dvh] w-full overflow-y-auto border border-border bg-elevated",
              variant === "sheet"
                ? "max-w-[620px] rounded-t-[26px] shadow-[0_-24px_80px_rgba(0,0,0,0.5)]"
                : "max-w-[620px] rounded-[26px] shadow-[0_24px_80px_rgba(0,0,0,0.5)]",
              "bg-[radial-gradient(circle_at_82%_0%,var(--brand-soft),transparent_29%)]",
              className,
            )}
            initial={{ y: variant === "sheet" ? "100%" : 24, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: variant === "sheet" ? "100%" : 24, opacity: 0 }}
            transition={{ duration: 0.32, ease: [0.2, 0.8, 0.2, 1] }}
            onMouseDown={(event) => event.stopPropagation()}
          >
            {variant === "sheet" && (
              <div className="-mt-4 mb-5 flex justify-center" aria-hidden="true">
                <span className="h-1 w-9 rounded-full bg-border-strong" />
              </div>
            )}
            {children}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body,
  );
}

/** Circular close button used inside dialogs. */
export function DialogClose({ onClose }: { onClose: () => void }) {
  return (
    <button
      type="button"
      aria-label="Close dialog"
      onClick={onClose}
      className="absolute right-4 top-4 grid h-9 w-9 place-items-center rounded-full border border-border bg-surface transition-colors hover:border-border-strong"
    >
      <span className="relative block h-3.5 w-3.5" aria-hidden="true">
        <span className="absolute left-0 top-1.5 h-px w-full rotate-45 bg-muted" />
        <span className="absolute left-0 top-1.5 h-px w-full -rotate-45 bg-muted" />
      </span>
    </button>
  );
}
