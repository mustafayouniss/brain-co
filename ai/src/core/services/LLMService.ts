import { ILLMProvider } from '../interfaces';
import { LLMRequest, LLMResponse, LLMError, LLMErrorType } from '../types';
import { ILogger } from '../../utils/Logger';

/**
 * Provider-agnostic LLM service
 * This is the main entry point for AI components to interact with LLMs
 * It depends only on the ILLMProvider interface, not on any specific provider
 */
export class LLMService {
  private provider: ILLMProvider;
  private logger: ILogger;

  constructor(provider: ILLMProvider, logger: ILogger) {
    this.provider = provider;
    this.logger = logger;
  }

  /**
   * Generate a completion using the configured provider
   * @param request - Provider-independent LLM request
   * @returns Normalized LLM response
   */
  async generate(request: LLMRequest): Promise<LLMResponse> {
    const correlationId = this.generateCorrelationId();
    const startTime = Date.now();

    this.logger.info({
      event: 'llm_request_started',
      correlationId,
      provider: this.provider.getProviderId(),
      model: request.model,
      messageCount: request.messages.length,
    });

    try {
      const response = await this.provider.generate(request);

      const latency = Date.now() - startTime;

      this.logger.info({
        event: 'llm_request_completed',
        correlationId,
        provider: this.provider.getProviderId(),
        model: response.model,
        latency,
        usage: response.usage,
        finishReason: response.finishReason,
      });

      return response;
    } catch (error) {
      const latency = Date.now() - startTime;
      const normalizedError = this.normalizeError(error);

      this.logger.error({
        event: 'llm_request_failed',
        correlationId,
        provider: this.provider.getProviderId(),
        model: request.model,
        latency,
        errorType: normalizedError.type,
        errorMessage: normalizedError.message,
      });

      throw normalizedError;
    }
  }

  /**
   * Get the current provider
   */
  getProvider(): ILLMProvider {
    return this.provider;
  }

  /**
   * Replace the provider (enables provider swapping without changing higher-level code)
   */
  setProvider(provider: ILLMProvider): void {
    this.provider = provider;
    this.logger.info({
      event: 'llm_provider_changed',
      newProvider: provider.getProviderId(),
    });
  }

  private normalizeError(error: unknown): LLMError {
    if (error instanceof LLMError) {
      return error;
    }

    // Unknown errors are wrapped in LLMError
    return new LLMError(
      LLMErrorType.UNKNOWN,
      error instanceof Error ? error.message : 'Unknown error',
      this.provider.getProviderId(),
      error
    );
  }

  private generateCorrelationId(): string {
    return `llm_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  }
}
