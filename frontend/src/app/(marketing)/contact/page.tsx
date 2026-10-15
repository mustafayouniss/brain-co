import type { Metadata } from "next";
import { Mail, MapPin, Clock, LifeBuoy } from "lucide-react";
import { contactCopy } from "@/content/marketing";
import { Breadcrumbs } from "@/components/marketing/breadcrumbs";
import { ContactForm } from "@/components/marketing/contact-form";
import { Reveal } from "@/components/marketing/sections/reveal";

export const metadata: Metadata = {
  title: contactCopy.meta.title,
  description: contactCopy.meta.description,
  alternates: { canonical: "/contact" },
};

const contactJsonLd = {
  "@context": "https://schema.org",
  "@type": "ContactPage",
  name: "Contact Brain-co",
  description: contactCopy.meta.description,
};

export default function ContactPage() {
  return (
    <>
      <Breadcrumbs items={[{ label: "Contact" }]} />

      <section className="container-page py-14 sm:py-20" aria-labelledby="contact-title">
        <div className="grid gap-12 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
          <Reveal>
            <p className="eyebrow">{contactCopy.eyebrow}</p>
            <h1 id="contact-title" className="section-title mt-4 text-balance">
              {contactCopy.title}
            </h1>
            <p className="mt-5 max-w-md text-base leading-relaxed text-muted">
              {contactCopy.description}
            </p>

            <h2 className="mt-10 text-sm font-semibold uppercase tracking-[0.14em] text-subtle">
              {contactCopy.direct.title}
            </h2>
            <ul className="mt-4 space-y-4">
              <ContactRow icon={Mail} label="Email">
                <a href={`mailto:${contactCopy.direct.email}`} className="text-[var(--ring)] underline-offset-4 hover:underline">
                  {contactCopy.direct.email}
                </a>
                <span className="block text-xs text-subtle">
                  Support: {contactCopy.direct.support}
                </span>
              </ContactRow>
              <ContactRow icon={MapPin} label="Address">
                {contactCopy.direct.address}
              </ContactRow>
              <ContactRow icon={Clock} label="Hours">
                {contactCopy.direct.hours}
              </ContactRow>
              <ContactRow icon={LifeBuoy} label="Response">
                Within one business day, from a human.
              </ContactRow>
            </ul>
          </Reveal>

          <Reveal delay={0.08}>
            <div className="rounded-2xl border border-border bg-surface p-6 sm:p-8">
              <ContactForm />
            </div>
          </Reveal>
        </div>
      </section>

      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(contactJsonLd) }} />
    </>
  );
}

function ContactRow({
  icon: Icon,
  label,
  children,
}: {
  icon: typeof Mail;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <li className="flex gap-4">
      <span className="mt-0.5 grid h-9 w-9 flex-none place-items-center rounded-xl border border-border-strong bg-surface text-[var(--ring)]">
        <Icon aria-hidden="true" className="h-4 w-4" />
      </span>
      <span className="text-sm leading-relaxed text-muted">
        <span className="mb-0.5 block text-xs font-semibold uppercase tracking-[0.1em] text-subtle">
          {label}
        </span>
        {children}
      </span>
    </li>
  );
}
