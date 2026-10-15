import Link from "next/link";
import { miscCopy } from "@/content/marketing";

export interface Crumb {
  label: string;
  href?: string;
}

/** Semantic breadcrumbs with BreadcrumbList JSON-LD. */
export function Breadcrumbs({ items }: { items: Crumb[] }) {
  const schema = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: miscCopy.breadcrumbs.home, item: "/" },
      ...items.map((item, index) => ({
        "@type": "ListItem",
        position: index + 2,
        name: item.label,
        ...(item.href ? { item: item.href } : {}),
      })),
    ],
  };

  return (
    <>
      <nav aria-label="Breadcrumb" className="container-page pt-6">
        <ol className="flex flex-wrap items-center gap-1.5 text-xs text-subtle">
          <li>
            <Link href="/" className="transition-colors hover:text-foreground">
              {miscCopy.breadcrumbs.home}
            </Link>
          </li>
          {items.map((item) => (
            <li key={item.label} className="flex items-center gap-1.5">
              <span aria-hidden="true">/</span>
              {item.href ? (
                <Link href={item.href} className="transition-colors hover:text-foreground">
                  {item.label}
                </Link>
              ) : (
                <span aria-current="page" className="text-muted">
                  {item.label}
                </span>
              )}
            </li>
          ))}
        </ol>
      </nav>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
      />
    </>
  );
}
