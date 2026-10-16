"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, FileText, Plus, RotateCw, X } from "lucide-react";
import { prototypeNote, uploadCopy } from "@/content/app";
import {
  FlowBody,
  FlowContinue,
  FlowShell,
  FlowTitle,
} from "@/components/onboarding/flow";
import { PrototypeBadge } from "@/components/auth/prototype-badge";
import { Button } from "@/components/ui/button";
import { useOnboarding } from "@/hooks/use-onboarding";
import { cn } from "@/lib/utils";

const copy = uploadCopy;

/** Prototype formats from the source app — explicitly unconfirmed (copy says so). */
const ALLOWED_EXTENSIONS = ["pdf", "docx", "txt"];
/** Expected upload contract location (docs/FLOW_AUDIT.md, contract 4). MOCK: does not exist yet — a real request is made and its real failure is surfaced. */
const UPLOAD_ENDPOINT = "/api/documents/upload";

type FileStatus = "Queued" | "Uploading" | "Processed" | "Failed";

interface UploadItem {
  id: string;
  name: string;
  size: number;
  file: File;
  status: FileStatus;
  error?: string;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function extensionOf(name: string): string {
  return name.split(".").pop()?.toLowerCase() ?? "";
}

/**
 * SOP/organizational document upload (source view `upload`).
 * Task G: real file selection (picker + drag/drop), per-file statuses, retry,
 * unsupported-file and server-error handling. MOCK/blocked: no upload or
 * status API exists — the real endpoint request fails with a real 404 which
 * is surfaced honestly; nothing is ever shown as uploaded or processed.
 */
export default function UploadScreen() {
  const router = useRouter();
  const { state, update, hydrated } = useOnboarding();
  const [items, setItems] = React.useState<UploadItem[]>([]);
  const [dragging, setDragging] = React.useState(false);
  const [rejectedNote, setRejectedNote] = React.useState<string | null>(null);
  const inputRef = React.useRef<HTMLInputElement>(null);

  // Deep-link/refresh guards: every prior stage must exist first.
  React.useEffect(() => {
    if (!hydrated) return;
    if (!state.domain) router.replace("/onboarding/domains");
    else if (!state.accountMode) router.replace("/onboarding/usage");
    else if (!state.account) router.replace("/onboarding/account");
    else if (!state.survey) router.replace("/onboarding/survey");
  }, [hydrated, state.domain, state.accountMode, state.account, state.survey, router]);

  if (!hydrated || !state.domain || !state.accountMode || !state.account || !state.survey) {
    return null;
  }

  function addFiles(list: FileList | null) {
    if (!list?.length) return;
    const accepted: UploadItem[] = [];
    const rejected: string[] = [];
    for (const file of Array.from(list)) {
      if (ALLOWED_EXTENSIONS.includes(extensionOf(file.name))) {
        accepted.push({
          id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
          name: file.name,
          size: file.size,
          file,
          status: "Queued",
        });
      } else {
        rejected.push(file.name);
      }
    }
    setRejectedNote(rejected.length ? copy.rejected(rejected.join(", ")) : null);
    if (accepted.length) setItems((prev) => [...prev, ...accepted]);
  }

  function removeItem(id: string) {
    setItems((prev) => prev.filter((item) => item.id !== id));
  }

  function patch(id: string, patchItem: Partial<UploadItem>) {
    setItems((prev) => prev.map((item) => (item.id === id ? { ...item, ...patchItem } : item)));
  }

  async function uploadItem(item: UploadItem) {
    patch(item.id, { status: "Uploading", error: undefined });
    const body = new FormData();
    body.append("file", item.file);
    try {
      const res = await fetch(UPLOAD_ENDPOINT, { method: "POST", body });
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        const message = errorData.error || copy.failedEndpoint(res.status);
        patch(item.id, { status: "Failed", error: message });
        return;
      }
      patch(item.id, { status: "Processed", error: undefined });
    } catch {
      patch(item.id, { status: "Failed", error: copy.failedNetwork });
    }
  }

  function uploadPending() {
    const pending = items.filter((i) => i.status === "Queued" || i.status === "Failed");
    void Promise.all(pending.map(uploadItem));
  }

  function retry(id: string) {
    const item = items.find((i) => i.id === id);
    if (item) void uploadItem(item);
  }

  const failedCount = items.filter((i) => i.status === "Failed").length;

  function continueToBuild() {
    update({
      uploaded: true,
      partial: failedCount > 0,
      upload: { total: items.length, failed: failedCount },
    });
    router.push("/onboarding/build");
  }

