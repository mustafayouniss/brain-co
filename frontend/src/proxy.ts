import { NextRequest, NextResponse } from "next/server";

const BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL || "http://localhost:8000/api/v1";
const AUTH_COOKIE = "backend_token";

/**
 * Route guard for the protected workspace.
 * Validates JWT token with FastAPI backend.
 * Next.js 16 renamed middleware → proxy (nodejs runtime).
 */
export async function proxy(request: NextRequest) {
  const token = request.cookies.get(AUTH_COOKIE)?.value;
  
  if (!token) {
    const login = new URL("/login", request.url);
    login.searchParams.set("next", "/workspace");
    return NextResponse.redirect(login);
  }

  // Validate token with backend
  try {
    const response = await fetch(`${BACKEND_API_URL}/auth/me`, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const login = new URL("/login", request.url);
      login.searchParams.set("next", "/workspace");
      return NextResponse.redirect(login);
    }
  } catch (error) {
    // Backend unreachable - fail closed and redirect to login
    const login = new URL("/login", request.url);
    login.searchParams.set("next", "/workspace");
    return NextResponse.redirect(login);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/workspace/:path*"],
};
