import { z } from 'zod';

/**
 * MCP Protocol Schemas and Types
 */

// Base MCP Protocol Types
export const MCPRequestSchema = z.object({
  jsonrpc: z.literal('2.0'),
  id: z.union([z.string(), z.number()]).optional(),
  method: z.string(),
  params: z.record(z.unknown()).optional(),
});

export const MCPResponseSchema = z.object({
  jsonrpc: z.literal('2.0'),
  id: z.union([z.string(), z.number()]),
  result: z.unknown().optional(),
  error: z.object({
    code: z.number(),
    message: z.string(),
  data: z.unknown().optional(),
  }).optional(),
});

export const MCPToolSchema = z.object({
  name: z.string(),
  description: z.string(),
  inputSchema: z.record(z.unknown()),
  serverId: z.string().optional(),
  version: z.string().optional(),
});

export const MCPServerInfoSchema = z.object({
  id: z.string(),
  name: z.string(),
  version: z.string(),
  protocolVersion: z.string(),
  url: z.string().optional(),
  lastSeen: z.string(),
  discoveredAt: z.number().optional(),
  lastUpdated: z.number().optional(),
});

// Tool Execution Types
export const ToolExecutionContextSchema = z.object({
  toolName: z.string(),
  arguments: z.record(z.unknown()),
  sessionId: z.string(),
  workflowId: z.string().optional(),
  priority: z.enum(['low', 'medium', 'high']).default('medium'),
  timeout: z.number().default(30000),
  retryCount: z.number().default(0),
  maxRetries: z.number().default(3),
});

export const ToolExecutionResultSchema = z.object({
  success: z.boolean(),
  result: z.unknown().optional(),
  error: z.string().optional(),
  executionTime: z.number(),
  toolName: z.string(),
  sessionId: z.string(),
  workflowId: z.string().optional(),
  timestamp: z.string(),
});

// API Request Schemas
export const ExecuteToolRequestSchema = z.object({
  parameters: z.record(z.unknown()).optional(),
  context: z.object({
    sessionId: z.string().optional(),
    timeout: z.number().optional(),
    priority: z.enum(['low', 'medium', 'high']).optional(),
    retryCount: z.number().optional(),
  }).optional(),
});

// Workflow Types
export const WorkflowStepSchema = z.object({
  id: z.string(),
  toolName: z.string(),
  arguments: z.record(z.unknown()),
  dependencies: z.array(z.string()).default([]),
  condition: z.string().optional(),
  onSuccess: z.string().optional(),
  onError: z.string().optional(),
  timeout: z.number().default(30000),
  retryPolicy: z.object({
    maxRetries: z.number().default(3),
    backoffMs: z.number().default(1000),
    exponentialBackoff: z.boolean().default(true),
  }).optional(),
});

export const WorkflowSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  steps: z.array(WorkflowStepSchema),
  metadata: z.record(z.unknown()).optional(),
  version: z.string().default('1.0.0'),
  createdAt: z.string(),
  updatedAt: z.string(),
});

export const WorkflowExecutionSchema = z.object({
  id: z.string(),
  workflowId: z.string(),
  sessionId: z.string(),
  status: z.enum(['pending', 'running', 'completed', 'failed', 'cancelled']),
  currentStep: z.string().optional(),
  startTime: z.string(),
  endTime: z.string().optional(),
  results: z.array(ToolExecutionResultSchema).default([]),
  errors: z.array(z.string()).default([]),
  metadata: z.record(z.unknown()).optional(),
});

// Orchestration Types
export const ToolRegistryEntrySchema = z.object({
  id: z.string(),
  tool: MCPToolSchema,
  serverId: z.string(),
  category: z.string(),
  tags: z.array(z.string()).default([]),
  isAvailable: z.boolean(),
  lastExecuted: z.number().optional(),
  executionCount: z.number(),
  averageExecutionTime: z.number(),
  successRate: z.number(),
  registeredAt: z.number(),
  lastUpdated: z.number(),
  dependencies: z.array(z.string()).default([]),
  conflictsWith: z.array(z.string()).default([]),
  estimatedExecutionTime: z.number().optional(),
  resourceRequirements: z.object({
    cpu: z.number().optional(),
    memory: z.number().optional(),
    network: z.boolean().default(false),
  }).optional(),
  healthStatus: z.enum(['healthy', 'degraded', 'unhealthy']).default('healthy'),
});

