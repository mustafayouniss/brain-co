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
  const [scrolled, setScrolled] = React.useState(false);
  const { user, logout } = useSession();

  // Close mobile menu on navigation
  const [lastPathname, setLastPathname] = React.useState(pathname);
  if (pathname !== lastPathname) {
    setLastPathname(pathname);
    setOpen(false);
  }

  // Keyboard accessibility
  React.useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && setOpen(false);
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  // Scroll detection for enhanced glass backdrop
  React.useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const isHome = pathname === "/";

  return (
    <header
      className="sticky top-0 z-50 w-full transition-all duration-300 bg-transparent border-transparent"
    >
      <div className="container-page flex h-16 items-center justify-between gap-4">
        {/* Brand Wordmark */}
        <Link
          href="/"
          aria-label="Brain-co home"
          className="shrink-0 transition-opacity duration-200 hover:opacity-90"
        >
          <Wordmark />
        </Link>

        {/* Desktop Primary Navigation */}
        <nav
          aria-label="Main"
          className="hidden items-center gap-1 rounded-full border border-white/[0.08] bg-black/25 px-3 py-1 md:flex"
        >
          {navCopy.primary.map((link) => {
            const active = isHome ? link.href === "/" : pathname.startsWith(link.href) && link.href !== "/";
            return (
              <Link
                key={link.href}
                href={link.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "relative rounded-full px-3.5 py-1.5 text-xs font-medium tracking-tight transition-colors duration-200",
                  active
                    ? "text-white font-semibold"
                    : "text-zinc-400 hover:text-white"
                )}
              >
                {active && (
                  <motion.span
                    layoutId="navbar-active-pill"
                    className="absolute inset-0 rounded-full bg-white/[0.08]"
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                  />
                )}
                <span className="relative z-10">{link.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5">
          <ThemeToggle className="grid h-8 w-8 place-items-center rounded-full border border-white/10 bg-white/[0.03] text-zinc-400 transition-colors hover:border-white/20 hover:text-white" />

          {user ? (
            <div className="hidden items-center gap-2 md:flex">
              <Link
                href="/workspace"
                className={cn(buttonClasses("pill-white", "sm"), "h-8 px-4 text-xs font-semibold")}
              >
                Workspace
              </Link>
              <button
                type="button"
                onClick={() => void logout()}
                className={cn(buttonClasses("ghost", "sm"), "h-8 text-xs text-zinc-400 hover:text-white")}
              >
                Log out
              </button>
            </div>
          ) : (
            <>
              <Link
                href="/login"
                className={cn(
                  buttonClasses("pill-glass", "sm"),
                  "hidden h-8 px-4 text-xs font-medium md:inline-flex"
                )}
              >
                {navCopy.login}
              </Link>
              <Link
                href="/onboarding"
                className={cn(
                  buttonClasses("pill-white", "sm"),
                  "hidden h-8 px-4 text-xs font-semibold md:inline-flex"
                )}
              >
                {navCopy.start}
              </Link>
            </>
          )}

          {/* Mobile Menu Trigger */}
          <button
            type="button"
            aria-label={open ? navCopy.closeAria : navCopy.menuAria}
            aria-expanded={open}
            onClick={() => setOpen((value) => !value)}
            className="grid h-9 w-9 place-items-center rounded-full border border-white/10 bg-white/[0.04] text-zinc-300 md:hidden transition-colors hover:border-white/20 hover:text-white"
          >
            <span className="relative block h-3.5 w-4" aria-hidden="true">
              <span
                className={cn(
                  "absolute left-0 h-px w-full bg-current transition-transform duration-200",
                  open ? "top-1.5 rotate-45" : "top-0"
                )}
              />
              <span
                className={cn(
                  "absolute left-0 h-px w-full bg-current transition-transform duration-200",
                  open ? "top-1.5 -rotate-45" : "top-3"
                )}
              />
            </span>
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      <AnimatePresence>
        {open && (
          <motion.nav
            aria-label="Mobile"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.24, ease: [0.16, 1, 0.3, 1] }}
            className="overflow-hidden border-t border-white/[0.08] bg-black/95 md:hidden"
          >
            <div className="container-page flex flex-col gap-1 py-5">
              {navCopy.primary.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="rounded-xl px-3 py-2.5 text-sm font-medium text-zinc-300 transition-colors hover:bg-white/[0.05] hover:text-white"
                >
                  {link.label}
                </Link>
              ))}

              <div className="mt-4 flex flex-col gap-2.5 border-t border-white/[0.08] pt-4">
                {user ? (
                  <>
                    <Link href="/workspace" className={buttonClasses("pill-white", "md")}>
                      Workspace
                    </Link>
                    <button
                      type="button"
                      onClick={() => void logout()}
                      className={buttonClasses("ghost", "md")}
                    >
                      Log out
                    </button>
                  </>
                ) : (
                  <>
                    <Link href="/login" className={buttonClasses("pill-glass", "md")}>
                      {navCopy.login}
                    </Link>
                    <Link href="/onboarding" className={buttonClasses("pill-white", "md")}>
                      {navCopy.start}
                    </Link>
                  </>
                )}
              </div>
            </div>
          </motion.nav>
        )}
      </AnimatePresence>
    </header>
  );
}
