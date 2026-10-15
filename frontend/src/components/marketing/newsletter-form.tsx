"use client";

import * as React from "react";
import { toast } from "sonner";
import { footerCopy } from "@/content/marketing";

/** Footer opt-in: validated client-side, POSTs to /api/newsletter. */
export function NewsletterForm() {
  const [email, setEmail] = React.useState("");
  const [busy, setBusy] = React.useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (busy) return;
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email.trim())) {
      toast.error(footerCopy.newsletter.error);
      return;
    }
    setBusy(true);
    try {
      const res = await fetch("/api/newsletter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim() }),
      });
      if (!res.ok) {
        const data = (await res.json().catch(() => ({}))) as { error?: string };
        toast.error(data.error ?? footerCopy.newsletter.error);
        return;
      }
      toast.success(footerCopy.newsletter.success);
      setEmail("");
    } catch {
      toast.error(footerCopy.newsletter.error);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="w-full max-w-sm" aria-label={footerCopy.newsletter.label}>
      <label htmlFor="newsletter-email" className="text-xs font-semibold uppercase tracking-[0.12em] text-subtle">
        {footerCopy.newsletter.label}
      </label>
      <div className="mt-2 flex gap-2">
        <input
          id="newsletter-email"
          type="email"
          name="email"
          autoComplete="email"
          placeholder={footerCopy.newsletter.placeholder}
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="h-10 w-full min-w-0 rounded-xl border border-border-strong bg-surface px-3.5 text-sm text-foreground placeholder:text-subtle focus:border-gold focus:outline-none"
        />
        <button
          type="submit"
          disabled={busy}
          className="h-10 flex-none rounded-xl bg-brand px-4 text-sm font-semibold text-white transition-colors hover:bg-brand-hover disabled:opacity-60"
        >
          {footerCopy.newsletter.submit}
        </button>
      </div>
    </form>
  );
}