export const OrchestrationContextSchema = z.object({
  sessionId: z.string(),
  userGoal: z.string(),
  availableTools: z.array(z.string()),
  executionHistory: z.array(ToolExecutionResultSchema).default([]),
  constraints: z.object({
    maxExecutionTime: z.number().optional(),
    maxConcurrentTools: z.number().default(5),
    allowedCategories: z.array(z.string()).optional(),
    forbiddenTools: z.array(z.string()).default([]),
  }).optional(),
  preferences: z.object({
    preferredTools: z.array(z.string()).default([]),
    executionStrategy: z.enum(['sequential', 'parallel', 'adaptive']).default('adaptive'),
    errorHandling: z.enum(['strict', 'lenient', 'skip']).default('lenient'),
  }).optional(),
});

// Performance Monitoring Types
export const PerformanceMetricsSchema = z.object({
  toolName: z.string(),
  executionCount: z.number(),
  averageExecutionTime: z.number(),
  successRate: z.number(),
  errorRate: z.number(),
  lastExecution: z.string(),
  resourceUsage: z.object({
    avgCpuUsage: z.number().optional(),
    avgMemoryUsage: z.number().optional(),
    networkRequests: z.number().optional(),
  }).optional(),
});

// Configuration Types
export const MCPControlConfigSchema = z.object({
  server: z.object({
    port: z.number().default(8052),
    host: z.string().default('localhost'),
    enableCors: z.boolean().default(true),
  }),
  archon: z.object({
    mcpUrl: z.string(),
    serverUrl: z.string(),
    uiUrl: z.string(),
    healthCheckInterval: z.number().default(30000),
  }),
  orchestration: z.object({
    maxConcurrentTools: z.number().default(10),
    defaultTimeout: z.number().default(30000),
    workflowTimeout: z.number().default(300000),
    enableCache: z.boolean().default(true),
  }),
  monitoring: z.object({
    enableAnalytics: z.boolean().default(true),
    retentionDays: z.number().default(30),
    performanceMetrics: z.boolean().default(true),
  }),
  security: z.object({
    allowedOrigins: z.array(z.string()).default([]),
    apiKeyRequired: z.boolean().default(false),
  }),
  logging: z.object({
    level: z.string().default('info'),
    enableFileLogging: z.boolean().default(true),
    maxFileSize: z.number().default(5242880), // 5MB
    maxFiles: z.number().default(5),
  }),
});

// Type exports
export type MCPRequest = z.infer<typeof MCPRequestSchema>;
export type MCPResponse = z.infer<typeof MCPResponseSchema>;
export type MCPTool = z.infer<typeof MCPToolSchema>;
export type MCPServerInfo = z.infer<typeof MCPServerInfoSchema>;
export type ToolExecutionContext = z.infer<typeof ToolExecutionContextSchema>;
export type ToolExecutionResult = z.infer<typeof ToolExecutionResultSchema>;
export type WorkflowStep = z.infer<typeof WorkflowStepSchema>;
export type Workflow = z.infer<typeof WorkflowSchema>;
export type WorkflowExecution = z.infer<typeof WorkflowExecutionSchema>;
export type ToolRegistryEntry = z.infer<typeof ToolRegistryEntrySchema>;
export type OrchestrationContext = z.infer<typeof OrchestrationContextSchema>;
export type PerformanceMetrics = z.infer<typeof PerformanceMetricsSchema>;
export type MCPControlConfig = z.infer<typeof MCPControlConfigSchema>;
export type ExecuteToolRequest = z.infer<typeof ExecuteToolRequestSchema>;

// Utility Types
export interface LogContext {
  sessionId?: string;
  workflowId?: string;
  toolName?: string;
  operation?: string;
  [key: string]: unknown;
}

export interface EventPayload {
  type: string;
  payload: unknown;
  timestamp: string;
  sessionId?: string;
  workflowId?: string;
}

export interface HealthCheckResult {
  status: 'healthy' | 'degraded' | 'unhealthy';
  checks: {
    [service: string]: {
      status: 'healthy' | 'degraded' | 'unhealthy';
      responseTime?: number;
      error?: string;
    };
  };
  timestamp: string;
}
