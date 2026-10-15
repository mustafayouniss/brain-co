import * as React from "react";
import { cn } from "@/lib/utils";

export function Card({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-border bg-surface p-5 sm:p-6",
        className,
      )}
      {...props}
    />
  );
}

export function CardTitle({
  className,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn("text-base font-semibold tracking-tight", className)}
      {...props}
    />
  );
}

export function CardDescription({
  className,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn("text-sm leading-relaxed text-muted", className)} {...props} />;
}

type BadgeVariant = "available" | "planned" | "brand" | "success" | "danger";

const badgeStyles: Record<BadgeVariant, string> = {
  available: "border-gold text-gold",
  planned: "border-border-strong text-muted",
  brand: "border-[color-mix(in_srgb,var(--brand)_55%,transparent)] text-ring",
  success: "border-[color-mix(in_srgb,var(--success)_55%,transparent)] text-success",
  danger: "border-[color-mix(in_srgb,var(--danger)_55%,transparent)] text-danger",
};

export function Badge({
  variant = "planned",
  className,
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { variant?: BadgeVariant }) {
  return (
    <span
      className={cn(
        "inline-flex min-h-6 items-center justify-center rounded-full border px-2.5 text-[10px] font-bold uppercase tracking-[0.09em]",
        badgeStyles[variant],
        className,
      )}
      {...props}
    />
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("skeleton h-4 w-full", className)} aria-hidden="true" />;
}
