# MCPControl

[![CI](https://github.com/jluna0413/Dmac-alt/actions/workflows/ci.yml/badge.svg)](https://github.com/jluna0413/Dmac-alt/actions/workflows/ci.yml)

MCPControl is a local orchestration service for MCP tools. It provides a centralized registry, workflow orchestration, context intelligence, and monitoring for MCP tools and Archon integrations.

## Quick start

Requirements: Node 18+ (Node 22 recommended), npm, Windows PowerShell (commands shown here).

1. Install dependencies

```powershell
cd A:\Projects\MCPControl
npm install
```

2. Run in development mode (tsx watch)

```powershell
cd A:\Projects\MCPControl
npm run dev
```

The server will bind to the host and port in `.env` (defaults to `127.0.0.1:8052`).

## Endpoints

- GET /health — full health payload (may be slightly heavier)
- GET /ready — lightweight readiness probe (true once server fully started)

## Security (optional API key)

You can enable a simple API key check for all non-public endpoints by setting the environment variable `MCPCONTROL_API_KEY`.

- Public (no key required): `GET /health`, `GET /ready`, `GET /ws`
- Protected (key required when enabled): all paths under `/api/*`

When enabled, clients must send header `x-api-key: <your-key>`.

## Troubleshooting

- If `npm run dev` shows errors about `package.json` not found, ensure you're in the project directory: `cd A:\Projects\MCPControl`.
- If a previous server is running, stop it with `Stop-Process -Name node -Force` in PowerShell, or kill the PID listed by `netstat -ano | findstr :8052`.

## Notes and TODOs

- DONE: Integration tests for health/readiness endpoints added (`test/health.test.ts`).
- DONE: Tool registry persistence implemented (saved to `data/tool-registry.json`).
- DONE: CI workflow added at `.github/workflows/ci.yml` which runs lint, build, tests, and a health check.
- DONE: Replace unsafe `any` types in schemas with safer `unknown` equivalents.
- DONE: Add integration with systemd / Windows service runner for production deployments (see `DEPLOYMENT.md`).
- DONE: Add unit tests for `ToolRegistry` and `WorkflowOrchestrator`.
- TODO: Tighten flexible schemas (`z.record(z.unknown())`) to concrete shapes where practical.
- DONE: Optional API key auth via `MCPCONTROL_API_KEY` with tests.

## Deployment

- Windows service (NSSM): see `DEPLOYMENT.md` for detailed steps.
- Quick commands:

```powershell
# From MCPControl root
npm run build
npm run svc:install   # installs and starts service via NSSM
# ... later
npm run svc:uninstall # stops and removes service
```

CI notes:

- The GitHub Actions workflow runs on ubuntu-latest. It runs `npm ci`, `npm run lint`, `npm run build`, `npm test`, and then checks `/ready` and `/health` using `curl` and `jq`.
- For Windows-based CI or on-runner checks, you can use `scripts/check-health.ps1`.

Local quick CI-style steps:

```powershell
cd A:\Projects\MCPControl
npm ci
npm run lint
npm run typecheck
npm run build
npm test
.
\scripts\check-health.ps1
```

## How I verified

I started the server locally and validated background services initialize; use `curl http://127.0.0.1:8052/ready` to verify readiness quickly.

Run the included health check script (PowerShell):

```powershell
cd A:\Projects\MCPControl
.
\scripts\check-health.ps1
```

Toolchain note:

- TypeScript is pinned to 5.3.x to match the supported range of the current `@typescript-eslint` toolchain and silence parser warnings. If you upgrade TypeScript, also upgrade `@typescript-eslint/*` packages accordingly.
