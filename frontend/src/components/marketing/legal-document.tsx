import { Breadcrumbs } from "@/components/marketing/breadcrumbs";
import { Reveal } from "@/components/marketing/sections/reveal";

interface LegalDocumentProps {
  title: string;
  updated: string;
  intro: string;
  sections: ReadonlyArray<{ h: string; items: readonly string[] }>;
  description: string;
}

/** Shared renderer for the Privacy Policy and Terms of Service pages. */
export function LegalDocument({
  title,
  updated,
  intro,
  sections,
  description,
}: LegalDocumentProps) {
  return (
    <div className="relative min-h-screen bg-[#020409] text-white">
      {/* Background ambient lighting */}
      <div
        className="pointer-events-none absolute top-0 left-1/2 -translate-x-1/2 h-[500px] w-[900px] rounded-full bg-cyan-500/[0.03] blur-[140px]"
        aria-hidden="true"
      />

      <Breadcrumbs items={[{ label: title }]} />

      <article className="container-page max-w-4xl py-16 sm:py-24">
        <Reveal>
          <div className="text-xs font-mono uppercase tracking-[0.2em] text-cyan-400">
            Legal & Compliance Framework
          </div>
          <h1 className="cinematic-title mt-4 font-normal tracking-tight text-white text-balance">
            {title}
          </h1>
          <p className="mt-3 text-xs font-mono uppercase tracking-[0.14em] text-zinc-500">
            {updated}
          </p>

          <div className="mt-12 rounded-2xl border border-white/[0.08] bg-white/[0.02] p-8 sm:p-12 backdrop-blur-2xl">
            <div className="prose-legal text-zinc-300 font-light leading-relaxed">
              <p className="text-base text-zinc-200 leading-relaxed">{intro}</p>
              {sections.map((section) => (
                <section key={section.h} className="mt-10 border-t border-white/[0.06] pt-8">
                  <h2 className="text-xl font-medium tracking-tight text-white mb-4">
                    {section.h}
                  </h2>
                  <ul className="space-y-3">
                    {section.items.map((item) => (
                      <li key={item} className="text-sm text-zinc-400 leading-relaxed flex items-start gap-2.5">
                        <span className="mt-2 h-1.5 w-1.5 rounded-full bg-cyan-400 flex-none" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </section>
              ))}
            </div>
          </div>
        </Reveal>
      </article>

      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "WebPage",
            name: title,
            description,
            inLanguage: "en",
          }),
        }}
      />
    </div>
  );
}
