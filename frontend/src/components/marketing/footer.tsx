import Link from "next/link";
import { footerCopy } from "@/content/marketing";
import { site } from "@/content/site";
import { Wordmark } from "@/components/brand/icons";
import { NewsletterForm } from "@/components/marketing/newsletter-form";

const socials = [
  { name: "LinkedIn", href: site.social.linkedin, icon: SocialLinkedIn },
  { name: "X", href: site.social.x, icon: SocialX },
  { name: "GitHub", href: site.social.github, icon: SocialGithub },
  { name: "YouTube", href: site.social.youtube, icon: SocialYoutube },
] as const;

export function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="border-t border-border band-deep">
      <div className="container-page grid gap-10 py-14 md:grid-cols-[1.4fr_1fr_1fr_1fr]">
        <div className="flex flex-col gap-5">
          <Link href="/" aria-label="Brain-co home">
            <Wordmark />
          </Link>
          <p className="max-w-xs text-sm leading-relaxed text-muted">{footerCopy.blurb}</p>
          <NewsletterForm />
        </div>

        <FooterColumn title={footerCopy.product.title} links={footerCopy.product.links} />
        <FooterColumn title={footerCopy.company.title} links={footerCopy.company.links} />
        <FooterColumn title={footerCopy.legal.title} links={footerCopy.legal.links} />
      </div>

      <div className="border-t border-border">
        <div className="container-page flex flex-col items-start justify-between gap-4 py-6 sm:flex-row sm:items-center">
          <p className="text-xs text-subtle">{footerCopy.rights(year)}</p>
          <ul className="flex items-center gap-2">
            {socials.map(({ name, href, icon: Icon }) => (
              <li key={name}>
                <a
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={footerCopy.socialAria(name)}
                  className="grid h-9 w-9 place-items-center rounded-full border border-border text-muted transition-colors hover:border-border-strong hover:text-foreground"
                >
                  <Icon />
                </a>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </footer>
  );
}

function FooterColumn({
  title,
  links,
}: {
  title: string;
  links: ReadonlyArray<{ href: string; label: string }>;
}) {
  return (
    <nav aria-label={title}>
      <h2 className="text-xs font-semibold uppercase tracking-[0.14em] text-subtle">{title}</h2>
      <ul className="mt-4 space-y-2.5">
        {links.map((link) => (
          <li key={link.href}>
            <Link
              href={link.href}
              className="text-sm text-muted transition-colors hover:text-foreground"
            >
              {link.label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}

const iconProps = {
  viewBox: "0 0 24 24",
  fill: "currentColor",
  className: "h-4 w-4",
  "aria-hidden": true,
} as const;

function SocialLinkedIn() {
  return (
    <svg {...iconProps}>
      <path d="M4.98 3.5A2.5 2.5 0 1 1 0 3.5a2.5 2.5 0 0 1 4.98 0ZM.3 8.2h4.4V24H.3V8.2Zm7.5 0h4.2v2.2h.06c.6-1.1 2-2.3 4.14-2.3 4.4 0 5.2 2.9 5.2 6.6V24h-4.4v-7.6c0-1.8 0-4.1-2.5-4.1s-2.9 2-2.9 4V24H7.8V8.2Z" />
    </svg>
  );
}

function SocialX() {
  return (
    <svg {...iconProps}>
      <path d="M18.24 2H21l-6.55 7.49L22.5 22h-6.03l-4.72-6.17L6.3 22H3.52l7-8-7.7-12h6.18l4.27 5.65L18.24 2Zm-1.06 18.3h1.53L7.9 3.62H6.26l10.92 16.68Z" />
    </svg>
  );
}

function SocialGithub() {
  return (
    <svg {...iconProps}>
      <path d="M12 .5A11.5 11.5 0 0 0 .5 12a11.5 11.5 0 0 0 7.86 10.92c.58.1.79-.25.79-.55v-2c-3.2.7-3.88-1.37-3.88-1.37-.53-1.34-1.3-1.7-1.3-1.7-1.05-.72.08-.7.08-.7 1.17.08 1.78 1.2 1.78 1.2 1.04 1.77 2.72 1.26 3.38.96.1-.75.4-1.26.73-1.55-2.55-.29-5.24-1.28-5.24-5.7 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11 11 0 0 1 5.8 0c2.2-1.5 3.17-1.18 3.17-1.18.63 1.59.23 2.76.12 3.05.74.81 1.18 1.84 1.18 3.1 0 4.43-2.69 5.4-5.25 5.69.41.36.78 1.06.78 2.14v3.17c0 .3.2.66.8.55A11.5 11.5 0 0 0 23.5 12 11.5 11.5 0 0 0 12 .5Z" />
    </svg>
  );
}

function SocialYoutube() {
  return (
    <svg {...iconProps}>
      <path d="M23.5 6.5a3 3 0 0 0-2.1-2.1C19.5 3.9 12 3.9 12 3.9s-7.5 0-9.4.5A3 3 0 0 0 .5 6.5 31.4 31.4 0 0 0 0 12a31.4 31.4 0 0 0 .5 5.5 3 3 0 0 0 2.1 2.1c1.9.5 9.4.5 9.4.5s7.5 0 9.4-.5a3 3 0 0 0 2.1-2.1A31.4 31.4 0 0 0 24 12a31.4 31.4 0 0 0-.5-5.5ZM9.6 15.6V8.4L15.8 12l-6.2 3.6Z" />
    </svg>
  );
}
