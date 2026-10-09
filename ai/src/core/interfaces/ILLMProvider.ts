import { LLMRequest, LLMResponse, LLMError } from '../types';

/**
 * Provider-agnostic LLM provider interface
 * All providers must implement this contract
 * No provider-specific SDK types should be exposed through this interface
 */
export interface ILLMProvider {
  /**
   * Generate a completion for the given request
   * @param request - Provider-independent LLM request
   * @returns Normalized LLM response
   * @throws LLMError - Normalized error, never provider-specific errors
   */
  generate(request: LLMRequest): Promise<LLMResponse>;

  /**
   * Get the provider identifier (e.g., 'openai', 'anthropic')
   */
  getProviderId(): string;

  /**
   * Check if the provider is available/configured
   */
  isAvailable(): boolean;
}
