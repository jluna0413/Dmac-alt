import { EventEmitter } from 'events';
import { logger, timeLogger } from '../utils/logger';
import { ToolRegistry } from './ToolRegistry';
import {
  Workflow,
  WorkflowExecution,
  ToolExecutionContext,
  ToolExecutionResult,
  OrchestrationContext,
} from '../types';

/**
 * Workflow Orchestrator Service
 * Manages execution of multi-step workflows and tool coordination
 */
export class WorkflowOrchestrator extends EventEmitter {
  private toolRegistry: ToolRegistry;
  private activeExecutions: Map<string, WorkflowExecution> = new Map();
  private isInitialized = false;

  constructor(toolRegistry: ToolRegistry) {
    super();
    this.toolRegistry = toolRegistry;
  }

  /**
   * Initialize the orchestrator
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) {
      logger.warn('WorkflowOrchestrator already initialized');
      return;
    }

    try {
      logger.info('🔧 Initializing WorkflowOrchestrator...');
      
      this.isInitialized = true;
      logger.info('✅ WorkflowOrchestrator initialized successfully');

    } catch (error) {
      logger.error('💥 Failed to initialize WorkflowOrchestrator:', error);
      throw error;
    }
  }

  /**
   * Execute a single tool
   */
  async executeTool(
    toolId: string,
    parameters: Record<string, unknown> | undefined,
    context?: ToolExecutionContext
  ): Promise<ToolExecutionResult> {
    const timer = timeLogger.start(`Tool Execution: ${toolId}`);
    
    try {
      logger.info(`🔧 Orchestrating tool execution: ${toolId}`);
      
      const result = await this.toolRegistry.executeTool(toolId, parameters, context);
      
      timer.end({ success: true, toolId });
      
      this.emit('toolExecuted', {
        toolId,
        parameters,
        result,
        context,
      });

      return result;

    } catch (error) {
      timer.end({ success: false, toolId, error: error instanceof Error ? error.message : String(error) });
      
      logger.error(`Tool orchestration failed: ${toolId}`, error);
      
      this.emit('toolExecutionFailed', {
        toolId,
        parameters,
        error,
        context,
      });

      throw error;
    }
  }

  /**
   * Execute a workflow (simplified implementation)
   */
  async executeWorkflow(
    workflow: Workflow,
    context: OrchestrationContext
  ): Promise<WorkflowExecution> {
    const timer = timeLogger.start(`Workflow Execution: ${workflow.name || 'Unknown'}`);
    const executionId = this.generateExecutionId();
    
    try {
      logger.info(`🚀 Starting workflow execution: ${workflow.name || 'Unknown'}`, {
        executionId,
        sessionId: context.sessionId,
      });

      // Simplified execution - just return success for now
      const execution: WorkflowExecution = {
        id: executionId,
        workflowId: workflow.id || 'unknown',
        sessionId: context.sessionId,
        status: 'completed',
        startTime: new Date().toISOString(),
        endTime: new Date().toISOString(),
        results: [],
        errors: [],
        metadata: context.executionHistory ? { historyCount: context.executionHistory.length } as unknown as Record<string, unknown> : undefined,
      } as WorkflowExecution;

      timer.end({ success: true });
      
      logger.info(`✅ Workflow completed successfully: ${workflow.name || 'Unknown'}`, {
        executionId,
      });

      this.emit('workflowCompleted', execution);

      return execution;

    } catch (error) {
      timer.end({ 
        success: false, 
        error: error instanceof Error ? error.message : String(error),
      });
      
      logger.error(`Workflow execution failed: ${workflow.name || 'Unknown'}`, error);
      throw error;
    }
  }

  /**
   * Generate unique execution ID
   */
  private generateExecutionId(): string {
    return `wf_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get active workflow executions
   */
  async getActiveExecutions(): Promise<WorkflowExecution[]> {
    return Array.from(this.activeExecutions.values());
  }

  /**
   * Get execution by ID
   */
  async getExecution(executionId: string): Promise<WorkflowExecution | undefined> {
    return this.activeExecutions.get(executionId);
  }

  /**
   * Cancel a workflow execution
   */
  async cancelExecution(executionId: string): Promise<boolean> {
    const execution = this.activeExecutions.get(executionId);
    
    if (!execution) {
      logger.warn(`Cannot cancel execution - not found: ${executionId}`);
      return false;
    }

    logger.info(`🛑 Cancelling workflow execution: ${executionId}`);
    
    this.emit('workflowCancelled', execution);
    this.activeExecutions.delete(executionId);
    
    return true;
  }

  /**
   * Get health status
   */
  async getHealthStatus(): Promise<{ status: 'healthy' | 'initializing'; activeExecutions: number; totalExecutions: number } > {
    return {
      status: this.isInitialized ? 'healthy' : 'initializing',
      activeExecutions: this.activeExecutions.size,
      totalExecutions: this.activeExecutions.size,
    };
  }
}
