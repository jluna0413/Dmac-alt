"""
Byterover MCP Client for Local Memory Mirror
Connects to existing Byterover MCP SSE endpoint for data synchronization
"""

import asyncio
import json
import time
import logging
from typing import Optional, Dict, List, Any, Callable
from datetime import datetime
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

from ...core.database import get_database_manager
from ...core.memory import get_memory_manager

logger = logging.getLogger(__name__)

class ByteroverMCPClient:
    """MCP client for Byterover synchronization using SSE"""

    def __init__(self, sse_url: str = "https://mcp.byterover.dev/sse?machineId=1f08699e-fcad-60d0-ad89-2ad5689b7a52"):
        self.sse_url = sse_url
        self.db = get_database_manager()
        self.memory = get_memory_manager()
        self.session = None
        self.connected = False
        self.last_sync = 0
        self.available_tools = []

    def connect(self) -> bool:
        """Establish connection to Byterover MCP server"""
        try:
            logger.info(f"Connecting to Byterover MCP: {self.sse_url}")

            # Test connection with a simple request
            response = requests.get(self.sse_url.replace('/sse', '/health'), timeout=10)

            if response.status_code == 200:
                self.connected = True
                logger.info("✅ Successfully connected to Byterover MCP")
                self._fetch_tool_list()
                return True
            else:
                logger.error(f"❌ Byterover MCP health check failed: HTTP {response.status_code}")
                return False

        except (ConnectionError, Timeout, RequestException) as e:
            logger.error(f"❌ Failed to connect to Byterover MCP: {e}")
            self.connected = False
            return False

    def _fetch_tool_list(self):
        """Fetch available tools from Byterover MCP"""
        try:
            # Attempt to get tools list via HTTP POST to MCP endpoint
            headers = {'Content-Type': 'application/json'}
            payload = {
                "method": "tools/list",
                "jsonrpc": "2.0",
                "id": 1
            }

            # Try different endpoints
            endpoints = [
                self.sse_url.replace('/sse', '/jsonrpc'),
                self.sse_url.replace('/sse', '/rpc'),
                "http://127.0.0.1:8054/mcp"  # Local Archon fallback
            ]

            for endpoint in endpoints:
                try:
                    response = requests.post(endpoint, headers=headers, json=payload, timeout=10)

                    if response.status_code == 200:
                        result = response.json()
                        if 'result' in result and 'tools' in result['result']:
                            self.available_tools = result['result']['tools']
                            logger.info(f"✅ Retrieved {len(self.available_tools)} tools from Byterover MCP")
                            break

                except RequestException:
                    continue

            if not self.available_tools:
                logger.warning("⚠️ Could not fetch tool list, using fallback tool definitions")
                self._set_fallback_tools()

        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch tool list: {e}, using fallback")
            self._set_fallback_tools()

    def _set_fallback_tools(self):
        """Set fallback tools based on MCP configuration"""
        self.available_tools = [
            {
                "name": "perform_rag_query",
                "description": "Query knowledge base using RAG",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "search_code_examples",
                "description": "Search for code examples",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Code search query"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_available_sources",
                "description": "Get available knowledge sources",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "list_projects",
                "description": "List available projects",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "list_tasks",
                "description": "List project tasks",
                "inputSchema": {"type": "object", "properties": {}}
            }
        ]

    async def sync_knowledge_base(self) -> Dict[str, Any]:
        """Sync knowledge base from Byterover MCP"""
        if not self.connected:
            return {"success": False, "error": "Not connected to Byterover MCP"}

        try:
            sync_results = await self._perform_knowledge_sync()
            self.last_sync = datetime.now().timestamp()

            # Update sync state
            self.db.update_sync_state('last_byterover_sync', str(self.last_sync))

            return {
                "success": True,
                "sources_synced": sync_results.get('sources', 0),
                "entries_added": sync_results.get('entries_added', 0),
                "last_sync": self.last_sync
            }

        except Exception as e:
            logger.error(f"❌ Knowledge base sync failed: {e}")
            return {"success": False, "error": str(e)}

    async def _perform_knowledge_sync(self) -> Dict[str, Any]:
        """Perform the actual knowledge synchronization"""
        sync_stats = {"sources": 0, "entries_added": 0}

        try:
            # Get available sources
            sources = await self._fetch_available_sources()

            for source in sources:
                entries = await self._sync_source(source)
                sync_stats["sources"] += 1
                sync_stats["entries_added"] += len(entries)

                logger.info(f"Synced {len(entries)} entries from source: {source.get('name', source.get('id', 'unknown'))}")

            # Sync other data types
            await self._sync_projects(sync_stats)
            await self._sync_tasks(sync_stats)

        except Exception as e:
            logger.error(f"Knowledge sync error: {e}")

        return sync_stats

    async def _fetch_available_sources(self) -> List[Dict[str, Any]]:
        """Fetch available knowledge sources from Byterover"""
        try:
            result = await self._call_tool("get_available_sources", {})
            return result.get("sources", []) if result else []
        except Exception as e:
            logger.warning(f"Failed to fetch sources: {e}")
            return []

    async def _sync_source(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Sync content from a specific source"""
        entries = []

        try:
            source_id = source.get('id', source.get('name', 'unknown'))

            # Query for content from this source
            query_result = await self._call_tool("perform_rag_query", {
                "query": f"source:{source_id}",
                "limit": 50
            })

            if query_result and 'results' in query_result:
                for item in query_result['results']:
                    if isinstance(item, dict):
                        # Create memory entry
                        memory_entry = {
                            'content': item.get('content', item.get('text', str(item))),
                            'content_type': 'knowledge',
                            'agent_id': 'byterover_sync',
                            'source': 'byterover',
                            'tags': [f"source:{source_id}"],
                            'metadata': {
                                'source_id': source_id,
                                'source_name': source.get('name'),
                                'rag_score': item.get('score'),
                                'sync_timestamp': datetime.now().isoformat()
                            }
                        }

                        # Store in local mirror (remove source parameter, put in metadata)
                        memory_entry_copy = memory_entry.copy()
                        memory_entry_copy.pop('source', None)  # Remove source from kwargs
                        if 'metadata' not in memory_entry_copy:
                            memory_entry_copy['metadata'] = {}
                        memory_entry_copy['metadata']['source'] = 'byterover'

                        self.memory.store_memory(**memory_entry_copy)
                        entries.append(memory_entry)

        except Exception as e:
            logger.error(f"Failed to sync source {source_id}: {e}")

        return entries

    async def _sync_projects(self, stats: Dict[str, Any]):
        """Sync project information from Byterover"""
        try:
            projects = await self._call_tool("list_projects", {})

            if projects and 'projects' in projects:
                for project in projects['projects']:
                    if isinstance(project, dict):
                        # Store as project knowledge
                        project_content = f"Project: {project.get('name', 'Unknown')}\n\nDescription: {project.get('description', 'No description')}"
                        self.memory.store_memory(
                            content=project_content,
                            content_type='project',
                            agent_id='byterover_sync',
                            tags=['project', f"project:{project.get('id')}"],
                            metadata={'project_data': project, 'source': 'byterover'}
                        )

        except Exception as e:
            logger.warning(f"Failed to sync projects: {e}")

    async def _sync_tasks(self, stats: Dict[str, Any]):
        """Sync task information from Byterover"""
        try:
            tasks = await self._call_tool("list_tasks", {})

            if tasks and 'tasks' in tasks:
                for task in tasks['tasks']:
                    if isinstance(task, dict):
                        task_content = f"Task: {task.get('description', 'No description')}\n\nStatus: {task.get('status', 'unknown')}"
                        self.memory.store_memory(
                            content=task_content,
                            content_type='task',
                            agent_id='byterover_sync',
                            tags=['task', f"status:{task.get('status')}"],
                            metadata={'task_data': task, 'source': 'byterover'}
                        )

        except Exception as e:
            logger.warning(f"Failed to sync tasks: {e}")

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call a tool via Byterover MCP"""
        try:
            # Find tool definition
            tool_def = next((t for t in self.available_tools if t['name'] == tool_name), None)
            if not tool_def:
                logger.warning(f"Tool not available: {tool_name}")
                return None

            # Make HTTP call to JSON-RPC endpoint
            headers = {'Content-Type': 'application/json'}
            payload = {
                "method": "tools/call",
                "jsonrpc": "2.0",
                "id": 2,
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }

            # Try multiple endpoints
            endpoints = [
                self.sse_url.replace('/sse', '/jsonrpc'),
                self.sse_url.replace('/sse', '/rpc'),
                "http://127.0.0.1:8054/mcp"  # Local fallback
            ]

            for endpoint in endpoints:
                try:
                    response = requests.post(endpoint, headers=headers, json=payload, timeout=30)

                    if response.status_code == 200:
                        result = response.json()
                        if 'result' in result:
                            return result['result']
                        elif 'error' in result:
                            logger.warning(f"Tool call error for {tool_name}: {result['error']}")
                            return None

                except RequestException as e:
                    logger.debug(f"Endpoint {endpoint} failed: {e}")
                    continue

            logger.warning(f"All endpoints failed for tool: {tool_name}")
            return None

        except Exception as e:
            logger.error(f"Tool call failed for {tool_name}: {e}")
            return None

    def get_sync_status(self) -> Dict[str, Any]:
        """Get synchronization status"""
        last_sync_str = self.db.get_sync_state('last_byterover_sync')
        last_sync = float(last_sync_str) if last_sync_str else 0

        return {
            "connected": self.connected,
            "last_sync": datetime.fromtimestamp(last_sync).isoformat() if last_sync else None,
            "tools_available": len(self.available_tools),
            "server_url": self.sse_url
        }

    def disconnect(self):
        """Disconnect from Byterover MCP"""
        self.connected = False
        self.session = None
        logger.info("Disconnected from Byterover MCP")

# Global instance
_byterover_client = None

def get_byterover_client() -> ByteroverMCPClient:
    """Get singleton Byterover MCP client instance"""
    global _byterover_client
    if _byterover_client is None:
        _byterover_client = ByteroverMCPClient()
    return _byterover_client
