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
      <label htmlFor="newsletter-email" className="text-xs font-mono uppercase tracking-[0.14em] text-zinc-400">
        {footerCopy.newsletter.label}
      </label>
      <div className="mt-2.5 flex gap-2">
        <input
          id="newsletter-email"
          type="email"
          name="email"
          autoComplete="email"
          placeholder={footerCopy.newsletter.placeholder}
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="h-10 w-full min-w-0 rounded-full border border-white/10 bg-white/[0.03] px-4 text-xs font-mono text-white placeholder:text-zinc-600 transition-colors focus:border-cyan-400/50 focus:outline-none focus:ring-1 focus:ring-cyan-400/20"
        />
        <button
          type="submit"
          disabled={busy}
          className="h-10 flex-none rounded-full bg-white px-4 text-xs font-semibold text-black transition-all hover:bg-zinc-200 disabled:opacity-50"
        >
          {footerCopy.newsletter.submit}
        </button>
      </div>
    </form>
  );
}
