import Fastify, { FastifyInstance } from 'fastify';
import cors from '@fastify/cors';
import websocket from '@fastify/websocket';
import { configManager } from '../config';
import { logger, requestLogger } from '../utils/logger';
import { ToolRegistry } from './ToolRegistry';
import { WorkflowOrchestrator } from './WorkflowOrchestrator';
import { ContextIntelligence } from './ContextIntelligence';
import { PerformanceMonitor } from './PerformanceMonitor';
import { OrchestrationContext } from '../types';

// Extend FastifyRequest to include startTime
declare module 'fastify' {
  interface FastifyRequest {
    startTime?: number;
  }
}

/**
 * Main MCPControl Server
 * Handles HTTP/WebSocket endpoints and orchestrates MCP tool interactions
 */
export class MCPControlServer {
  private server: FastifyInstance;
  private toolRegistry: ToolRegistry;
  private orchestrator: WorkflowOrchestrator;
  private contextIntelligence: ContextIntelligence;
  private performanceMonitor: PerformanceMonitor;
  private isInitialized = false;
  private isStarted = false;

  constructor() {
    this.server = Fastify({
      logger: false, // Use our custom logger
    });
    
    this.toolRegistry = new ToolRegistry();
    this.orchestrator = new WorkflowOrchestrator(this.toolRegistry);
    this.contextIntelligence = new ContextIntelligence();
    this.performanceMonitor = new PerformanceMonitor();
  }

  /**
   * Initialize the server with all plugins and routes
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) {
      logger.warn('MCPControl Server already initialized');
      return;
    }

    try {
      logger.info('🔧 Initializing MCPControl Server...');

      // Register plugins
      await this.registerPlugins();
      
      // Setup middleware
      this.setupMiddleware();
      
      // Register routes
      this.registerRoutes();
      
      // Initialize services
      await this.initializeServices();

      this.isInitialized = true;
      logger.info('✅ MCPControl Server initialized successfully');

    } catch (error) {
      logger.error('💥 Failed to initialize MCPControl Server:', error);
      throw error;
    }
  }

  /**
   * Start the server
   */
  async start(): Promise<void> {
    if (!this.isInitialized) {
      throw new Error('Server must be initialized before starting');
    }
    
    if (this.isStarted) {
      logger.warn('MCPControl Server already started');
      return;
    }

    try {
      const { host, port } = configManager.serverConfig;
      
      await this.server.listen({ 
        host, 
        port,
        listenTextResolver: (address) => `MCPControl Server listening at ${address}`
      });
      
      this.isStarted = true;
      logger.info(`🚀 MCPControl Server started successfully`, {
        host,
        port,
        address: `http://${host}:${port}`,
      });

      // Start background services
      await this.startBackgroundServices();

    } catch (error) {
      logger.error('💥 Failed to start MCPControl Server:', error);
      throw error;
    }
  }

  /**
   * Stop the server gracefully
   */
  async stop(): Promise<void> {
    if (!this.isStarted) {
      logger.warn('MCPControl Server not started');
      return;
    }

    try {
      logger.info('🛑 Stopping MCPControl Server...');

      // Stop background services
      await this.stopBackgroundServices();
      
      // Close server
      await this.server.close();
      
      this.isStarted = false;
      logger.info('✅ MCPControl Server stopped successfully');

    } catch (error) {
      logger.error('💥 Error stopping MCPControl Server:', error);
      throw error;
    }
  }

  /**
   * Register Fastify plugins
   */
  private async registerPlugins(): Promise<void> {
    // CORS plugin
    if (configManager.serverConfig.enableCors) {
      await this.server.register(cors, {
        origin: configManager.securityConfig.allowedOrigins.length > 0 
          ? configManager.securityConfig.allowedOrigins 
          : true,
        credentials: true,
      });
    }

    // WebSocket plugin
    await this.server.register(websocket);
  }

