import Link from "next/link";
import { landingCopy } from "@/content/marketing";
import { domainDetails, shapeUrls, storyCopy } from "@/content/app";
import { ArrowIcon } from "@/components/brand/icons";
import { buttonClasses } from "@/components/ui/button";
import { Reveal } from "@/components/marketing/sections/reveal";
import { cn } from "@/lib/utils";

const accents = {
  gold: "border-gold/50",
  mint: "border-mint/50",
  violet: "border-violet/50",
} as const;

/** Product tour: faithful miniatures of the real app screens. */
export function Showcase() {
  const { showcase } = landingCopy;

  return (
    <section aria-labelledby="showcase-title" className="section-base py-20 sm:py-28">
      <div className="container-page">
        <Reveal className="max-w-2xl">
          <p className="eyebrow">{showcase.eyebrow}</p>
          <h2 id="showcase-title" className="section-title mt-4 text-balance">
            {showcase.title}
          </h2>
          <p className="mt-5 text-base leading-relaxed text-muted">{showcase.description}</p>
        </Reveal>

        <div className="mt-12 grid gap-5 lg:grid-cols-3">
          {showcase.shots.map((shot, index) => (
            <Reveal key={shot.title} delay={index * 0.08}>
              <article className="flex h-full flex-col overflow-hidden rounded-2xl border border-border bg-surface">
                <div
                  className={cn(
                    "relative flex min-h-56 items-center justify-center border-b border-border bg-deep p-5",
                    accents[shot.accent],
                  )}
                >
                  <div className="grid-overlay absolute inset-0 opacity-60" aria-hidden="true" />
                  <div className="relative w-full max-w-[280px]">
                    {index === 0 && <MockStory />}
                    {index === 1 && <MockDomains />}
                    {index === 2 && <MockDocuments />}
                  </div>
                </div>
                <div className="flex flex-1 flex-col p-6">
                  <h3 className="text-base font-semibold tracking-tight">{shot.title}</h3>
                  <p className="mt-2 flex-1 text-sm leading-relaxed text-muted">{shot.body}</p>
                </div>
              </article>
            </Reveal>
          ))}
        </div>

        <Reveal delay={0.1} className="mt-10">
          <Link href="/onboarding" className={buttonClasses("primary", "lg")}>
            <span>{showcase.cta}</span>
            <ArrowIcon />
          </Link>
        </Reveal>
      </div>
    </section>
  );
}

/** Miniature of the onboarding story screen. */
function MockStory() {
  const step = storyCopy.steps[1];
  return (
    <div className="rounded-2xl border border-border bg-surface p-4 text-center shadow-[0_16px_40px_rgba(0,0,0,0.35)]">
      <img
        src={shapeUrls.brain}
        alt=""
        aria-hidden="true"
        className="mx-auto h-20 w-20"
        decoding="async"
      />
      <p className="mt-2 text-[13px] font-semibold leading-snug">{step.title}</p>
      <div className="mt-3 flex justify-center gap-1.5" aria-hidden="true">
        {[0, 1, 2, 3, 4, 5].map((i) => (
          <i
            key={i}
            className={cn(
              "h-1.5 w-1.5 rounded-full",
              i === 1 ? "w-4 rounded-sm bg-white" : "bg-border-strong",
            )}
          />
        ))}
      </div>
    </div>
  );
}

/** Miniature of the domain picker. */
function MockDomains() {
  return (
    <div className="flex flex-col gap-2.5 rounded-2xl border border-border bg-surface p-4 shadow-[0_16px_40px_rgba(0,0,0,0.35)]">
      {(Object.keys(domainDetails) as Array<keyof typeof domainDetails>).map((key) => (
        <div key={key} className="flex items-center gap-3 rounded-xl border border-border bg-deep px-3 py-2.5">
          <img src={shapeUrls[key]} alt="" aria-hidden="true" className="h-9 w-9" decoding="async" />
          <span className="text-sm font-semibold">{domainDetails[key].title}</span>
          <span
            className={cn(
              "ml-auto rounded-full border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider",
              domainDetails[key].status === "Available"
                ? "border-gold text-gold"
                : "border-border-strong text-muted",
            )}
          >
            {domainDetails[key].status}
          </span>
        </div>
      ))}
    </div>
  );
}

/** Miniature of the document ingestion list. */
function MockDocuments() {
  const docs = [
    ["Operations handbook.pdf", "Processed"],
    ["Matter intake SOP.docx", "Processing"],
    ["Records policy.txt", "Queued"],
    ["Client procedure.pdf", "Uploading"],
  ] as const;

  return (
    <div className="rounded-2xl border border-border bg-surface p-4 shadow-[0_16px_40px_rgba(0,0,0,0.35)]">
      <div className="flex flex-col gap-2">
        {docs.map(([name, status]) => (
          <div
            key={name}
            className="flex items-center gap-2 border-b border-border pb-2 text-[11px] last:border-0 last:pb-0"
          >
            <span className="truncate text-foreground/90">{name}</span>
            <i className={cn("status-chip ml-auto", status.toLowerCase())}>{status}</i>
          </div>
        ))}
      </div>
    </div>
  );
}
