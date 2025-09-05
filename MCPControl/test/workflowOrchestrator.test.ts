import { describe, test, expect, jest, beforeAll } from '@jest/globals';
import { WorkflowOrchestrator } from '../src/services/WorkflowOrchestrator';
import type { ToolRegistry } from '../src/services/ToolRegistry';
import type { OrchestrationContext, Workflow, ToolExecutionResult, ToolExecutionContext } from '../src/types';

describe('WorkflowOrchestrator', () => {
  const executeToolMock = jest.fn(async (_toolId: string, _params: Record<string, unknown> | undefined, _ctx?: ToolExecutionContext) => ({
    success: true,
    result: { ok: true },
    executionTime: 10,
    toolName: 'toolA',
    sessionId: 's1',
    timestamp: new Date().toISOString(),
  } as ToolExecutionResult)) as unknown as (
    toolId: string,
    params: Record<string, unknown> | undefined,
    ctx?: ToolExecutionContext
  ) => Promise<ToolExecutionResult>;

  const mockRegistry = {
    executeTool: executeToolMock,
  } as unknown as ToolRegistry;

  const orchestrator = new WorkflowOrchestrator(mockRegistry);

  beforeAll(async () => {
    // Stub only the methods we use
    await orchestrator.initialize();
  });

  test('executeTool delegates to ToolRegistry and returns result', async () => {
    const res = await orchestrator.executeTool('server:toolA', { a: 1 }, {
      toolName: 'toolA',
      arguments: { a: 1 },
      sessionId: 's1',
      timeout: 1000,
      retryCount: 0,
      maxRetries: 1,
      priority: 'low',
    });
  expect(executeToolMock).toHaveBeenCalledWith('server:toolA', { a: 1 }, expect.any(Object));
    expect(res.success).toBe(true);
  });

  test('executeWorkflow returns a completed execution skeleton', async () => {
    const wf: Workflow = {
      id: 'wf1',
      name: 'Test WF',
      description: 'desc',
      steps: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      version: '1.0.0',
    } as Workflow;

    const ctx: OrchestrationContext = {
      sessionId: 's1',
      userGoal: 'goal',
      availableTools: [],
      executionHistory: [],
    };

    const exec = await orchestrator.executeWorkflow(wf, ctx);
    expect(exec.status).toBe('completed');
    expect(exec.workflowId).toBe('wf1');
  });
});
