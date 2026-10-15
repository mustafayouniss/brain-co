import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind classes with conflict resolution. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Input sanitization used by API routes before storing or reflecting
 * user-supplied text (contact form, auth, survey payloads).
 */
export function sanitizeText(value: string, maxLength = 4000): string {
  return value
    .replace(/[<>]/g, "")
    .replace(/javascript:/gi, "")
    .trim()
    .slice(0, maxLength);
}

/** Basic email shape check mirroring the Zod schema. */
export function isEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(value.trim());
}

/** Smoothly scroll to a hash target (marketing anchors like /#faq). */
export function scrollToHash(hash: string): void {
  if (typeof document === "undefined") return;
  const el = document.querySelector(hash);
  if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
}
