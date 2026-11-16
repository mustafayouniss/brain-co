import { NextRequest, NextResponse } from "next/server";
import { getServerBackendApiUrl } from "@/lib/server-backend-url";

const COOKIE_NAME = "backend_token";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ caseId: string }> }
) {
  try {
    const { caseId } = await params;
    const token = request.cookies.get(COOKIE_NAME)?.value;
    const { searchParams } = new URL(request.url);
    const runId = searchParams.get("run_id");
    const sinceSequence = searchParams.get("since_sequence");
    const limit = searchParams.get("limit");

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const backendUrl = new URL(`${getServerBackendApiUrl()}/cases/${caseId}/events`);
    if (runId) backendUrl.searchParams.set("run_id", runId);
    if (sinceSequence) backendUrl.searchParams.set("since_sequence", sinceSequence);
    if (limit) backendUrl.searchParams.set("limit", limit);

    const res = await fetch(backendUrl.toString(), {
      method: "GET",
      headers,
      cache: "no-store",
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return NextResponse.json(err, { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Failed to retrieve case events" },
      { status: 500 }
    );
  }
}
