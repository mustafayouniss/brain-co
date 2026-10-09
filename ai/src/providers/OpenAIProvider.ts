import OpenAI from 'openai';
import { ILLMProvider } from '../core/interfaces';
import { LLMRequest, LLMResponse, LLMError, LLMErrorType, LLMFinishReason } from '../core/types';

/**
 * OpenAI implementation of ILLMProvider
 * This is isolated behind the interface - no OpenAI-specific types leak out
 */
export class OpenAIProvider implements ILLMProvider {
  private client: OpenAI | null = null;
  private readonly providerId = 'openai';
  private apiKey: string;
  private baseUrl?: string;

  constructor(apiKey: string, baseUrl?: string) {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
    
    if (apiKey) {
      this.client = new OpenAI({
        apiKey,
        baseURL: baseUrl,
      });
    }
  }

  async generate(request: LLMRequest): Promise<LLMResponse> {
    if (!this.client) {
      throw new LLMError(
        LLMErrorType.AUTHENTICATION_FAILED,
        'OpenAI client not initialized - API key is required',
        this.providerId
      );
    }

    try {
      // Map internal request to OpenAI format
      const openAIRequest = this.mapToOpenAIRequest(request);

      // Call OpenAI API
      const response = await this.client.chat.completions.create(openAIRequest);

      // Map OpenAI response to internal format
      return this.mapFromOpenAIResponse(response);
    } catch (error) {
      throw this.normalizeError(error);
    }
  }

  getProviderId(): string {
    return this.providerId;
  }

  isAvailable(): boolean {
    return this.client !== null && this.apiKey.length > 0;
  }

  private mapToOpenAIRequest(request: LLMRequest): OpenAI.ChatCompletionCreateParamsNonStreaming {
    return {
      model: request.model,
      messages: request.messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
      })),
      temperature: request.temperature,
      max_tokens: request.maxTokens,
    };
  }

  private mapFromOpenAIResponse(response: OpenAI.ChatCompletion): LLMResponse {
    const choice = response.choices[0];
    const finishReason = this.mapFinishReason(choice.finish_reason);

    return {
      content: choice.message.content || '',
      model: response.model,
      usage: response.usage
        ? {
            promptTokens: response.usage.prompt_tokens,
            completionTokens: response.usage.completion_tokens,
            totalTokens: response.usage.total_tokens,
          }
        : undefined,
      finishReason,
      metadata: {
        id: response.id,
        created: response.created,
      },
    };
  }

  private mapFinishReason(reason: string | null): LLMFinishReason {
    switch (reason) {
      case 'stop':
        return 'stop';
      case 'length':
        return 'length';
      case 'content_filter':
        return 'content_filter';
      default:
        return 'unknown';
    }
  }

  private normalizeError(error: unknown): LLMError {
    if (this.isOpenAIError(error)) {
      // Map OpenAI errors to internal error types
      if (error.status === 401) {
        return new LLMError(
          LLMErrorType.AUTHENTICATION_FAILED,
          'OpenAI authentication failed',
          this.providerId,
          error
        );
      }
      if (error.status === 429) {
        return new LLMError(
          LLMErrorType.RATE_LIMITED,
          'OpenAI rate limit exceeded',
          this.providerId,
          error
        );
      }
      if (error.status === 404) {
        return new LLMError(
          LLMErrorType.MODEL_UNAVAILABLE,
          'OpenAI model not found',
          this.providerId,
          error
        );
      }
      if (error.status === 400) {
        return new LLMError(
          LLMErrorType.INVALID_REQUEST,
          'Invalid request to OpenAI',
          this.providerId,
          error
        );
      }
    }

    if (error instanceof Error) {
      if (error.message.includes('timeout') || error.message.includes('ETIMEDOUT')) {
        return new LLMError(
          LLMErrorType.TIMEOUT,
          'OpenAI request timeout',
          this.providerId,
          error
        );
      }
    }

    return new LLMError(
      LLMErrorType.UNKNOWN,
      error instanceof Error ? error.message : 'Unknown OpenAI error',
      this.providerId,
      error
    );
  }

  private isOpenAIError(error: unknown): error is { status: number } {
    return (
      typeof error === 'object' &&
      error !== null &&
      'status' in error &&
      typeof (error as { status: number }).status === 'number'
    );
  }
}
