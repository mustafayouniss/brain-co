/**
 * AI Configuration
 * Centralized configuration for provider and model selection
 * This is isolated within the AI folder - integration with global .env
 * would require modifying files outside the AI folder, which is not allowed
 */

export interface AIProviderConfig {
  providerId: string;
  model: string;
  apiKey?: string;
  baseUrl?: string;
  [key: string]: unknown;
}

export class AIConfig {
  private static instance: AIConfig;
  private config: AIProviderConfig;

  private constructor() {
    // Default configuration - in production this would come from environment
    // Since we cannot modify global .env files, we use a local approach
    this.config = {
      providerId: process.env.AI_PROVIDER || 'openai',
      model: process.env.AI_MODEL || 'gpt-4',
      apiKey: process.env.OPENAI_API_KEY,
      baseUrl: process.env.OPENAI_BASE_URL,
    };
  }

  static getInstance(): AIConfig {
    if (!AIConfig.instance) {
      AIConfig.instance = new AIConfig();
    }
    return AIConfig.instance;
  }

  getProviderConfig(): AIProviderConfig {
    return { ...this.config };
  }

  updateConfig(config: Partial<AIProviderConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Get the provider ID (e.g., 'openai', 'anthropic')
   */
  getProviderId(): string {
    return this.config.providerId;
  }

  /**
   * Get the model name
   */
  getModel(): string {
    return this.config.model;
  }

  /**
   * Get the API key for the current provider
   */
  getApiKey(): string | undefined {
    return this.config.apiKey;
  }
}
