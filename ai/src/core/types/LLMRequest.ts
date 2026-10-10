/**
 * Provider-independent LLM request contract
 * This abstraction must not leak provider-specific concepts
 */

export interface LLMMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface LLMRequest {
  messages: LLMMessage[];
  model: string;
  temperature?: number;
  maxTokens?: number;
  metadata?: Record<string, unknown>;
}
