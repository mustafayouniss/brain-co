import { ILLMProvider } from '../core/interfaces';
import { LLMRequest, LLMResponse, LLMError } from '../core/types';
import { FakeLLMProvider } from '../providers/FakeLLMProvider';

describe('ILLMProvider Contract', () => {
  let provider: ILLMProvider;

  beforeEach(() => {
    provider = new FakeLLMProvider();
  });

  describe('generate method', () => {
    it('should return a valid LLMResponse', async () => {
      const request: LLMRequest = {
        messages: [{ role: 'user', content: 'test' }],
        model: 'test-model',
      };

      const response = await provider.generate(request);

      expect(response).toBeDefined();
      expect(response.content).toBeDefined();
      expect(typeof response.content).toBe('string');
      expect(response.model).toBe('test-model');
      expect(response.finishReason).toBeDefined();
    });

    it('should handle system messages', async () => {
      const request: LLMRequest = {
        messages: [
          { role: 'system', content: 'You are a helpful assistant' },
          { role: 'user', content: 'test' },
        ],
        model: 'test-model',
      };

      const response = await provider.generate(request);

      expect(response).toBeDefined();
    });

    it('should handle temperature parameter', async () => {
      const request: LLMRequest = {
        messages: [{ role: 'user', content: 'test' }],
        model: 'test-model',
        temperature: 0.7,
      };

      const response = await provider.generate(request);

      expect(response).toBeDefined();
    });

    it('should handle maxTokens parameter', async () => {
      const request: LLMRequest = {
        messages: [{ role: 'user', content: 'test' }],
        model: 'test-model',
        maxTokens: 100,
      };

      const response = await provider.generate(request);

      expect(response).toBeDefined();
    });

    it('should handle metadata parameter', async () => {
      const request: LLMRequest = {
        messages: [{ role: 'user', content: 'test' }],
        model: 'test-model',
        metadata: { requestId: '123' },
      };

      const response = await provider.generate(request);

      expect(response).toBeDefined();
    });

    it('should throw LLMError on failure', async () => {
      const failingProvider = new FakeLLMProvider({ shouldFail: true });
      const request: LLMRequest = {
        messages: [{ role: 'user', content: 'test' }],
        model: 'test-model',
      };

      await expect(failingProvider.generate(request)).rejects.toThrow(LLMError);
    });
  });

  describe('getProviderId method', () => {
    it('should return a provider identifier', () => {
      const providerId = provider.getProviderId();
      expect(typeof providerId).toBe('string');
      expect(providerId.length).toBeGreaterThan(0);
    });
  });

  describe('isAvailable method', () => {
    it('should return a boolean', () => {
      const available = provider.isAvailable();
      expect(typeof available).toBe('boolean');
    });

    it('FakeLLMProvider should always be available', () => {
      expect(provider.isAvailable()).toBe(true);
    });
  });
});
