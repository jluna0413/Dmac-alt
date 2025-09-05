import { createLogger, format, transports } from 'winston';

/**
 * Centralized logging utility for MCPControl
 * Provides structured logging with different levels and formats
 */

const { combine, timestamp, printf, colorize, errors, json } = format;

// Custom log format for development
const developmentFormat = printf((info) => {
  const { level, message, timestamp, stack, ...meta } = info as Record<string, unknown>;
  let metaStr = '';
  const metaObj = meta as Record<string, unknown>;
  if (Object.keys(metaObj).length) {
    try {
      metaStr = `\n${JSON.stringify(metaObj, null, 2)}`;
    } catch (circularError) {
      // Handle circular references by creating a simplified version
      const simplifiedMeta = Object.keys(metaObj).reduce((acc, key) => {
        try {
          JSON.stringify((metaObj as Record<string, unknown>)[key]);
          (acc as Record<string, unknown>)[key] = (metaObj as Record<string, unknown>)[key];
        } catch {
          (acc as Record<string, unknown>)[key] = '[Circular Reference]';
        }
        return acc;
      }, {} as Record<string, unknown>);
      metaStr = `\n${JSON.stringify(simplifiedMeta, null, 2)}`;
    }
  }
  const stackStr = stack ? `\n${String(stack)}` : '';
  return `${String(timestamp)} [${String(level)}]: ${String(message)}${metaStr}${stackStr}`;
});

// Custom log format for production
const productionFormat = combine(
  timestamp(),
  errors({ stack: true }),
  json()
);

// Determine log format based on environment
const logFormat = process.env.NODE_ENV === 'production' 
  ? productionFormat 
  : combine(
      timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
      colorize(),
      errors({ stack: true }),
      developmentFormat
    );

// Create logger instance
export const logger = createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: logFormat,
  defaultMeta: { 
    service: 'MCPControl',
    version: process.env.npm_package_version || '1.0.0'
  },
  transports: [
    // Console transport
    new transports.Console({
      handleExceptions: true,
      handleRejections: true,
    }),
    
    // File transport for errors
    new transports.File({
      filename: 'logs/error.log',
      level: 'error',
      handleExceptions: true,
      handleRejections: true,
      maxsize: 5242880, // 5MB
      maxFiles: 5,
    }),
    
    // File transport for all logs
    new transports.File({
      filename: 'logs/combined.log',
      handleExceptions: true,
      handleRejections: true,
      maxsize: 5242880, // 5MB
      maxFiles: 5,
    }),
  ],
  exitOnError: false,
});

// Add stream interface for HTTP request logging
// Attach a stream-compatible writer for integrations (e.g., morgan)
// Cast to unknown then to a minimal stream-like shape to satisfy the logger type
(logger as unknown as { stream?: { write: (msg: string) => void } }).stream = {
  write: (message: string) => {
    logger.info(message.trim());
  },
};

// Log unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled Rejection at:', { promise, reason });
});

// Log uncaught exceptions
process.on('uncaughtException', (error) => {
  logger.error('Uncaught Exception:', error);
});

/**
 * Create a child logger with additional context
 */
export const createChildLogger = (context: Record<string, unknown>) => {
  return logger.child(context as Record<string, unknown>);
};

/**
 * Performance timing utility
 */
export const timeLogger = {
  start: (label: string) => {
    const startTime = Date.now();
    return {
      end: (additionalData?: Record<string, unknown>) => {
        const duration = Date.now() - startTime;
        logger.info(`⏱️  ${label} completed`, {
          duration: `${duration}ms`,
          ...additionalData,
        });
        return duration;
      },
    };
  },
};

/**
 * Request logging middleware helper
 */
export const requestLogger = {
  logRequest: (method: string, url: string, userAgent?: string) => {
    logger.info(`📥 ${method} ${url}`, {
      method,
      url,
      userAgent,
      timestamp: new Date().toISOString(),
    });
  },
  
  logResponse: (method: string, url: string, statusCode: number, duration: number) => {
    const level = statusCode >= 400 ? 'warn' : 'info';
    logger[level](`📤 ${method} ${url} - ${statusCode}`, {
      method,
      url,
      statusCode,
      duration: `${duration}ms`,
      timestamp: new Date().toISOString(),
    });
  },
  
  logError: (method: string, url: string, error: Error) => {
    logger.error(`💥 ${method} ${url} - Error`, {
      method,
      url,
      error: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString(),
    });
  },
};

export default logger;
