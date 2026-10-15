"use client";

import * as React from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { cookieCopy } from "@/content/marketing";
import { site } from "@/content/site";

const CONSENT_KEY = "brainco:cookie-consent";

/**
 * Cookie consent banner. Rendered only when analytics is configured
 * (NEXT_PUBLIC_GA_ID) — without tracking there is nothing to consent to.
 */
export function CookieConsent() {
  const [visible, setVisible] = React.useState(false);

  React.useEffect(() => {
    if (!site.gaId) return;
    const stored = window.localStorage.getItem(CONSENT_KEY);
    if (!stored) {
      const timer = window.setTimeout(() => setVisible(true), 1200);
      return () => window.clearTimeout(timer);
    }
  }, []);

  const decide = (value: "granted" | "denied") => {
    window.localStorage.setItem(CONSENT_KEY, value);
    setVisible(false);
  };

  if (!site.gaId) return null;

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          role="region"
          aria-label={cookieCopy.title}
          initial={{ y: 80, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 80, opacity: 0 }}
          transition={{ duration: 0.35, ease: [0.2, 0.8, 0.2, 1] }}
          className="fixed inset-x-4 bottom-4 z-40 mx-auto max-w-xl rounded-2xl border border-border bg-elevated p-5 shadow-[0_24px_60px_rgba(0,0,0,0.45)]"
        >
          <h2 className="text-sm font-semibold">{cookieCopy.title}</h2>
          <p className="mt-1.5 text-sm leading-relaxed text-muted">{cookieCopy.body}</p>
          <div className="mt-4 flex flex-wrap items-center gap-2.5">
            <button
              type="button"
              onClick={() => decide("granted")}
              className="min-h-10 rounded-xl bg-brand px-4 text-sm font-semibold text-white transition-colors hover:bg-brand-hover"
            >
              {cookieCopy.accept}
            </button>
            <button
              type="button"
              onClick={() => decide("denied")}
              className="min-h-10 rounded-xl border border-border-strong px-4 text-sm font-semibold text-muted transition-colors hover:text-foreground"
            >
              {cookieCopy.decline}
            </button>
            <Link
              href="/privacy"
              className="ml-auto text-xs text-subtle underline underline-offset-4 hover:text-foreground"
            >
              {cookieCopy.policy}
            </Link>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
