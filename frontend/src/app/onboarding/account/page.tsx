"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { AlertCircle, Building2, CheckCircle2, ShieldCheck } from "lucide-react";
import { FlowBody, FlowShell, FlowTitle } from "@/components/onboarding/flow";
import { PrototypeBadge } from "@/components/auth/prototype-badge";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/input";
import { PasswordInput } from "@/components/auth/password-input";
import { useOnboarding } from "@/hooks/use-onboarding";

export default function AccountScreen() {
  const router = useRouter();
  const { state, update, hydrated } = useOnboarding();

  const [companyName, setCompanyName] = React.useState(state.account?.companyName || "");
  const [adminFullName, setAdminFullName] = React.useState(state.account?.fullName || "");
  const [adminEmail, setAdminEmail] = React.useState(state.account?.email || "");
  const [password, setPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const selectedDomain = state.domain || "legal";

  // Deep-link guard: if no domain selected, pick domain first
  React.useEffect(() => {
    if (!hydrated) return;
    if (!state.domain) router.replace("/onboarding/domains");
  }, [hydrated, state.domain, router]);

  if (!hydrated || !state.domain) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!companyName.trim()) {
      setError("Please enter your organization or law firm name.");
      return;
    }
    if (!adminFullName.trim()) {
      setError("Please enter the administrator's full name.");
      return;
    }
    if (!adminEmail.trim() || !adminEmail.includes("@")) {
      setError("Please enter a valid work email address.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          company_name: companyName.trim(),
          admin_full_name: adminFullName.trim(),
          admin_email: adminEmail.trim(),
          password,
          domain: selectedDomain,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "Failed to create organization account");
      }

      // Update local onboarding state
      update({
        domain: selectedDomain,
        account: {
          fullName: adminFullName.trim(),
          email: adminEmail.trim(),
          companyName: companyName.trim(),
        },
      });

      toast.success("Organization workspace initialized successfully!");
      router.push("/workspace");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed. Please check inputs.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <FlowShell as="section" className="max-w-xl">
      <PrototypeBadge className="mt-8" />
      <FlowTitle className="mt-5">
        Create Organization Workspace
      </FlowTitle>
      <FlowBody>
        Register your organization and provision your administrator account.
      </FlowBody>

      {/* Selected Domain Banner */}
      <div className="mt-6 flex w-full items-center justify-between rounded-xl border border-gold/40 bg-gold/5 px-4 py-3 text-left">
        <div className="flex items-center gap-2.5">
          <ShieldCheck className="size-5 text-gold" aria-hidden="true" />
          <div>
            <p className="text-xs font-semibold text-white">
              Selected Domain: <span className="text-gold capitalize">{selectedDomain} Intelligence</span>
            </p>
            <p className="text-[11px] text-[#a7b0c1]">
              Egyptian Civil Law &amp; Case Cognitive Workspace
            </p>
          </div>
        </div>
        <span className="tag tag-available text-[11px]">Active</span>
      </div>

      <form onSubmit={handleSubmit} noValidate className="mt-6 flex w-full flex-col gap-4 text-left">
        <Field label="Organization / Law Firm Name" htmlFor="company-name">
          <div className="relative">
            <Input
              id="company-name"
              type="text"
              placeholder="e.g. Cairo Legal Partners"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              disabled={submitting}
              required
              className="pl-9"
            />
            <Building2 className="pointer-events-none absolute left-3 top-3.5 size-4 text-[#8a94a8]" />
          </div>
        </Field>

        <Field label="Administrator Full Name" htmlFor="admin-name">
          <Input
            id="admin-name"
            type="text"
            placeholder="e.g. Counselor Tarek Mansour"
            value={adminFullName}
            onChange={(e) => setAdminFullName(e.target.value)}
            disabled={submitting}
            required
          />
        </Field>

        <Field label="Administrator Work Email" htmlFor="admin-email">
          <Input
            id="admin-email"
            type="email"
            placeholder="admin@cairolegal.com"
            value={adminEmail}
            onChange={(e) => setAdminEmail(e.target.value)}
            disabled={submitting}
            required
          />
        </Field>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Password" htmlFor="admin-password">
            <PasswordInput
              id="admin-password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={submitting}
              required
            />
          </Field>

          <Field label="Confirm Password" htmlFor="admin-confirm-password">
            <PasswordInput
              id="admin-confirm-password"
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={submitting}
              required
            />
          </Field>
        </div>

        {error && (
          <p
            role="alert"
            className="mt-2 flex items-start gap-2 rounded-xl border border-danger/40 bg-danger/10 px-3.5 py-2.5 text-sm text-danger"
          >
            <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
            <span>{error}</span>
          </p>
        )}

        <Button
          type="submit"
          size="lg"
          disabled={submitting}
          className="mt-4 w-full bg-[#946eff] hover:bg-[#7c3aed]"
        >
          {submitting ? "Provisioning Organization..." : "Create Organization Workspace"}
        </Button>
      </form>

      <div className="mt-6 flex flex-col items-center gap-2 text-xs text-[#8a94a8]">
        <p>
          Already have an account?{" "}
          <Link href="/login" className="font-semibold text-white hover:underline">
            Log in to existing workspace
          </Link>
        </p>
        <button
          type="button"
          onClick={() => router.push("/onboarding/domains")}
          className="text-[#6a748a] hover:text-white hover:underline"
        >
          &larr; Switch business domain
        </button>
      </div>
    </FlowShell>
  );
}
