/**
 * Backend AI Integration
 *
 * This module provides integration with the backend AI API.
 * For browser client, uses frontend proxy endpoint to avoid CORS.
 * Backend endpoint: POST /api/v1/ai/prompt
 * Frontend proxy: POST /api/ai/prompt
 */

const FRONTEND_API_URL = ""; // Use relative URL for same-origin
const BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL || "http://localhost:8000/api/v1";

export interface PromptRequest {
  prompt: string;
  model?: string;
}

export interface PromptResponse {
  content: string;
  model: string;
  tokens: number;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}

/**
 * Generate AI response using frontend proxy endpoint (for browser)
 */
export async function generateAIResponse(
  token: string,
  request: PromptRequest
): Promise<PromptResponse> {
  // Use frontend proxy for browser requests (same-origin)
  const apiUrl = typeof window !== "undefined" ? `${FRONTEND_API_URL}/api/ai/prompt` : `${BACKEND_API_URL}/ai/prompt`;

  const response = await fetch(apiUrl, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = (await response.json()) as ApiError;
    throw new Error(error.error?.message || "AI request failed");
  }

  return response.json() as Promise<PromptResponse>;
}
