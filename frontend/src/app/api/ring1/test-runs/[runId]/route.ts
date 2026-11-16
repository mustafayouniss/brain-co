import { NextRequest, NextResponse } from "next/server";
import { getServerBackendApiUrl } from "@/lib/server-backend-url";

const COOKIE_NAME = "backend_token";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ runId: string }> }
) {
  try {
    const { runId } = await params;
    const token = request.cookies.get(COOKIE_NAME)?.value;

    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const backendResponse = await fetch(`${getServerBackendApiUrl()}/ring1/test-runs/${runId}`, {
      method: "GET",
      headers,
    });

    if (!backendResponse.ok) {
      const err = await backendResponse.json().catch(() => ({}));
      return NextResponse.json(err, { status: backendResponse.status });
    }

    const data = await backendResponse.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to fetch test run details", details: String(error) },
      { status: 500 }
    );
  }
}
