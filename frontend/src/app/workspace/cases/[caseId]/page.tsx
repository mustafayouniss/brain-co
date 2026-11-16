import type { Metadata } from "next";
import { CaseWorkspaceClient } from "@/components/workspace/case-workspace-client";

export const metadata: Metadata = {
  title: { absolute: "Case Workspace — Brain-co" },
  robots: { index: false, follow: false },
};

export default async function CaseWorkspacePage({
  params,
}: {
  params: Promise<{ caseId: string }>;
}) {
  const { caseId } = await params;
  return <CaseWorkspaceClient caseId={caseId} />;
}
