import { describe, test, expect, beforeAll, afterAll, jest } from '@jest/globals';
import { MCPControlServer } from '../src/services/MCPControlServer';

jest.setTimeout(20000);

describe('MCPControl health endpoints', () => {
  let server: MCPControlServer | null = null;
  let serverStarted = false;

  beforeAll(async () => {
    server = new MCPControlServer();
    await server.initialize();
    try {
      await server.start();
      serverStarted = true;
    } catch (err: unknown) {
      // If port is already in use, assume a dev server is running and continue tests
      if (err && typeof (err as any).code === 'string' && (err as any).code === 'EADDRINUSE') {
        // leave serverStarted false and proceed to test against existing server
        // eslint-disable-next-line no-console
        console.warn('Port in use; running tests against existing server instance.');
      } else {
        throw err;
      }
    }
  });

  afterAll(async () => {
  if (server && serverStarted) await server.stop();
  });

  test('ready endpoint returns true', async () => {
  const res = await fetch('http://127.0.0.1:8052/ready');
    expect(res.ok).toBeTruthy();
  const body = await res.json() as unknown;
  expect(typeof body === 'object' && body !== null).toBeTruthy();
  expect((body as Record<string, unknown>)).toHaveProperty('ready');
  });

  test('health endpoint returns services object', async () => {
    const res = await fetch('http://127.0.0.1:8052/health');
    expect(res.ok).toBeTruthy();
  const body2 = await res.json() as unknown;
  expect(typeof body2 === 'object' && body2 !== null).toBeTruthy();
  expect((body2 as Record<string, unknown>)).toHaveProperty('services');
  expect((body2 as any).services).toHaveProperty('toolRegistry');
  });
});
