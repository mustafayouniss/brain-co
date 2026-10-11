"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { AlertCircle } from "lucide-react";
import { authCopy } from "@/content/marketing";
import { loginSchema, type LoginInput } from "@/lib/validation";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/input";
import { PasswordInput } from "@/components/auth/password-input";

const copy = authCopy.login;

/**
 * Only same-site absolute paths are accepted as post-login redirects
 * ("/x"), never protocol-relative ("//host") or external URLs.
 */
function safeNext(raw: string | null): string {
  if (raw && raw.startsWith("/") && !raw.startsWith("//") && !raw.startsWith("/\\")) {
    return raw;
  }
  return "/workspace";
}

/**
 * MOCK: there is no real auth backend — `POST /api/auth/login` validates
 * input and issues a simulated session (docs/FLOW_AUDIT.md §5). The form
 * exercises the real client code path (validation, server error surface,
 * double-submit guard, redirect preservation) that a real endpoint will reuse.
 */
export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = safeNext(searchParams.get("next"));
  const [serverError, setServerError] = React.useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  async function onSubmit(values: LoginInput) {
    if (isSubmitting) return; // hard guard against double submit
    setServerError(null);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: values.email, password: values.password }),
      });
      if (!res.ok) {
        const data = (await res.json().catch(() => ({}))) as { error?: string };
        setServerError(data.error ?? copy.invalid);
        return;
      }
      toast.success(copy.success);
      router.push(next);
      router.refresh();
    } catch {
      setServerError(copy.networkError);
    }
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      noValidate
      className="mt-8 w-full max-w-sm text-left"
    >
      <div className="flex flex-col gap-4">
        <Field label={copy.email} htmlFor="login-email" error={errors.email?.message}>
          <Input
            id="login-email"
            type="email"
            autoComplete="email"
            inputMode="email"
            placeholder="you@company.com"
            aria-invalid={errors.email ? true : undefined}
            aria-describedby={errors.email ? "login-email-error" : undefined}
            disabled={isSubmitting}
            {...register("email")}
          />
        </Field>

        <Field
          label={copy.password}
          htmlFor="login-password"
          error={errors.password?.message}
        >
          <PasswordInput
            id="login-password"
            autoComplete="current-password"
            placeholder="••••••••"
            aria-invalid={errors.password ? true : undefined}
            aria-describedby={errors.password ? "login-password-error" : undefined}
            disabled={isSubmitting}
            {...register("password")}
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

      <p className="mt-4 text-center text-xs text-subtle">{copy.demoHint}</p>

      <p className="mt-6 text-center text-sm text-muted">
        {copy.noAccount}{" "}
        <Link
          href="/onboarding/usage"
          className="font-semibold text-foreground underline-offset-4 hover:underline"
        >
          {copy.create}
        </Link>
      </p>
    </form>
  );
}
