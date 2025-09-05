import { describe, test, expect, beforeAll, afterAll, jest } from '@jest/globals';
import { MCPControlServer } from '../src/services/MCPControlServer';

describe('POST /api/tools/:toolId/execute success path', () => {
  let server: MCPControlServer;
  let started = false;

  beforeAll(async () => {
    server = new MCPControlServer();
    await server.initialize();
    try {
      await server.start();
      started = true;
    } catch {}
  });

  afterAll(async () => {
    if (started) await server.stop();
  });

  test('returns 200 and result when orchestrator resolves', async () => {
    // Mock orchestrator.executeTool to return a fake result
    const anyServer = server as unknown as { orchestrator: { executeTool: (...args: unknown[]) => Promise<unknown> } };
    const fakeResult = {
      success: true,
      result: { echoed: true },
      error: undefined,
      executionTime: 12,
      toolName: 'server:echo',
      sessionId: 's-test',
      workflowId: undefined,
      timestamp: new Date().toISOString(),
    };

  const spy = jest
      .spyOn(anyServer.orchestrator, 'executeTool')
      .mockResolvedValueOnce(fakeResult as unknown);

    const res = await fetch('http://127.0.0.1:8052/api/tools/server:echo/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ parameters: { msg: 'hi' }, context: { sessionId: 's-test' } }),
    });

    expect(res.status).toBe(200);
    const body = (await res.json()) as { result: typeof fakeResult };
    expect(body.result.success).toBe(true);
    expect(spy).toHaveBeenCalled();
  });
});
