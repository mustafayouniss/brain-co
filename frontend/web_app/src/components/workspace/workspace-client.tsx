"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { workspaceCopy } from "@/content/app";
import { authCopy } from "@/content/marketing";
import { BrandMark } from "@/components/brand/icons";
import { PrototypeBadge } from "@/components/auth/prototype-badge";
import { buttonClasses } from "@/components/ui/button";
import { TabPanel, Tabs } from "@/components/ui/tabs";
import { useOnboarding } from "@/hooks/use-onboarding";
import { useSession } from "@/hooks/use-session";

const tabIds = ["overview", "cases", "clients", "knowledge", "insights", "ai-employee"] as const;
const tabItems = workspaceCopy.tabs.map((label, index) => ({ id: tabIds[index], label }));

/**
 * Legal Intelligence workspace (task H). MOCK/D8: no workspace API or data
 * source exists — every panel is an honest empty state; the prototype's
 * sample metrics (12 cases, 24 clients, …) are deliberately NOT shown.
 * Session enforcement happens server-side in src/proxy.ts; this component
 * additionally handles an expired session found after hydration.
 */
export function WorkspaceClient() {
  const router = useRouter();
  const { user, loading } = useSession();
  const { state, hydrated } = useOnboarding();
  const [active, setActive] = React.useState<string>("overview");

  // Expired/missing session discovered client-side (cookie cleared mid-session).
  React.useEffect(() => {
    if (hydrated && !loading && !user) router.replace("/login?next=/workspace");
  }, [hydrated, loading, user, router]);

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }

  if (loading || !user) {
    return (
      <div className="dark flex min-h-dvh items-center justify-center screen-base text-white">
        <p className="text-sm text-[#8a94a8]" role="status">
          {workspaceCopy.loading}
        </p>
      </div>
    );
  }

  const domain = state.domain;
  const orgLabel =
    state.survey?.organizationName ?? state.account?.companyName ?? workspaceCopy.subtitle;

  return (
    <div className="dark min-h-dvh screen-base text-white">
      <header className="sticky top-0 z-30 border-b border-[#202a3e] bg-[#050b1a]/85 backdrop-blur-xl">
        <div className="mx-auto flex h-14 w-full max-w-5xl items-center justify-between gap-4 px-4 sm:px-6">
          <Link href="/" className="flex items-center gap-2.5">
            <BrandMark className="h-7 w-7" />
            <strong className="text-sm font-semibold tracking-[-0.03em]">Brain-co</strong>
          </Link>
          <div className="flex min-w-0 items-center gap-3">
            <span className="hidden min-w-0 truncate text-xs text-[#8a94a8] sm:block">
              {user.email}
            </span>
            <button
              type="button"
              onClick={handleLogout}
              className="flex h-9 items-center rounded-full border border-[#34405a] px-3 text-xs font-semibold text-[#a7b0c1] transition-colors hover:border-[#946eff] hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
            >
              {authCopy.logout}
            </button>
          </div>
        </div>
      </header>

      <main id="main" className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6">
        <div className="flex flex-wrap items-center gap-2">
          <PrototypeBadge />
          <span className="tag">{workspaceCopy.notConnected}</span>
        </div>

        <h1 className="mt-4 text-3xl font-medium tracking-[-0.04em]">{orgLabel}</h1>
        <p className="mt-1 text-sm text-[#a7b0c1]">
          {workspaceCopy.title} · {workspaceCopy.subtitle}
        </p>

        {domain === "legal" ? (
          <section className="mt-6">
            <span className="tag">{workspaceCopy.kicker}</span>
            <Tabs
              items={tabItems}
              activeId={active}
              onChange={setActive}
              ariaLabel="Workspace sections"
              className="mt-4"
            />
            {tabIds.map((id) => (
              <TabPanel key={id} id={id} active={active === id} className="pt-6">
                {id === "overview" ? (
                  <OverviewPanel />
                ) : (
                  <p className="rounded-2xl border border-[#202a3e] bg-[#0b1425] p-8 text-center text-sm text-[#a7b0c1]">
                    {id === "ai-employee"
                      ? workspaceCopy.aiUnavailable
                      : workspaceCopy.emptyNote(
                          workspaceCopy.tabs[tabIds.indexOf(id)],
                        )}
                  </p>
                )}
              </TabPanel>
            ))}
          </section>
        ) : domain ? (
          /* Sales / HR can never reach here through the flow (H: explicit
             not-available state, never a fake workspace). */
          <p className="mt-6 rounded-2xl border border-[#202a3e] bg-[#0b1425] p-8 text-center text-sm text-[#a7b0c1]">
            <strong className="block text-base text-white">{workspaceCopy.plannedTitle}</strong>
            <span className="mt-2 block">{workspaceCopy.plannedBody}</span>
          </p>
        ) : (
          /* Signed in without onboarding context (e.g. direct login). */
          <div className="mt-6 rounded-2xl border border-[#202a3e] bg-[#0b1425] p-8 text-center">
            <p className="text-base font-semibold">{workspaceCopy.noOrgTitle}</p>
            <p className="mt-2 text-sm text-[#a7b0c1]">{workspaceCopy.noOrgBody}</p>
            <Link
              href="/onboarding/domains"
              className={`${buttonClasses("primary", "md", "mt-5")} no-underline`}
            >
              {workspaceCopy.startOnboarding}
            </Link>
          </div>
        )}
      </main>
    </div>
  );
}

function OverviewPanel() {
  return (
    <div>
      <p className="text-sm text-[#a7b0c1]">
        No cases, clients or metrics are invented here — this workspace will populate once a
        real workspace API exists (docs/FLOW_AUDIT.md, D8 / contract 5).
      </p>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {workspaceCopy.cards.map((card) => (
          <div key={card.label} className="rounded-2xl border border-[#202a3e] bg-[#0b1425] p-5">
            <p className="text-xs text-[#8a94a8]">{card.label}</p>
            <p className="mt-2 text-2xl font-medium text-[#34405a]">{workspaceCopy.noData}</p>
            <p className="mt-1 text-[11px] text-[#8a94a8]">{workspaceCopy.notConnected}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
