# MCP Config Utility

A small CLI to manage MCP test configuration (JSON file + env overrides).

Features
- Load defaults, merge `mcp_config.json` if present, then apply env vars
- Validate required settings and writable result folder
- Dot-notation get/set and persistence
- Connectivity smoke test to the MCP server
- Windows-safe output (emojis fall back to ASCII in non-UTF consoles)
 - Custom config path with `--config`/`-c`

Common env vars
- `MCP_SERVER_URL` (e.g., http://localhost:8051/mcp)
- `MCP_TIMEOUT` (int seconds)
- `MCP_RETRY_ATTEMPTS` (int)
- `MCP_RETRY_DELAY` (float seconds)
- `DEBUG_VERBOSE` (true/false)
- `LOG_LEVEL` (e.g., INFO)
- `TEST_RESULTS_DIR` (path)

Notes
- Use `generate-config -f` to overwrite without prompt.
- On Windows terminals that are not UTF-8, the tool automatically switches emoji icons to ASCII.
 - To use a different config file: `python mcp_config.py --config ./alt.json show` or `python mcp_config.py -c A:\\Projects\\my.json validate`.
