import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { domainDetails, type DomainKey } from "@/content/app";
import { DomainFlow } from "@/components/onboarding/domain-flow";

export const metadata: Metadata = {
  title: "Domain",
  robots: { index: false, follow: false },
};

const validKeys = Object.keys(domainDetails) as DomainKey[];

export default async function DomainStepPage({
  params,
}: {
  params: Promise<{ domain: string }>;
}) {
  const { domain } = await params;
  if (!validKeys.includes(domain as DomainKey)) notFound();

  return <DomainFlow domain={domain as DomainKey} />;
}
