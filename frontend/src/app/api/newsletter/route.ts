import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { clientIp, rateLimit } from "@/lib/rate-limit";

const schema = z.object({
  email: z.string().trim().email("Enter a valid email address."),
});

/**
 * POST /api/newsletter — product-update opt-in. Forwards to NEWSLETTER_ENDPOINT
 * when configured; otherwise acknowledges (demo mode, documented in README).
 */
export async function POST(request: NextRequest) {
  const ip = clientIp(request);
  if (!rateLimit(`news:${ip}`, 5, 60_000)) {
    return NextResponse.json({ error: "Too many attempts. Try again shortly." }, { status: 429 });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }

  const parsed = schema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: parsed.error.issues[0]?.message ?? "Invalid email." },
      { status: 400 },
    );
  }

  const endpoint = process.env.NEWSLETTER_ENDPOINT ?? "";
  if (endpoint) {
    try {
      const upstream = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: parsed.data.email, source: "brain-co-website" }),
        signal: AbortSignal.timeout(8000),
      });
      if (!upstream.ok) throw new Error("upstream failed");
    } catch {
      return NextResponse.json({ error: "Subscription failed. Try again later." }, { status: 502 });
    }
  }

  return NextResponse.json({ ok: true });
}
