import { NextRequest, NextResponse } from "next/server";
import { loginSchema } from "@/lib/validation";
import { createSessionToken, sessionCookieOptions, SESSION_COOKIE } from "@/lib/session";
import { rateLimit, clientIp } from "@/lib/rate-limit";

/**
 * POST /api/auth/login — simulated session (no user database exists in the
 * source product). Accepts any valid email + password of 8+ characters and
 * issues an HMAC-signed, httpOnly session cookie.
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

  const { email } = parsed.data;
  const token = createSessionToken({
    email,
    name: email.split("@")[0].replace(/[._-]+/g, " "),
  });

  const response = NextResponse.json({ ok: true });
  response.cookies.set(SESSION_COOKIE, token, sessionCookieOptions);
  return response;
}
