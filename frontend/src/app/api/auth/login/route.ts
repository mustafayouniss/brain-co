import { NextRequest, NextResponse } from "next/server";
import { loginToBackend } from "@/lib/backend-auth";

const BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL || "http://localhost:8000/api/v1";
const COOKIE_NAME = "backend_token";
const COOKIE_MAX_AGE = 60 * 60; // 60 minutes in seconds (matches backend ACCESS_TOKEN_EXPIRE_MINUTES)

/**
 * Simple CSRF protection: verify request comes from same origin for state-changing operations.
 * This is a basic check; for production, consider implementing CSRF tokens.
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
    const { email, password } = body;

    if (!email || !password) {
      return NextResponse.json(
        { error: "Email and password are required" },
        { status: 400 }
      );
    }

    // Authenticate with FastAPI backend
    const response = await loginToBackend({ email, password });

    // Set HttpOnly cookie with JWT
    const cookieValue = response.access_token;
    const isSecure = process.env.NODE_ENV === "production";

    const cookieOptions = [
      `${COOKIE_NAME}=${cookieValue}`,
      "HttpOnly",
      "Path=/",
      `Max-Age=${COOKIE_MAX_AGE}`,
      isSecure ? "Secure" : "",
      "SameSite=Lax",
    ].filter(Boolean).join("; ");

    const headers = new Headers();
    headers.append("Set-Cookie", cookieOptions);

    return NextResponse.json(
      { success: true },
      { headers, status: 200 }
    );
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : "Login failed";
    return NextResponse.json(
      { error: errorMessage },
      { status: 401 }
    );
  }
}
