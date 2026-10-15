import * as React from "react";
import Link from "next/link";
import { ArrowIcon } from "@/components/brand/icons";
import { buttonClasses } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/**
 * Shared scaffolding for onboarding screens. The source app used absolute
 * pixel offsets inside an 820px phone frame; here the same rhythm becomes a
 * responsive, naturally flowing centered column.
 */
export function FlowShell({
  children,
  className,
  as: Tag = "div",
}: {
  children: React.ReactNode;
  className?: string;
  as?: "div" | "section";
}) {
  return (
    <Tag
      className={cn(
        "mx-auto flex w-full max-w-xl flex-col items-center px-5 pb-16 pt-10 text-center sm:px-8 sm:pt-14",
        className,
      )}
    >
      {children}
    </Tag>
  );
}

/** Fixed-height visual slot so copy never jumps between states. */
export function FlowVisual({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "relative flex w-full items-center justify-center",
        className ?? "min-h-[240px]",
      )}
    >
      {children}
    </div>
  );
}

export function FlowTag({ children }: { children: React.ReactNode }) {
  return <span className="tag mt-8">{children}</span>;
}

export function FlowTitle({
  children,
  className,
  id,
}: {
  children: React.ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <h1
      id={id}
      className={cn(
        "mt-5 max-w-lg text-balance text-3xl font-medium leading-tight tracking-[-0.04em] sm:text-4xl",
        className,
      )}
    >
      {children}
    </h1>
  );
}

export function FlowBody({ children }: { children: React.ReactNode }) {
  return <p className="mt-4 max-w-md text-sm leading-relaxed text-[#a7b0c1] sm:text-base">{children}</p>;
}

/** Action row pinned under the content (never absolutely positioned). */
export function FlowActions({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "mt-8 flex w-full max-w-sm flex-col items-stretch gap-2.5 sm:flex-row sm:items-center sm:justify-center",
        className,
      )}
    >
      {children}
    </div>
  );
}

/** "Back to domains"-style secondary link with arrow. */
export function FlowBackLink({
  href,
  children,
}: {
  href: string;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className={buttonClasses("ghost", "sm", "mx-auto mt-6 text-[#a7b0c1]")}
    >
      <ArrowIcon className="rotate-180" />
      <span>{children}</span>
    </Link>
  );
}

/** Primary continue button matching the source's button rhythm. */
export function FlowContinue({
  children,
  disabled,
  onClick,
  type = "button",
  href,
}: {
  children: React.ReactNode;
  disabled?: boolean;
  onClick?: () => void;
  type?: "button" | "submit";
  href?: string;
}) {
  if (href) {
    return (
      <Link href={href} className={buttonClasses("primary", "lg", "w-full sm:w-auto")}>
        <span>{children}</span>
        <ArrowIcon />
      </Link>
    );
  }
  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={buttonClasses("primary", "lg", "w-full sm:w-auto")}
    >
      <span>{children}</span>
      <ArrowIcon />
    </button>
  );
}

/** 6-dot story progress (source: Splash progress dots). */
export function StepDots({
  total,
  active,
  ariaLabel,
}: {
  total: number;
  active: number;
  ariaLabel: string;
}) {
  return (
    <div className="progress-dots" role="img" aria-label={ariaLabel}>
      {Array.from({ length: total }, (_, index) => (
        <i key={index} className={index === active ? "active" : undefined} />
      ))}
    </div>
  );
}
