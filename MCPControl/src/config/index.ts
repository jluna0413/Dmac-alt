import { config } from 'dotenv';
import { MCPControlConfig } from '@/types';

// Load environment variables
config();

/**
 * Application Configuration
 * Centralizes all configuration management for MCPControl
 */
export class ConfigManager {
  private static instance: ConfigManager;
  private _config: MCPControlConfig;

  private constructor() {
    this._config = this.loadConfig();
  }

  public static getInstance(): ConfigManager {
    if (!ConfigManager.instance) {
      ConfigManager.instance = new ConfigManager();
    }
    return ConfigManager.instance;
  }

  private loadConfig(): MCPControlConfig {
    return {
      server: {
        port: parseInt(process.env.PORT || '8052', 10),
        host: process.env.HOST || 'localhost',
        enableCors: process.env.ENABLE_CORS !== 'false',
      },
      archon: {
        mcpUrl: process.env.ARCHON_MCP_URL || 'http://localhost:8051/mcp',
        serverUrl: process.env.ARCHON_SERVER_URL || 'http://localhost:8181',
        uiUrl: process.env.ARCHON_UI_URL || 'http://localhost:3737',
        healthCheckInterval: parseInt(process.env.HEALTH_CHECK_INTERVAL || '30000', 10),
      },
      orchestration: {
        maxConcurrentTools: parseInt(process.env.MAX_CONCURRENT_TOOLS || '10', 10),
        defaultTimeout: parseInt(process.env.TOOL_TIMEOUT_MS || '30000', 10),
        workflowTimeout: parseInt(process.env.WORKFLOW_TIMEOUT_MS || '300000', 10),
        enableCache: process.env.ENABLE_WORKFLOW_CACHE !== 'false',
      },
      monitoring: {
        enableAnalytics: process.env.ENABLE_ANALYTICS !== 'false',
        retentionDays: parseInt(process.env.ANALYTICS_RETENTION_DAYS || '30', 10),
        performanceMetrics: process.env.PERFORMANCE_METRICS !== 'false',
      },
      security: {
        allowedOrigins: process.env.ALLOWED_ORIGINS?.split(',') || [],
        apiKeyRequired: process.env.API_KEY_REQUIRED === 'true',
      },
      logging: {
        level: process.env.LOG_LEVEL || 'info',
        enableFileLogging: process.env.ENABLE_FILE_LOGGING !== 'false',
        maxFileSize: parseInt(process.env.LOG_MAX_FILE_SIZE || '5242880', 10),
        maxFiles: parseInt(process.env.LOG_MAX_FILES || '5', 10),
      },
    };
  }

  public get config(): MCPControlConfig {
    return this._config;
  }

  public reload(): void {
    this._config = this.loadConfig();
  }

  public updateConfig(updates: Partial<MCPControlConfig>): void {
    this._config = { ...this._config, ...updates };
  }

  // Convenience getters
  public get serverConfig() {
    return this._config.server;
  }

  public get archonConfig() {
    return this._config.archon;
  }

  public get orchestrationConfig() {
    return this._config.orchestration;
  }

  public get monitoringConfig() {
    return this._config.monitoring;
  }

  public get securityConfig() {
    return this._config.security;
  }

  public get loggingConfig() {
    return this._config.logging;
  }

  // Validation helpers
  public validateConfig(): boolean {
    const required = [
      this._config.archon.mcpUrl,
      this._config.archon.serverUrl,
    ];

    return required.every(value => value && value.length > 0);
  }

  public getHealthCheckEndpoints(): string[] {
    return [
      this._config.archon.mcpUrl.replace('/mcp', '/health'),
      this._config.archon.serverUrl + '/health',
      this._config.archon.uiUrl + '/health',
    ];
  }
}

// Export singleton instance
export const configManager = ConfigManager.getInstance();
export { configManager as config };
