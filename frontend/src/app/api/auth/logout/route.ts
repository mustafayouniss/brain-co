import { NextRequest, NextResponse } from "next/server";

const COOKIE_NAME = "backend_token";

/**
 * Simple CSRF protection: verify request comes from same origin for state-changing operations.
 */
function verifySameOrigin(request: NextRequest): boolean {
  const origin = request.headers.get("origin");
  const host = request.headers.get("host");

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

  // Clear the HttpOnly cookie using Set-Cookie header
  const isSecure = process.env.NODE_ENV === "production";
  const cookieOptions = [
    `${COOKIE_NAME}=`,
    "HttpOnly",
    "Path=/",
    "Max-Age=0",
    "Expires=Thu, 01 Jan 1970 00:00:00 GMT",
    isSecure ? "Secure" : "",
    "SameSite=Lax",
  ].filter(Boolean).join("; ");

  const headers = new Headers();
  headers.append("Set-Cookie", cookieOptions);

  return NextResponse.json(
    { success: true },
    { headers, status: 200 }
  );
}
