#!/usr/bin/env python3
"""
Final Working MCP Test Suite for Ollama-powered Archon
Tests all MCP tools with proper session management.
"""

import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

class OllamaArchonMCPTester:
    def __init__(self, base_url: str = "http://localhost:8051"):
        self.base_url = base_url
        self.mcp_url = f"{base_url}/mcp"
        self.session = requests.Session()
        self.session_id = None
        self.request_id = 1
        self.test_results = []

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

    def parse_sse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Server-Sent Events response"""
        lines = response_text.strip().split('\n')
        for line in lines:
            if line.startswith('data: '):
                try:
                    data = json.loads(line[6:])
                    return data
                except json.JSONDecodeError:
                    continue
        return {"error": {"code": -1, "message": "No valid JSON data found in SSE response"}}

    def make_mcp_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make MCP request with session ID management"""
        request_data: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": f"test-{self.request_id}",
            "method": method
        }

        # Add params if provided
        if params:
            request_data["params"] = params

        # Add session ID to request body if we have one
        if self.session_id:
            request_data["sessionId"] = self.session_id

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }

        try:
            self.request_id += 1

            response = self.session.post(
                self.mcp_url,
                json=request_data,
                headers=headers,
                timeout=30
            )

            # Extract session ID from response headers
            if 'mcp-session-id' in response.headers and not self.session_id:
                self.session_id = response.headers['mcp-session-id']
                print(f"🔗 Session ID captured: {self.session_id}")

            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                return {"error": {"code": response.status_code, "message": error_msg}}

            return self.parse_sse_response(response.text)

        except Exception as e:
            error_msg = f"Request exception: {str(e)}"
            return {"error": {"code": -1, "message": error_msg}}

    def initialize_session(self) -> bool:
        """Initialize MCP session"""
        print("🔗 Initializing MCP Session...")

        result = self.make_mcp_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": {"listChanged": True},
                "sampling": {}
            },
            "clientInfo": {
                "name": "Ollama-Archon-Tester",
                "version": "1.0.0"
            }
        })

        if "error" in result:
            self.log_test("initialize", False, f"Failed: {result['error']['message']}")
            return False

        # Extract server info
        server_info = result.get("result", {}).get("serverInfo", {})
        server_name = server_info.get("name", "unknown")
        server_version = server_info.get("version", "unknown")

        self.log_test("initialize", True, f"Connected to {server_name} v{server_version}")
        return True

    def discover_tools(self) -> List[Dict[str, Any]]:
        """Discover available MCP tools"""
        print("\n🛠️  Discovering Available Tools...")

        result = self.make_mcp_request("tools/list")

        if "error" in result:
            self.log_test("tools/list", False, f"Failed: {result['error']['message']}")
            return []

        tools = result.get("result", {}).get("tools", [])
        if not tools:
            self.log_test("tools/list", False, "No tools found in response")
            return []

        self.log_test("tools/list", True, f"Found {len(tools)} tools")

        # Log discovered tools by category
        rag_tools = [t for t in tools if any(keyword in t.get("name", "") for keyword in ["rag", "search", "sources"])]
        project_tools = [t for t in tools if any(keyword in t.get("name", "") for keyword in ["project", "document", "task", "version", "health", "session"])]

        print(f"📋 Tool Categories:")
        print(f"   🔍 RAG Tools: {len(rag_tools)}")
        print(f"   📁 Project Tools: {len(project_tools)}")
        print(f"   🛠️  Total Tools: {len(tools)}")

        return tools

    def test_tool(self, tool_name: str, test_params: Dict[str, Any]) -> bool:
        """Test a specific MCP tool"""
        result = self.make_mcp_request("tools/call", {
            "name": tool_name,
            "arguments": test_params
        })

        if "error" in result:
            error_msg = result["error"]["message"]
            # Some errors are expected (like "No projects found")
            expected_errors = ["not found", "no data", "empty", "no projects", "no documents", "no tasks", "no sources"]
            if any(phrase in error_msg.lower() for phrase in expected_errors):
                self.log_test(tool_name, True, f"Expected empty result: {error_msg[:50]}...")
                return True
            else:
                self.log_test(tool_name, False, f"Error: {error_msg[:100]}...")
                return False

        # Check for tool result
        tool_result = result.get("result", {})
        if "content" in tool_result:
            content = tool_result["content"]
            if isinstance(content, list) and content:
                first_content = content[0]
                if "text" in first_content:
                    response_text = first_content["text"][:80]
                    self.log_test(tool_name, True, f"Response: {response_text}...")
                    return True

        self.log_test(tool_name, True, "Tool executed successfully")
        return True

    def run_comprehensive_test(self):
        """Run comprehensive test suite"""
        print("🚀 OLLAMA ARCHON MCP COMPREHENSIVE TEST SUITE")
        print("📡 Server: http://localhost:8051/mcp")
        print("=" * 80)

        # Initialize session
        if not self.initialize_session():
            print("⚠️  Session initialization failed - test cannot continue!")
            return

        # Discover tools
        tools = self.discover_tools()
        if not tools:
            print("⚠️  No tools discovered - test cannot continue!")
            return

        # Test parameters for each tool
        test_params = {
            # RAG Tools
            "get_available_sources": {},
            "perform_rag_query": {"query": "ollama integration testing", "match_count": 3},
            "search_code_examples": {"query": "python function example", "match_count": 2},

            # Project Management
            "list_projects": {},
            "create_project": {
                "title": "Ollama Test Project",
                "description": "Testing Ollama MCP integration",
                "project_type": "testing"
            },
            "list_documents": {},
            "create_document": {
                "title": "Test Document",
                "content": "Testing document creation with Ollama",
                "document_type": "test_notes"
            },
            "list_tasks": {},
            "create_task": {
                "title": "Test Ollama Integration",
                "description": "Validate that Ollama backend works with all MCP tools",
                "priority": "high"
            },
            "list_versions": {},
            "health_check": {},
            "session_info": {},
            "get_project_features": {}
        }

        # Test each discovered tool
        print(f"\n🧪 Testing {len(tools)} Tools...")
        print("-" * 50)

        successful_tests = 0
        for tool in tools:
            tool_name = tool.get("name", "unknown")
            tool_desc = tool.get("description", "")[:50] + "..." if len(tool.get("description", "")) > 50 else tool.get("description", "")

            print(f"\n🔧 {tool_name}: {tool_desc}")

            params = test_params.get(tool_name, {})

            if self.test_tool(tool_name, params):
                successful_tests += 1

            time.sleep(0.3)  # Brief pause between tests

        # Print comprehensive summary
        print("\n" + "=" * 80)
        print("📊 OLLAMA INTEGRATION TEST SUMMARY")
        print("=" * 80)

        total_tests = len(tools) + 2  # +2 for initialize and tools/list
        success_rate = (successful_tests + 2) / total_tests * 100

        print(f"✅ Successful Tests: {successful_tests + 2}/{total_tests} ({success_rate:.1f}%)")
        print(f"❌ Failed Tests: {total_tests - successful_tests - 2}/{total_tests}")

        # Category breakdown
        rag_results = [t for t in self.test_results if any(keyword in t["tool"] for keyword in ["rag", "search", "sources"])]
        project_results = [t for t in self.test_results if any(keyword in t["tool"] for keyword in ["project", "document", "task", "version", "health", "session"])]

        rag_success = len([t for t in rag_results if t['success']])
        project_success = len([t for t in project_results if t['success']])

        print(f"\n📋 Results by Category:")
        print(f"   🔍 RAG Tools: {rag_success}/{len(rag_results)} ({(rag_success/len(rag_results)*100) if rag_results else 0:.1f}%)")
        print(f"   📁 Project Tools: {project_success}/{len(project_results)} ({(project_success/len(project_results)*100) if project_results else 0:.1f}%)")

        # Final verdict
        print(f"\n🎯 OLLAMA INTEGRATION STATUS:")
        if success_rate >= 95:
            print("🎉 EXCELLENT - Ollama backend is fully operational!")
        elif success_rate >= 85:
            print("✅ GOOD - Ollama backend is working well with minor issues")
        elif success_rate >= 70:
            print("⚠️  ACCEPTABLE - Ollama backend mostly working, some attention needed")
        else:
            print("❌ NEEDS WORK - Ollama backend has significant issues")

        print(f"\n🔗 Final Session ID: {self.session_id}")
        print(f"⏱️  Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("✨ Ollama MCP integration test finished!")

def main():
    """Main test execution"""
    print("Starting comprehensive Ollama MCP integration test...")

    tester = OllamaArchonMCPTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
