import { NextRequest, NextResponse } from "next/server";
import { registerOrganizationToBackend } from "@/lib/backend-auth";

const COOKIE_NAME = "backend_token";
const COOKIE_MAX_AGE = 60 * 60; // 60 minutes in seconds

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
    const body = await request.json();
    const { company_name, admin_full_name, admin_email, password, domain } = body;

    if (!company_name || !admin_full_name || !admin_email || !password) {
      return NextResponse.json(
        { error: "Company name, administrator name, work email, and password are required" },
        { status: 400 }
      );
    }

    // Call FastAPI backend to atomically register organization + user + membership
    const response = await registerOrganizationToBackend({
      company_name,
      admin_full_name,
      admin_email,
      password,
      domain: domain || "legal",
    });

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
      {
        success: true,
        organization: response.organization,
        user: response.user,
        membership: response.membership,
      },
      { headers, status: 201 }
    );
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : "Registration failed";
    return NextResponse.json(
      { error: errorMessage },
      { status: 400 }
    );
  }
}
