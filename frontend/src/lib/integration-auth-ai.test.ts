import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { getServerBackendApiUrl } from "./server-backend-url.ts";
import { generateAIResponse } from "./backend-ai.ts";
import { loginToBackend, getCurrentUser } from "./backend-auth.ts";

describe("server-side auth and AI URL routing", () => {
  it("resolves backend-auth and proxy target to internal Docker URL when INTERNAL_BACKEND_URL is set", () => {
    const prev = process.env.INTERNAL_BACKEND_URL;
    try {
      process.env.INTERNAL_BACKEND_URL = "http://backend:8000";
      assert.equal(getServerBackendApiUrl(), "http://backend:8000/api/v1");
    } finally {
      process.env.INTERNAL_BACKEND_URL = prev;
    }
  });

  it("loginToBackend uses the resolved server internal backend URL", async () => {
    const originalFetch = globalThis.fetch;
    const requestedUrls: string[] = [];

    globalThis.fetch = (async (input: RequestInfo | URL) => {
      requestedUrls.push(String(input));
      return {
        ok: true,
        json: async () => ({
          access_token: "mock-jwt-token",
          token_type: "bearer",
        }),
      } as Response;
    }) as typeof fetch;

    try {
      process.env.INTERNAL_BACKEND_URL = "http://backend:8000";
      const res = await loginToBackend({ email: "test@example.com", password: "Password123!" });
      assert.equal(res.access_token, "mock-jwt-token");
      assert.equal(requestedUrls.length, 1);
      assert.equal(requestedUrls[0], "http://backend:8000/api/v1/auth/login");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("getCurrentUser uses the resolved server internal backend URL", async () => {
    const originalFetch = globalThis.fetch;
    const requestedUrls: string[] = [];

    globalThis.fetch = (async (input: RequestInfo | URL) => {
      requestedUrls.push(String(input));
      return {
        ok: true,
        json: async () => ({
          id: "u-123",
          email: "test@example.com",
          full_name: "Test User",
          role: "admin",
          is_active: true,
          created_at: "2026-11-16T00:00:00Z",
        }),
      } as Response;
    }) as typeof fetch;

    try {
      process.env.INTERNAL_BACKEND_URL = "http://backend:8000";
      const user = await getCurrentUser("mock-token");
      assert.equal(user.email, "test@example.com");
      assert.equal(requestedUrls.length, 1);
      assert.equal(requestedUrls[0], "http://backend:8000/api/v1/auth/me");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("generateAIResponse uses same-origin proxy in browser and internal backend on server", async () => {
    const originalFetch = globalThis.fetch;
    const requestedUrls: string[] = [];

    // Mock fetch
    globalThis.fetch = (async (input: RequestInfo | URL) => {
      requestedUrls.push(String(input));
      return {
        ok: true,
        json: async () => ({
          content: "AI response",
          model: "gemini-3.5-flash-lite",
          tokens: 42,
        }),
      } as Response;
    }) as typeof fetch;

    try {
      process.env.INTERNAL_BACKEND_URL = "http://backend:8000";

      // 1. In server context (window is undefined)
      await generateAIResponse("mock-token", { prompt: "Test prompt" });
      assert.equal(requestedUrls.length, 1);
      assert.equal(requestedUrls[0], "http://backend:8000/api/v1/ai/prompt");

      // 2. In browser context (window is defined)
      (globalThis as unknown as { window: unknown }).window = {};
      await generateAIResponse("mock-token", { prompt: "Client prompt" });
      assert.equal(requestedUrls.length, 2);
      assert.equal(requestedUrls[1], "/api/ai/prompt");
    } finally {
      delete (globalThis as unknown as { window?: unknown }).window;
      globalThis.fetch = originalFetch;
    }
  });
});
