import Link from "next/link";
import { notFoundCopy } from "@/content/marketing";
import { shapeUrls } from "@/content/app";
import { Wordmark, ArrowIcon } from "@/components/brand/icons";
import { buttonClasses } from "@/components/ui/button";

export const metadata = {
  title: "Page not found",
  robots: { index: false, follow: false },
};

export default function NotFound() {
  return (
    <main
      id="main"
      className="relative flex min-h-dvh flex-col items-center justify-center overflow-hidden bg-deep px-6 text-center"
    >
      <div className="grid-overlay" aria-hidden="true" />
      <div
        className="purple-glow pointer-events-none absolute left-1/2 top-1/2 h-[560px] w-[560px] -translate-x-1/2 -translate-y-1/2"
        aria-hidden="true"
      />

      <div className="relative animate-fade-up">
        <Link href="/" aria-label="Brain-co home" className="inline-flex">
          <Wordmark />
        </Link>

        <img
          src={shapeUrls.dust}
          alt=""
          aria-hidden="true"
          className="mx-auto mt-10 h-40 w-40 opacity-90"
          decoding="async"
        />

        <p className="mt-6 text-sm font-bold uppercase tracking-[0.2em] text-gold">
          {notFoundCopy.code}
        </p>
        <h1 className="mt-3 text-balance text-3xl font-semibold tracking-tight sm:text-4xl">
          {notFoundCopy.title}
        </h1>
        <p className="mx-auto mt-4 max-w-md text-sm leading-relaxed text-muted">
          {notFoundCopy.body}
        </p>

        <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Link href="/" className={buttonClasses("primary", "lg")}>
            <span>{notFoundCopy.home}</span>
            <ArrowIcon />
          </Link>
          <Link href="/modules" className={buttonClasses("secondary", "lg")}>
            <span>{notFoundCopy.modules}</span>
            <ArrowIcon />
          </Link>
        </div>
      </div>
    </main>
  );
}
