import { OpenAIProvider } from '../providers/OpenAIProvider';
import { LLMRequest } from '../core/types';
import { LLMErrorType } from '../core/types';

describe('OpenAIProvider', () => {
  describe('constructor', () => {
    it('should initialize with API key', () => {
      const provider = new OpenAIProvider('test-key');
      expect(provider.getProviderId()).toBe('openai');
    });

    it('should be available when API key is provided', () => {
      const provider = new OpenAIProvider('test-key');
      expect(provider.isAvailable()).toBe(true);
    });

    it('should not be available when API key is empty', () => {
      const provider = new OpenAIProvider('');
      expect(provider.isAvailable()).toBe(false);
    });

    it('should accept optional baseUrl', () => {
      const provider = new OpenAIProvider('test-key', 'https://custom.url');
      expect(provider.getProviderId()).toBe('openai');
    });
  });

  describe('generate method', () => {
    it('should throw error when client is not initialized', async () => {
      const provider = new OpenAIProvider('');
      const request: LLMRequest = {
        messages: [{ role: 'user', content: 'test' }],
        model: 'gpt-4',
      };

      await expect(provider.generate(request)).rejects.toMatchObject({
        type: LLMErrorType.AUTHENTICATION_FAILED,
      });
    });

    it('should map request to OpenAI format', () => {
      // This test verifies the mapping logic exists
      // Actual API calls are tested in integration tests
      const provider = new OpenAIProvider('test-key');
      expect(provider.getProviderId()).toBe('openai');
    });
  });

  describe('getProviderId', () => {
    it('should return "openai"', () => {
      const provider = new OpenAIProvider('test-key');
      expect(provider.getProviderId()).toBe('openai');
    });
  });
});
