"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { navCopy } from "@/content/marketing";
import { Wordmark } from "@/components/brand/icons";
import { ThemeToggle } from "@/components/theme-toggle";
import { buttonClasses } from "@/components/ui/button";
import { useSession } from "@/hooks/use-session";
import { cn } from "@/lib/utils";

export function Navbar() {
  const pathname = usePathname();
  const [open, setOpen] = React.useState(false);
  const { user, logout } = useSession();

  // Close the mobile menu on navigation (React-docs "adjust state during
  // render" pattern — no effect needed).
  const [lastPathname, setLastPathname] = React.useState(pathname);
  if (pathname !== lastPathname) {
    setLastPathname(pathname);
    setOpen(false);
  }

  React.useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && setOpen(false);
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  const isHome = pathname === "/";

  return (
    <header className="sticky top-0 z-40 border-b border-border/80 bg-background/80 backdrop-blur-xl">
      <div className="container-page flex h-16 items-center justify-between gap-4">
        <Link href="/" aria-label="Brain-co home" className="shrink-0">
          <Wordmark />
        </Link>

        <nav aria-label="Main" className="hidden items-center gap-1 md:flex">
          {navCopy.primary.map((link) => {
            const active = isHome ? link.href === "/" : pathname.startsWith(link.href) && link.href !== "/";
            return (
              <Link
                key={link.href}
                href={link.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  active ? "text-foreground" : "text-muted hover:text-foreground",
                )}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-2">
          <ThemeToggle />
          {user ? (
            <div className="hidden items-center gap-2 md:flex">
              <Link href="/workspace" className={buttonClasses("secondary", "sm")}>
                Workspace
              </Link>
              <button type="button" onClick={() => void logout()} className={buttonClasses("ghost", "sm")}>
                Log out
              </button>
            </div>
          ) : (
            <Link href="/login" className={cn(buttonClasses("ghost", "sm"), "hidden md:inline-flex")}>
              {navCopy.login}
            </Link>
          )}
          <Link href="/onboarding" className={cn(buttonClasses("primary", "sm"), "hidden md:inline-flex")}>
            {navCopy.start}
          </Link>

          <button
            type="button"
            aria-label={open ? navCopy.closeAria : navCopy.menuAria}
            aria-expanded={open}
            onClick={() => setOpen((value) => !value)}
            className="grid h-9 w-9 place-items-center rounded-full border border-border bg-surface md:hidden"
          >
            <span className="relative block h-3.5 w-4" aria-hidden="true">
              <span
                className={cn(
                  "absolute left-0 h-px w-full bg-current transition-transform duration-200",
                  open ? "top-1.5 rotate-45" : "top-0",
                )}
              />
              <span
                className={cn(
                  "absolute left-0 h-px w-full bg-current transition-transform duration-200",
                  open ? "top-1.5 -rotate-45" : "top-3",
                )}
              />
            </span>
          </button>
        </div>
      </div>

      <AnimatePresence>
        {open && (
          <motion.nav
            aria-label="Mobile"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.28, ease: [0.2, 0.8, 0.2, 1] }}
            className="overflow-hidden border-t border-border bg-background md:hidden"
          >
            <div className="container-page flex flex-col gap-1 py-4">
              {navCopy.primary.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="rounded-xl px-3 py-3 text-base font-medium text-muted transition-colors hover:bg-surface hover:text-foreground"
                >
                  {link.label}
                </Link>
              ))}
              <div className="mt-3 flex flex-col gap-2">
                {user ? (
                  <>
                    <Link href="/workspace" className={buttonClasses("secondary", "md")}>
                      Workspace
                    </Link>
                    <button type="button" onClick={() => void logout()} className={buttonClasses("ghost", "md")}>
                      Log out
                    </button>
                  </>
                ) : (
                  <Link href="/login" className={buttonClasses("secondary", "md")}>
                    {navCopy.login}
                  </Link>
                )}
                <Link href="/onboarding" className={buttonClasses("primary", "md")}>
                  {navCopy.start}
                </Link>
              </div>
            </div>
          </motion.nav>
        )}
      </AnimatePresence>
    </header>
  );
}
