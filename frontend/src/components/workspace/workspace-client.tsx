"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { workspaceCopy } from "@/content/app";
import { authCopy } from "@/content/marketing";
import { BrandMark } from "@/components/brand/icons";
import { buttonClasses } from "@/components/ui/button";
import { TabPanel, Tabs } from "@/components/ui/tabs";
import { useOnboarding } from "@/hooks/use-onboarding";
import { useSession } from "@/hooks/use-session";
import { Building2, FileText, Plus, ShieldCheck, Upload, Users } from "lucide-react";

const tabIds = ["overview", "cases", "clients", "knowledge", "insights", "ai-employee"] as const;
const tabItems = [
  { id: "overview", label: "Overview" },
  { id: "cases", label: "Cases" },
  { id: "clients", label: "Team & Members" },
  { id: "knowledge", label: "Knowledge & Docs" },
  { id: "insights", label: "Insights" },
  { id: "ai-employee", label: "AI Employee" },
];

export function WorkspaceClient() {
  const router = useRouter();
  const { user, loading } = useSession();
  const { state, hydrated } = useOnboarding();
  const [active, setActive] = React.useState<string>("overview");

  // Expired/missing session discovered client-side
  React.useEffect(() => {
    if (hydrated && !loading && !user) router.replace("/login?next=/workspace");
  }, [hydrated, loading, user, router]);

  async function handleLogout() {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } catch (error) {
      console.error("Logout failed:", error);
    }
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

  const domain = user.active_domain || state.domain || "legal";
  const orgLabel =
    user.active_organization_name ||
    state.account?.companyName ||
    state.survey?.organizationName ||
    "Organization Workspace";

  return (
    <div className="dark min-h-dvh screen-base text-white">
      <header className="sticky top-0 z-30 border-b border-[#202a3e] bg-[#050b1a]/85 backdrop-blur-xl">
        <div className="mx-auto flex h-14 w-full max-w-5xl items-center justify-between gap-4 px-4 sm:px-6">
          <Link href="/" className="flex items-center gap-2.5">
            <BrandMark className="h-7 w-7" />
            <strong className="text-sm font-semibold tracking-[-0.03em]">Brain-co</strong>
          </Link>
          <div className="flex min-w-0 items-center gap-3">
            <div className="hidden sm:flex flex-col text-right">
              <span className="text-xs font-medium text-white">{user.name || user.email}</span>
              <span className="text-[10px] text-[#8a94a8]">{user.role === "admin" ? "Organization Admin" : "Employee"}</span>
            </div>
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
          <span className="tag tag-available">Domain: {domain.toUpperCase()}</span>
          {user.role && (
            <span className="tag border-[#946eff]/40 text-[#946eff] capitalize">
              Role: {user.role}
            </span>
          )}
          {user.active_organization_id && (
            <span className="tag border-white/20 text-[#8a94a8] font-mono text-[10px]">
              Tenant: {user.active_organization_id}
            </span>
          )}
        </div>

        <h1 className="mt-4 text-3xl font-medium tracking-[-0.04em]">{orgLabel}</h1>
        <p className="mt-1 text-sm text-[#a7b0c1]">
          {workspaceCopy.title} · Authenticated Multi-Tenant SaaS Workspace
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
                  <OverviewPanel user={user} />
                ) : id === "cases" ? (
                  <CasesPanel />
                ) : id === "clients" ? (
                  <TeamPanel user={user} />
                ) : id === "knowledge" ? (
                  <KnowledgePanel />
                ) : id === "ai-employee" ? (
                  <AIEmployeePanel />
                ) : (
                  <p className="rounded-2xl border border-[#202a3e] bg-[#0b1425] p-8 text-center text-sm text-[#a7b0c1]">
                    {workspaceCopy.emptyNote(
                      tabItems.find((t) => t.id === id)?.label || id,
                    )}
                  </p>
                )}
              </TabPanel>
            ))}
          </section>
        ) : domain ? (
          <p className="mt-6 rounded-2xl border border-[#202a3e] bg-[#0b1425] p-8 text-center text-sm text-[#a7b0c1]">
            <strong className="block text-base text-white">{workspaceCopy.plannedTitle}</strong>
            <span className="mt-2 block">{workspaceCopy.plannedBody}</span>
          </p>
        ) : (
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

function OverviewPanel({ user }: { user: any }) {
  const [status, setStatus] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    fetch("/api/brain/status")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setStatus(data))
      .catch(() => setStatus(null))
      .finally(() => setLoading(false));
  }, []);

  const isHealthy = status?.status === "healthy";

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <p className="text-sm text-[#a7b0c1]">
          Authoritative Brain platform, cognitive engines, and persistence status.
        </p>
        <span
          className={`flex items-center gap-1.5 text-xs font-mono px-3 py-1 rounded-full border font-medium ${
            loading
              ? "bg-[#202a3e] text-[#8a94a8] border-[#34405a]"
              : isHealthy
              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
              : "bg-amber-500/10 text-amber-300 border-amber-500/30"
          }`}
        >
          <span className={`w-2 h-2 rounded-full ${isHealthy ? "bg-emerald-400" : "bg-amber-400"}`} />
          {loading ? "Checking Status..." : isHealthy ? "Ring 1 Live & Operational" : "Degraded / Offline"}
        </span>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-2xl border border-[#202a3e] bg-[#0b1425] p-5">
          <p className="text-xs text-[#8a94a8]">Organization Tenant</p>
          <p className="mt-2 text-base font-semibold text-white truncate">{user.active_organization_name || "Active Workspace"}</p>
          <p className="mt-1 text-[11px] text-[#8a94a8] font-mono truncate">{user.active_organization_id || "Tenant Isolated"}</p>
        </div>

        <div className="rounded-2xl border border-[#202a3e] bg-[#0b1425] p-5">
          <p className="text-xs text-[#8a94a8]">PostgreSQL Storage</p>
          <p className="mt-2 text-xl font-medium text-emerald-400">{status?.database === "up" ? "Active" : "Connected"}</p>
          <p className="mt-1 text-[11px] text-[#8a94a8]">Multi-Tenant Authoritative Isolation</p>
        </div>

        <div className="rounded-2xl border border-[#202a3e] bg-[#0b1425] p-5">
          <p className="text-xs text-[#8a94a8]">Cognitive Engines</p>
          <p className="mt-2 text-xl font-medium text-[#946eff]">6 Engines</p>
          <p className="mt-1 text-[11px] text-[#8a94a8]">Perception, Obs, Ctx, Mem, Retr, Plan</p>
        </div>

        <div className="rounded-2xl border border-[#202a3e] bg-[#0b1425] p-5">
          <p className="text-xs text-[#8a94a8]">Gemini Intelligence</p>
          <p className="mt-2 text-xl font-medium text-white">Live AI Employee</p>
          <p className="mt-1 text-[11px] text-[#8a94a8]">Grounded Reasoning &amp; Egyptian Law</p>
        </div>
      </div>
    </div>
  );
}

