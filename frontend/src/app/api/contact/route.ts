import { NextRequest, NextResponse } from "next/server";
import { contactSchema } from "@/lib/validation";
import { sanitizeText, isEmail } from "@/lib/utils";
import { clientIp, rateLimit } from "@/lib/rate-limit";
import { site } from "@/content/site";

/**
 * POST /api/contact — validates (Zod) + sanitizes the contact form, applies a
 * honeypot and a rate limit, then forwards to CONTACT_ENDPOINT when configured.
 * Without an endpoint it acknowledges locally (the source product has no
 * backend to receive messages).
 */
export async function POST(request: NextRequest) {
  const ip = clientIp(request);
  if (!rateLimit(`contact:${ip}`, 5, 60_000)) {
    return NextResponse.json(
      { error: "Too many messages. Please wait a moment and try again." },
      { status: 429 },
    );
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }

  const parsed = contactSchema.safeParse(body);
  if (!parsed.success) {
    const issue = parsed.error.issues[0];
    return NextResponse.json(
      { error: issue?.message ?? "Invalid input.", field: issue?.path[0] },
      { status: 400 },
    );
  }

  const payload = {
    name: sanitizeText(parsed.data.name, 120),
    email: sanitizeText(parsed.data.email, 200),
    company: sanitizeText(parsed.data.company ?? "", 120),
    topic: parsed.data.topic,
    message: sanitizeText(parsed.data.message, 4000),
    source: "brain-co-website",
    submittedAt: new Date().toISOString(),
  };

  if (!isEmail(payload.email)) {
    return NextResponse.json({ error: "Invalid email." }, { status: 400 });
  }

  if (site.contactEndpoint) {
    try {
      const upstream = await fetch(site.contactEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(8000),
      });
      if (!upstream.ok) {
        return NextResponse.json(
          { error: "The message could not be delivered. Please email us directly." },
          { status: 502 },
        );
      }
    } catch {
      return NextResponse.json(
        { error: "The message could not be delivered. Please email us directly." },
        { status: 502 },
      );
    }
  } else {
    // No endpoint configured: acknowledge and log for the demo deployment.
    console.info("[contact]", payload.topic, payload.email, payload.message.length);
  }

  return NextResponse.json({ ok: true });
}
