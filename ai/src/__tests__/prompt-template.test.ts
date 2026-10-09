import { PromptTemplate } from '../prompts/PromptTemplate';

describe('PromptTemplate', () => {
  describe('render', () => {
    it('should replace single variable', () => {
      const template = new PromptTemplate({
        template: 'Hello {{name}}',
      });

      const rendered = template.render({ name: 'World' });

      expect(rendered).toBe('Hello World');
    });

    it('should replace multiple variables', () => {
      const template = new PromptTemplate({
        template: 'Hello {{name}}, you are {{age}} years old',
      });

      const rendered = template.render({ name: 'Alice', age: '30' });

      expect(rendered).toBe('Hello Alice, you are 30 years old');
    });

    it('should replace repeated variables', () => {
      const template = new PromptTemplate({
        template: '{{name}} loves {{name}}',
      });

      const rendered = template.render({ name: 'Bob' });

      expect(rendered).toBe('Bob loves Bob');
    });

    it('should leave unreplaced variables if not provided', () => {
      const template = new PromptTemplate({
        template: 'Hello {{name}} {{missing}}',
      });

      const rendered = template.render({ name: 'World' });

      expect(rendered).toBe('Hello World {{missing}}');
    });

    it('should handle empty variables object', () => {
      const template = new PromptTemplate({
        template: 'Hello {{name}}',
      });

      const rendered = template.render({});

      expect(rendered).toBe('Hello {{name}}');
    });
  });

  describe('toMessages', () => {
    it('should convert to user message without system prompt', () => {
      const template = new PromptTemplate({
        template: 'Hello {{name}}',
      });

      const messages = template.toMessages({ name: 'World' });

      expect(messages).toHaveLength(1);
      expect(messages[0].role).toBe('user');
      expect(messages[0].content).toBe('Hello World');
    });

    it('should include system prompt if provided', () => {
      const template = new PromptTemplate({
        template: 'Hello {{name}}',
        systemPrompt: 'You are a helpful assistant',
      });

      const messages = template.toMessages({ name: 'World' });

      expect(messages).toHaveLength(2);
      expect(messages[0].role).toBe('system');
      expect(messages[0].content).toBe('You are a helpful assistant');
      expect(messages[1].role).toBe('user');
      expect(messages[1].content).toBe('Hello World');
    });

    it('should work without variables', () => {
      const template = new PromptTemplate({
        template: 'Hello World',
      });

      const messages = template.toMessages();

      expect(messages).toHaveLength(1);
      expect(messages[0].content).toBe('Hello World');
    });
  });

  describe('extractVariables', () => {
    it('should extract single variable', () => {
      const template = new PromptTemplate({
        template: 'Hello {{name}}',
      });

      const variables = template.extractVariables();

      expect(variables).toEqual(['name']);
    });

    it('should extract multiple variables', () => {
      const template = new PromptTemplate({
        template: 'Hello {{name}}, you are {{age}}',
      });

      const variables = template.extractVariables();

      expect(variables).toEqual(['name', 'age']);
    });

    it('should extract unique variables only', () => {
      const template = new PromptTemplate({
        template: '{{name}} loves {{name}}',
      });

      const variables = template.extractVariables();

      expect(variables).toEqual(['name']);
    });

    it('should return empty array if no variables', () => {
      const template = new PromptTemplate({
        template: 'Hello World',
      });

      const variables = template.extractVariables();

      expect(variables).toEqual([]);
    });
  });

  describe('getters', () => {
    it('should return template string', () => {
      const template = new PromptTemplate({
        template: 'Hello {{name}}',
      });

      expect(template.getTemplate()).toBe('Hello {{name}}');
    });

    it('should return system prompt if set', () => {
      const template = new PromptTemplate({
        template: 'Hello {{name}}',
        systemPrompt: 'System prompt',
      });

      expect(template.getSystemPrompt()).toBe('System prompt');
    });

    it('should return undefined for system prompt if not set', () => {
      const template = new PromptTemplate({
        template: 'Hello {{name}}',
      });

      expect(template.getSystemPrompt()).toBeUndefined();
    });

    it('should return metadata if set', () => {
      const metadata = { version: '1.0' };
      const template = new PromptTemplate({
        template: 'Hello {{name}}',
        metadata,
      });

      expect(template.getMetadata()).toEqual(metadata);
    });

    it('should return undefined for metadata if not set', () => {
      const template = new PromptTemplate({
        template: 'Hello {{name}}',
      });

      expect(template.getMetadata()).toBeUndefined();
    });
  });
});
