import { LLMService } from '../core/services/LLMService';
import { FakeLLMProvider } from '../providers/FakeLLMProvider';
import { ConsoleLogger } from '../utils/Logger';
import { LLMRequest } from '../core/types';

describe('Provider Swappability', () => {
  let service: LLMService;
  let provider1: FakeLLMProvider;
  let provider2: FakeLLMProvider;
  let logger: ConsoleLogger;

  beforeEach(() => {
    provider1 = new FakeLLMProvider({ customResponse: 'Response from provider 1' });
    provider2 = new FakeLLMProvider({ customResponse: 'Response from provider 2' });
    logger = new ConsoleLogger();
    service = new LLMService(provider1, logger);
  });

  it('should work with initial provider', async () => {
    const request: LLMRequest = {
      messages: [{ role: 'user', content: 'test' }],
      model: 'gpt-4',
    };

    const response = await service.generate(request);

    expect(response.content).toBe('Response from provider 1');
  });

  it('should work after swapping provider', async () => {
    const request: LLMRequest = {
      messages: [{ role: 'user', content: 'test' }],
      model: 'gpt-4',
    };

    // First request with provider 1
    const response1 = await service.generate(request);
    expect(response1.content).toBe('Response from provider 1');

    // Swap provider
    service.setProvider(provider2);

    // Second request with provider 2
    const response2 = await service.generate(request);
    expect(response2.content).toBe('Response from provider 2');
  });

  it('should not require changes to higher-level code when swapping', async () => {
    const request: LLMRequest = {
      messages: [{ role: 'user', content: 'test' }],
      model: 'gpt-4',
    };

    // This function represents higher-level AI logic
    async function processWithLLM(llmService: LLMService, req: LLMRequest) {
      return await llmService.generate(req);
    }

    // Works with provider 1
    const response1 = await processWithLLM(service, request);
    expect(response1.content).toBe('Response from provider 1');

    // Swap provider
    service.setProvider(provider2);

    // Same function works with provider 2 - no changes needed
    const response2 = await processWithLLM(service, request);
    expect(response2.content).toBe('Response from provider 2');
  });

  it('should maintain service interface after provider swap', async () => {
    const request: LLMRequest = {
      messages: [{ role: 'user', content: 'test' }],
      model: 'gpt-4',
    };

    service.setProvider(provider2);

    // All service methods should still work
    expect(service.getProvider()).toBe(provider2);
    const response = await service.generate(request);
    expect(response).toBeDefined();
  });

  it('should allow swapping between different provider types', async () => {
    // This test proves the architecture allows swapping between
    // different provider implementations (e.g., OpenAI -> Anthropic)
    // as long as they implement ILLMProvider

    const request: LLMRequest = {
      messages: [{ role: 'user', content: 'test' }],
      model: 'gpt-4',
    };

    // Start with one fake provider
    const response1 = await service.generate(request);

    // Swap to another fake provider (simulating different provider type)
    const differentProvider = new FakeLLMProvider({
      customResponse: 'Different provider response',
    });
    service.setProvider(differentProvider);

    // Service works identically
    const response2 = await service.generate(request);
    expect(response2.content).toBe('Different provider response');
  });
});
