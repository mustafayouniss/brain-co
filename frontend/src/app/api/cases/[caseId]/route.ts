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
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch(`${getServerBackendApiUrl()}/cases/${caseId}`, {
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
      { error: error instanceof Error ? error.message : "Failed to retrieve case details" },
      { status: 500 }
    );
  }
}
