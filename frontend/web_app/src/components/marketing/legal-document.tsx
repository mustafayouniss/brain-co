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
    <>
      <Breadcrumbs items={[{ label: title }]} />
      <article className="container-page max-w-3xl py-14 sm:py-20">
        <Reveal>
          <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">{title}</h1>
          <p className="mt-3 text-xs font-semibold uppercase tracking-[0.14em] text-subtle">
            {updated}
          </p>
          <div className="prose-legal mt-8">
            <p>{intro}</p>
            {sections.map((section) => (
              <section key={section.h}>
                <h2>{section.h}</h2>
                <ul>
                  {section.items.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </section>
            ))}
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
    </>
  );
}
