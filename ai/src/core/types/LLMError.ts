/**
 * Provider-independent LLM error model
 * Normalized errors that don't leak provider-specific error types
 */

export enum LLMErrorType {
  PROVIDER_UNAVAILABLE = 'PROVIDER_UNAVAILABLE',
  AUTHENTICATION_FAILED = 'AUTHENTICATION_FAILED',
  RATE_LIMITED = 'RATE_LIMITED',
  INVALID_REQUEST = 'INVALID_REQUEST',
  MODEL_UNAVAILABLE = 'MODEL_UNAVAILABLE',
  TIMEOUT = 'TIMEOUT',
  UNKNOWN = 'UNKNOWN',
}

export class LLMError extends Error {
  public readonly type: LLMErrorType;
  public readonly provider?: string;
  public readonly originalError?: unknown;

  constructor(
    type: LLMErrorType,
    message: string,
    provider?: string,
    originalError?: unknown
  ) {
    super(message);
    this.name = 'LLMError';
    this.type = type;
    this.provider = provider;
    this.originalError = originalError;
  }
}
