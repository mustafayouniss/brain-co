import { createHmac, timingSafeEqual } from "node:crypto";

/**
 * Signed session cookies — the source app has no backend, so sessions are a
 * minimal HMAC-signed cookie layer that enables real protected routes without
 * inventing a user database. Demo mode accepts any valid email + 8-char
 * password (clearly documented in the UI and README).
 */
export const SESSION_COOKIE = "brainco_session";
export const SESSION_MAX_AGE = 60 * 60 * 24 * 7; // 7 days

const SECRET = process.env.SESSION_SECRET ?? "brain-co-dev-secret-change-in-prod";

export interface SessionUser {
  email: string;
  name: string;
  exp: number;
}

function sign(body: string): string {
  return createHmac("sha256", SECRET).update(body).digest("base64url");
}

export function createSessionToken(user: { email: string; name: string }): string {
  const payload: SessionUser = {
    email: user.email,
    name: user.name,
    exp: Date.now() + SESSION_MAX_AGE * 1000,
  };
  const body = Buffer.from(JSON.stringify(payload)).toString("base64url");
  return `${body}.${sign(body)}`;
}

export function verifySessionToken(token: string | undefined | null): SessionUser | null {
  if (!token) return null;
  const [body, signature] = token.split(".");
  if (!body || !signature) return null;

  const expected = Buffer.from(sign(body));
  const actual = Buffer.from(signature);
  if (expected.length !== actual.length || !timingSafeEqual(expected, actual)) {
    return null;
  }

  try {
    const payload = JSON.parse(
      Buffer.from(body, "base64url").toString("utf8"),
    ) as SessionUser;
    if (typeof payload.exp !== "number" || payload.exp < Date.now()) return null;
    if (typeof payload.email !== "string") return null;
    return payload;
  } catch {
    return null;
  }
}

export const sessionCookieOptions = {
  httpOnly: true,
  sameSite: "lax" as const,
  secure: process.env.NODE_ENV === "production",
  path: "/",
  maxAge: SESSION_MAX_AGE,
};
