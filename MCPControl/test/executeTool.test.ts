import { describe, test, expect, beforeAll, afterAll } from '@jest/globals';
import { MCPControlServer } from '../src/services/MCPControlServer';

describe('POST /api/tools/:toolId/execute validation', () => {
  let server: MCPControlServer;
  let started = false;

  beforeAll(async () => {
    server = new MCPControlServer();
    await server.initialize();
    try {
      await server.start();
      started = true;
    } catch (e: unknown) {
      // If port already in use, assume an instance is running
    }
  });

  afterAll(async () => {
    if (started) await server.stop();
  });

  test('returns 400 for invalid payload', async () => {
    const res = await fetch('http://127.0.0.1:8052/api/tools/x/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ parameters: 'not-an-object' }),
    });
    expect(res.status).toBe(400);
    const body = (await res.json()) as unknown;
    expect(typeof body === 'object' && body !== null).toBeTruthy();
  });
});
