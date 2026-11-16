import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  resolveServerBackendUrl,
  getServerBackendApiUrl,
  getServerBackendBaseUrl,
} from "./server-backend-url.ts";

describe("server-backend-url resolver", () => {
  it("resolves basic Docker internal URL correctly", () => {
    const res = resolveServerBackendUrl("http://backend:8000");
    assert.equal(res.baseUrl, "http://backend:8000");
    assert.equal(res.apiUrl, "http://backend:8000/api/v1");
  });

  it("normalizes trailing slashes on base URL", () => {
    const res = resolveServerBackendUrl("http://backend:8000///");
    assert.equal(res.baseUrl, "http://backend:8000");
    assert.equal(res.apiUrl, "http://backend:8000/api/v1");
  });

  it("normalizes URL that already includes /api/v1", () => {
    const res = resolveServerBackendUrl("http://backend:8000/api/v1");
    assert.equal(res.baseUrl, "http://backend:8000");
    assert.equal(res.apiUrl, "http://backend:8000/api/v1");
  });

  it("normalizes URL that already includes /api/v1/ with trailing slash", () => {
    const res = resolveServerBackendUrl("http://backend:8000/api/v1/");
    assert.equal(res.baseUrl, "http://backend:8000");
    assert.equal(res.apiUrl, "http://backend:8000/api/v1");
  });

  it("prevents duplicate /api/v1 prefixes if erroneously concatenated", () => {
    const res = resolveServerBackendUrl("http://backend:8000/api/v1/api/v1");
    assert.equal(res.baseUrl, "http://backend:8000");
    assert.equal(res.apiUrl, "http://backend:8000/api/v1");
  });

  it("handles URLs with custom subpaths", () => {
    const res = resolveServerBackendUrl("https://example.com/org/service");
    assert.equal(res.baseUrl, "https://example.com/org/service");
    assert.equal(res.apiUrl, "https://example.com/org/service/api/v1");
  });

  it("throws clear configuration error on invalid URL", () => {
    assert.throws(
      () => resolveServerBackendUrl("not-a-valid-url"),
      /Configuration Error: Invalid backend URL/
    );
  });

  it("throws clear configuration error on unsupported protocol", () => {
    assert.throws(
      () => resolveServerBackendUrl("ftp://backend:21"),
      /Configuration Error: Unsupported protocol 'ftp:'/
    );
  });

  it("prioritizes INTERNAL_BACKEND_URL over NEXT_PUBLIC_BACKEND_API_URL", () => {
    const prevInternal = process.env.INTERNAL_BACKEND_URL;
    const prevPublic = process.env.NEXT_PUBLIC_BACKEND_API_URL;

    try {
      process.env.INTERNAL_BACKEND_URL = "http://backend:8000";
      process.env.NEXT_PUBLIC_BACKEND_API_URL = "http://localhost:8000/api/v1";

      assert.equal(getServerBackendBaseUrl(), "http://backend:8000");
      assert.equal(getServerBackendApiUrl(), "http://backend:8000/api/v1");
    } finally {
      process.env.INTERNAL_BACKEND_URL = prevInternal;
      process.env.NEXT_PUBLIC_BACKEND_API_URL = prevPublic;
    }
  });

  it("falls back to NEXT_PUBLIC_BACKEND_API_URL when INTERNAL_BACKEND_URL is absent", () => {
    const prevInternal = process.env.INTERNAL_BACKEND_URL;
    const prevPublic = process.env.NEXT_PUBLIC_BACKEND_API_URL;

    try {
      delete process.env.INTERNAL_BACKEND_URL;
      delete process.env.BACKEND_API_URL;
      process.env.NEXT_PUBLIC_BACKEND_API_URL = "http://localhost:8000/api/v1";

      assert.equal(getServerBackendBaseUrl(), "http://localhost:8000");
      assert.equal(getServerBackendApiUrl(), "http://localhost:8000/api/v1");
    } finally {
      process.env.INTERNAL_BACKEND_URL = prevInternal;
      process.env.NEXT_PUBLIC_BACKEND_API_URL = prevPublic;
    }
  });

  it("falls back to default localhost:8000 when all env vars are absent", () => {
    const prevInternal = process.env.INTERNAL_BACKEND_URL;
    const prevPublic = process.env.NEXT_PUBLIC_BACKEND_API_URL;
    const prevBackend = process.env.BACKEND_API_URL;

    try {
      delete process.env.INTERNAL_BACKEND_URL;
      delete process.env.BACKEND_API_URL;
      delete process.env.NEXT_PUBLIC_BACKEND_API_URL;

      assert.equal(getServerBackendBaseUrl(), "http://localhost:8000");
      assert.equal(getServerBackendApiUrl(), "http://localhost:8000/api/v1");
    } finally {
      process.env.INTERNAL_BACKEND_URL = prevInternal;
      process.env.NEXT_PUBLIC_BACKEND_API_URL = prevPublic;
      process.env.BACKEND_API_URL = prevBackend;
    }
  });

  it("throws security error when invoked in a browser-like environment", () => {
    // Simulate window global
    (globalThis as unknown as { window: unknown }).window = {};
    try {
      assert.throws(
        () => resolveServerBackendUrl(),
        /Security Error: server-backend-url must only be invoked in server-side execution contexts/
      );
    } finally {
      delete (globalThis as unknown as { window?: unknown }).window;
    }
  });
});
