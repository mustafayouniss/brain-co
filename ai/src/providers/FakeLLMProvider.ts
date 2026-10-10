import { ILLMProvider } from '../core/interfaces';
import { LLMRequest, LLMResponse, LLMError, LLMErrorType } from '../core/types';

/**
 * Fake/Mock LLM provider for testing
 * This enables testing AI infrastructure without real API calls
 */
export class FakeLLMProvider implements ILLMProvider {
  private readonly providerId = 'fake';
  private responseDelay: number = 0;
  private shouldFail: boolean = false;
  private errorType?: LLMErrorType;
  private customResponse?: string;

  constructor(config?: {
    responseDelay?: number;
    shouldFail?: boolean;
    errorType?: LLMErrorType;
    customResponse?: string;
  }) {
    this.responseDelay = config?.responseDelay || 0;
    this.shouldFail = config?.shouldFail || false;
    this.errorType = config?.errorType;
    this.customResponse = config?.customResponse;
  }

  async generate(request: LLMRequest): Promise<LLMResponse> {
    if (this.responseDelay > 0) {
      await new Promise((resolve) => setTimeout(resolve, this.responseDelay));
    }

    if (this.shouldFail) {
      throw new LLMError(
        this.errorType || LLMErrorType.UNKNOWN,
        'Fake provider error',
        this.providerId
      );
    }

    // Generate a deterministic response based on the last user message
    const lastUserMessage = request.messages
      .filter((m) => m.role === 'user')
      .pop();

    const content =
      this.customResponse ||
      `Fake response to: ${lastUserMessage?.content || 'empty message'}`;

    return {
      content,
      model: request.model,
      usage: {
        promptTokens: 10,
        completionTokens: 5,
        totalTokens: 15,
      },
      finishReason: 'stop',
      metadata: {
        fake: true,
      },
    };
  }

  getProviderId(): string {
    return this.providerId;
  }

  isAvailable(): boolean {
    return true;
  }

  // Configuration methods for test control
  setResponseDelay(delay: number): void {
    this.responseDelay = delay;
  }

  setShouldFail(shouldFail: boolean, errorType?: LLMErrorType): void {
    this.shouldFail = shouldFail;
    this.errorType = errorType;
  }

  setCustomResponse(response: string): void {
    this.customResponse = response;
  }
}
