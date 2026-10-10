import { LLMError, LLMErrorType } from '../core/types';

describe('LLMError', () => {
  describe('constructor', () => {
    it('should create error with type and message', () => {
      const error = new LLMError(
        LLMErrorType.AUTHENTICATION_FAILED,
        'Auth failed'
      );

      expect(error).toBeInstanceOf(Error);
      expect(error.type).toBe(LLMErrorType.AUTHENTICATION_FAILED);
      expect(error.message).toBe('Auth failed');
      expect(error.name).toBe('LLMError');
    });

    it('should accept optional provider parameter', () => {
      const error = new LLMError(
        LLMErrorType.RATE_LIMITED,
        'Rate limited',
        'openai'
      );

      expect(error.provider).toBe('openai');
    });

    it('should accept optional originalError parameter', () => {
      const originalError = new Error('Original error');
      const error = new LLMError(
        LLMErrorType.UNKNOWN,
        'Wrapped error',
        'provider',
        originalError
      );

      expect(error.originalError).toBe(originalError);
    });
  });

  describe('error types', () => {
    it('should have all required error types', () => {
      expect(LLMErrorType.PROVIDER_UNAVAILABLE).toBeDefined();
      expect(LLMErrorType.AUTHENTICATION_FAILED).toBeDefined();
      expect(LLMErrorType.RATE_LIMITED).toBeDefined();
      expect(LLMErrorType.INVALID_REQUEST).toBeDefined();
      expect(LLMErrorType.MODEL_UNAVAILABLE).toBeDefined();
      expect(LLMErrorType.TIMEOUT).toBeDefined();
      expect(LLMErrorType.UNKNOWN).toBeDefined();
    });
  });
});
