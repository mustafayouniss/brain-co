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
    <div className="relative min-h-screen bg-[#020409] text-white">
      <Breadcrumbs items={[{ label: "Contact" }]} />

      <section className="container-page py-16 sm:py-24" aria-labelledby="contact-title">
        <div className="grid gap-16 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
          <Reveal>
            <div className="text-xs font-mono uppercase tracking-[0.2em] text-cyan-400">
              {contactCopy.eyebrow}
            </div>
            <h1 id="contact-title" className="cinematic-title mt-4 font-normal tracking-tight text-white text-balance">
              {contactCopy.title}
            </h1>
            <p className="mt-6 max-w-md text-base sm:text-lg text-zinc-400 font-light leading-relaxed">
              {contactCopy.description}
            </p>

            <div className="mt-12 border-t border-white/[0.08] pt-8">
              <h2 className="text-xs font-mono font-medium uppercase tracking-[0.16em] text-zinc-500">
                {contactCopy.direct.title}
              </h2>
              <ul className="mt-6 space-y-5">
                <ContactRow icon={Mail} label="Email">
                  <a
                    href={`mailto:${contactCopy.direct.email}`}
                    className="text-cyan-400 font-mono text-xs hover:underline"
                  >
                    {contactCopy.direct.email}
                  </a>
                  <span className="block text-[11px] text-zinc-500 mt-0.5">
                    Enterprise SLA: {contactCopy.direct.support}
                  </span>
                </ContactRow>
                <ContactRow icon={MapPin} label="Address">
                  <span className="text-xs text-zinc-300 font-light">
                    {contactCopy.direct.address}
                  </span>
                </ContactRow>
                <ContactRow icon={Clock} label="Hours">
                  <span className="text-xs text-zinc-300 font-light">
                    {contactCopy.direct.hours}
                  </span>
                </ContactRow>
                <ContactRow icon={LifeBuoy} label="Guaranteed Response">
                  <span className="text-xs text-zinc-300 font-light">
                    Within one business day, directly from a principal systems architect.
                  </span>
                </ContactRow>
              </ul>
            </div>
          </Reveal>

          <Reveal delay={0.08}>
            <div className="rounded-2xl border border-white/[0.08] bg-black/40 p-8 sm:p-10">
              <h3 className="text-lg font-medium text-white mb-6">
                Send a direct message
              </h3>
              <ContactForm />
            </div>
          </Reveal>
        </div>
      </section>

      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(contactJsonLd) }}
      />
    </div>
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
    <li className="flex gap-4 items-start">
      <span className="mt-0.5 grid h-9 w-9 flex-none place-items-center rounded-xl border border-white/10 bg-white/[0.03] text-cyan-400">
        <Icon aria-hidden="true" className="h-4 w-4" />
      </span>
      <div className="leading-relaxed">
        <span className="mb-0.5 block text-[10px] font-mono uppercase tracking-widest text-zinc-500">
          {label}
        </span>
        {children}
      </div>
    </li>
  );
}
