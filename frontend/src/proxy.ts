import { NextRequest, NextResponse } from "next/server";
import { getServerBackendApiUrl } from "@/lib/server-backend-url";

const AUTH_COOKIE = "backend_token";

function buildLoginRedirect(request: NextRequest): NextResponse {
  const login = new URL("/login", request.url);
  const pathname = request.nextUrl.pathname;
  // Preserve target workspace route while preventing open redirect
  const safeNext = pathname.startsWith("/workspace") ? pathname : "/workspace";
  login.searchParams.set("next", safeNext);
  return NextResponse.redirect(login);
}

/**
 * Route guard for the protected workspace.
 * Validates JWT token with FastAPI backend via internal server-to-server URL.
 * Next.js 16 renamed middleware → proxy (nodejs runtime).
 */
export async function proxy(request: NextRequest) {
  const token = request.cookies.get(AUTH_COOKIE)?.value;
  
  if (!token) {
    return buildLoginRedirect(request);
  }

  // Validate token with backend using internal Docker network or server URL
  try {
    const backendApiUrl = getServerBackendApiUrl();
    const response = await fetch(`${backendApiUrl}/auth/me`, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      return buildLoginRedirect(request);
    }
  } catch (_error) {
    // Backend unreachable - fail closed and redirect to login
    return buildLoginRedirect(request);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/workspace/:path*"],
};
