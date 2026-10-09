import { LLMMessage } from '../core/types';

/**
 * Prompt template abstraction
 * Provides a clean way to manage prompts without scattering strings
 */

export interface PromptVariable {
  name: string;
  value: string;
}

export class PromptTemplate {
  private template: string;
  private systemPrompt?: string;
  private metadata?: Record<string, unknown>;

  constructor(config: {
    template: string;
    systemPrompt?: string;
    metadata?: Record<string, unknown>;
  }) {
    this.template = config.template;
    this.systemPrompt = config.systemPrompt;
    this.metadata = config.metadata;
  }

  /**
   * Interpolate variables into the template
   * Variables are denoted by {{variableName}}
   */
  render(variables: Record<string, string>): string {
    let result = this.template;

    for (const [key, value] of Object.entries(variables)) {
      const placeholder = `{{${key}}}`;
      result = result.replace(new RegExp(placeholder, 'g'), value);
    }

    return result;
  }

  /**
   * Convert the rendered template to LLM message format
   */
  toMessages(variables?: Record<string, string>): LLMMessage[] {
    const messages: LLMMessage[] = [];

    if (this.systemPrompt) {
      messages.push({
        role: 'system',
        content: this.systemPrompt,
      });
    }

    const rendered = variables ? this.render(variables) : this.template;

    messages.push({
      role: 'user',
      content: rendered,
    });

    return messages;
  }

  /**
   * Get the raw template
   */
  getTemplate(): string {
    return this.template;
  }

  /**
   * Get the system prompt
   */
  getSystemPrompt(): string | undefined {
    return this.systemPrompt;
  }

  /**
   * Get metadata
   */
  getMetadata(): Record<string, unknown> | undefined {
    return this.metadata;
  }

  /**
   * Extract variable names from the template
   */
  extractVariables(): string[] {
    const matches = this.template.matchAll(/{{(\w+)}}/g);
    const variables = Array.from(matches).map((match) => match[1]);
    return [...new Set(variables)];
  }
}
