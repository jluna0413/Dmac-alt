import axios from 'axios';
import { EventEmitter } from 'events';
import { configManager } from '../config';
import { logger, timeLogger } from '../utils/logger';
import fs from 'fs/promises';
import path from 'path';
import { 
  MCPTool, 
  MCPServerInfo, 
  ToolRegistryEntry,
  ToolExecutionContext,
  ToolExecutionResult 
} from '../types';

/**
 * Tool Registry Service
 * Manages discovery, registration, and execution of MCP tools
 */
export class ToolRegistry extends EventEmitter {
  private tools: Map<string, ToolRegistryEntry> = new Map();
  private servers: Map<string, MCPServerInfo> = new Map();
  private discoveryInterval?: NodeJS.Timeout | undefined;
  private isInitialized = false;
  private isDiscovering = false;
  // Persistence
  private persistenceDir: string;
  private persistenceFile: string;
  private saveTimer?: NodeJS.Timeout;

  constructor() {
    super();
    this.setMaxListeners(50); // Allow many listeners for tool events
  this.persistenceDir = path.resolve(process.cwd(), 'data');
  this.persistenceFile = path.join(this.persistenceDir, 'tool-registry.json');
  }

  /**
   * Initialize the tool registry
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) {
      logger.warn('ToolRegistry already initialized');
      return;
    }

    try {
      logger.info('🔧 Initializing ToolRegistry...');
      // Try to load persisted registry first, then perform discovery
      await this.loadPersistedRegistry().catch(err => {
        logger.debug('No persisted registry loaded or failed to load:', err instanceof Error ? err.message : String(err));
      });

      // Perform initial discovery (will merge/update persisted data)
      await this.discoverTools();
      
      this.isInitialized = true;
      logger.info('✅ ToolRegistry initialized successfully', {
        toolCount: this.tools.size,
        serverCount: this.servers.size,
      });

    } catch (error) {
      logger.error('💥 Failed to initialize ToolRegistry:', error);
      throw error;
    }
  }

  /**
   * Load persisted registry from disk if present
   */
  private async loadPersistedRegistry(): Promise<void> {
    try {
      const content = await fs.readFile(this.persistenceFile, { encoding: 'utf8' });
      const parsed = JSON.parse(content) as { tools?: unknown; servers?: unknown };

      if (Array.isArray(parsed.tools)) {
        for (const t of parsed.tools as ToolRegistryEntry[]) {
          // Best-effort restore; entries should match ToolRegistryEntry shape
          this.tools.set(t.id, t);
        }
      }

      if (Array.isArray(parsed.servers)) {
        for (const s of parsed.servers as MCPServerInfo[]) {
          this.servers.set(s.id, s);
        }
      }

      logger.info('✅ Loaded persisted tool registry', { toolCount: this.tools.size, serverCount: this.servers.size });
    } catch (error: unknown) {
      // If file does not exist, that's fine
      if (typeof error === 'object' && error !== null) {
        const errObj = error as Record<string, unknown>;
        if (typeof errObj['code'] === 'string' && errObj['code'] === 'ENOENT') return;
      }
      throw error;
    }
  }

  /**
   * Debounced save to disk to avoid excessive writes
   */
  private saveRegistryDebounced(delay = 500): void {
    if (this.saveTimer) clearTimeout(this.saveTimer);
    this.saveTimer = setTimeout(() => void this.saveRegistry().catch(err => logger.error('Failed to persist registry:', err)), delay);
  }

  private async saveRegistry(): Promise<void> {
    try {
      await fs.mkdir(this.persistenceDir, { recursive: true });

      const payload = {
        tools: Array.from(this.tools.values()),
        servers: Array.from(this.servers.values()),
        metadata: {
          savedAt: Date.now(),
        },
      };

      await fs.writeFile(this.persistenceFile, JSON.stringify(payload, null, 2), { encoding: 'utf8' });
      logger.debug('Persisted tool registry to disk', { file: this.persistenceFile });
    } catch (error) {
      logger.error('Error saving tool registry:', error);
      throw error;
    }
  }

