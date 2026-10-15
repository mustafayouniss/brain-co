import * as React from "react";
import { cn } from "@/lib/utils";

type Variant =
  | "primary"
  | "white"
  | "secondary"
  | "ghost"
  | "gold"
  | "danger"
  | "link";
type Size = "sm" | "md" | "lg";

const variants: Record<Variant, string> = {
  primary:
    "border border-[#946eff] bg-brand text-brand-fg shadow-[var(--shadow-glow)] hover:bg-brand-hover",
  white:
    "border border-white bg-white text-[#050b1a] hover:bg-[#e9edf5] dark:border-white dark:bg-white dark:text-[#050b1a] dark:hover:bg-[#e9edf5]",
  secondary:
    "border border-border-strong bg-surface text-foreground hover:border-gold hover:bg-surface-2",
  ghost:
    "border border-transparent bg-transparent text-muted hover:text-foreground hover:bg-surface-2",
  gold: "border border-gold bg-transparent text-gold hover:bg-[color-mix(in_srgb,var(--gold)_12%,transparent)]",
  danger:
    "border border-[color-mix(in_srgb,var(--danger)_55%,transparent)] bg-transparent text-danger hover:bg-[color-mix(in_srgb,var(--danger)_12%,transparent)]",
  link: "border-0 bg-transparent p-0 text-muted underline-offset-4 hover:text-foreground hover:underline",
};

const sizes: Record<Size, string> = {
  sm: "min-h-9 px-3.5 text-[13px]",
  md: "min-h-11 px-5 text-sm",
  lg: "min-h-[52px] px-7 text-[15px]",
};

export function buttonClasses(
  variant: Variant = "primary",
  size: Size = "md",
  className?: string,
): string {
  return cn(
    "inline-flex cursor-pointer items-center justify-center gap-2 rounded-xl font-semibold",
    "transition-[transform,background-color,border-color,color] duration-200",
    "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
    "disabled:pointer-events-none disabled:opacity-50",
    "motion-safe:hover:-translate-y-px",
    variants[variant],
    sizes[size],
    className,
  );
}

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

/** Primary interactive primitive. Use `buttonClasses()` for links. */
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", type = "button", ...props }, ref) => (
    <button
      ref={ref}
      type={type}
      className={buttonClasses(variant, size, className)}
      {...props}
    />
  ),
);
Button.displayName = "Button";
