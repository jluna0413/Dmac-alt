#!/usr/bin/env node

import { MCPControlServer } from './services/MCPControlServer';
import { logger } from './utils/logger';
import { configManager } from './config';

/**
 * MCPControl - Enhanced tooling orchestration for MCP servers
 * Main entry point for the application
 */

async function bootstrap() {
  try {
    logger.info('🚀 Starting MCPControl Server...', {
      version: process.env.npm_package_version || '1.0.0',
      nodeVersion: process.version,
      environment: process.env.NODE_ENV || 'development',
    });

    // Validate configuration
    if (!configManager.validateConfig()) {
      throw new Error('Invalid configuration. Please check your environment variables.');
    }

    // Initialize and start the MCPControl server
    const server = new MCPControlServer();
    await server.initialize();
    await server.start();

    // Graceful shutdown handling
    const gracefulShutdown = async (signal: string) => {
      logger.info(`📴 Received ${signal}. Starting graceful shutdown...`);
      
      try {
        await server.stop();
        logger.info('✅ MCPControl server shutdown completed');
        process.exit(0);
      } catch (error) {
        logger.error('❌ Error during shutdown:', error);
        process.exit(1);
      }
    };

    // Register shutdown handlers
    process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
    process.on('SIGINT', () => gracefulShutdown('SIGINT'));
    process.on('SIGUSR2', () => gracefulShutdown('SIGUSR2')); // Nodemon restart

    // Handle uncaught exceptions
    process.on('uncaughtException', (error) => {
      logger.error('💥 Uncaught Exception:', error);
      gracefulShutdown('uncaughtException');
    });

    process.on('unhandledRejection', (reason, promise) => {
      logger.error('💥 Unhandled Rejection at:', promise, 'reason:', reason);
      gracefulShutdown('unhandledRejection');
    });

    logger.info('🎉 MCPControl Server started successfully!', {
      port: configManager.serverConfig.port,
      host: configManager.serverConfig.host,
      archonMcpUrl: configManager.archonConfig.mcpUrl,
    });

  } catch (error) {
    logger.error('💥 Failed to start MCPControl Server:', error);
    process.exit(1);
  }
}

// Start the application
if (require.main === module) {
  bootstrap().catch((error) => {
    console.error('💥 Bootstrap failed:', error);
    process.exit(1);
  });
}

export { bootstrap };
