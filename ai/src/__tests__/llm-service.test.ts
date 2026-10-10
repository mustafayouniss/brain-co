import { LLMService } from '../core/services/LLMService';
import { FakeLLMProvider } from '../providers/FakeLLMProvider';
import { ConsoleLogger } from '../utils/Logger';
import { LLMRequest } from '../core/types';

describe('LLMService', () => {
  let service: LLMService;
  let provider: FakeLLMProvider;
  let logger: ConsoleLogger;

  beforeEach(() => {
    provider = new FakeLLMProvider();
    logger = new ConsoleLogger();
    service = new LLMService(provider, logger);
  });

  describe('generate method', () => {
    it('should successfully generate a response', async () => {
      const request: LLMRequest = {
        messages: [{ role: 'user', content: 'Hello' }],
        model: 'gpt-4',
      };

      const response = await service.generate(request);

      expect(response).toBeDefined();
      expect(response.content).toBeDefined();
      expect(response.model).toBe('gpt-4');
    });

    it('should log request started event', async () => {
      const logSpy = jest.spyOn(logger, 'info').mockImplementation();
      const request: LLMRequest = {
        messages: [{ role: 'user', content: 'Hello' }],
        model: 'gpt-4',
      };

      await service.generate(request);

      expect(logSpy).toHaveBeenCalled();
      const firstCall = logSpy.mock.calls[0];
      expect(firstCall[0].event).toBe('llm_request_started');
      expect(firstCall[0].provider).toBe('fake');
      expect(firstCall[0].model).toBe('gpt-4');

      logSpy.mockRestore();
    });

    it('should log request completed event', async () => {
      const logSpy = jest.spyOn(logger, 'info').mockImplementation();
      const request: LLMRequest = {
        messages: [{ role: 'user', content: 'Hello' }],
        model: 'gpt-4',
      };

      await service.generate(request);

      expect(logSpy).toHaveBeenCalled();
      const calls = logSpy.mock.calls;
      const completedCall = calls.find((call) => call[0].event === 'llm_request_completed');
      expect(completedCall).toBeDefined();
      expect(completedCall![0].provider).toBe('fake');

      logSpy.mockRestore();
    });

    it('should log request failed event on error', async () => {
      const logSpy = jest.spyOn(logger, 'error').mockImplementation();
      provider.setShouldFail(true);
      const request: LLMRequest = {
        messages: [{ role: 'user', content: 'Hello' }],
        model: 'gpt-4',
      };

      await expect(service.generate(request)).rejects.toThrow();

      expect(logSpy).toHaveBeenCalled();
      const errorCall = logSpy.mock.calls[0];
      expect(errorCall[0].event).toBe('llm_request_failed');
      expect(errorCall[0].provider).toBe('fake');

      logSpy.mockRestore();
    });

    it('should include correlation ID in logs', async () => {
      const logSpy = jest.spyOn(logger, 'info').mockImplementation();
      const request: LLMRequest = {
        messages: [{ role: 'user', content: 'Hello' }],
        model: 'gpt-4',
      };

      await service.generate(request);

      const firstCall = logSpy.mock.calls[0];
      expect(firstCall[0].correlationId).toBeDefined();
      expect(typeof firstCall[0].correlationId).toBe('string');

      logSpy.mockRestore();
    });
  });

  describe('getProvider method', () => {
    it('should return the current provider', () => {
      const currentProvider = service.getProvider();
      expect(currentProvider).toBe(provider);
    });
  });

  describe('setProvider method', () => {
    it('should replace the provider', () => {
      const newProvider = new FakeLLMProvider();
      service.setProvider(newProvider);

      expect(service.getProvider()).toBe(newProvider);
      expect(service.getProvider()).not.toBe(provider);
    });

    it('should log provider change event', () => {
      const logSpy = jest.spyOn(logger, 'info').mockImplementation();
      const newProvider = new FakeLLMProvider();

      service.setProvider(newProvider);

      expect(logSpy).toHaveBeenCalled();
      const call = logSpy.mock.calls[0];
      expect(call[0].event).toBe('llm_provider_changed');
      expect(call[0].newProvider).toBe('fake');

      logSpy.mockRestore();
    });
  });
});