  /**
   * Setup middleware
   */
  private setupMiddleware(): void {
    // Request logging
  this.server.addHook('onRequest', async (request, _reply) => {
      const timer = Date.now();
      request.startTime = timer;
      
      requestLogger.logRequest(
        request.method,
        request.url,
        request.headers['user-agent']
      );
    });

    // Optional API key auth (enabled when MCPCONTROL_API_KEY is set)
    this.server.addHook('preHandler', async (request, reply) => {
      const apiKey = process.env.MCPCONTROL_API_KEY;
      if (!apiKey) return; // auth disabled by default

      // Public endpoints bypass auth
      const url = request.url || '';
      if (url === '/health' || url === '/ready' || url.startsWith('/ws')) return;

      const provided = request.headers['x-api-key'] as string | undefined;
      if (provided !== apiKey) {
        reply.code(401);
        return reply.send({ error: 'Unauthorized' });
      }
    });

    // Response logging
    this.server.addHook('onResponse', async (request, _reply) => {
      const duration = Date.now() - (request.startTime || Date.now());
      
      requestLogger.logResponse(
        request.method,
        request.url,
        _reply.statusCode,
        duration
      );
    });

    // Error handling
    this.server.addHook('onError', async (request, _reply, error) => {
      requestLogger.logError(request.method, request.url, error);
    });
  }

  /**
   * Register all routes
   */
  private registerRoutes(): void {
    // Health check
  this.server.get('/health', async (_request, _reply) => {
      const health = await this.getHealthStatus();
      return health;
    });

    // Readiness probe - lightweight and safe to call during startup
  this.server.get('/ready', async (_request, _reply) => {
      return {
        ready: this.isStarted === true,
        timestamp: new Date().toISOString(),
      };
    });

    // Tool registry routes
  this.server.get('/api/tools', async (_request, _reply) => {
      const tools = await this.toolRegistry.listTools();
      return { tools };
    });

    this.server.get('/api/tools/:toolId', async (request, reply) => {
      const { toolId } = request.params as { toolId: string };
      const tool = await this.toolRegistry.getTool(toolId);
      
      if (!tool) {
        reply.code(404);
        return { error: 'Tool not found' };
      }
      
      return { tool };
    });

    // Tool execution
    this.server.post('/api/tools/:toolId/execute', async (request, reply) => {
      const { toolId } = request.params as { toolId: string };
      const body = request.body as unknown;

      // Validate request body
      const { ExecuteToolRequestSchema } = await import('../types');
      const parsed = ExecuteToolRequestSchema.safeParse(body);
      if (!parsed.success) {
        reply.code(400);
        return { error: 'Invalid tool execution payload', details: parsed.error.format() };
      }

      const { parameters, context } = parsed.data;

      try {
        // Normalize lightweight context into the full ToolExecutionContext expected by the registry
        const execContext = context
          ? ({
              toolName: toolId,
              arguments: (parameters as Record<string, unknown>) || {},
              sessionId: context.sessionId || `session_${Date.now()}`,
              timeout: context.timeout ?? 30000,
              retryCount: context.retryCount ?? 0,
              maxRetries: 3,
              priority: context.priority ?? 'medium',
            } as unknown as import('../types').ToolExecutionContext)
          : ({
              toolName: toolId,
              arguments: (parameters as Record<string, unknown>) || {},
              sessionId: `session_${Date.now()}`,
              timeout: 30000,
              retryCount: 0,
              maxRetries: 3,
              priority: 'medium',
            } as unknown as import('../types').ToolExecutionContext);

  const result = await this.orchestrator.executeTool(toolId, parameters, execContext);
        return { result };
      } catch (error) {
        logger.error(`Tool execution failed for ${toolId}:`, error);
        reply.code(500);
        return { error: 'Tool execution failed' };
      }
    });

    // Workflow routes
    this.server.post('/api/workflows/execute', async (request, reply) => {
      const { workflow, context } = request.body as { workflow: unknown; context?: OrchestrationContext };

      try {
        // Validate workflow using schema to avoid unsafe casts
        const parseResult = (await import('../types')).WorkflowSchema.safeParse(workflow);
        if (!parseResult.success) {
          reply.code(400);
          return { error: 'Invalid workflow payload', details: parseResult.error.format() };
        }

        const validatedWorkflow = parseResult.data;
        const result = await this.orchestrator.executeWorkflow(validatedWorkflow, context || ({} as OrchestrationContext));
        return { result };
      } catch (error: unknown) {
        logger.error('Workflow execution failed:', error);
        reply.code(500);
        return { error: 'Workflow execution failed' };
      }
    });

    // Context intelligence
    this.server.post('/api/intelligence/analyze', async (request, reply) => {
      const { context, objective } = request.body as { context: Record<string, unknown>; objective?: string };
      
      try {
        const analysis = await this.contextIntelligence.analyzeContext(context, objective);
        return { analysis };
      } catch (error: unknown) {
        logger.error('Context analysis failed:', error);
        reply.code(500);
        return { error: 'Context analysis failed' };
      }
    });

    // Performance metrics
    this.server.get('/api/metrics', async (_request, _reply) => {
      const metrics = await this.performanceMonitor.getMetrics();
      return { metrics };
    });

    // WebSocket endpoint for real-time updates
    this.server.register(async function (fastify) {
  fastify.get('/ws', { websocket: true }, (connection, _req) => {
        logger.info('WebSocket connection established');
        
        connection.socket.on('message', (message) => {
          // Handle WebSocket messages
          logger.debug('WebSocket message received:', message.toString());
        });
        
        connection.socket.on('close', () => {
          logger.info('WebSocket connection closed');
        });
      });
    });
  }

