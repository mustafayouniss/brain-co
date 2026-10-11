import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE, verifySessionToken } from "@/lib/session";

/**
 * Route guard for the protected workspace.
 * Next.js 16 renamed middleware → proxy (nodejs runtime).
 */
export function proxy(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!verifySessionToken(token)) {
    const login = new URL("/login", request.url);
    login.searchParams.set("next", "/workspace");
    return NextResponse.redirect(login);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/workspace/:path*"],
};
