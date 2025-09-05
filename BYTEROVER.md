# Byterover Handbook

*Generated: September 3, 2025*

## Layer 1: System Overview

**Purpose**: Autonomous Coding Ecosystem (ACE) - A comprehensive multi-repo system for intelligent code management, knowledge processing, and AI-powered project automation. The ecosystem consists of Archon (knowledge engine), Dmac-alt (MCP client), and supporting tools for autonomous code generation and management.

**Tech Stack**: 
- **Backend**: Python 3.11, FastAPI, Supabase (PostgreSQL with vector extensions)
- **MCP Protocol**: Model Context Protocol for AI client integration (SSE transport)
- **HTTP Client**: httpx, requests with retry/backoff patterns
- **Testing**: pytest, mypy for strict type checking
- **Container**: Docker Compose for orchestration
- **AI Integration**: PydanticAI agents, OpenAI embeddings, vector search

**Architecture**: Microservices architecture with clear separation of concerns:
- **Archon Server** (port 8080): FastAPI backend with business logic, RAG, and project management
- **Archon MCP** (port 8051): MCP protocol server exposing 14 tools for AI clients
- **Dmac Client**: HTTP client library for MCP integration with offline fallback
- **Agent Services** (port 8052): PydanticAI agents for document processing and RAG

**Key Technical Decisions**:
- MCP-first architecture for AI client compatibility (Cursor, Windsurf, Claude Code)
- Service layer pattern: MCP makes HTTP calls to Server API (no direct database access)
- Vector embeddings with hybrid search (semantic + keyword) using Supabase pgvector
- Offline-first client design with JSON fallback for resilient integration testing
- Strict type checking with mypy and comprehensive pytest coverage

**Entry Points**: 
- `A:\Projects\Archon\python\src\server\main.py` - Main FastAPI server
- `A:\Projects\Archon\python\src\mcp\mcp_server.py` - MCP protocol server
- `A:\Projects\Dmac-alt\src\dmac\client.py` - MCP client library
- `A:\Projects\mcp-stub\app\main.py` - Local MCP stub for testing

---

## Layer 2: Module Map

**Core Modules**:
- **archon/server**: FastAPI backend with modular API routes (settings, knowledge, projects, MCP management)
- **archon/mcp**: MCP protocol server with 14 tools (7 RAG + 7 Project tools)
- **archon/agents**: PydanticAI agents for document processing, RAG queries, and code generation
- **dmac/client**: Resilient HTTP client with auth token support and offline JSON fallback
- **mcp-stub**: Lightweight local MCP server for integration testing and development

**Data Layer**:
- **Supabase**: PostgreSQL with vector extensions for embeddings and full-text search
- **Knowledge Base**: `archon_sources`, `archon_crawled_pages`, `archon_code_examples` tables
- **Project Management**: `archon_projects`, `archon_tasks`, `archon_document_versions` tables
- **Configuration**: `archon_settings` table with encrypted credentials and feature flags

**Integration Points**:
- **MCP Protocol**: SSE transport on port 8051 for AI client connections
- **HTTP APIs**: RESTful endpoints with Socket.IO for real-time updates
- **Service Discovery**: Automatic MCP URL resolution with Docker/localhost fallback
- **Authentication**: Bearer token auth with service role and authenticated user policies

**Utilities**:
- **Logging**: Pydantic Logfire integration with custom FastAPI middleware
- **Testing**: pytest fixtures, integration test harnesses, offline replay capabilities
- **Scripts**: PowerShell automation for environment setup and container management
- **Documentation**: Technical docs, ADRs, and interactive API reference

**Module Dependencies**:
```
Dmac Client → Archon MCP → Archon Server → Supabase
AI Clients → MCP Protocol → HTTP APIs → Service Layer → Database
Agent Services → MCP Client → Server APIs → Business Logic
```

---

## Layer 3: Integration Guide

**API Endpoints**:
- **MCP Server**: `http://localhost:8051/sse` - SSE transport for AI clients
- **Server API**: `http://localhost:8080/api/` - REST endpoints for all operations
- **Health Check**: `/health`, `/api/health` - Service availability monitoring
- **Knowledge**: `/api/knowledge-items/`, `/api/rag/` - Document and search operations
- **Projects**: `/api/projects/`, `/api/tasks/` - Project and task management
- **Settings**: `/api/settings/` - Configuration and credential management

**Configuration Files**:
- `A:\Projects\Archon\.env` - Supabase credentials and feature flags
- `A:\Projects\Archon\docker-compose.yml` - Container orchestration
- `A:\Projects\Dmac-alt\pyproject.toml` - Python project configuration
- `A:\Projects\.github\workflows\` - CI/CD pipeline definitions

**External Integrations**:
- **Supabase**: Hosted PostgreSQL with vector search capabilities
- **OpenAI**: Embeddings (text-embedding-3-small) and language models
- **GitHub**: Repository management, CI/CD workflows, issue tracking
- **Docker**: Container runtime for Archon services

**Workflows**:
1. **MCP Client Connection**: AI client → SSE transport → MCP tools → HTTP APIs
2. **Knowledge Ingestion**: Web crawling → Document chunking → Vector embeddings → Storage
3. **RAG Queries**: Query → Embedding → Vector search → Reranking → Response
4. **Project Automation**: Task creation → Agent processing → Code generation → Validation

**Interface Definitions**:
- **MCP Protocol**: JSON-RPC over SSE with 14 standardized tools
- **HTTP Client**: Retry patterns, auth headers, timeout handling
- **Database Schema**: Foreign key constraints, RLS policies, vector indexes

---

## Layer 4: Extension Points

**Design Patterns**:
- **Service Layer Pattern**: Clear separation between API routes and business logic
- **MCP Adapter Pattern**: Protocol translation from MCP to HTTP APIs
- **Factory Pattern**: Service discovery and client instantiation
- **Observer Pattern**: Socket.IO for real-time progress updates
- **Strategy Pattern**: Multiple embedding models and search algorithms

**Extension Points**:
- **MCP Tools**: Add new tools in `archon/mcp/modules/` following existing patterns
- **Agent Types**: Extend PydanticAI agents for specialized code generation tasks
- **Search Strategies**: Implement new RAG algorithms in service layer
- **Authentication**: Plugin additional auth providers via settings table
- **Transport Layers**: Add stdio MCP transport alongside existing SSE

**Customization Areas**:
- **Embedding Models**: Configure via `EMBEDDING_MODEL` setting (currently text-embedding-3-small)
- **LLM Providers**: Support OpenAI, Ollama, Google via `LLM_PROVIDER` setting
- **Search Parameters**: Batch sizes, worker counts, and performance tuning via settings
- **UI Themes**: Frontend customization through project metadata
- **Code Templates**: Extend document builders with custom schema patterns

**Plugin Architecture**:
- **Settings-Driven**: All features controlled via `archon_settings` table
- **Hot-Reload**: Configuration changes apply without restart
- **Module Loading**: Dynamic import of agent modules and MCP tools
- **Environment Aware**: Automatic Docker vs localhost detection

**Recent Changes**:
- Migrated from local Supabase to hosted instance for reliability
- Enhanced Dmac client with offline JSON fallback for resilient testing
- Implemented comprehensive code quality pipeline with mypy strict mode
- Added performance optimization settings for batch processing and embedding generation
- Disabled Claude Code action per user preference while maintaining workflow structure

---

*Byterover handbook optimized for agent navigation and human developer onboarding*
