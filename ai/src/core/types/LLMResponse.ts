/**
 * Provider-independent LLM response contract
 * Normalized response that doesn't expose provider-specific objects
 */

export interface LLMUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
}

export type LLMFinishReason = 'stop' | 'length' | 'content_filter' | 'unknown';

export interface LLMResponse {
  content: string;
  model: string;
  usage?: LLMUsage;
  finishReason: LLMFinishReason;
  metadata?: Record<string, unknown>;
}
