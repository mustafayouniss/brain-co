/**
 * Server-only Backend URL Resolver
 *
 * Centralizes resolution of the FastAPI backend URL for server-side code
 * (Next.js Route Handlers, Server Actions, Middleware/Proxy).
 *
 * Enforces:
 * 1. Server-side only execution (never leaks internal Docker hostnames to browser).
 * 2. Preference for `INTERNAL_BACKEND_URL` (Docker service DNS: http://backend:8000).
 * 3. Fallback to `BACKEND_API_URL`, `NEXT_PUBLIC_BACKEND_API_URL`, or `http://localhost:8000`.
 * 4. Trailing slash normalization.
 * 5. Exactly one `/api/v1` segment in the API URL.
 * 6. Explicit validation of URL structure and HTTP/HTTPS protocol.
 */

export interface ResolvedBackendUrls {
  /** Root backend URL without `/api/v1`, e.g. "http://backend:8000" */
  baseUrl: string;
  /** Full API v1 URL, e.g. "http://backend:8000/api/v1" */
  apiUrl: string;
}

/**
 * Normalizes and resolves backend URLs from a raw URL string or environment variables.
 *
 * @param overrideUrl Optional URL to resolve (primarily for testing)
 */
export function resolveServerBackendUrl(overrideUrl?: string): ResolvedBackendUrls {
  if (typeof window !== "undefined") {
    throw new Error(
      "Security Error: server-backend-url must only be invoked in server-side execution contexts."
    );
  }

  const rawUrl =
    overrideUrl ??
    process.env.INTERNAL_BACKEND_URL ??
    process.env.BACKEND_API_URL ??
    process.env.NEXT_PUBLIC_BACKEND_API_URL ??
    "http://localhost:8000";

  const trimmed = rawUrl.trim();
  if (!trimmed) {
    throw new Error("Configuration Error: Backend URL configuration is empty.");
  }

  let parsed: URL;
  try {
    parsed = new URL(trimmed);
  } catch {
    throw new Error(
      `Configuration Error: Invalid backend URL '${trimmed}'. Must be a valid absolute URL.`
    );
  }

  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error(
      `Configuration Error: Unsupported protocol '${parsed.protocol}' in backend URL. Only HTTP and HTTPS are supported.`
    );
  }

  // Normalize origin and path: strip trailing slashes and any trailing /api/v1 or /api segments
  const origin = parsed.origin;
  let pathname = parsed.pathname.replace(/\/+$/, "");

  // Strip duplicate /api/v1 or /api at the end of pathname
  pathname = pathname.replace(/\/api\/v1(?:\/api\/v1)*\/?$/, "");
  pathname = pathname.replace(/\/api\/?$/, "");
  pathname = pathname.replace(/\/+$/, "");

  const baseUrl = `${origin}${pathname}`;
  const apiUrl = `${baseUrl}/api/v1`;

  return { baseUrl, apiUrl };
}

/**
 * Returns the resolved server-side API URL with `/api/v1` appended exactly once.
 * E.g., "http://backend:8000/api/v1"
 */
export function getServerBackendApiUrl(): string {
  return resolveServerBackendUrl().apiUrl;
}

/**
 * Returns the resolved server-side base URL without `/api/v1`.
 * E.g., "http://backend:8000"
 */
export function getServerBackendBaseUrl(): string {
  return resolveServerBackendUrl().baseUrl;
}
