import { NextRequest, NextResponse } from "next/server";

const BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL || "http://localhost:8000/api/v1";
const COOKIE_NAME = "backend_token";

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const token = request.cookies.get(COOKIE_NAME)?.value;

    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const backendResponse = await fetch(`${BACKEND_API_URL}/ring1/upload-pdf`, {
      method: "POST",
      headers,
      body: formData,
    });

    if (!backendResponse.ok) {
      const err = await backendResponse.json().catch(() => ({}));
      return NextResponse.json(err, { status: backendResponse.status });
    }

    const contentType = backendResponse.headers.get("content-type") || "";
    if (contentType.includes("text/event-stream") && backendResponse.body) {
      return new NextResponse(backendResponse.body, {
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache, no-transform",
          "Connection": "keep-alive",
          "X-Accel-Buffering": "no",
        },
      });
    }

    const data = await backendResponse.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to forward PDF to Ring 1 pipeline", details: String(error) },
      { status: 500 }
    );
  }
}
