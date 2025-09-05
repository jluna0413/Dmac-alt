# PRP Task List — Autonomous Coding Ecosystem (MVP)

This file lists the initial implementation tasks extracted from PRP-001. Status: TODO/IN_PROGRESS/DONE.

## Project: Autonomous Coding Ecosystem (PRP-001)

- [x] TASK-001: Repo skeleton & CI  - Status: DONE
  - Owner: Archon
  - Priority: High
  - Description: Create repository structure, GitHub Actions for lint/test, initial README, and CONTRIBUTING.

- [ ] TASK-002: Database schema & migrations
  - Owner: Archon
  - Priority: High
  - Description: Design metadata schema for tasks, plans, agents, and knowledge entries.

- [ ] TASK-011: CI Sanity & ENV Setup
  - Owner: DevOpsAgent
  - Priority: High
  - Status: IN_PROGRESS
  - Description: Add GitHub Actions job to run sanity tests (`tests/test_sanity_checks.py`) and full pytest; document per-project `.venv` setup and MCP env variables in `Tecnical_Docs/ENV_SETUP.md`.

  - NOTE: A local MCP stub was added at `A:\Projects\mcp-stub` to support integration testing and local multi-repo workflows.
  - Acceptance criteria:
  - NOTE: A local MCP stub was added at `A:\Projects\mcp-stub` to support integration testing and local multi-repo workflows.
  - Acceptance criteria:
    - GitHub Action `integration.yml` exists and runs the `mcp-stub/tests` integration tests. CI may start the stub via docker-compose or use the pytest `conftest` fixture which starts uvicorn programmatically (fixture-based is preferred for speed).
    - `Tecnical_Docs/ENV_SETUP.md` includes local stub run instructions.
    - An integration helper script exists at `mcp-stub/scripts/run_integration_tests.ps1` and runs locally without leaving orphan processes.

 - [x] TASK-002: MCP adapter core  - Status: DONE
  - Owner: IntegrationAgent
  - Priority: High
  - Description: Implement thin client wrapping listed byterover-* tools with an offline fallback.

- [ ] TASK-003: Agent scaffolds  - Status: IN_PROGRESS
  - Owner: CodeGenerationAgent
  - Priority: High
  - Description: Minimal implementations for CodeGenerationAgent, TestingAgent, DocumentationAgent; include MCP client integration and basic process_task interface.
