# Per-project Environment Setup

To avoid dependency conflicts between cloned projects, each project should create an isolated environment named `.venv` in the project root.

Files added:

- `scripts/setup-env.ps1` — PowerShell script to create a per-project `.venv` and install dependencies (Windows)
- `scripts/setup-env.sh` — Bash script to create a per-project `.venv` and install dependencies (Linux/macOS)
- `scripts/setup-all-project-envs.ps1` — Bulk initializer to create envs for all subfolders under `A:\Projects`

Usage (PowerShell):

```powershell
.\scripts\setup-env.ps1 -ProjectPath . -PythonExe python
```

Usage (Bash):

```bash
./scripts/setup-env.sh .
```

Bulk init (PowerShell):

```powershell
.\scripts\setup-all-project-envs.ps1 -Root "A:\Projects"
```

Add `.venv/` to each project's `.gitignore` to avoid committing environments.


## MCP integration

Set MCP-related environment variables per project (do not commit).

Example `.env` keys (place in project root or use CI secrets):

- BYTEROVER_MCP_URL — MCP base URL (e.g. https://mcp.local:8443)
- BYTEROVER_EXTENSION_ID — extension id to use (example: byterover.byterover)
- BYTEROVER_AUTH_TOKEN — bearer token for Authorization header

For local multi-repo workflows, run a shared MCP server (e.g., Archon's MCP server) and point all projects to it using `BYTEROVER_MCP_URL`.

### Local MCP stub (development)

If you want a lightweight local MCP for integration testing, a minimal stub is available at `A:\Projects\mcp-stub`.

- Run with uvicorn (development):

```powershell
python -m uvicorn main:app --app-dir A:\Projects\mcp-stub\app --host 127.0.0.1 --port 8080
```

- Run with Docker Compose (rebuild on change):

```powershell
docker-compose -f A:\Projects\mcp-stub\docker-compose.yml up --build
```

- Run the provided integration helper (starts stub, runs test, stops stub):

```powershell
A:\Projects\mcp-stub\scripts\run_integration_tests.ps1
```

When running tests locally, set `BYTEROVER_MCP_URL` to `http://127.0.0.1:8080` or export the variable in your test runner/CI.

CI notes:

- The `integration.yml` workflow runs a pytest that uses a `conftest` fixture to programmatically start the local stub (uvicorn) on a free port. This keeps CI fast and avoids requiring Docker on the runner.
- If you prefer container parity, the previous docker-compose-based job exists in the repo history and can be restored.

### Try it (PowerShell)

1. Start the stub on port 8080 (from repo root):

```powershell
python -m uvicorn main:app --app-dir A:\Projects\mcp-stub\app --host 127.0.0.1 --port 8080
```

2. In a new PowerShell session set the env var and run the focused integration test:

```powershell
$env:BYTEROVER_MCP_URL = 'http://127.0.0.1:8080'
pytest A:\Projects\mcp-stub\tests -q
```

3. Use the helper to run the stub, tests, and stop the stub automatically:

```powershell
A:\Projects\mcp-stub\scripts\run_integration_tests.ps1
```

If tests fail, open `mcp-stub/app/main.py` and `mcp-stub/tests/conftest.py` to diagnose readiness probe mismatches or port conflicts.
