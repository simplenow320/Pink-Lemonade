/**
 * Winston Logger Configuration
 * Provides structured logging similar to Python's logging module
 */

import winston from 'winston';
import path from 'path';

const { combine, timestamp, label, printf, colorize, errors } = winston.format;

// Custom log format
const logFormat = printf(({ level, message, label, timestamp, stack }) => {
  return `${timestamp} [${label}] ${level}: ${stack || message}`;
});

// Create logs directory if it doesn't exist
const logsDir = path.join(process.cwd(), 'logs');

/**
 * Create a logger instance
 * @param {string} moduleName - Name of the module/component
 * @returns {winston.Logger} Configured logger instance
 */
export function createLogger(moduleName) {
  return winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: combine(
      errors({ stack: true }),
      label({ label: moduleName }),
      timestamp(),
      logFormat
    ),
    transports: [
      // Console transport
      new winston.transports.Console({
        format: combine(
          colorize(),
          label({ label: moduleName }),
          timestamp(),
          logFormat
        )
      }),
      // File transport for errors
      new winston.transports.File({
        filename: path.join(logsDir, 'error.log'),
        level: 'error',
        maxsize: 5242880, // 5MB
        maxFiles: 5
      }),
      // File transport for all logs
      new winston.transports.File({
        filename: path.join(logsDir, 'combined.log'),
        maxsize: 5242880, // 5MB
        maxFiles: 5
      })
    ]
  });
}

// Default logger
export const logger = createLogger('Server');
export default logger;