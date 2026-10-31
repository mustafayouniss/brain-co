import { NextRequest, NextResponse } from "next/server";

const BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL || "http://localhost:8000/api/v1";
const COOKIE_NAME = "backend_token";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const token = request.cookies.get(COOKIE_NAME)?.value;

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const backendResponse = await fetch(`${BACKEND_API_URL}/ring1/test-run`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });

    if (!backendResponse.ok) {
      const err = await backendResponse.json().catch(() => ({}));
      return NextResponse.json(err, { status: backendResponse.status });
    }

    // If client requested SSE streaming, pipe the ReadableStream directly
    if (body.stream && backendResponse.body) {
      return new NextResponse(backendResponse.body, {
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache, no-transform",
          "Connection": "keep-alive",
          "X-Accel-Buffering": "no",
        },
      });
    }

    // Otherwise return JSON
    const data = await backendResponse.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to communicate with Ring 1 test runner", details: String(error) },
      { status: 500 }
    );
  }
}
