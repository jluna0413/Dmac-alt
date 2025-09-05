# Autonomous Coding Ecosystem
## Autonomous Coding Ecosystem (Archon)

Build an MCP‑powered, agentic coding platform that automates repetitive dev work, keeps context synchronized, and lets humans and AI collaborate through standardized tools and protocols.

### Why this exists
- Reduce developer friction by centralizing context and automating code/tasks via AI agents
- Standardize agent <-> tool communication using Model Context Protocol (MCP)
- Keep knowledge, design intent, and code in sync with repeatable workflows

## Architecture at a glance
- Archon (MCP Server): orchestrator and context hub for agents and tools
- Agent microservices: code generation, testing, docs, static analysis, etc.
- Protocols: MCP (agent ↔ tools), ACP/gRPC (agent ↔ services)
- Knowledge & memory: Knowledge Graph (Neo4j) + Vector DB (e.g., Pinecone), Redis for short‑term memory
- Platform: Docker + Kubernetes, CI/CD pipelines, Observability (Prometheus, Grafana, ELK)

See: Tecnical_Docs/Architecture Decision Records ADR.md

## Tech stack
- Languages: Python, Go
- Interfaces & protocols: MCP, gRPC, REST
- Data & memory: Neo4j, Vector DB (Pinecone or equivalent), Redis
- Runtime: Docker, Kubernetes
- Tooling: pre‑commit, Black/Isort, Codacy
- Editors/Clients: VS Code, Cursor, Windsurf, Claude Code (MCP clients)

## Roadmap and progress
- [x] Configuration CLI for MCP tests (`mcp_config.py`): env overrides, deep merge, validation, connection test, search‑path resolution, `--config`, `show --json`
- [x] Repo hygiene: EditorConfig + pre‑commit hooks (trailing whitespace, EOF, JSON/YAML checks, Black/Isort)
- [ ] MCP client/server integration flows and smoke tests in CI
- [ ] Agent microservices (codegen, tests, docs, static analysis)
- [ ] Knowledge graph + vector search wiring and sync jobs
- [ ] Observability (dashboards, tracing) and SLOs

Details: Tecnical_Docs/Product Requirements Plan (PRP), Tecnical_Docs/Component Responsibility Outline.md, Tecnical_Docs/Sequence Diagram.md

## Getting started (Windows PowerShell)
Prereqs: Python 3.10+, Git, PowerShell, optional: Figma desktop for Dev Mode MCP server

1) Create a virtual env and install minimal deps
```powershell
python -m venv A:/Projects/.venv
& A:/Projects/.venv/Scripts/Activate.ps1
pip install --upgrade pip
pip install requests
```

2) Configure MCP server URL (pick one)
- Environment variable
```powershell
$env:MCP_SERVER_URL = "http://127.0.0.1:3845/mcp"  # Figma Dev Mode MCP
```
- Config file (auto‑discovered): `./mcp_config.json`, `%APPDATA%/mcp/mcp_config.json`, or `~/.config/mcp/mcp_config.json`
```json
{
	"mcp_server": { "url": "http://127.0.0.1:3845/mcp", "timeout": 30 }
}
```

3) Validate and inspect config
```powershell
python A:/Projects/mcp_config.py validate
python A:/Projects/mcp_config.py show
python A:/Projects/mcp_config.py show --json | ConvertFrom-Json | Format-List
```

4) Update settings and test connectivity
```powershell
python A:/Projects/mcp_config.py set mcp_server.url http://127.0.0.1:3845/mcp
python A:/Projects/mcp_config.py test-connection
```

Tip: Target a specific file
```powershell
python A:/Projects/mcp_config.py --config A:/Projects/my_config.json show --json
```

## Using the Figma Dev Mode MCP server
1) Enable the local MCP server in Figma desktop (Preferences → Enable local MCP Server)
2) Point your client to http://127.0.0.1:3845/mcp (set via env or config above)
3) Generate code or extract variables from a selected frame via your MCP client

Guide: Tecnical_Docs/Guide to the Dev Mode MCP Server.md

## Developer workflow
- Code style & linting: see Tecnical_Docs/Code Style Guide & Linting Rules.md
- Pre‑commit (optional but recommended):
```powershell
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Key documents
- Product scope & goals: Tecnical_Docs/Product Requirements Plan (PRP)
- ADRs: Tecnical_Docs/Architecture Decision Records ADR.md
- MCP & context: Tecnical_Docs/MCP in Agentic AI_ A Guide to Context Intelligence.md
- Data contracts: Tecnical_Docs/Data Models & Schema Definitions.md
- Teaming: Tecnical_Docs/Autonomous Coding Team Integration_.md

## Status and next steps
Short‑term
- Wire MCP smoke tests into CI (validate, show --json)
- Seed knowledge graph and vector index scaffolding

Mid‑term
- First agent microservice (codegen) behind a simple API
- Integrate metrics/tracing and quality gates in PRs

Have feedback or need a missing section? Open an issue with context and desired outcome.

Repository root for the Autonomous Coding Ecosystem (ACE). This repo contains the Archon orchestrator, agent scaffolds, MCP adapters, docs, and CI configuration.

See `Tecnical_Docs/` for product docs, PRP, ADRs, and templates.

Quickstart

1. Install Python 3.11
2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

3. Run tests

```powershell
.\scripts\run-tests.ps1
```

Project layout

- `src/` — application code (Archon, agents)
- `tests/` — unit and integration tests
- `Tecnical_Docs/` — specifications, PRP, ADRs, and memory templates
- `.github/workflows/` — CI workflows
