import { describe, test, expect, beforeAll, afterAll } from '@jest/globals';
import { MCPControlServer } from '../src/services/MCPControlServer';

const RUN = process.env.ARCHON_INTEGRATION_TEST === 'true';

const describeFn = RUN ? describe : describe.skip;

describeFn('Archon integration (optional)', () => {
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

  test('discovers tools from live Archon and exposes them via /api/tools', async () => {
    // Give discovery a brief moment
    await new Promise((r) => setTimeout(r, 300));
    const res = await fetch('http://127.0.0.1:8052/api/tools');
    expect(res.status).toBe(200);
    const body = (await res.json()) as { tools: unknown[] };
    expect(Array.isArray(body.tools)).toBe(true);
    // Expect at least one tool available when Archon is live
    expect(body.tools.length).toBeGreaterThan(0);
  });
});
