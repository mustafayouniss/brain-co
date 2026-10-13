import { NextRequest, NextResponse } from "next/server";
import { loginSchema } from "@/lib/validation";
import { rateLimit, clientIp } from "@/lib/rate-limit";
import { loginToBackend } from "@/lib/backend-auth";

/**
 * POST /api/auth/login — Backend JWT authentication
 * 
 * This endpoint now proxies to the backend JWT authentication API.
 * The backend performs real credential validation and returns a JWT token.
 * 
 * Backend contract: docs/backend/api/auth.md
 * Backend endpoint: POST /api/v1/auth/login
 */
export async function POST(request: NextRequest) {
  const ip = clientIp(request);
  if (!rateLimit(`login:${ip}`, 10, 60_000)) {
    return NextResponse.json({ error: "Too many attempts. Try again shortly." }, { status: 429 });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }

  const parsed = loginSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: parsed.error.issues[0]?.message ?? "Invalid input." },
      { status: 400 },
    );
  }

  const { email, password } = parsed.data;

  try {
    // Call backend JWT authentication
    const backendResponse = await loginToBackend({ email, password });

    // Return the backend token to the client
    // The client should store this token and include it in Authorization headers
    const response = NextResponse.json({
      ok: true,
      access_token: backendResponse.access_token,
      token_type: backendResponse.token_type,
    });

    return response;
  } catch (error) {
    const message = error instanceof Error ? error.message : "Authentication failed";
    return NextResponse.json({ error: message }, { status: 401 });
  }
}
