/**
 * Backend JWT Authentication Integration
 * 
 * This module provides integration with the backend JWT authentication API
 * as documented in docs/backend/api/auth.md.
 * 
 * Backend API: http://localhost:8000/api/v1
 * Auth scheme: Bearer token (JWT HS256)
 */

const BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL || "http://localhost:8000/api/v1";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "employee";
  is_active: boolean;
  created_at: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}

/**
 * Login to backend and receive JWT token
 */
export async function loginToBackend(credentials: LoginRequest): Promise<LoginResponse> {
  const response = await fetch(`${BACKEND_API_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    const error = (await response.json()) as ApiError;
    throw new Error(error.error?.message || "Login failed");
  }

  return response.json() as Promise<LoginResponse>;
}

/**
 * Get current user profile from backend
 */
export async function getCurrentUser(token: string): Promise<User> {
  const response = await fetch(`${BACKEND_API_URL}/auth/me`, {
    method: "GET",
    headers: {
      "Authorization": `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = (await response.json()) as ApiError;
    throw new Error(error.error?.message || "Failed to get user profile");
  }

  return response.json() as Promise<User>;
}

/**
 * Create a new user (admin only)
 */
export async function createUser(
  token: string,
  userData: {
    email: string;
    full_name: string;
    password: string;
    role: "admin" | "employee";
  }
): Promise<User> {
  const response = await fetch(`${BACKEND_API_URL}/users`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(userData),
  });

  if (!response.ok) {
    const error = (await response.json()) as ApiError;
    throw new Error(error.error?.message || "Failed to create user");
  }

  return response.json() as Promise<User>;
}

/**
 * Store token in localStorage (client-side only)
 * DEPRECATED: Use server-side HttpOnly cookies instead for security.
 * This function is kept for backward compatibility only.
 * In production, use httpOnly cookies from backend.
 */
export function storeToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("backend_token", token);
  }
}

/**
 * Retrieve stored token
 * DEPRECATED: Use server-side HttpOnly cookies instead for security.
 * This function is kept for backward compatibility only.
 */
export function getStoredToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem("backend_token");
  }
  return null;
}

/**
 * Clear stored token (logout)
 * DEPRECATED: Use server-side HttpOnly cookies instead for security.
 * This function is kept for backward compatibility only.
 */
export function clearToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem("backend_token");
  }
}

/**
 * Get Authorization header value
 * DEPRECATED: Use server-side HttpOnly cookies instead for security.
 * This function is kept for backward compatibility only.
 */
export function getAuthHeader(): { Authorization: string } | {} {
  const token = getStoredToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}
