import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

const BACKEND_URL =
  process.env.INTERNAL_BACKEND_URL ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  "http://127.0.0.1:8000";

/**
 * Issues a short-lived single-use WebSocket ticket without exposing the JWT to JavaScript.
 *
 * Reads the HttpOnly `backend_token` cookie server-side and exchanges it for a 60-second
 * cryptographically secure ticket bound to the user's organization and case scope.
 */
export async function POST(req: NextRequest) {
  const cookieStore = await cookies();
  const token = cookieStore.get("backend_token")?.value;

  if (!token) {
    return NextResponse.json(
      { error: "Authentication required" },
      { status: 401 }
    );
  }

  let body = {};
  try {
    body = await req.json();
  } catch {
    // optional body
  }

  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/auth/ws-ticket`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return NextResponse.json(
        { error: err.detail || "Failed to obtain WebSocket ticket" },
        { status: res.status }
      );
    }

    const data = await res.json();
    // Return only the ephemeral ticket and expiration; NEVER expose the JWT!
    return NextResponse.json({
      ticket: data.ticket,
      expires_in: data.expires_in,
    });
  } catch (error) {
    console.error("Failed to request WebSocket ticket from backend:", error);
    return NextResponse.json(
      { error: "Internal server error communicating with backend" },
      { status: 500 }
    );
  }
}