  return (
    <FlowShell as="section">
      <PrototypeBadge className="mt-8" />
      <FlowTitle id="upload-title" className="mt-5">
        {copy.title}
      </FlowTitle>
      <FlowBody>{copy.subtitle}</FlowBody>

      {/* Real blocker notice (task G: show "status unavailable" + list blocker). */}
      <p
        role="note"
        className="mt-6 flex w-full max-w-md items-start gap-2 rounded-xl border border-gold/40 bg-gold/10 px-3.5 py-3 text-left text-sm text-[#f3ca78]"
      >
        <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
        <span>{copy.blocker}</span>
      </p>

      {/* Drop zone with real file input. */}
      <div
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          addFiles(event.dataTransfer.files);
        }}
        className={cn(
          "mt-6 flex w-full max-w-md flex-col items-center gap-3 rounded-2xl border border-dashed px-5 py-8 text-center transition-colors",
          dragging ? "border-[#946eff] bg-[#946eff]/10" : "border-[#34405a] bg-[#0b1425]",
        )}
      >
        <FileText className="size-8 text-[#8a94a8]" aria-hidden="true" />
        <input
          ref={inputRef}
          id="upload-input"
          type="file"
          multiple
          accept=".pdf,.docx,.txt"
          className="sr-only"
          tabIndex={-1}
          aria-hidden="true"
          onChange={(event) => {
            addFiles(event.target.files);
            event.target.value = ""; // allow re-selecting the same file
          }}
        />
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className={buttonLike}
        >
          {copy.choose}
        </button>
        <p className="text-xs text-[#8a94a8]">{copy.dropHint}</p>
        <p className="text-xs text-[#8a94a8]">
          {copy.formats} — {copy.sampleNote}
        </p>
      </div>

      {rejectedNote && (
        <p role="alert" className="mt-3 w-full max-w-md text-sm text-danger">
          {rejectedNote}
        </p>
      )}

      {/* Per-file list with real statuses. */}
      {items.length === 0 ? (
        <p className="mt-6 text-sm text-[#8a94a8]">{copy.empty}</p>
      ) : (
        <ul className="mt-6 w-full max-w-md space-y-2">
          {items.map((item) => (
            <li
              key={item.id}
              className="flex flex-wrap items-center gap-3 rounded-xl border border-[#202a3e] bg-[#0b1425] px-3.5 py-3"
            >
              <FileText className="size-4 shrink-0 text-[#8a94a8]" aria-hidden="true" />
              <span className="min-w-0 flex-1 truncate text-left text-sm">{item.name}</span>
              <span className="text-xs text-[#8a94a8]">{formatSize(item.size)}</span>
              <span
                className={cn(
                  "status-chip",
                  item.status === "Processed" && "processed",
                  item.status === "Failed" && "failed",
                  item.status === "Uploading" && "uploading",
                  item.status === "Queued" && "queued",
                )}
              >
                {item.status === "Processed"
                  ? "Processed"
                  : item.status === "Uploading"
                    ? copy.uploading
                    : item.status === "Failed"
                      ? "Failed"
                      : "Queued"}
              </span>
              <span className="flex items-center gap-1">
                {item.status === "Failed" && (
                  <button
                    type="button"
                    onClick={() => retry(item.id)}
                    aria-label={`${copy.retry}: ${item.name}`}
                    className="rounded-lg p-1.5 text-[#a7b0c1] transition-colors hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
                  >
                    <RotateCw className="size-3.5" aria-hidden="true" />
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => removeItem(item.id)}
                  aria-label={`${copy.remove}: ${item.name}`}
                  className="rounded-lg p-1.5 text-[#a7b0c1] transition-colors hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
                >
                  <X className="size-3.5" aria-hidden="true" />
                </button>
              </span>
              {item.error && (
                <span className="w-full text-left text-xs text-danger">{item.error}</span>
              )}
            </li>
          ))}
        </ul>
      )}

      <div className="mt-8 flex w-full max-w-md flex-col gap-2.5 sm:flex-row sm:justify-center">
        <Button
          variant="secondary"
          size="lg"
          className="w-full sm:w-auto"
          disabled={items.length === 0}
          onClick={uploadPending}
        >
          <Plus className="size-4" aria-hidden="true" />
          {copy.uploadAll}
        </Button>
        <FlowContinue
          onClick={continueToBuild}
          disabled={items.some((i) => i.status === "Uploading")}
        >
          {copy.continue}
        </FlowContinue>
      </div>

      <p className="mt-6 max-w-md text-xs leading-relaxed text-[#8a94a8]">{prototypeNote}</p>
    </FlowShell>
  );
}

const buttonLike =
  "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-xl border border-[#946eff] bg-brand px-5 text-sm font-semibold text-brand-fg transition-transform hover:-translate-y-px focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring";
