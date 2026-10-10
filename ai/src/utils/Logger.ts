/**
 * Simple logging interface for AI infrastructure
 * This is a basic abstraction that can be extended later
 */

export interface LogEntry {
  event: string;
  [key: string]: unknown;
}

export interface ILogger {
  info(entry: LogEntry): void;
  error(entry: LogEntry): void;
  warn(entry: LogEntry): void;
  debug(entry: LogEntry): void;
}

/**
 * Basic console logger implementation
 * In production, this could be replaced with Winston, Pino, etc.
 */
export class ConsoleLogger implements ILogger {
  info(entry: LogEntry): void {
    console.log('[INFO]', JSON.stringify(entry));
  }

  error(entry: LogEntry): void {
    console.error('[ERROR]', JSON.stringify(entry));
  }

  warn(entry: LogEntry): void {
    console.warn('[WARN]', JSON.stringify(entry));
  }

  debug(entry: LogEntry): void {
    console.debug('[DEBUG]', JSON.stringify(entry));
  }
}
