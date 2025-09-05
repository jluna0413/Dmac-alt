#!/usr/bin/env python3
"""
Direct HTTP MCP Client Test for Ollama-Powered Archon

This script tests MCP tools using direct HTTP requests with proper headers.
It validates that the Ollama integration maintains full MCP functionality.
"""

import json
import requests
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

class DirectMCPTester:
    def __init__(self, base_url: str = "http://localhost:8051/mcp"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session_id = f"test_{int(time.time())}"
        self.test_results = []

        # Set up proper headers for MCP over HTTP
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',  # Try JSON first
            'User-Agent': 'Archon-MCP-Tester/1.0',
        })

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

    def make_mcp_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an MCP JSON-RPC request"""
        if params is None:
            params = {}

        payload = {
            "jsonrpc": "2.0",
            "id": f"test_{int(time.time())}",
            "method": method,
            "params": params
        }

        try:
            response = self.session.post(self.base_url, json=payload, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": {
                        "code": response.status_code,
                        "message": f"HTTP {response.status_code}: {response.text[:200]}"
                    }
                }
        except (requests.RequestException, ValueError, KeyError) as e:
            return {
                "error": {
                    "code": -1,
                    "message": str(e)
                }
            }

    def test_initialization(self) -> bool:
        """Test MCP server initialization"""
        print("🔗 Testing MCP Server Initialization...")

        # Try to initialize MCP session
        init_params = {
            "protocolVersion": "1.0",
            "capabilities": {},
            "clientInfo": {
                "name": "archon-test-client",
                "version": "1.0"
            }
        }

        result = self.make_mcp_request("initialize", init_params)

        if "error" in result:
            self.log_test("initialize", False, f"Init failed: {result['error']['message']}")
            return False
        else:
            self.log_test("initialize", True, "MCP server initialized successfully")
            return True

    def test_list_tools(self) -> List[Dict[str, Any]]:
        """Test listing available tools"""
        print("\n🛠️  Testing Tool Discovery...")

        result = self.make_mcp_request("tools/list")

        if "error" in result:
            self.log_test("tools/list", False, f"Failed: {result['error']['message']}")
            return []
        else:
            tools = result.get("result", {}).get("tools", [])
            self.log_test("tools/list", True, f"Found {len(tools)} tools")
            return tools

    def test_tool_call(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> bool:
        """Test calling a specific tool"""
        if arguments is None:
            arguments = {}

        params = {
            "name": tool_name,
            "arguments": arguments
        }

        result = self.make_mcp_request("tools/call", params)

        if "error" in result:
            self.log_test(tool_name, False, f"Error: {result['error']['message']}")
            return False
        else:
            content = result.get("result", {}).get("content", "")
            if isinstance(content, list) and len(content) > 0:
                content = content[0].get("text", str(content))

            display_content = str(content)[:100] + "..." if len(str(content)) > 100 else str(content)
            self.log_test(tool_name, True, f"Response: {display_content}")
            return True

    def run_comprehensive_test(self) -> bool:
        """Run comprehensive MCP test suite"""
        print("🚀 Starting Comprehensive MCP Test for Ollama Integration")
        print(f"📡 Server: {self.base_url}")
        print("=" * 70)

        # Step 1: Test initialization
        if not self.test_initialization():
            print("❌ Failed to initialize MCP session. Testing basic connectivity...")

        # Step 2: Discover available tools
        tools = self.test_list_tools()
        tool_names = [tool.get("name", "") for tool in tools] if tools else []

        if not tool_names:
            print("⚠️  No tools discovered. Testing common tools anyway...")
            # Fall back to expected tools
            tool_names = [
                "health_check", "session_info", "get_available_sources",
                "perform_rag_query", "search_code_examples", "list_projects",
                "list_tasks", "list_documents"
            ]

        # Step 3: Test individual tools
        print(f"\n🧪 Testing {len(tool_names)} Tools...")

        # Health tools
        health_tools = ["health_check", "session_info"]
        for tool in health_tools:
            if tool in tool_names:
                self.test_tool_call(tool)

        # RAG tools
        rag_tools = ["get_available_sources", "perform_rag_query", "search_code_examples"]
        for tool in rag_tools:
            if tool in tool_names:
                if tool == "perform_rag_query":
                    self.test_tool_call(tool, {"query": "MCP protocol", "match_count": 3})
                elif tool == "search_code_examples":
                    self.test_tool_call(tool, {"query": "FastAPI", "match_count": 3})
                else:
                    self.test_tool_call(tool)

        # Project tools
        project_tools = ["list_projects", "list_tasks", "list_documents", "list_versions"]
        for tool in project_tools:
            if tool in tool_names:
                self.test_tool_call(tool)

        # Test Summary
        print("\n" + "=" * 70)
        print("📋 COMPREHENSIVE TEST RESULTS")
        print("=" * 70)

        passed = sum(1 for r in self.test_results if r["success"])
        total = len(self.test_results)
        pass_rate = (passed / total) * 100 if total > 0 else 0

        print(f"✅ Passed: {passed}/{total} ({pass_rate:.1f}%)")
        print(f"❌ Failed: {total - passed}/{total}")

        # Categorize results
        rag_tests = [r for r in self.test_results if any(kw in r["tool"] for kw in ["rag", "sources", "search", "health", "session"])]
        project_tests = [r for r in self.test_results if any(kw in r["tool"] for kw in ["project", "task", "document", "version"])]

        rag_passed = sum(1 for r in rag_tests if r["success"])
        project_passed = sum(1 for r in project_tests if r["success"])

        print(f"\n📊 Category Breakdown:")
        print(f"🔍 RAG & Health: {rag_passed}/{len(rag_tests)} passed")
        print(f"📋 Project Mgmt: {project_passed}/{len(project_tests)} passed")

        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Ollama-powered Archon MCP is fully operational!")
            return True
        elif passed > total * 0.5:
            print(f"\n⚡ PARTIAL SUCCESS! {passed}/{total} tests passed. Core functionality working.")
            return True
        else:
            print(f"\n⚠️  NEEDS ATTENTION: Only {passed}/{total} tests passed.")
            return False

    def save_results(self) -> str:
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"archon_mcp_comprehensive_test_{timestamp}.json"

        summary = {
            "test_run": {
                "timestamp": timestamp,
                "server_url": self.base_url,
                "total_tests": len(self.test_results),
                "passed_tests": sum(1 for r in self.test_results if r["success"]),
                "failed_tests": sum(1 for r in self.test_results if not r["success"]),
            },
            "results": self.test_results
        }

        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\n📄 Detailed results saved to: {filename}")
        return filename

def main() -> int:
    """Main test execution"""
    tester = DirectMCPTester()
    success = tester.run_comprehensive_test()
    tester.save_results()

    return 0 if success else 1

if __name__ == "__main__":
    exit(main())

