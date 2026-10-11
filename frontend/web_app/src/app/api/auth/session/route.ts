import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import {
  createSessionToken,
  sessionCookieOptions,
  SESSION_COOKIE,
  verifySessionToken,
} from "@/lib/session";

/** GET /api/auth/session — current session (used by the navbar). */
export async function GET(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  const user = verifySessionToken(token);
  return NextResponse.json({ user: user ? { email: user.email, name: user.name } : null });
}

const startSchema = z.object({
  email: z.string().trim().email(),
  name: z.string().trim().min(1).max(120),
});

/**
 * POST /api/auth/session — called when onboarding finishes ("Enter your
 * workspace"), mirroring the source flow where completing onboarding is what
 * grants access to the workspace.
 */
export async function POST(request: NextRequest) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }

  const parsed = startSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: "Invalid input." }, { status: 400 });
  }

  const response = NextResponse.json({ ok: true });
  response.cookies.set(
    SESSION_COOKIE,
    createSessionToken(parsed.data),
    sessionCookieOptions,
  );
  return response;
}
