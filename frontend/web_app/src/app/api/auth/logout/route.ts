import { NextResponse } from "next/server";
import { SESSION_COOKIE } from "@/lib/session";

/**
 * POST /api/auth/logout — clears the session cookie and instructs client to clear backend token.
 * 
 * The backend uses stateless JWT tokens with no server-side revocation.
 * Logout is performed by the client discarding the token.
 */
export async function POST() {
  const response = NextResponse.json({ ok: true, clearToken: true });
  // Clear legacy session cookie if present
  response.cookies.set(SESSION_COOKIE, "", {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 0,
  });
  return response;
}
