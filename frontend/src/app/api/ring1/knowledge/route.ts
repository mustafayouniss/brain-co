import { NextRequest, NextResponse } from "next/server";

const BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL || "http://localhost:8000/api/v1";
const COOKIE_NAME = "backend_token";

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const orgId = searchParams.get("organization_id") || "";
    const caseId = searchParams.get("case_id") || "";
    const query = searchParams.get("query") || "";

    const token = request.cookies.get(COOKIE_NAME)?.value;
    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const backendUrl = new URL(`${BACKEND_API_URL}/ring1/knowledge`);
    backendUrl.searchParams.set("organization_id", orgId);
    backendUrl.searchParams.set("case_id", caseId);
    if (query) {
      backendUrl.searchParams.set("query", query);
    }

    const backendResponse = await fetch(backendUrl.toString(), {
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
      { error: "Failed to query case knowledge", details: String(error) },
      { status: 500 }
    );
  }
}
