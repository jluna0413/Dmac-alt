#!/usr/bin/env python3
"""
Comprehensive MCP Tools Test Suite for Ollama-Powered Archon

Tests all 14 MCP tools available in the Archon MCP server:
- 7 RAG Tools: query, search, sources, health, session
- 7 Project Management Tools: projects, tasks, documents, versions, features

This script validates that Ollama integration maintains full MCP functionality.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, Optional

import requests

import httpx

class ArchonMCPTester:
    def __init__(self, base_url: str = "http://localhost:8051"):
        self.base_url = base_url
        self.mcp_url = f"{base_url}/mcp"
        self.session_id = f"test_session_{int(time.time())}"
        self.client = None
        self.test_results = []

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    def log_test(self, tool_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "tool": tool_name,
            "status": status,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status} {tool_name}: {details}")

    async def call_mcp_tool(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call an MCP tool via JSON-RPC over HTTP"""
        if params is None:
            params = {}

        payload = {
            "jsonrpc": "2.0",
            "id": f"test_{int(time.time())}",
            "method": f"tools/call",
            "params": {
                "name": method,
                "arguments": params
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "X-Session-ID": self.session_id
        }

        try:
            if not self.client:
                return {"error": {"code": -1, "message": "HTTP client not initialized"}}

            response = await self.client.post(self.mcp_url, json=payload, headers=headers)

            if response.status_code == 200:
                # Handle SSE response
                if response.headers.get("content-type", "").startswith("text/event-stream"):
                    # Parse SSE data
                    lines = response.text.strip().split('\n')
                    for line in lines:
                        if line.startswith('data: '):
                            try:
                                return json.loads(line[6:])
                            except json.JSONDecodeError:
                                continue
                    return {"error": {"code": -1, "message": "No valid SSE data found"}}
                else:
                    return response.json()
            else:
                return {
                    "error": {
                        "code": response.status_code,
                        "message": response.text
                    }
                }
        except (requests.RequestException, ValueError, KeyError, TypeError) as e:
            return {
                "error": {
                    "code": -1,
                    "message": str(e)
                }
            }

    async def test_health_check(self):
        """Test: health_check tool"""
        result = await self.call_mcp_tool("health_check")
        success = "error" not in result and "health" in str(result).lower()
        self.log_test("health_check", success, f"Response: {str(result)[:100]}...")

    async def test_session_info(self):
        """Test: session_info tool"""
        result = await self.call_mcp_tool("session_info")
        success = "error" not in result
        self.log_test("session_info", success, f"Response: {str(result)[:100]}...")

    # RAG Tools Tests
    async def test_get_available_sources(self):
        """Test: get_available_sources tool"""
        result = await self.call_mcp_tool("get_available_sources")
        success = "error" not in result and ("sources" in str(result) or "success" in str(result))
        self.log_test("get_available_sources", success, f"Response: {str(result)[:100]}...")

    async def test_perform_rag_query(self):
        """Test: perform_rag_query tool"""
        params = {
            "query": "What is MCP protocol?",
            "match_count": 3
        }
        result = await self.call_mcp_tool("perform_rag_query", params)
        success = "error" not in result and ("results" in str(result) or "success" in str(result))
        self.log_test("perform_rag_query", success, f"Query: '{params['query']}' - Response: {str(result)[:100]}...")

    async def test_search_code_examples(self):
        """Test: search_code_examples tool"""
        params = {
            "query": "FastAPI endpoint",
            "match_count": 3
        }
        result = await self.call_mcp_tool("search_code_examples", params)
        success = "error" not in result and ("results" in str(result) or "success" in str(result))
        self.log_test("search_code_examples", success, f"Query: '{params['query']}' - Response: {str(result)[:100]}...")

    # Project Management Tools Tests
    async def test_list_projects(self):
        """Test: list_projects tool"""
        result = await self.call_mcp_tool("list_projects")
        success = "error" not in result and ("projects" in str(result) or "success" in str(result))
        self.log_test("list_projects", success, f"Response: {str(result)[:100]}...")

    async def test_create_project(self):
        """Test: create_project tool"""
        params = {
            "title": f"Test Project {int(time.time())}",
            "description": "Test project created by MCP test suite"
        }
        result = await self.call_mcp_tool("create_project", params)
        success = "error" not in result and ("success" in str(result) or "project" in str(result))
        self.log_test("create_project", success, f"Project: '{params['title']}' - Response: {str(result)[:100]}...")

        # Store project ID for other tests
        if success and "result" in str(result):
            try:
                data = json.loads(str(result)) if isinstance(result, str) else result
                if "result" in data and "content" in data["result"]:
                    content_data = json.loads(data["result"]["content"])
                    if "project_id" in content_data:
                        self.test_project_id = content_data["project_id"]
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

    async def test_get_project(self):
        """Test: get_project tool"""
        # Use a test project ID (this may fail if no projects exist)
        params = {"project_id": getattr(self, 'test_project_id', '1')}
        result = await self.call_mcp_tool("get_project", params)
        success = "error" not in result or "not found" in str(result).lower()
        self.log_test("get_project", success, f"Project ID: {params['project_id']} - Response: {str(result)[:100]}...")

    async def test_list_tasks(self):
        """Test: list_tasks tool"""
        result = await self.call_mcp_tool("list_tasks")
        success = "error" not in result and ("tasks" in str(result) or "success" in str(result))
        self.log_test("list_tasks", success, f"Response: {str(result)[:100]}...")

    async def test_create_task(self):
        """Test: create_task tool"""
        params = {
            "title": f"Test Task {int(time.time())}",
            "description": "Test task created by MCP test suite",
            "project_id": getattr(self, 'test_project_id', None)
        }
        if not params["project_id"]:
            del params["project_id"]  # Remove if no project available

        result = await self.call_mcp_tool("create_task", params)
        success = "error" not in result and ("success" in str(result) or "task" in str(result))
        self.log_test("create_task", success, f"Task: '{params['title']}' - Response: {str(result)[:100]}...")

    async def test_list_documents(self):
        """Test: list_documents tool"""
        result = await self.call_mcp_tool("list_documents")
        success = "error" not in result and ("documents" in str(result) or "success" in str(result))
        self.log_test("list_documents", success, f"Response: {str(result)[:100]}...")

    async def test_create_document(self):
        """Test: create_document tool"""
        params = {
            "title": f"Test Document {int(time.time())}",
            "content": "This is a test document created by MCP test suite",
            "document_type": "note"
        }
        result = await self.call_mcp_tool("create_document", params)
        success = "error" not in result and ("success" in str(result) or "document" in str(result))
        self.log_test("create_document", success, f"Document: '{params['title']}' - Response: {str(result)[:100]}...")

    async def test_list_versions(self):
        """Test: list_versions tool"""
        result = await self.call_mcp_tool("list_versions")
        success = "error" not in result and ("versions" in str(result) or "success" in str(result))
        self.log_test("list_versions", success, f"Response: {str(result)[:100]}...")

    async def test_get_project_features(self):
        """Test: get_project_features tool"""
        params = {"project_id": getattr(self, 'test_project_id', '1')}
        result = await self.call_mcp_tool("get_project_features", params)
        success = "error" not in result or "not found" in str(result).lower()
        self.log_test("get_project_features", success, f"Project ID: {params['project_id']} - Response: {str(result)[:100]}...")

    async def run_all_tests(self):
        """Run all MCP tool tests"""
        print(f"🚀 Starting Archon MCP Tools Test Suite with Ollama")
        print(f"📡 MCP Server: {self.mcp_url}")
        print(f"🔗 Session ID: {self.session_id}")
        print("=" * 70)

        # Health & Session Tests
        print("\n🏥 Health & Session Tools:")
        await self.test_health_check()
        await self.test_session_info()

        # RAG Tools Tests
        print("\n🔍 RAG & Knowledge Base Tools:")
        await self.test_get_available_sources()
        await self.test_perform_rag_query()
        await self.test_search_code_examples()

        # Project Management Tests
        print("\n📊 Project Management Tools:")
        await self.test_list_projects()
        await self.test_create_project()
        await self.test_get_project()
        await self.test_list_tasks()
        await self.test_create_task()
        await self.test_list_documents()
        await self.test_create_document()
        await self.test_list_versions()
        await self.test_get_project_features()

        # Results Summary
        print("\n" + "=" * 70)
        print("📋 TEST RESULTS SUMMARY")
        print("=" * 70)

        passed = sum(1 for r in self.test_results if r["success"])
        total = len(self.test_results)
        pass_rate = (passed / total) * 100 if total > 0 else 0

        print(f"✅ Passed: {passed}/{total} ({pass_rate:.1f}%)")
        print(f"❌ Failed: {total - passed}/{total}")

        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Ollama-powered Archon MCP is fully operational!")
        else:
            print(f"\n⚠️  {total - passed} tests failed. Check details above.")

        print("\n📊 Tool Categories Status:")
        rag_tools = [r for r in self.test_results if any(tool in r["tool"] for tool in ["rag", "sources", "search", "health", "session"])]
        project_tools = [r for r in self.test_results if any(tool in r["tool"] for tool in ["project", "task", "document", "version", "feature"])]

        rag_passed = sum(1 for r in rag_tools if r["success"])
        project_passed = sum(1 for r in project_tools if r["success"])

        print(f"🔍 RAG Tools: {rag_passed}/{len(rag_tools)} passed")
        print(f"📊 Project Tools: {project_passed}/{len(project_tools)} passed")

        return {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": pass_rate,
            "results": self.test_results
        }

async def main():
    """Main test execution"""
    async with ArchonMCPTester() as tester:
        results = await tester.run_all_tests()

        # Save detailed results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"archon_mcp_test_results_{timestamp}.json"

        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n📄 Detailed results saved to: {results_file}")
        return results

if __name__ == "__main__":
    asyncio.run(main())