  /**
   * Start automatic tool discovery
   */
  async startDiscovery(): Promise<void> {
    if (this.isDiscovering) {
      logger.warn('Tool discovery already running');
      return;
    }

    logger.info('🔍 Starting automatic tool discovery...');
    
    // Initial discovery
    await this.discoverTools();
    
    // Set up periodic discovery
    const interval = configManager.archonConfig.healthCheckInterval || 30000;
    this.discoveryInterval = setInterval(async () => {
      try {
        await this.discoverTools();
      } catch (error) {
        logger.error('Tool discovery failed:', error);
      }
    }, interval);

    this.isDiscovering = true;
    logger.info('✅ Tool discovery started', { interval: `${interval}ms` });
  }

  /**
   * Stop automatic tool discovery
   */
  async stopDiscovery(): Promise<void> {
    if (!this.isDiscovering) {
      logger.warn('Tool discovery not running');
      return;
    }

    logger.info('🛑 Stopping tool discovery...');
    
    if (this.discoveryInterval) {
      clearInterval(this.discoveryInterval);
      this.discoveryInterval = undefined;
    }

    this.isDiscovering = false;
    logger.info('✅ Tool discovery stopped');
  }

  /**
   * Discover tools from Archon MCP server
   */
  async discoverTools(): Promise<void> {
    const timer = timeLogger.start('Tool Discovery');
    
    try {
      logger.debug('🔍 Discovering tools from Archon MCP server...');
      
      const archonUrl = configManager.archonConfig.mcpUrl;
      
      // Get list of available tools from Archon
      const response = await axios.get(`${archonUrl}/tools`, {
        timeout: 10000,
        headers: {
          'Accept': 'application/json',
          'User-Agent': 'MCPControl/1.0.0',
        },
      });

      const { tools, servers } = response.data;
      
      if (!Array.isArray(tools)) {
        throw new Error('Invalid tools response format');
      }

      // Update server information
      if (Array.isArray(servers)) {
  await this.updateServers(servers);
      }

      // Update tools
      await this.updateTools(tools);
  // Persist registry after updating
  this.saveRegistryDebounced();
      
      const discoveredCount = tools.length;
      timer.end({ discoveredCount, serverCount: this.servers.size });
      
      // Emit discovery event
      this.emit('toolsDiscovered', {
        tools: this.tools,
        servers: this.servers,
        timestamp: Date.now(),
      });

    } catch (error) {
      timer.end({ error: error instanceof Error ? error.message : String(error) });
      
      if (axios.isAxiosError(error)) {
        if (error.code === 'ECONNREFUSED') {
          logger.warn('Archon MCP server not available for tool discovery', {
            url: configManager.archonConfig.mcpUrl,
            message: 'Connection refused - server may not be running',
          });
        } else if (error.response?.status === 404) {
          logger.warn('Archon MCP tools endpoint not found', {
            url: `${configManager.archonConfig.mcpUrl}/tools`,
            status: error.response.status,
            message: 'The /tools endpoint may not be implemented yet',
          });
        } else {
          logger.error('Tool discovery request failed:', {
            status: error.response?.status,
            message: error.message,
            url: error.config?.url,
          });
        }
      } else {
        logger.error('Tool discovery failed:', error);
      }
      
      // Don't throw error - continue initialization with empty tool set
      logger.info('Continuing without tool discovery - tools can be registered manually');
    }
  }

  /**
   * Update server information
   */
  private async updateServers(servers: MCPServerInfo[]): Promise<void> {
    for (const server of servers) {
      const existing = this.servers.get(server.id);
      
      if (!existing || existing.lastSeen !== server.lastSeen) {
        this.servers.set(server.id, {
          ...server,
          discoveredAt: existing?.discoveredAt || Date.now(),
          lastUpdated: Date.now(),
        });
        
        logger.debug(`Updated server: ${server.name} (${server.id})`);
      }
  // Save after server updates
  this.saveRegistryDebounced();
    }
  }

