import * as React from "react";
import { cn } from "@/lib/utils";

const base =
  "w-full rounded-xl border border-border-strong bg-surface px-3.5 text-sm text-foreground " +
  "placeholder:text-subtle transition-colors focus:border-gold focus:outline-none " +
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring disabled:opacity-60";

export const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className, ...props }, ref) => (
  <input ref={ref} className={cn(base, "h-11", className)} {...props} />
));
Input.displayName = "Input";

export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(base, "min-h-32 resize-y py-3 leading-relaxed", className)}
    {...props}
  />
));
Textarea.displayName = "Textarea";

export function Label({
  className,
  ...props
}: React.LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      className={cn("text-[13px] font-semibold text-muted", className)}
      {...props}
    />
  );
}

/** Inline field error announced to assistive tech. */
export function FieldError({
  id,
  children,
}: {
  id?: string;
  children: React.ReactNode;
}) {
  if (!children) return null;
  return (
    <p id={id} role="alert" className="text-xs font-medium text-danger">
      {children}
    </p>
  );
}

/** Labelled form field wrapper used across auth + onboarding forms. */
export function Field({
  label,
  htmlFor,
  error,
  children,
  className,
}: {
  label: string;
  htmlFor?: string;
  error?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <Label htmlFor={htmlFor}>{label}</Label>
      {children}
      <FieldError id={htmlFor ? `${htmlFor}-error` : undefined}>{error}</FieldError>
    </div>
  );
}
