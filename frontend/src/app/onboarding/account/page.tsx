"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { AlertCircle } from "lucide-react";
import { accountCopy, type AccountMode } from "@/content/app";
import { authCopy } from "@/content/marketing";
import { accountSchema, type AccountInput } from "@/lib/validation";
import { FlowBody, FlowShell, FlowTitle } from "@/components/onboarding/flow";
import { PrototypeBadge } from "@/components/auth/prototype-badge";
import { PasswordInput } from "@/components/auth/password-input";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/input";
import { useOnboarding } from "@/hooks/use-onboarding";

const copy = accountCopy;

/**
 * Account registration (source view `AccountScreen`). "Company name" is
 * required only for the Company account mode, exactly like the source app.
 * MOCK: `POST /api/auth/register` is a simulated endpoint — success is only
 * shown after it responds ok; server field errors are surfaced per field.
 */
export default function AccountScreen() {
  const router = useRouter();
  const { state, update, hydrated } = useOnboarding();
  const accountMode: AccountMode | null = state.accountMode;
  const requireCompany = accountMode === "company";

  // Deep-link/refresh guards: domain → account mode → registration.
  React.useEffect(() => {
    if (!hydrated) return;
    if (!state.domain) router.replace("/onboarding/domains");
    else if (!state.accountMode) router.replace("/onboarding/usage");
  }, [hydrated, state.domain, state.accountMode, router]);

  if (!hydrated || !state.domain || !accountMode) return null;

  return (
    <RegistrationForm
      requireCompany={requireCompany}
      accountMode={accountMode}
      onDone={(account) => {
        update({ account });
        toast.success("Account details saved (prototype).");
        router.push("/onboarding/survey");
      }}
    />
  );
}

function RegistrationForm({
  requireCompany,
  accountMode,
  onDone,
}: {
  requireCompany: boolean;
  accountMode: AccountMode;
  onDone: (account: {
    fullName: string;
    email: string;
    companyName?: string;
  }) => void;
}) {
  const [serverError, setServerError] = React.useState<string | null>(null);
  const router = useRouter();
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<AccountInput>({
    resolver: zodResolver(accountSchema(requireCompany)),
    defaultValues: {
      companyName: "",
      fullName: "",
      email: "",
      password: "",
      confirmPassword: "",
    },
  });

  async function onSubmit(values: AccountInput) {
    if (isSubmitting) return; // hard guard against double submit
    setServerError(null);
    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          accountMode,
          fullName: values.fullName,
          email: values.email,
          password: values.password,
          confirmPassword: values.confirmPassword,
          companyName: values.companyName,
        }),
      });
      if (!res.ok) {
        const data = (await res.json().catch(() => ({}))) as {
          error?: string;
          fields?: Record<string, string>;
        };
        if (data.fields) {
          for (const [name, message] of Object.entries(data.fields)) {
            setError(name as keyof AccountInput, { message });
          }
        }
        setServerError(data.error ?? authCopy.login.networkError);
        return;
      }
      onDone({
        fullName: values.fullName.trim(),
        email: values.email.trim(),
        ...(values.companyName?.trim() ? { companyName: values.companyName.trim() } : {}),
      });
    } catch {
      setServerError(authCopy.login.networkError);
    }
  }

  return (
    <FlowShell as="section">
      <PrototypeBadge className="mt-8" />
      <FlowTitle id="account-title" className="mt-5">
        {copy.title}
      </FlowTitle>
      <FlowBody>
        {copy.prototypeNote}
      </FlowBody>

      <form
        onSubmit={handleSubmit(onSubmit)}
        noValidate
        className="mt-8 w-full max-w-sm text-left"
      >
        <div className="flex flex-col gap-4">
          {requireCompany && (
            <Field
              label={copy.fields.companyName}
              htmlFor="account-company"
              error={errors.companyName?.message}
            >
              <Input
                id="account-company"
                autoComplete="organization"
                placeholder="Acme Legal"
                aria-invalid={errors.companyName ? true : undefined}
                aria-describedby={errors.companyName ? "account-company-error" : undefined}
                disabled={isSubmitting}
                {...register("companyName")}
              />
            </Field>
          )}

          <Field
            label={copy.fields.fullName}
            htmlFor="account-name"
            error={errors.fullName?.message}
          >
            <Input
              id="account-name"
              autoComplete="name"
              placeholder="Your full name"
              aria-invalid={errors.fullName ? true : undefined}
              aria-describedby={errors.fullName ? "account-name-error" : undefined}
              disabled={isSubmitting}
              {...register("fullName")}
            />
          </Field>

          <Field
            label={copy.fields.email}
            htmlFor="account-email"
            error={errors.email?.message}
          >
            <Input
              id="account-email"
              type="email"
              autoComplete="email"
              inputMode="email"
              placeholder="you@company.com"
              aria-invalid={errors.email ? true : undefined}
              aria-describedby={errors.email ? "account-email-error" : undefined}
              disabled={isSubmitting}
              {...register("email")}
            />
          </Field>

          <Field
            label={copy.fields.password}
            htmlFor="account-password"
            error={errors.password?.message}
          >
            <PasswordInput
              id="account-password"
              autoComplete="new-password"
              placeholder="••••••••"
              aria-invalid={errors.password ? true : undefined}
              aria-describedby={errors.password ? "account-password-error" : undefined}
              disabled={isSubmitting}
              {...register("password")}
            />
          </Field>

          <Field
            label={copy.fields.confirmPassword}
            htmlFor="account-confirm"
            error={errors.confirmPassword?.message}
          >
            <Input
              id="account-confirm"
              type="password"
              autoComplete="new-password"
              placeholder="••••••••"
              aria-invalid={errors.confirmPassword ? true : undefined}
              aria-describedby={errors.confirmPassword ? "account-confirm-error" : undefined}
              disabled={isSubmitting}
              {...register("confirmPassword")}
            />
          </Field>
        </div>

        {serverError && (
          <p
            role="alert"
            className="mt-4 flex items-start gap-2 rounded-xl border border-danger/40 bg-danger/10 px-3.5 py-2.5 text-sm text-danger"
          >
            <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
            <span>{serverError}</span>
          </p>
        )}

        <Button type="submit" size="lg" disabled={isSubmitting} className="mt-6 w-full">
          {isSubmitting ? copy.submitting : copy.submit}
        </Button>
      </form>

      <p className="mt-6 text-sm text-[#a7b0c1]">
        {copy.loginLead}{" "}
        <Link
          href="/login"
          className="font-semibold text-white underline-offset-4 hover:underline"
        >
          {copy.loginLink}
        </Link>
      </p>

      <Button variant="ghost" size="sm" onClick={() => router.back()} className="mt-2">
        Back
      </Button>
    </FlowShell>
  );
}
