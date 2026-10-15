import type { Metadata } from "next";
import { WorkspaceClient } from "@/components/workspace/workspace-client";

export const metadata: Metadata = {
  title: { absolute: "Workspace — Brain-co" },
  robots: { index: false, follow: false },
};

/**
 * Protected Legal workspace (task H). Access is enforced server-side by
 * src/proxy.ts (session cookie verified before this route renders).
 */
export default function WorkspacePage() {
  return <WorkspaceClient />;
}
