import * as React from "react";
import { cn } from "@/lib/utils";

/** The Brain-co mark: rounded square holding a 5-dot constellation (CSS). */
export function BrandMark({ className }: { className?: string }) {
  return (
    <span className={cn("brand-mark", className)} aria-hidden="true">
      <i />
      <i />
      <i />
      <i />
      <i />
    </span>
  );
}

export function Wordmark({ className }: { className?: string }) {
  return (
    <span className={cn("flex items-center gap-2.5", className)}>
      <BrandMark />
      <strong className="text-[17px] font-semibold tracking-[-0.03em]">Brain-co</strong>
    </span>
  );
}

export function ArrowIcon({ className }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      fill="none"
      viewBox="0 0 20 20"
      className={cn("h-[18px] w-[18px]", className)}
    >
      <path
        d="M4 10h11M11 6l4 4-4 4"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
      />
    </svg>
  );
}

/** Brain glyph used in the workspace header (from source BrainMark). */
export function BrainMark({ className }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      fill="none"
      viewBox="0 0 24 24"
      className={cn("h-6 w-6", className)}
    >
      <path
        d="M12 4v16M9 5a4 4 0 0 0-3 6 4 4 0 0 0 3 7M15 5a4 4 0 0 1 3 6 4 4 0 0 1-3 7M7 10h2m6 0h2M7 15h2m6 0h2"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
      />
    </svg>
  );
}

/** Upload glyph used by the document drop zone (from source UploadIcon). */
export function UploadIcon({ className }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      fill="none"
      viewBox="0 0 24 24"
      className={cn("h-[30px] w-[30px]", className)}
    >
      <path
        d="M12 16V4m0 0L7 9m5-5 5 5M5 15v5h14v-5"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
      />
    </svg>
  );
}
