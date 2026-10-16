import { NextRequest, NextResponse } from "next/server";

const BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL || "http://localhost:8000/api/v1";
const COOKIE_NAME = "backend_token";

/**
 * Simple CSRF protection: verify request comes from same origin for state-changing operations.
 */
function verifySameOrigin(request: NextRequest): boolean {
  const origin = request.headers.get("origin");
  const referer = request.headers.get("referer");
  const host = request.headers.get("host");

  if (!origin && referer) {
    try {
      const refererUrl = new URL(referer);
      const allowedHosts = [
        "localhost:3000",
        "localhost:3001",
        host || "",
      ];
      return allowedHosts.includes(refererUrl.host);
    } catch {
      return false;
    }
  }

  if (!origin) {
    return true;
  }

  const originUrl = new URL(origin);
  const allowedHosts = [
    "localhost:3000",
    "localhost:3001",
    host || "",
  ];

  return allowedHosts.includes(originUrl.host);
}

export async function POST(request: NextRequest) {
  // CSRF protection
  if (!verifySameOrigin(request)) {
    return NextResponse.json(
      { error: "Invalid origin" },
      { status: 403 }
    );
  }

  try {
    const token = request.cookies.get(COOKIE_NAME)?.value;
    if (!token) {
      return NextResponse.json(
        { error: "Authentication required — please log in to upload documents." },
        { status: 401 }
      );
    }

    const formData = await request.formData();
    const file = formData.get("file");

    if (!file || !(file instanceof Blob)) {
      return NextResponse.json(
        { error: "A valid file is required." },
        { status: 400 }
      );
    }

    // Forward file to FastAPI backend /sources endpoint
    const backendFormData = new FormData();
    backendFormData.append("file", file, file instanceof File ? file.name : "upload.txt");

    const response = await fetch(`${BACKEND_API_URL}/sources`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
      },
      body: backendFormData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const message = errorData.detail || errorData.error?.message || "Source ingestion failed";
      return NextResponse.json(
        { error: message },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json({ success: true, source: data }, { status: 201 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Document upload failed";
    return NextResponse.json(
      { error: message },
      { status: 500 }
    );
  }
}
