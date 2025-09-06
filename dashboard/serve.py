#!/usr/bin/env python3
"""
Deep-Wiki Dashboard Server
Autonomous Coding Ecosystem - TASK-002 Implementation

This dashboard provides:
- Real-time service monitoring
- Deep-Wiki knowledge base access
- Agent performance tracking
- Ecosystem orchestration control
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Standard imports
import uvicorn
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

# Database imports
from database.models.base import get_db_session, init_db
try:
    from database.models import Project
except ImportError:
    Project = None
    logger.warning("Project model not available")

# MCP imports
try:
    from Archon.python.src.mcp_server.mcp_server import MCP_SERVER_PORT
except ImportError:
    MCP_SERVER_PORT = 8051

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Deep-Wiki Dashboard",
    description="Autonomous Coding Ecosystem Dashboard with Knowledge Base",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Templates and static files
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Global state
service_status = {}
last_health_check = None

# Request/Response Models
class ServiceStatus(BaseModel):
    name: str
    status: str  # 'healthy', 'unhealthy', 'unknown'
    url: Optional[str] = None
    last_checked: Optional[datetime] = None
    details: Optional[Dict[str, Any]] = None

class KnowledgeEntry(BaseModel):
    id: str
    title: str
    content: str
    category: str
    tags: List[str]
    source: str
    confidence_score: float = 0.0
    created_at: datetime

class AgentStatus(BaseModel):
    name: str
    status: str
    tasks_completed: int = 0
    active_tasks: int = 0
    performance_score: float = 0.0
    last_activity: Optional[datetime] = None

# Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page with Deep-Wiki interface"""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Deep-Wiki Dashboard",
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ecosystem_title": "Autonomous Coding Ecosystem v1.0"
        }
    )

@app.get("/api/health")
async def health_check():
    """Dashboard health endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "deep-wiki-dashboard",
        "version": "1.0.0"
    }

@app.get("/api/ecosystem/status")
async def get_ecosystem_status():
    """Get overall ecosystem status"""
    global service_status, last_health_check

    # Check MCP server health
    mcp_status = await check_mcp_health()

    # Check other services (stub for now)
    services = [
        {"name": "MCP Server", "url": f"http://localhost:{MCP_SERVER_PORT}", "status": mcp_status},
        {"name": "Archon API", "url": "http://localhost:8000", "status": "unknown"},
        {"name": "MCP Control", "url": "http://localhost:8052", "status": "unknown"},
        {"name": "Knowledge Base", "url": "http://localhost:5432", "status": "healthy"},
    ]

    return {
        "timestamp": datetime.now().isoformat(),
        "services": services,
        "overall_status": "healthy" if all(s["status"] == "healthy" for s in services) else "degraded"
    }

@app.get("/api/knowledge/search")
async def search_knowledge(q: str = "", category: str = "", limit: int = 20):
    """Search knowledge base entries"""
    # This is a stub - in real implementation, this would query the knowledge base
    knowledge_entries = [
        {
            "id": "kb_001",
            "title": "MCP Server Configuration Guide",
            "content": "# MCP Server Setup\n\nThis guide covers MCP server configuration...",
            "category": "infrastructure",
            "tags": ["mcp", "server", "configuration"],
            "source": "documentation",
            "confidence_score": 0.95,
            "created_at": datetime.now().isoformat()
        },
        {
            "id": "kb_002",
            "title": "Agent Development Best Practices",
            "content": "# Agent Development Guide\n\nBest practices for developing autonomous agents...",
            "category": "development",
            "tags": ["agents", "development", "best-practices"],
            "source": "archon_docs",
            "confidence_score": 0.88,
            "created_at": datetime.now().isoformat()
        }
    ]

    if q:
        # Filter by query
        knowledge_entries = [entry for entry in knowledge_entries
                           if q.lower() in entry["title"].lower() or q.lower() in entry["content"].lower()]

    if category:
        # Filter by category
        knowledge_entries = [entry for entry in knowledge_entries if entry["category"] == category]

    return {
        "query": q,
        "category": category,
        "total_results": len(knowledge_entries),
        "results": knowledge_entries[:limit]
    }

@app.get("/api/agents/status")
async def get_agents_status():
    """Get agent performance and status"""
    # Stub data - in real implementation, this would be from database
    agents = [
        {
            "name": "Documentation Agent",
            "status": "active",
            "tasks_completed": 45,
            "active_tasks": 2,
            "performance_score": 0.92,
            "last_activity": datetime.now().isoformat()
        },
        {
            "name": "Testing Agent",
            "status": "active",
            "tasks_completed": 67,
            "active_tasks": 1,
            "performance_score": 0.87,
            "last_activity": datetime.now().isoformat()
        },
        {
            "name": "Code Generation Agent",
            "status": "idle",
            "tasks_completed": 23,
            "active_tasks": 0,
            "performance_score": 0.94,
            "last_activity": datetime.now().isoformat()
        }
    ]

    return {
        "timestamp": datetime.now().isoformat(),
        "total_agents": len(agents),
        "active_agents": len([a for a in agents if a["status"] == "active"]),
        "agents": agents
    }

@app.get("/api/projects")
async def get_projects():
    """Get project listings from database"""
    try:
        if Project is None:
            return {"projects": [], "total": 0}

        session = get_db_session()
        projects = session.query(Project).all()

        project_list = []
        for project in projects:
            project_list.append(project.to_dict())

        session.close()
        return {"projects": project_list, "total": len(project_list)}

    except Exception as e:
        logger.error(f"Error fetching projects: {e}")
        return {"projects": [], "total": 0}

# Helper functions
async def check_mcp_health() -> str:
    """Check MCP server health"""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://localhost:{MCP_SERVER_PORT}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    return "healthy"
                else:
                    return "unhealthy"
    except Exception:
        return "unreachable"

# Lifecycle events
@app.on_event("startup")
async def startup_event():
    """Initialize dashboard on startup"""
    logger.info("🚀 Deep-Wiki Dashboard starting...")

    # Initialize database
    try:
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")

    logger.info("✅ Deep-Wiki Dashboard ready!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Deep-Wiki Dashboard shutting down...")

if __name__ == "__main__":
    # Run the dashboard server
    uvicorn.run(
        "serve:app",
        host="0.0.0.0",
        port=3000,
        reload=True,
        log_level="info"
    )
