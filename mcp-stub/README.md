# MCP Stub (Byterover Local MCP)

Purpose

This repository contains a small, local MCP (Byterover) stub useful for local development and integration testing. It implements a minimal set of POST endpoints that mirror the production MCP endpoints the `ByteroverClient` expects.

Quick start (PowerShell)

1. Install dependencies:

```powershell
python -m pip install -r A:\Projects\mcp-stub\requirements.txt
```

2a. Run locally with uvicorn (recommended for development):

```powershell
# from A:\Projects\mcp-stub
python -m uvicorn main:app --app-dir A:\Projects\mcp-stub\app --host 127.0.0.1 --port 8080
```

2b. Or run via Docker Compose:

```powershell
docker-compose -f A:\Projects\mcp-stub\docker-compose.yml up --build
```

Run integration tests

- A helper PowerShell script is provided to start the stub, run the integration tests, and stop the stub when finished:

```powershell
A:\Projects\mcp-stub\scripts\run_integration_tests.ps1
```

Environment

- The client uses `BYTEROVER_MCP_URL` to locate the MCP; for local testing set it to `http://127.0.0.1:8080`.

Notes

- The stub is intentionally minimal and returns simple echo responses. It's designed for fast iteration and local integration tests.
- If you prefer Linux/macOS, the same commands apply with path adjustments.
