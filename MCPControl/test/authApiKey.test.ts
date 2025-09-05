import { describe, test, expect, beforeAll, afterAll } from '@jest/globals';
import { MCPControlServer } from '../src/services/MCPControlServer';

describe('API key auth (negative path and success)', () => {
  let server: MCPControlServer;
  let started = false;
  const prevKey = process.env.MCPCONTROL_API_KEY;
  const KEY = 'super-secret-key';

  beforeAll(async () => {
    process.env.MCPCONTROL_API_KEY = KEY;
    server = new MCPControlServer();
    await server.initialize();
    try {
      await server.start();
      started = true;
    } catch {}
  });

  afterAll(async () => {
    process.env.MCPCONTROL_API_KEY = prevKey;
    if (started) await server.stop();
  });

  test('protected endpoint without key returns 401', async () => {
    const res = await fetch('http://127.0.0.1:8052/api/tools');
    expect(res.status).toBe(401);
  });

  test('protected endpoint with incorrect key returns 401', async () => {
    const res = await fetch('http://127.0.0.1:8052/api/tools', {
      headers: { 'x-api-key': 'wrong' },
    });
    expect(res.status).toBe(401);
  });

  test('protected endpoint with correct key returns 200', async () => {
    const res = await fetch('http://127.0.0.1:8052/api/tools', {
      headers: { 'x-api-key': KEY },
    });
    expect(res.status).toBe(200);
    const body = (await res.json()) as unknown;
    expect(typeof body === 'object' && body !== null).toBeTruthy();
    expect((body as Record<string, unknown>)).toHaveProperty('tools');
  });
});
// This suite verifies that when MCPCONTROL_API_KEY is set, protected endpoints require it

describe('API key auth (optional)', () => {
  const ORIGINAL = process.env.MCPCONTROL_API_KEY;
  let server: MCPControlServer;
  let started = false;

  beforeAll(async () => {
    process.env.MCPCONTROL_API_KEY = 'test-key';
    server = new MCPControlServer();
    await server.initialize();
    try {
      await server.start();
      started = true;
    } catch {}
  });

  afterAll(async () => {
    process.env.MCPCONTROL_API_KEY = ORIGINAL;
    if (started) await server.stop();
  });

  test('rejects request without x-api-key header', async () => {
    const res = await fetch('http://127.0.0.1:8052/api/tools/x/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ parameters: {} }),
    });
    expect(res.status).toBe(401);
  });

  test('accepts request with correct x-api-key header', async () => {
    const res = await fetch('http://127.0.0.1:8052/api/tools/x/execute', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': 'test-key',
      },
      body: JSON.stringify({ parameters: {}, context: { sessionId: 't' } }),
    });
    // Will be 404 or 500 depending on tool existence after auth; just assert not 401
    expect(res.status).not.toBe(401);
  });
});
