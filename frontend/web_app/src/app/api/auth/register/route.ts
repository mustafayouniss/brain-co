import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { accountSchema } from "@/lib/validation";
import { createSessionToken, sessionCookieOptions, SESSION_COOKIE } from "@/lib/session";
import { rateLimit, clientIp } from "@/lib/rate-limit";

const bodySchema = z.object({
  accountMode: z.enum(["personal", "company"]),
  fullName: z.string(),
  email: z.string(),
  password: z.string(),
  confirmPassword: z.string(),
  companyName: z.string().optional(),
});

/**
 * POST /api/auth/register — MOCK registration (docs/FLOW_AUDIT.md §5-6).
 * No user database exists: this route validates exactly like the future real
 * endpoint (same Zod schema, same field-error shape, same session cookie) and
 * issues the simulated session. Replace with a real contract — never present
 * this as real account creation (the UI labels the flow as prototype/MOCK).
 */
export async function POST(request: NextRequest) {
  const ip = clientIp(request);
  if (!rateLimit(`register:${ip}`, 10, 60_000)) {
    return NextResponse.json({ error: "Too many attempts. Try again shortly." }, { status: 429 });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }

  const parsedBody = bodySchema.safeParse(body);
  if (!parsedBody.success) {
    return NextResponse.json({ error: "Invalid input." }, { status: 400 });
  }

  const { accountMode, ...values } = parsedBody.data;
  const parsed = accountSchema(accountMode === "company").safeParse(values);
  if (!parsed.success) {
    const fields: Record<string, string> = {};
    for (const issue of parsed.error.issues) {
      const key = String(issue.path[0] ?? "");
      if (key && !fields[key]) fields[key] = issue.message;
    }
    return NextResponse.json(
      { error: "Please fix the highlighted fields.", fields },
      { status: 400 },
    );
  }

  // MOCK: a real backend would create the user (and organization) here.
  const token = createSessionToken({ email: parsed.data.email, name: parsed.data.fullName });
  const response = NextResponse.json({
    ok: true,
    mock: true,
    user: { email: parsed.data.email, name: parsed.data.fullName },
  });
  response.cookies.set(SESSION_COOKIE, token, sessionCookieOptions);
  return response;
}