  /**
   * Update tool information
   */
  private async updateTools(tools: MCPTool[]): Promise<void> {
    const updatedTools = new Set<string>();
    
    for (const tool of tools) {
      const toolId = this.generateToolId(tool);
      updatedTools.add(toolId);
      
      const existing = this.tools.get(toolId);
      
      if (!existing || this.hasToolChanged(existing.tool, tool)) {
        const registryEntry: ToolRegistryEntry = {
          id: toolId,
          tool,
          serverId: tool.serverId || 'unknown',
          category: this.categorizeTool(tool),
          tags: this.generateTags(tool),
          isAvailable: true,
          lastExecuted: existing?.lastExecuted,
          executionCount: existing?.executionCount || 0,
          averageExecutionTime: existing?.averageExecutionTime || 0,
          successRate: existing?.successRate || 1.0,
          registeredAt: existing?.registeredAt || Date.now(),
          lastUpdated: Date.now(),
          dependencies: existing?.dependencies || [],
          conflictsWith: existing?.conflictsWith || [],
          estimatedExecutionTime: undefined,
          resourceRequirements: existing?.resourceRequirements,
          healthStatus: 'healthy',
        };
        
        this.tools.set(toolId, registryEntry);
        
  if (existing) {
          logger.debug(`Updated tool: ${tool.name} (${toolId})`);
          this.emit('toolUpdated', registryEntry);
        } else {
          logger.info(`Registered new tool: ${tool.name} (${toolId})`);
          this.emit('toolRegistered', registryEntry);
        }
  // Persist changes
  this.saveRegistryDebounced();
      }
    }

    // Mark missing tools as unavailable
    for (const [toolId, entry] of this.tools.entries()) {
      if (!updatedTools.has(toolId) && entry.isAvailable) {
        entry.isAvailable = false;
        entry.lastUpdated = Date.now();
        logger.warn(`Tool became unavailable: ${entry.tool.name} (${toolId})`);
        this.emit('toolUnavailable', entry);
          this.saveRegistryDebounced();
      }
    }
  }

  /**
   * Generate unique tool ID
   */
  private generateToolId(tool: MCPTool): string {
    const serverId = tool.serverId || 'unknown';
    return `${serverId}:${tool.name}`;
  }

  /**
   * Check if tool has changed
   */
  private hasToolChanged(existing: MCPTool, updated: MCPTool): boolean {
    return (
      existing.description !== updated.description ||
      JSON.stringify(existing.inputSchema) !== JSON.stringify(updated.inputSchema) ||
      existing.version !== updated.version
    );
  }

  /**
   * Categorize tool based on its properties
   */
  private categorizeTool(tool: MCPTool): string {
    const name = tool.name.toLowerCase();
    const description = tool.description?.toLowerCase() || '';
    
  // RAG tools
  if (name.includes('rag') || description.includes('rag') || name.includes('search') || description.includes('search') || name.includes('retrieval') || description.includes('retrieval')) {
      return 'rag';
    }
    
    // Project management tools
  if (name.includes('project') || description.includes('project') || name.includes('task') || description.includes('task') || name.includes('document') || description.includes('document')) {
      return 'project-management';
    }
    
    // Data tools
  if (name.includes('data') || description.includes('data') || name.includes('database') || description.includes('database') || name.includes('sql') || description.includes('sql')) {
      return 'data';
    }
    
    // Development tools
  if (name.includes('code') || description.includes('code') || name.includes('git') || description.includes('git') || name.includes('build') || description.includes('build')) {
      return 'development';
    }
    
    // Communication tools
  if (name.includes('notification') || description.includes('notification') || name.includes('message') || description.includes('message') || name.includes('email') || description.includes('email')) {
      return 'communication';
    }
    
    // File tools
  if (name.includes('file') || description.includes('file') || name.includes('upload') || description.includes('upload') || name.includes('download') || description.includes('download')) {
      return 'file-management';
    }
    
    return 'general';
  }

  /**
   * Generate tags for a tool
   */
  private generateTags(tool: MCPTool): string[] {
    const tags: string[] = [];
    const name = tool.name.toLowerCase();
    const description = tool.description?.toLowerCase() || '';
    
    // Add category-based tags
    if (name.includes('create') || description.includes('create')) tags.push('create');
    if (name.includes('update') || description.includes('update')) tags.push('update');
    if (name.includes('delete') || description.includes('delete')) tags.push('delete');
    if (name.includes('list') || description.includes('list')) tags.push('list');
    if (name.includes('search') || description.includes('search')) tags.push('search');
    
    // Add domain-specific tags
    if (name.includes('ai') || description.includes('ai')) tags.push('ai');
    if (name.includes('async') || description.includes('async')) tags.push('async');
    if (name.includes('real-time') || description.includes('real-time')) tags.push('real-time');
    
    return tags;
  }

  /**
   * Get all registered tools
   */
  async listTools(): Promise<ToolRegistryEntry[]> {
    return Array.from(this.tools.values());
  }