function CasesPanel() {
  const [cases, setCases] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [showCreate, setShowCreate] = React.useState(false);
  const [caseNumber, setCaseNumber] = React.useState("");
  const [title, setTitle] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const loadCases = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/cases");
      if (res.ok) {
        const data = await res.json();
        setCases(Array.isArray(data) ? data : []);
      } else {
        setError("Could not load organization cases");
      }
    } catch {
      setError("Failed to fetch cases");
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    loadCases();
  }, []);

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!caseNumber.trim() || !title.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch("/api/cases", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          case_number: caseNumber.trim(),
          title: title.trim(),
          description: description.trim() || undefined,
        }),
      });
      if (res.ok) {
        setCaseNumber("");
        setTitle("");
        setDescription("");
        setShowCreate(false);
        loadCases();
      } else {
        const err = await res.json().catch(() => ({}));
        setError(err.error?.message || err.detail?.message || "Failed to create case");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create case");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-white">Active Legal Cases</h3>
          <p className="text-xs text-[#a7b0c1]">
            Cases strictly partitioned and isolated for this organization.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-1.5 rounded-lg bg-[#946eff] px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-[#7c3aed] transition-colors"
        >
          <Plus className="size-4" />
          {showCreate ? "Cancel" : "New Case"}
        </button>
      </div>

      {showCreate && (
        <form onSubmit={handleCreateCase} className="rounded-2xl border border-[#202a3e] bg-[#0b1425] p-5 space-y-3">
          <h4 className="text-sm font-semibold text-white">Register New Legal Case</h4>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="text-xs text-[#8a94a8]">Case Number / Reference</label>
              <input
                type="text"
                placeholder="e.g. 1042/2026-Commercial"
                value={caseNumber}
                onChange={(e) => setCaseNumber(e.target.value)}
                required
                className="mt-1 w-full rounded-lg bg-[#050b1a] border border-[#202a3e] px-3 py-1.5 text-xs text-white placeholder-[#8a94a8] focus:border-[#946eff] focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs text-[#8a94a8]">Case Title</label>
              <input
                type="text"
                placeholder="e.g. Nile Port Cargo Breach Dispute"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                className="mt-1 w-full rounded-lg bg-[#050b1a] border border-[#202a3e] px-3 py-1.5 text-xs text-white placeholder-[#8a94a8] focus:border-[#946eff] focus:outline-none"
              />
            </div>
          </div>
          <div>
            <label className="text-xs text-[#8a94a8]">Description (Optional)</label>
            <textarea
              placeholder="Case background, parties, and scope..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="mt-1 w-full rounded-lg bg-[#050b1a] border border-[#202a3e] px-3 py-1.5 text-xs text-white placeholder-[#8a94a8] focus:border-[#946eff] focus:outline-none min-h-[60px]"
            />
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="rounded-lg bg-[#946eff] px-4 py-1.5 text-xs font-semibold text-white hover:bg-[#7c3aed] disabled:opacity-50"
          >
            {submitting ? "Creating Case..." : "Save Case"}
          </button>
        </form>
      )}

      {error && (
        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-xs text-red-400">
          {error}
        </div>
      )}

      {loading ? (
        <p className="text-center text-xs text-[#8a94a8] py-8">Loading cases...</p>
      ) : cases.length === 0 ? (
        <div className="rounded-2xl border border-[#202a3e] bg-[#0b1425] p-8 text-center text-xs text-[#8a94a8]">
          No legal cases registered yet. Click &quot;New Case&quot; to initialize your first case.
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {cases.map((c: any) => (
            <div
              key={c.id}
              className="rounded-xl border border-[#202a3e] bg-[#0b1425] hover:border-[#946eff]/40 transition-all p-4 text-xs space-y-3 flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[#946eff] font-semibold">{c.case_number}</span>
                  <span className="tag text-[10px] capitalize">{c.status || "open"}</span>
                </div>
                <p className="text-sm font-medium text-white">{c.title}</p>
                {c.description && <p className="text-[#a7b0c1] line-clamp-2">{c.description}</p>}
              </div>

              <div className="pt-2 border-t border-[#202a3e] flex items-center justify-between">
                <span className="text-[11px] text-[#8a94a8]">
                  {c.created_at ? new Date(c.created_at).toLocaleDateString() : ""}
                </span>
                <Link
                  href={`/workspace/cases/${c.id}`}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-[#946eff]/10 border border-[#946eff]/30 px-2.5 py-1 text-[11px] font-semibold text-[#946eff] hover:bg-[#946eff] hover:text-white transition-colors"
                >
                  <span>Open Workspace</span>
                  <span aria-hidden="true">→</span>
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function TeamPanel({ user }: { user: any }) {
  const [members, setMembers] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [email, setEmail] = React.useState("");
  const [fullName, setFullName] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [role, setRole] = React.useState("employee");
  const [submitting, setSubmitting] = React.useState(false);
  const [message, setMessage] = React.useState<{ text: string; error: boolean } | null>(null);

  const loadMembers = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/organizations/members");
      if (res.ok) {
        const data = await res.json();
        setMembers(Array.isArray(data) ? data : []);
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    loadMembers();
  }, []);

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !fullName.trim() || !password) return;
    setSubmitting(true);
    setMessage(null);
    try {
      const res = await fetch("/api/organizations/members", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.trim(),
          full_name: fullName.trim(),
          password,
          role,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        setEmail("");
        setFullName("");
        setPassword("");
        setMessage({ text: `Employee '${data.email}' successfully added to organization!`, error: false });
        loadMembers();
      } else {
        setMessage({ text: data.error?.message || data.detail || "Failed to add member", error: true });
      }
    } catch {
      setMessage({ text: "Network error adding member", error: true });
    } finally {
      setSubmitting(false);
    }
  };

  const isAdmin = user.role === "admin";

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-base font-semibold text-white">Organization Team &amp; Members</h3>
        <p className="text-xs text-[#a7b0c1]">
          Authorized members belonging to <span className="text-white font-medium">{user.active_organization_name}</span>.
        </p>
      </div>

      {isAdmin && (
        <form onSubmit={handleAddMember} className="rounded-2xl border border-[#202a3e] bg-[#0b1425] p-5 space-y-3">
          <h4 className="text-sm font-semibold text-white flex items-center gap-2">
            <Users className="size-4 text-[#946eff]" /> Add Employee to Organization
          </h4>
          <div className="grid gap-3 sm:grid-cols-3">
            <div>
              <label className="text-xs text-[#8a94a8]">Full Name</label>
              <input
                type="text"
                placeholder="e.g. Sarah Adel"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                className="mt-1 w-full rounded-lg bg-[#050b1a] border border-[#202a3e] px-3 py-1.5 text-xs text-white placeholder-[#8a94a8] focus:border-[#946eff] focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs text-[#8a94a8]">Work Email</label>
              <input
                type="email"
                placeholder="sarah@lawfirm.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="mt-1 w-full rounded-lg bg-[#050b1a] border border-[#202a3e] px-3 py-1.5 text-xs text-white placeholder-[#8a94a8] focus:border-[#946eff] focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs text-[#8a94a8]">Password</label>
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="mt-1 w-full rounded-lg bg-[#050b1a] border border-[#202a3e] px-3 py-1.5 text-xs text-white placeholder-[#8a94a8] focus:border-[#946eff] focus:outline-none"
              />
            </div>
          </div>
          <div className="flex items-center justify-between pt-1">
            <div className="flex items-center gap-4 text-xs text-[#8a94a8]">
              <label className="flex items-center gap-1.5">
                <input
                  type="radio"
                  name="role"
                  value="employee"
                  checked={role === "employee"}
                  onChange={() => setRole("employee")}
                />
                Employee
              </label>
              <label className="flex items-center gap-1.5">
                <input
                  type="radio"
                  name="role"
                  value="admin"
                  checked={role === "admin"}
                  onChange={() => setRole("admin")}
                />
                Admin
              </label>
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="rounded-lg bg-[#946eff] px-4 py-1.5 text-xs font-semibold text-white hover:bg-[#7c3aed] disabled:opacity-50"
            >
              {submitting ? "Adding..." : "Add Member"}
            </button>
          </div>
          {message && (
            <div className={`p-2.5 rounded-lg text-xs ${message.error ? "bg-red-500/10 border border-red-500/30 text-red-400" : "bg-emerald-500/10 border border-emerald-500/30 text-emerald-300"}`}>
              {message.text}
            </div>
          )}
        </form>
      )}

      {loading ? (
        <p className="text-center text-xs text-[#8a94a8] py-8">Loading members...</p>
      ) : (
        <div className="divide-y divide-[#202a3e] rounded-xl border border-[#202a3e] bg-[#0b1425] overflow-hidden">
          {members.map((m: any) => (
            <div key={m.id} className="p-3.5 flex items-center justify-between text-xs">
              <div className="flex items-center gap-3">
                <div className="size-8 rounded-full bg-[#202a3e] flex items-center justify-center font-semibold text-[#946eff]">
                  {(m.full_name || m.email || "U")[0].toUpperCase()}
                </div>
                <div>
                  <p className="font-semibold text-white">{m.full_name || "Team Member"}</p>
                  <p className="text-[#8a94a8] text-[11px]">{m.email}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`tag text-[10px] capitalize ${m.role === "admin" ? "tag-available" : ""}`}>
                  {m.role}
                </span>
                <span className="text-[10px] text-[#6a748a]">
                  Joined {new Date(m.joined_at || m.created_at || Date.now()).toLocaleDateString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function KnowledgePanel() {
  const [caseId, setCaseId] = React.useState("");
  const [query, setQuery] = React.useState("");
  const [records, setRecords] = React.useState<any[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [hasSearched, setHasSearched] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // PDF Upload states
  const [uploadCaseId, setUploadCaseId] = React.useState("");
  const [uploadFile, setUploadFile] = React.useState<File | null>(null);
  const [isUploading, setIsUploading] = React.useState(false);
  const [uploadMsg, setUploadMsg] = React.useState<string | null>(null);

  const fetchKnowledge = async () => {
    setIsLoading(true);
    setError(null);
    setHasSearched(true);
    try {
      const url = new URL("/api/ring1/knowledge", window.location.origin);
      if (caseId.trim()) url.searchParams.set("case_id", caseId.trim());
      if (query.trim()) url.searchParams.set("query", query.trim());

      const res = await fetch(url.toString());
      if (!res.ok) {
        throw new Error(`Failed to query knowledge (${res.status})`);
      }
      const data = await res.json();
      setRecords(data.records || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error querying case memory");
    } finally {
      setIsLoading(false);
    }
  };

  const handleUploadPdf = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile || !uploadCaseId.trim()) return;
    setIsUploading(true);
    setUploadMsg(null);
    try {
      const fd = new FormData();
      fd.append("file", uploadFile);
      fd.append("case_id", uploadCaseId.trim());
      fd.append("mode", "normal");
      fd.append("stream", "false");

      const res = await fetch("/api/ring1/upload-pdf", {
        method: "POST",
        body: fd,
      });
      const data = await res.json();
      if (res.ok) {
        setUploadMsg(`Document processed! Extracted ${data.summary?.scorecard?.persisted_facts || 0} facts into case memory.`);
        setCaseId(uploadCaseId.trim());
        setUploadFile(null);
        fetchKnowledge();
      } else {
        setUploadMsg(`Upload failed: ${data.detail || data.error || "Error processing PDF"}`);
      }
    } catch (err) {
      setUploadMsg(`Upload failed: ${String(err)}`);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Document Ingestion Card */}
      <div className="rounded-2xl border border-[#202a3e] bg-[#0b1425] p-5">
        <h3 className="text-base font-semibold text-white mb-1 flex items-center gap-2">
          <Upload className="size-4 text-[#946eff]" /> Ingest Legal PDF into Case Memory
        </h3>
        <p className="text-xs text-[#a7b0c1] mb-4">
          Upload contracts, filings, or evidence. Ring 1 Capability Mesh extracts facts, obligations, and parties.
        </p>

        <form onSubmit={handleUploadPdf} className="flex flex-wrap items-end gap-3">
          <div>
            <label className="text-xs text-[#8a94a8]">Target Case ID</label>
            <input
              type="text"
              placeholder="e.g. case-1042"
              value={uploadCaseId}
              onChange={(e) => setUploadCaseId(e.target.value)}
              required
              className="mt-1 block rounded-lg bg-[#050b1a] border border-[#202a3e] px-3 py-1.5 text-xs text-white placeholder-[#8a94a8] focus:border-[#946eff] focus:outline-none"
            />
          </div>
          <div className="flex-1 min-w-[220px]">
            <label className="text-xs text-[#8a94a8]">PDF File</label>
            <input
              type="file"
              accept=".pdf,application/pdf"
              onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
              required
              className="mt-1 block w-full text-xs text-[#a7b0c1] file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-[#202a3e] file:text-white hover:file:bg-[#34405a]"
            />
          </div>
          <button
            type="submit"
            disabled={isUploading || !uploadFile || !uploadCaseId.trim()}
            className="rounded-lg bg-[#946eff] px-4 py-1.5 text-xs font-semibold text-white hover:bg-[#7c3aed] disabled:opacity-50 transition-colors"
          >
            {isUploading ? "Ingesting..." : "Process via Mesh"}
          </button>
        </form>

        {uploadMsg && (
          <div className="mt-3 p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-300">
            {uploadMsg}
          </div>
        )}
      </div>

      {/* Case Memory Search Card */}
      <div className="rounded-2xl border border-[#202a3e] bg-[#0b1425] p-5">
        <h3 className="text-base font-semibold text-white mb-1">Case Knowledge &amp; Memory Records</h3>
        <p className="text-xs text-[#a7b0c1] mb-4">
          Query validated facts and structured legal knowledge persisted in PostgreSQL case memory.
        </p>

        <div className="flex flex-wrap gap-2">
          <input
            type="text"
            placeholder="Case ID (e.g. case-123)"
            value={caseId}
            onChange={(e) => setCaseId(e.target.value)}
            className="rounded-lg bg-[#050b1a] border border-[#202a3e] px-3 py-1.5 text-xs text-white placeholder-[#8a94a8] focus:border-[#946eff] focus:outline-none"
          />
          <input
            type="text"
            placeholder="Search keywords (e.g. contract, obligation)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 min-w-[200px] rounded-lg bg-[#050b1a] border border-[#202a3e] px-3 py-1.5 text-xs text-white placeholder-[#8a94a8] focus:border-[#946eff] focus:outline-none"
          />
          <button
            type="button"
            onClick={fetchKnowledge}
            disabled={isLoading}
            className="rounded-lg bg-[#946eff] px-4 py-1.5 text-xs font-semibold text-white hover:bg-[#7c3aed] disabled:opacity-50 transition-colors"
          >
            {isLoading ? "Searching..." : "Search Memory"}
          </button>
        </div>

        {error && (
          <div className="mt-3 p-2.5 rounded-lg bg-red-500/10 border border-red-500/30 text-xs text-red-400">
            {error}
          </div>
        )}
      </div>

      {hasSearched && (
        <div className="space-y-2">
          {records.length === 0 ? (
            <p className="rounded-2xl border border-[#202a3e] bg-[#0b1425] p-6 text-center text-xs text-[#8a94a8]">
              No validated memory records found matching criteria.
            </p>
          ) : (
            records.map((rec: any, idx: number) => (
              <div key={rec.id || idx} className="rounded-xl border border-[#202a3e] bg-[#0b1425] p-4 text-xs space-y-1.5">
                <div className="flex items-center justify-between text-[#8a94a8]">
                  <span className="font-mono text-[11px] font-semibold text-[#946eff]">
                    {rec.record_type || "knowledge_fact"}
                  </span>
                  <span className="text-[10px]">{rec.case_id ? `Case: ${rec.case_id}` : ""}</span>
                </div>
                <div className="text-white">
                  {rec.payload?.facts ? (
                    <ul className="list-disc pl-4 space-y-1">
                      {rec.payload.facts.map((f: any, fIdx: number) => (
                        <li key={fIdx}>{typeof f === "string" ? f : f.statement || JSON.stringify(f)}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>{rec.payload?.claim || rec.payload?.text || JSON.stringify(rec.payload)}</p>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

interface MessageItem {
  role: "user" | "assistant";
  content: string;
  context_ref_id?: string | null;
  retrieved_facts_count?: number;
  observation_id?: string | null;
}

function AIEmployeePanel() {
  const [input, setInput] = React.useState("");
  const [caseId, setCaseId] = React.useState("");
  const [messages, setMessages] = React.useState<MessageItem[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    const trimmedInput = input.trim();
    if (!trimmedInput || isLoading) return;

    setMessages((prev) => [...prev, { role: "user", content: trimmedInput }]);
    setInput("");
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/ai/prompt", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt: trimmedInput,
          context: "legal",
          case_id: caseId.trim() || undefined,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const message =
          errorData.error?.message ||
          (typeof errorData.error === "string" ? errorData.error : "") ||
          errorData.detail ||
          "AI request failed";
        throw new Error(message);
      }

      const data = await response.json();
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.content,
          context_ref_id: data.context_ref_id,
          retrieved_facts_count: data.retrieved_facts_count,
          observation_id: data.observation_id,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get AI response");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="rounded-2xl border border-[#202a3e] bg-[#0b1425] p-6">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white">Legal AI Employee</h3>
          <p className="text-xs text-[#8a94a8]">
            Cognitive architecture: Perception &rarr; Context &rarr; Retrieval &rarr; Reasoning &rarr; Observation
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-[#8a94a8]">Grounded Case Scope:</label>
          <input
            type="text"
            placeholder="Optional Case ID"
            value={caseId}
            onChange={(e) => setCaseId(e.target.value)}
            className="w-40 rounded-lg bg-[#050b1a] border border-[#202a3e] px-2.5 py-1 text-xs text-white placeholder-[#8a94a8] focus:border-[#946eff] focus:outline-none"
          />
        </div>
      </div>

      <div className="h-[400px] overflow-y-auto mb-4 space-y-4 p-4 rounded-xl bg-[#050b1a] border border-[#202a3e]">
        {messages.length === 0 ? (
          <div className="flex h-full items-center justify-center text-center">
            <p className="text-sm text-[#8a94a8]">
              Ask a question to test the Ring 1 AI Employee integration
            </p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-lg p-3 ${
                  msg.role === "user"
                    ? "bg-[#946eff] text-white"
                    : "bg-[#202a3e] text-[#a7b0c1]"
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>

                {msg.role === "assistant" && (msg.retrieved_facts_count ?? 0) > 0 && (
                  <div className="mt-2 pt-2 border-t border-white/10 text-[10px] text-emerald-300 flex items-center gap-1.5 flex-wrap">
                    <span className="font-semibold">&bull; Grounded:</span>
                    <span>{msg.retrieved_facts_count} verified case facts</span>
                    {msg.observation_id && (
                      <span className="text-[#8a94a8]">
                        | Audit Obs: <span className="font-mono">{msg.observation_id.slice(0, 8)}...</span>
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/30 p-3 text-sm text-red-400">
          {error}
        </div>
      )}

      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask the Legal AI Employee..."
          disabled={isLoading}
          className="flex-1 rounded-lg bg-[#050b1a] border border-[#202a3e] px-4 py-2 text-sm text-white placeholder-[#8a94a8] focus:outline-none focus:border-[#946eff] disabled:opacity-50"
        />
        <button
          onClick={sendMessage}
          disabled={isLoading || !input.trim()}
          className="rounded-lg bg-[#946eff] px-4 py-2 text-sm font-semibold text-white hover:bg-[#7c3aed] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? "Sending..." : "Send"}
        </button>
      </div>
    </div>
  );
}
