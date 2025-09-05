import { describe, test, expect, beforeEach, afterEach, jest } from '@jest/globals';
import axios from 'axios';
import { ToolRegistry } from '../src/services/ToolRegistry';

jest.mock('axios');

describe('ToolRegistry - discovery robustness', () => {
  const mockedAxios = axios as jest.Mocked<typeof axios>;

  beforeEach(() => {
    jest.useFakeTimers();
    jest.spyOn(global, 'setInterval');
    jest.spyOn(global, 'clearInterval');
  });

  afterEach(() => {
    jest.clearAllTimers();
    jest.resetAllMocks();
  });

  test('initialize tolerates ECONNREFUSED from Archon', async () => {
    mockedAxios.get.mockRejectedValueOnce(
      Object.assign(new Error('connect ECONNREFUSED'), { code: 'ECONNREFUSED' })
    );

    const registry = new ToolRegistry();
    await expect(registry.initialize()).resolves.toBeUndefined();
    await expect(registry.listTools()).resolves.toEqual([]);
  });

  test('initialize tolerates 404 /tools endpoint missing', async () => {
    mockedAxios.get.mockRejectedValueOnce({
      isAxiosError: true,
      response: { status: 404 },
      message: 'Not Found',
      config: { url: 'http://localhost:8051/mcp/tools' },
    });

    const registry = new ToolRegistry();
    await expect(registry.initialize()).resolves.toBeUndefined();
    await expect(registry.listTools()).resolves.toEqual([]);
  });

  test('startDiscovery sets up interval and stopDiscovery clears it', async () => {
    // First discovery attempt will reject, but should be tolerated
    mockedAxios.get.mockRejectedValueOnce(
      Object.assign(new Error('connect ECONNREFUSED'), { code: 'ECONNREFUSED' })
    );

    const registry = new ToolRegistry();
    await registry.startDiscovery();

    expect(setInterval).toHaveBeenCalled();

    await registry.stopDiscovery();
    expect(clearInterval).toHaveBeenCalled();
  });
});
