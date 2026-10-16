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

  // In development/same-site, Origin may be null - check referer instead
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
    const body = await request.json();
    
    // Get token from HttpOnly cookie
    const token = request.cookies.get(COOKIE_NAME)?.value;
    if (!token) {
      return NextResponse.json(
        { error: "Missing authentication" },
        { status: 401 }
      );
    }

    // Forward request to backend with Bearer token
    const response = await fetch(`${BACKEND_API_URL}/ai/prompt`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        errorData,
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to process AI request" },
      { status: 500 }
    );
  }
}