  /**
   * Get a specific tool by ID
   */
  async getTool(toolId: string): Promise<ToolRegistryEntry | undefined> {
    return this.tools.get(toolId);
  }

  /**
   * Get tools by category
   */
  async getToolsByCategory(category: string): Promise<ToolRegistryEntry[]> {
    return Array.from(this.tools.values()).filter(entry => entry.category === category);
  }

  /**
   * Search tools by tags or name
   */
  async searchTools(query: string): Promise<ToolRegistryEntry[]> {
    const searchTerm = query.toLowerCase();
    
    return Array.from(this.tools.values()).filter(entry => {
      return (
        entry.tool.name.toLowerCase().includes(searchTerm) ||
        entry.tool.description?.toLowerCase().includes(searchTerm) ||
        entry.category.includes(searchTerm) ||
        entry.tags.some(tag => tag.includes(searchTerm))
      );
    });
  }

  /**
   * Execute a tool through Archon MCP
   */
  async executeTool(
    toolId: string,
    parameters: Record<string, unknown> | undefined,
    context?: ToolExecutionContext
  ): Promise<ToolExecutionResult> {
    const timer = timeLogger.start(`Tool Execution: ${toolId}`);
    
    try {
      const tool = this.tools.get(toolId);
      if (!tool) {
        throw new Error(`Tool not found: ${toolId}`);
      }

      if (!tool.isAvailable) {
        throw new Error(`Tool is not available: ${toolId}`);
      }

      logger.info(`🔧 Executing tool: ${tool.tool.name}`, {
        toolId,
        parameters: parameters ? Object.keys(parameters) : [],
        context: context?.sessionId,
      });

      // Execute through Archon MCP
      const archonUrl = configManager.archonConfig.mcpUrl;
      const response = await axios.post(
        `${archonUrl}/tools/${encodeURIComponent(toolId)}/execute`,
        {
          parameters,
          context,
        },
        {
          timeout: configManager.orchestrationConfig.defaultTimeout,
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
        }
      );

  const result: ToolExecutionResult = response.data as ToolExecutionResult;
      const duration = timer.end({ success: true });

      // Update tool statistics
      await this.updateToolStatistics(toolId, duration, true);

      this.emit('toolExecuted', {
        toolId,
        parameters,
        result,
        duration,
        context,
      });

      return result;

    } catch (error) {
      const duration = timer.end({ success: false, error: error instanceof Error ? error.message : String(error) });
      
      // Update tool statistics
      await this.updateToolStatistics(toolId, duration, false);

      logger.error(`Tool execution failed: ${toolId}`, error);
      
      this.emit('toolExecutionFailed', {
        toolId,
        parameters,
        error,
        duration,
        context,
      });

      throw error;
    }
  }

  /**
   * Update tool execution statistics
   */
  private async updateToolStatistics(
    toolId: string, 
    duration: number, 
    success: boolean
  ): Promise<void> {
    const tool = this.tools.get(toolId);
    if (!tool) return;

    tool.executionCount += 1;
    tool.lastExecuted = Date.now();
    
    // Update average execution time
    if (tool.averageExecutionTime === 0) {
      tool.averageExecutionTime = duration;
    } else {
      tool.averageExecutionTime = (tool.averageExecutionTime + duration) / 2;
    }
    
    // Update success rate
    const totalExecutions = tool.executionCount;
    const previousSuccesses = Math.round((tool.successRate || 1.0) * (totalExecutions - 1));
    const currentSuccesses = previousSuccesses + (success ? 1 : 0);
    tool.successRate = currentSuccesses / totalExecutions;
    
    tool.lastUpdated = Date.now();
  }

  /**
   * Get health status
   */
  async getHealthStatus(): Promise<{
    status: 'healthy' | 'initializing' | 'degraded';
    toolCount: number;
    availableTools: number;
    serverCount: number;
    isDiscovering: boolean;
    lastDiscovery: number | undefined;
  }> {
    return {
      status: this.isInitialized ? 'healthy' : 'initializing',
      toolCount: this.tools.size,
      availableTools: Array.from(this.tools.values()).filter(t => t.isAvailable).length,
      serverCount: this.servers.size,
      isDiscovering: this.isDiscovering,
      lastDiscovery: this.discoveryInterval ? Date.now() : undefined,
    };
  }
}