  /**
   * Initialize all services
   */
  private async initializeServices(): Promise<void> {
    logger.info('🔧 Initializing services...');
    
    await this.toolRegistry.initialize();
    await this.orchestrator.initialize();
    await this.contextIntelligence.initialize();
    await this.performanceMonitor.initialize();
    
    logger.info('✅ All services initialized');
  }

  /**
   * Start background services
   */
  private async startBackgroundServices(): Promise<void> {
    logger.info('🔧 Starting background services...');
    
    await this.performanceMonitor.start();
    await this.toolRegistry.startDiscovery();
    
    logger.info('✅ Background services started');
  }

  /**
   * Stop background services
   */
  private async stopBackgroundServices(): Promise<void> {
    logger.info('🛑 Stopping background services...');
    
    await this.performanceMonitor.stop();
    await this.toolRegistry.stopDiscovery();
    
    logger.info('✅ Background services stopped');
  }

  /**
   * Get health status
   */
    private async getHealthStatus(): Promise<{
    status: string;
    timestamp: string;
    version: string;
    uptime: number;
    services: Record<string, unknown>;
    system: Record<string, unknown>;
    config: Record<string, unknown>;
  }> {
    const startTime = Date.now();
    
    // Run service health checks in parallel and tolerate failures per-service
    const services = await Promise.allSettled([
      this.toolRegistry.getHealthStatus(),
      this.orchestrator.getHealthStatus(),
      this.contextIntelligence.getHealthStatus(),
      this.performanceMonitor.getHealthStatus(),
    ]);

    const mapResult = (res: PromiseSettledResult<unknown>, name: string) => {
      if (res.status === 'fulfilled') return { name, ok: true, info: res.value };
      const reason = (res as PromiseRejectedResult).reason;
      const message = reason instanceof Error ? reason.message : String(reason);
      return { name, ok: false, error: message };
    };

    const status = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: process.env.npm_package_version || '1.0.0',
      uptime: process.uptime(),
      services: {
        toolRegistry: mapResult(services[0], 'toolRegistry'),
        orchestrator: mapResult(services[1], 'orchestrator'),
        contextIntelligence: mapResult(services[2], 'contextIntelligence'),
        performanceMonitor: mapResult(services[3], 'performanceMonitor'),
      },
      system: {
        memory: process.memoryUsage(),
        platform: process.platform,
        nodeVersion: process.version,
      },
      config: {
        environment: process.env.NODE_ENV || 'development',
        archonMcpUrl: configManager.archonConfig.mcpUrl,
      },
    };

    const responseTime = Date.now() - startTime;
    logger.debug(`Health check completed in ${responseTime}ms`);

    return status;
  }

  /**
   * Get server instance (for testing)
   */
  public getServer(): FastifyInstance {
    return this.server;
  }
}
