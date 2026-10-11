"use client";

import { useTheme } from "next-themes";
import { useMounted } from "@/lib/use-mounted";

/** Light/dark switch (next-themes). Renders a stable placeholder pre-hydration. */
export function ThemeToggle({ className }: { className?: string }) {
  const { resolvedTheme, setTheme } = useTheme();
  const mounted = useMounted();

  const isDark = resolvedTheme === "dark";
  // Gate both icon AND label on `mounted` so the server-rendered markup matches
  // the first client render (resolvedTheme is undefined during SSR), avoiding a
  // hydration mismatch on the aria-label/title.
  const label = mounted
    ? isDark
      ? "Switch to light mode"
      : "Switch to dark mode"
    : "Toggle theme";

  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className={
        className ??
        "grid h-9 w-9 place-items-center rounded-full border border-border bg-surface text-muted transition-colors hover:border-border-strong hover:text-foreground"
      }
    >
      <span aria-hidden="true" className="relative block h-4 w-4">
        {mounted ? (
          isDark ? (
            // Sun
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round">
              <circle cx="12" cy="12" r="4.2" />
              <path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5 5l1.4 1.4M17.6 17.6L19 19M19 5l-1.4 1.4M6.4 17.6L5 19" />
            </svg>
          ) : (
            // Moon
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 14.5A8.2 8.2 0 0 1 9.5 4 8.5 8.5 0 1 0 20 14.5Z" />
            </svg>
          )
        ) : (
          <span className="block h-4 w-4 rounded-full border border-current opacity-40" />
        )}
      </span>
    </button>
  );
}
